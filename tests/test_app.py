# Copyright (c) 2026 Vidafix contributors. Licensed under MIT; see LICENSE.
import json
import threading
import unittest
from urllib.parse import urlsplit, parse_qs
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from server.app import create_app
from server.plex_api import PlexClient, PlexError, local_server


class FakePlex(BaseHTTPRequestHandler):
    calls = []
    mode = 'normal'

    def log_message(self, *args):
        pass

    def do_GET(self):
        self.calls.append((self.path, self.headers.get('X-Plex-Token')))
        if self.mode == 'unauthorized':
            self.send_response(401)
            self.end_headers()
            return
        if self.mode == 'redirect':
            self.send_response(302)
            self.send_header('Location', 'https://example.com/')
            self.end_headers()
            return
        if '/thumb/' in self.path:
            self.send_response(200)
            self.send_header('Content-Type', 'image/jpeg')
            self.end_headers()
            self.wfile.write(b'fixture-image')
            return
        if self.path == '/library/sections':
            payload = {'Directory': [
                {'key': '1', 'title': 'Movies', 'type': 'movie'},
                {'key': '2', 'title': 'Music', 'type': 'artist'},
                {'key': '3', 'title': 'TV', 'type': 'show'}]}
        else:
            items = [{'ratingKey': str(i), 'title': 'Film ' + str(i), 'type': 'movie',
                      'summary': '<script>untrusted</script>', 'thumb': '/library/metadata/1/thumb/123',
                      'art': 'https://example.com/art.jpg', 'Role': [{'tag': 'Actor'}]}
                     for i in range(1, 26)]
            if '/sections/' in self.path:
                offset = int(parse_qs(urlsplit(self.path).query).get('X-Plex-Container-Start', ['0'])[0])
                payload = {'Metadata': items[offset:offset + 20], 'totalSize': len(items)}
            else:
                payload = {'Metadata': items[:1]}
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'bad json' if self.mode == 'malformed' else json.dumps({'MediaContainer': payload}).encode())


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), FakePlex)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.plex = PlexClient('http://127.0.0.1:' + str(cls.server.server_port), 'test-secret')
        cls.client = create_app(client=cls.plex).test_client()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        FakePlex.calls.clear()
        FakePlex.mode = 'normal'

    def test_libraries_exclude_music(self):
        response = self.client.get('/api/libraries')
        self.assertEqual([x['id'] for x in response.json['libraries']], ['1', '3'])
        self.assertNotIn(b'test-secret', response.data)

    def test_twenty_posters_and_pagination(self):
        response = self.client.get('/api/library/1')
        self.assertEqual(len(response.json['items']), 20)
        self.assertIn('X-Plex-Container-Size=20', FakePlex.calls[-1][0])
        self.assertTrue(all(token == 'test-secret' for _, token in FakePlex.calls))
        self.assertEqual(response.json['items'][0]['poster'], '/art/1/thumb')
        self.assertNotIn(b'https://example.com', response.data)

    def test_music_and_invalid_library_rejected(self):
        self.assertEqual(self.client.get('/api/library/2').status_code, 404)
        self.assertEqual(self.client.get('/api/library/99').status_code, 404)

    def test_library_pagination(self):
        first = self.client.get('/api/library/1').json
        second = self.client.get('/api/library/1?offset=20').json
        self.assertEqual(first['total'], 25)
        self.assertEqual(first['next'], 20)
        self.assertIsNone(first['previous'])
        self.assertEqual([x['id'] for x in second['items']], ['21', '22', '23', '24', '25'])
        self.assertEqual(second['previous'], 0)
        self.assertIsNone(second['next'])
        empty = self.client.get('/api/library/1?offset=40').json
        self.assertEqual(empty['items'], [])
        self.assertIsNone(empty['next'])
        self.assertEqual(empty['previous'], 20)

    def test_library_rejects_invalid_offsets(self):
        for offset in ('-20', '1', 'foo', '20.0', '99999999999999999999'):
            self.assertEqual(self.client.get('/api/library/1?offset=' + offset).status_code, 400)

    def test_library_sort(self):
        for section in ('1', '3'):
            for sort, expected in (('title', 'titleSort:asc'), ('recent', 'addedAt:desc')):
                response = self.client.get('/api/library/' + section + '?sort=' + sort + '&offset=20')
                self.assertEqual(response.status_code, 200)
                query = parse_qs(urlsplit(FakePlex.calls[-1][0]).query)
                self.assertEqual(query['sort'], [expected])
                self.assertEqual(query['X-Plex-Container-Start'], ['20'])
        self.assertEqual(self.client.get('/api/library/1?sort=random').status_code, 400)

    def test_details(self):
        data = self.client.get('/api/item/1').json
        self.assertEqual(data['title'], 'Film 1')
        self.assertEqual(data['cast'], ['Actor'])

    def test_artwork_proxy(self):
        response = self.client.get('/art/1/thumb')
        self.assertEqual(response.data, b'fixture-image')
        self.assertEqual(response.mimetype, 'image/jpeg')
        self.assertIn('max-age', response.headers['Cache-Control'])

    def test_external_artwork_and_arbitrary_kinds_rejected(self):
        self.assertEqual(self.client.get('/art/1/art').status_code, 404)
        self.assertEqual(self.client.get('/art/1/anything').status_code, 404)
        self.assertFalse(any('example.com' in path for path, _ in FakePlex.calls))

    def test_errors_are_safe(self):
        for mode in ('unauthorized', 'redirect', 'malformed'):
            FakePlex.mode = mode
            response = self.client.get('/api/libraries')
            self.assertEqual(response.status_code, 502)
            self.assertIn('error', response.json)
            self.assertNotIn(b'test-secret', response.data)

    def test_missing_token(self):
        app = create_app(client=PlexClient('http://127.0.0.1:32400', ''))
        self.assertEqual(app.test_client().get('/api/libraries').status_code, 503)

    def test_network_errors(self):
        from unittest.mock import patch
        import requests
        for error, status in ((requests.Timeout(), 504), (requests.ConnectionError(), 502)):
            with patch('requests.Session.get', side_effect=error):
                self.assertEqual(self.client.get('/api/libraries').status_code, status)

    def test_frontend_and_headers(self):
        for path in ('/', '/app.js', '/navigation.js', '/styles.css', '/static/app.js', '/static/navigation.js', '/static/styles.css'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertNotIn(b'test-secret', response.data)
            self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
            response.close()

    def test_only_local_origins(self):
        for url in ('http://8.8.8.8:32400', 'https://plex.tv', 'http://127.0.0.1/path',
                    'http://user:pass@127.0.0.1', 'http://127.0.0.1?url=bad', 'ftp://127.0.0.1'):
            with self.assertRaises(ValueError):
                local_server(url)
        self.assertEqual(local_server('http://192.168.0.20:32400/'), 'http://192.168.0.20:32400')


if __name__ == '__main__':
    unittest.main()
