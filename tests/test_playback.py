# Copyright (c) 2026 Vidafix contributors. Licensed under MIT; see LICENSE.
import copy
import time
import unittest
from unittest.mock import Mock, patch

from server.app import create_app
from server.plex_api import PlexClient, PlexError


class PlaybackTests(unittest.TestCase):
    def setUp(self):
        self.plex = PlexClient('http://127.0.0.1:32400', 'private-token')
        self.item = {'ratingKey': '1', 'type': 'movie', 'librarySectionID': '1', 'duration': 120000,
                     'viewOffset': 30000, 'Media': [{'Part': [{'id': 10, 'Stream': [
                         {'id': 20, 'streamType': 2, 'displayTitle': 'English', 'selected': True},
                         {'id': 21, 'streamType': 3, 'displayTitle': 'English SDH'}]}]}]}
        self.plex.metadata = Mock(side_effect=lambda key: copy.deepcopy(self.item))
        self.plex.libraries = Mock(return_value=[{'id': '1', 'type': 'movie'}])
        app = create_app(client=self.plex)
        self.client = app.test_client()
        self.player = app.extensions['playback']
        self.player.raw = Mock(side_effect=self.raw)
        self.headers = {'X-VidPlex': '1'}

    def raw(self, path, sid, params=None, **kwargs):
        if path.endswith('start.m3u8'):
            return ('#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1000000\nsession/' + sid + '/base/index.m3u8?X-Plex-Token=private-token\n').encode(), 'application/vnd.apple.mpegurl'
        if 'index.m3u8' in path:
            return ('#EXTM3U\n#EXT-X-TARGETDURATION:10\n' + ''.join('#EXTINF:10,\n%d.ts\n' % i for i in range(12)) + '#EXT-X-ENDLIST\n').encode(), 'application/vnd.apple.mpegurl'
        if path.endswith('.ts'):
            return b'segment', 'video/mp2t'
        return b'', 'text/html'

    def start(self, **body):
        return self.client.post('/api/playback/1/start', json=body, headers=self.headers)

    def test_hls_rewrites_nested_resources_and_hides_token(self):
        result = self.start(offset=30000, audio='20', subtitle='21')
        self.assertEqual(result.status_code, 200)
        sid = result.json['session']
        master = self.client.get(result.json['url'])
        self.assertNotIn(b'private-token', master.data)
        child = self.client.get('/playback/' + sid + '/resource/0')
        self.assertIn(('/playback/' + sid + '/resource/1').encode(), child.data)
        self.assertEqual(self.client.get('/playback/' + sid + '/resource/1').data, b'segment')
        self.assertEqual(self.client.get('/playback/' + sid + '/resource/999').status_code, 404)
        start = [c for c in self.player.raw.call_args_list if c.args[0].endswith('start.m3u8')][0]
        self.assertEqual(start.args[2]['offset'], 30)
        self.assertEqual(start.args[2]['subtitles'], 'burn')
        self.assertEqual(start.args[2]['directStream'], 1)
        self.assertEqual(start.args[2]['directStreamAudio'], 1)
        self.assertEqual(start.args[2]['protocol'], 'hls')

    def test_rejects_external_and_traversing_manifests(self):
        sid = self.start().json['session']
        for uri in ('https://example.com/steal', '//evil.test/x', '../../library/metadata/1',
                    'session/%2e%2e/%2e%2e/x', 'session/x/%5c..%5cx'):
            with self.subTest(uri=uri), self.assertRaises(PlexError):
                self.player.manifest(sid, '/video/:/transcode/universal/start.m3u8', ('#EXTM3U\n' + uri).encode())
        with self.assertRaises(PlexError):
            self.player.manifest(sid, '/', b'#EXTM3U\n#EXT-X-KEY:METHOD=AES-128,URI="https://evil.test/key"')

    def test_start_validation_and_local_only(self):
        for data in ({'offset': -1}, {'offset': True}, {'offset': 120001}, {'audio': '999'}, {'subtitle': '999'}):
            self.assertEqual(self.start(**data).status_code, 400)
        self.item['librarySectionID'] = '99'
        self.assertEqual(self.start().status_code, 404)
        self.item['librarySectionID'] = '1'
        self.item['type'] = 'show'
        self.assertEqual(self.start().status_code, 400)

    def test_cross_origin_and_non_json_rejected(self):
        self.assertEqual(self.client.post('/api/playback/1/start', json={}).status_code, 403)
        self.assertEqual(self.client.post('/api/playback/1/start', json={}, headers={**self.headers, 'Origin': 'http://evil.test'}).status_code, 403)
        self.assertEqual(self.client.post('/api/playback/1/start', json=[], headers=self.headers).status_code, 400)

    def test_progress_and_stop(self):
        sid = self.start().json['session']
        url = '/api/playback/' + sid
        self.assertEqual(self.client.post(url + '/progress', json={'time': 50000, 'state': 'paused'}, headers=self.headers).status_code, 200)
        self.assertEqual(self.player.raw.call_args.args[2]['time'], 50000)
        self.assertEqual(self.client.post(url + '/progress', json={'time': -1, 'state': 'playing'}, headers=self.headers).status_code, 400)
        self.assertEqual(self.client.post(url + '/stop', json={'time': 55000}, headers=self.headers).status_code, 200)
        self.assertNotIn(sid, self.player.sessions)
        self.assertEqual(self.client.get('/playback/' + sid + '/master.m3u8').status_code, 404)

    def test_start_failure_and_abandoned_session_cleanup(self):
        self.player.raw.side_effect = PlexError('Unavailable')
        self.assertEqual(self.start().status_code, 502)
        self.assertFalse(self.player.sessions)
        self.player.raw.side_effect = self.raw
        sid = self.start().json['session']
        self.player.sessions[sid]['seen'] = time.monotonic() - 121
        self.player.reap()
        self.assertFalse(self.player.sessions)

    def test_progress_pings_and_stop_without_progress(self):
        sid = self.start().json['session']
        self.player.raw.reset_mock()
        self.player.progress(sid, {'time': 30000, 'state': 'paused'})
        self.assertTrue(any(c.args[0].endswith('/ping') for c in self.player.raw.call_args_list))
        self.player.raw.reset_mock()
        self.assertEqual(self.client.post('/api/playback/' + sid + '/stop', json={}, headers=self.headers).status_code, 200)
        self.assertFalse(any(c.args[0] == '/:/timeline' for c in self.player.raw.call_args_list))

    def test_raw_rejects_redirects_and_limits_payload(self):
        from server.playback import Playback
        player = Playback(self.plex)
        with patch('server.playback.requests.Session') as session:
            response = session.return_value.__enter__.return_value.request.return_value.__enter__.return_value
            response.status_code = 302
            with self.assertRaises(PlexError):
                player.raw('/video/:/transcode/universal/start.m3u8', 'session')
            response.status_code = 200
            response.iter_content.return_value = [b'12345']
            with self.assertRaises(PlexError):
                player.raw('/video/:/transcode/universal/start.m3u8', 'session', limit=4)
            response.iter_content.return_value = [b'123']
            response.headers = {'Content-Type': 'video/MP2T'}
            self.assertEqual(player.raw('/segment', 'session')[1], 'video/mp2t')

    def test_episode_pages_and_validation(self):
        self.item['type'] = 'show'
        self.plex.fetch = Mock(return_value={'Metadata': [
            {'ratingKey': str(i), 'type': 'episode', 'title': 'Episode', 'grandparentTitle': 'Series'}
            for i in range(21, 25)], 'totalSize': 24})
        page = self.client.get('/api/show/1/episodes?offset=20')
        self.assertEqual(page.status_code, 200)
        self.assertEqual(len(page.json['items']), 4)
        self.assertEqual(page.json['previous'], 0)
        self.assertIsNone(page.json['next'])
        self.assertEqual(self.client.get('/api/show/1/episodes?offset=1').status_code, 400)
        self.item['type'] = 'movie'
        self.assertEqual(self.client.get('/api/show/1/episodes').status_code, 400)

    def test_resume_playlist_starts_at_saved_segment(self):
        from server.playback import trim_resume_playlist
        source = '#EXTM3U\n#EXT-X-MEDIA-SEQUENCE:0\n#EXT-X-START:TIME-OFFSET=9\n'
        source += ''.join('#EXTINF:4,\n%d.ts\n' % i for i in range(4))
        source += '#EXT-X-ENDLIST\n'
        trimmed, base = trim_resume_playlist(source, 9000)
        self.assertEqual(base, 8000)
        self.assertNotIn('0.ts', trimmed)
        self.assertNotIn('1.ts', trimmed)
        self.assertIn('2.ts', trimmed)
        self.assertIn('#EXT-X-MEDIA-SEQUENCE:2', trimmed)
        self.assertIn('#EXT-X-START:TIME-OFFSET=1.000', trimmed)
        self.assertIn('#EXT-X-ENDLIST', trimmed)
        self.assertEqual(trim_resume_playlist(source, 0), (source, 0))
        self.assertEqual(trim_resume_playlist(source, 8000)[1], 8000)
        result = self.start(offset=35000).json
        self.assertEqual(result['timelineBase'], 30000)
        manifest = self.client.get(result['url']).data
        self.assertIn(b'#EXTINF:', manifest)
        self.assertNotIn(b'#EXT-X-STREAM-INF:', manifest)

    def test_options_do_not_expose_private_metadata(self):
        result = self.client.get('/api/playback/1/options')
        self.assertEqual(result.json['resume'], 30000)
        self.assertEqual(result.json['audio'][0]['label'], 'English')
        self.assertNotIn(b'private-token', result.data)
        self.assertNotIn(b'Media', result.data)



    def test_subtitle_search_opaque_and_item_bound(self):
        self.plex.fetch = Mock(return_value={'Stream': [{'key': 'provider://opaque', 'title': 'English release'}]})
        result = self.client.post('/api/playback/1/subtitles/search', json={'language': 'en'}, headers=self.headers)
        self.assertEqual(result.status_code, 200)
        self.assertNotIn('provider://', result.get_data(as_text=True))
        ident = result.json['items'][0]['id']
        self.assertEqual(self.client.post('/api/playback/2/subtitles/download', json={'id': ident}, headers=self.headers).status_code, 400)
        response = self.client.post('/api/playback/1/subtitles/download', json={'id': ident}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.player.raw.assert_called_with('/library/metadata/1/subtitles', 'subtitles', {'key': 'provider://opaque'}, method='PUT', limit=65536)
        self.player.subtitle_results[ident]['created'] -= 601
        self.assertEqual(self.client.post('/api/playback/1/subtitles/download', json={'id': ident}, headers=self.headers).status_code, 400)
        self.assertEqual(self.client.post('/api/playback/1/subtitles/search', json={'language': '../'}, headers=self.headers).status_code, 400)
        self.assertEqual(self.client.post('/api/playback/1/subtitles/search', json={}, headers={**self.headers,'Origin':'https://evil.example'}).status_code, 403)

    def test_next_episode_handles_missing_section_in_children(self):
        self.item.update(type='episode', grandparentRatingKey='9', parentIndex=1, index=12)
        candidate = dict(self.item, ratingKey='2', parentIndex=2, index=1)
        self.plex.metadata.side_effect = lambda key: copy.deepcopy(candidate if key == '2' else self.item)
        self.plex.fetch = Mock(return_value={'Metadata': [
            {'ratingKey':'1','grandparentRatingKey':'9','type':'episode'},
            {'ratingKey':'2','grandparentRatingKey':'9','type':'episode'}]})
        self.assertEqual(self.client.get('/api/playback/1/next').json['item']['id'], '2')
        self.assertIsNone(self.client.get('/api/playback/2/next').json['item'])
        self.item['type']='movie'
        self.assertIsNone(self.client.get('/api/playback/1/next').json['item'])

if __name__ == '__main__':
    unittest.main()
