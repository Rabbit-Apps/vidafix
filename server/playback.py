# Copyright (c) 2026 Vidafix contributors. Licensed under MIT; see LICENSE.
"""Bounded HLS sessions. Only server-issued resources are exposed to the TV."""
import re
import uuid
import threading
import time
from urllib.parse import urljoin, urlsplit, parse_qsl, urlencode, unquote

import requests
from flask import Blueprint, Response, jsonify, request
from server.plex_api import PlexError


def trim_resume_playlist(source, offset):
    """Trim complete segments before offset; retain the containing segment.

    The player reports currentTime relative to this playlist, so return its
    absolute origin in milliseconds. Seeking before this origin needs a new
    session. Plex's MPEG-TS profile emits standalone, unencrypted segments.
    """
    if not offset:
        return source, 0
    lines = source.splitlines()
    elapsed, skipped, remove, pending = 0.0, 0, set(), None
    for i, line in enumerate(lines):
        if line.startswith('#EXTINF:'):
            try:
                length = float(line.split(':', 1)[1].split(',')[0])
                if not 0 < length < 3600:
                    raise ValueError()
            except ValueError:
                raise PlexError('Plex returned an invalid segment duration.') from None
            pending = (i, length)
        elif line and not line.startswith('#') and pending:
            start, length = pending
            if elapsed + length > offset / 1000:
                break
            remove.update(range(start, i + 1))
            elapsed += length
            skipped += 1
            pending = None
    if not skipped:
        return source, 0
    output, has_sequence = [], False
    for i, line in enumerate(lines):
        if i in remove or line.startswith('#EXT-X-START:'):
            continue
        if line.startswith('#EXT-X-MEDIA-SEQUENCE:'):
            try:
                line = '#EXT-X-MEDIA-SEQUENCE:' + str(int(line.split(':')[1]) + skipped)
            except ValueError:
                raise PlexError('Plex returned an invalid media sequence.') from None
            has_sequence = True
        output.append(line)
    if not has_sequence:
        output.insert(1, '#EXT-X-MEDIA-SEQUENCE:' + str(skipped))
    output.insert(1, '#EXT-X-START:TIME-OFFSET=%.3f' % max(0, offset / 1000 - elapsed))
    return '\n'.join(output) + '\n', round(elapsed * 1000)


class Playback:
    def __init__(self, plex):
        self.plex = plex
        self.sessions = {}
        self.lock = threading.RLock()
        self.subtitle_results = {}

    def raw(self, path, sid, params=None, method='GET', limit=32 * 1024 * 1024):
        if not self.plex.token:
            raise PlexError('Configure a Plex token before playing.', 503)
        try:
            with requests.Session() as http:
                http.trust_env = False
                with http.request(method, self.plex.server + path, params=params,
                                  headers={'X-Plex-Token': self.plex.token,
                                           'X-Plex-Client-Identifier': 'vidplex-' + sid,
                                           'X-Plex-Product': 'Vidafix', 'X-Plex-Version': '0.2',
                                           'X-Plex-Platform': 'Generic',
                                           'X-Plex-Client-Profile-Name': 'Generic',
                                           'X-Plex-Client-Profile-Extra': 'add-transcode-target(type=videoProfile&context=streaming&protocol=hls&container=mpegts&videoCodec=h264&audioCodec=aac&replace=true)'},
                                  timeout=(3, 30), allow_redirects=False, stream=True) as response:
                    if response.status_code not in (200, 204):
                        raise PlexError('Plex playback returned HTTP ' + str(response.status_code) + '. Check server transcoding and media availability.')
                    chunks, size = [], 0
                    for chunk in response.iter_content(65536):
                        size += len(chunk)
                        if size > limit:
                            raise PlexError('Playback response exceeded the size limit.')
                        chunks.append(chunk)
                    return b''.join(chunks), response.headers.get('Content-Type', '').split(';')[0].lower()
        except requests.RequestException:
            raise PlexError('Plex playback connection failed or timed out.', 502) from None

    def options(self, key):
        item = self.plex.metadata(key)
        if item.get('type') not in ('movie', 'episode'):
            raise PlexError('Choose an episode to play.', 400)
        if str(item.get('librarySectionID')) not in [x['id'] for x in self.plex.libraries()]:
            raise PlexError('Playback is limited to the configured local libraries.', 404)
        media = item.get('Media', [])
        parts = media[0].get('Part', []) if media else []
        if len(parts) != 1 or not str(parts[0].get('id', '')).isdigit():
            raise PlexError('This version supports single-part media only.', 400)
        streams = parts[0].get('Stream', [])
        def tracks(kind):
            return [{'id': str(s['id']), 'label': s.get('displayTitle') or s.get('language') or s.get('codec', 'Track'),
                     'selected': bool(s.get('selected'))}
                    for s in streams if s.get('streamType') == kind and str(s.get('id', '')).isdigit()]
        return item, parts[0], {'audio': tracks(2), 'subtitles': tracks(3),
                                'duration': int(item.get('duration') or 0),
                                'resume': int(item.get('viewOffset') or 0)}

    def search_subtitles(self, key, language):
        self.options(key)  # Local playable item and library validation.
        if not isinstance(language, str) or not re.fullmatch(r'[a-z]{2}', language):
            raise PlexError('Choose a subtitle language.', 400)
        data = self.plex.fetch('/library/metadata/' + key + '/subtitles',
                               {'language': language, 'hearingImpaired': 0, 'forced': 0})
        results = []
        with self.lock:
            now = time.monotonic()
            self.subtitle_results = {k: v for k, v in self.subtitle_results.items() if now - v['created'] < 600}
            if len(self.subtitle_results) > 500:
                self.subtitle_results.clear()
            for stream in data.get('Stream', [])[:20]:
                provider_key = stream.get('key')
                if not isinstance(provider_key, str) or not provider_key or len(provider_key) > 4096:
                    continue
                ident = str(uuid.uuid4())
                self.subtitle_results[ident] = {'item': key, 'key': provider_key, 'created': now}
                label = stream.get('title') or stream.get('displayTitle') or stream.get('language') or language
                results.append({'id': ident, 'label': str(label)[:300]})
        return {'items': results}

    def download_subtitle(self, key, ident):
        self.options(key)
        with self.lock:
            result = self.subtitle_results.get(str(ident))
            if not result or result['item'] != key or time.monotonic() - result['created'] >= 600:
                raise PlexError('Subtitle result expired. Search again.', 400)
        # Provider keys never become a request URL or leave the backend.
        self.raw('/library/metadata/' + key + '/subtitles', 'subtitles',
                 {'key': result['key']}, method='PUT', limit=65536)
        return {'ok': True}

    def next_episode(self, key):
        item, _, _ = self.options(key)
        if item.get('type') != 'episode':
            return None
        show = str(item.get('grandparentRatingKey', ''))
        if not show.isdigit():
            raise PlexError('Plex did not identify the parent series.')
        found = False
        for offset in range(0, 10000, 100):
            data = self.plex.fetch('/library/metadata/' + show + '/allLeaves', {
                'X-Plex-Container-Start': offset, 'X-Plex-Container-Size': 100,
                'sort': 'parentIndex:asc,index:asc'})
            entries = data.get('Metadata', [])
            for entry in entries:
                if entry.get('type') != 'episode' or str(entry.get('grandparentRatingKey')) != show:
                    continue
                if found:
                    candidate = self.plex.metadata(str(entry.get('ratingKey', '')))
                    if str(candidate.get('librarySectionID')) != str(item.get('librarySectionID')):
                        continue
                    return self.plex.public(candidate)
                if str(entry.get('ratingKey')) == key:
                    found = True
            if len(entries) < 100:
                return None
        raise PlexError('Series is too large to determine the next episode safely.')

    def get(self, sid):
        with self.lock:
            state = self.sessions.get(sid)
            if not state:
                raise PlexError('Playback session expired. Return to details and play again.', 404)
            state['seen'] = time.monotonic()
            return state

    def reap(self):
        with self.lock:
            expired = [sid for sid, s in self.sessions.items() if time.monotonic() - s['seen'] > 120]
        for sid in expired:
            self.stop(sid)

    def stop(self, sid):
        with self.lock:
            state = self.sessions.get(sid)
        if state:
            with state['io']:
                with self.lock:
                    if self.sessions.pop(sid, None) is None:
                        return
                try:
                    self.raw('/video/:/transcode/universal/stop', sid, {'session': sid}, limit=65536)
                except PlexError:
                    pass  # Plex also expires disconnected clients.

    def start(self, key, body):
        self.reap()
        item, part, options = self.options(key)
        offset = body.get('offset', 0)
        if type(offset) is not int or not 0 <= offset <= options['duration']:
            raise PlexError('Invalid playback position.', 400)
        offset = (offset // 1000) * 1000
        audio = str(body.get('audio', ''))
        subtitle = str(body.get('subtitle', '0'))
        if audio and audio not in [x['id'] for x in options['audio']]:
            raise PlexError('Choose an available audio track.', 400)
        if subtitle != '0' and subtitle not in [x['id'] for x in options['subtitles']]:
            raise PlexError('Choose an available subtitle track.', 400)
        sid = str(uuid.uuid4())
        with self.lock:
            if len(self.sessions) >= 4:
                raise PlexError('Too many playback sessions. Stop another player or wait two minutes.', 409)
            self.sessions[sid] = {'key': key, 'duration': options['duration'], 'offset': offset,
                                  'seen': time.monotonic(), 'resources': {}, 'reverse': {}, 'io': threading.RLock()}
        try:
            # Plex stores this user's stream preference. Values come only from this item's part.
            selection = {'subtitleStreamID': subtitle}
            if audio:
                selection['audioStreamID'] = audio
            self.raw('/library/parts/' + str(part['id']), sid, selection, method='PUT', limit=65536)
            params = {'path': '/library/metadata/' + key, 'mediaIndex': 0, 'partIndex': 0,
                      'protocol': 'hls', 'session': sid, 'offset': offset // 1000,
                      'directPlay': 0, 'directStream': 1, 'videoCodec': 'h264', 'audioCodec': 'aac',
                      'audioChannelCount': 2, 'maxVideoBitrate': 8000, 'videoResolution': '1920x1080',
                      'subtitles': 'burn' if subtitle != '0' else 'none', 'subtitleSize': 100,
                      'hasMDE': 1, 'location': 'lan', 'fastSeek': 1, 'videoQuality': 75,
                      'audioBoost': 100, 'directStreamAudio': 1, 'mediaBufferSize': 32768, 'secondsPerSegment': 4}
            path = '/video/:/transcode/universal/start.m3u8'
            self.raw('/video/:/transcode/universal/decision', sid, params, limit=1024 * 1024)
            content, _ = self.raw(path, sid, params, limit=1024 * 1024)
            manifest = self.manifest(sid, path, content)
            # Native desktop HLS may ignore EXT-X-START and fetch every empty
            # segment preceding a resume point. Serve a media playlist starting
            # at that point rather than making the browser scan those segments.
            for _ in range(3):
                if '#EXTINF:' in manifest:
                    break
                links = [line for line in manifest.splitlines() if line and not line.startswith('#')]
                if not links:
                    raise PlexError('Plex returned an empty playback playlist.')
                rid = links[0].rsplit('/', 1)[-1]
                path = self.get(sid)['resources'][rid]
                content, _ = self.raw(path, sid, limit=1024 * 1024)
                manifest = self.manifest(sid, path, content)
            if '#EXTINF:' not in manifest:
                raise PlexError('Plex did not return a playable media playlist.')
            self.get(sid)['manifest'] = manifest
            return {'session': sid, 'url': '/playback/' + sid + '/master.m3u8',
                    'offset': offset, 'timelineBase': self.get(sid).get('timelineBase', 0),
                    'duration': options['duration']}
        except Exception:
            self.stop(sid)
            raise

    def manifest(self, sid, base, content):
        try:
            source = content.decode('utf-8')
        except UnicodeError:
            raise PlexError('Plex returned an invalid playlist.') from None
        if not source.startswith('#EXTM3U'):
            raise PlexError('Plex did not return an HLS playlist.')
        state = self.get(sid)
        if '#EXTINF:' in source:
            source, timeline_base = trim_resume_playlist(source, state['offset'])
            state['timelineBase'] = timeline_base
        def resource(value):
            url = urlsplit(urljoin(self.plex.server + base, value))
            origin = urlsplit(self.plex.server)
            path = unquote(url.path)
            prefix = '/video/:/transcode/universal/session/'
            if ((url.scheme, url.netloc) != (origin.scheme, origin.netloc) or
                    not path.startswith(prefix) or '..' in path or '\\' in path or
                    not re.fullmatch(r'[A-Za-z0-9_./:\-]+', path)):
                raise PlexError('Plex returned an unsupported stream resource.')
            query = urlencode([(k, v) for k, v in parse_qsl(url.query) if k.lower() != 'x-plex-token'])
            target = url.path + ('?' + query if query else '')
            with self.lock:
                rid = state['reverse'].get(target)
                if rid is None:
                    if len(state['resources']) >= 20000:
                        raise PlexError('Playback resource limit reached.')
                    rid = str(len(state['resources']))
                    state['resources'][rid] = target
                    state['reverse'][target] = rid
            return '/playback/' + sid + '/resource/' + rid
        lines = []
        for line in source.splitlines():
            if line.startswith('#'):
                if 'URI=' in line:
                    line = re.sub(r'URI="([^"]+)"', lambda m: 'URI="' + resource(m[1]) + '"', line)
                # Tokens must not survive in comments or extension attributes.
                if 'x-plex-token' in line.lower() or (self.plex.token and self.plex.token in line):
                    raise PlexError('Unsafe playlist metadata returned by Plex.')
                lines.append(line)
            elif line.strip():
                lines.append(resource(line.strip()))
            else:
                lines.append(line)
        return '\n'.join(lines) + '\n'

    def progress(self, sid, body):
        state = self.get(sid)
        position, status = body.get('time'), body.get('state')
        if type(position) is not int or not 0 <= position <= state['duration'] or status not in ('playing', 'paused', 'stopped'):
            raise PlexError('Invalid playback progress.', 400)
        with state['io']:
            with self.lock:
                if sid not in self.sessions:
                    raise PlexError('Playback session has stopped.', 404)
            if status != 'stopped':
                self.raw('/video/:/transcode/universal/ping', sid, {'session': sid}, limit=65536)
            self.raw('/:/timeline', sid, {'ratingKey': state['key'], 'key': '/library/metadata/' + state['key'],
                                         'state': status, 'time': position, 'duration': state['duration']}, limit=65536)


def install_playback(app, plex):
    playback = Playback(plex)
    app.extensions['playback'] = playback
    routes = Blueprint('playback', __name__)

    @routes.before_request
    def same_origin():
        if request.method == 'POST':
            if not request.is_json or request.headers.get('X-VidPlex') != '1':
                raise PlexError('Playback requests must come from Vidafix.', 403)
            origin = request.headers.get('Origin')
            if origin and origin != request.host_url.rstrip('/'):
                raise PlexError('Cross-origin playback requests are not allowed.', 403)
            if not isinstance(request.get_json(silent=True), dict):
                raise PlexError('Invalid playback request.', 400)

    @routes.get('/api/playback/<int:key>/options')
    def options(key):
        return jsonify(playback.options(str(key))[2])

    @routes.get('/api/playback/<int:key>/next')
    def next_episode(key):
        return jsonify(item=playback.next_episode(str(key)))

    @routes.post('/api/playback/<int:key>/subtitles/search')
    def search_subtitles(key):
        return jsonify(playback.search_subtitles(str(key), request.get_json().get('language', 'en')))

    @routes.post('/api/playback/<int:key>/subtitles/download')
    def download_subtitle(key):
        return jsonify(playback.download_subtitle(str(key), request.get_json().get('id')))

    @routes.post('/api/playback/<int:key>/start')
    def start(key):
        return jsonify(playback.start(str(key), request.get_json()))

    @routes.post('/api/playback/<sid>/progress')
    def progress(sid):
        playback.progress(sid, request.get_json())
        return jsonify(ok=True)

    @routes.post('/api/playback/<sid>/stop')
    def stop(sid):
        state = playback.get(sid)
        with state['io']:
            try:
                if 'time' in request.get_json():
                    playback.progress(sid, dict(request.get_json(), state='stopped'))
            finally:
                playback.stop(sid)
        return jsonify(ok=True)

    @routes.get('/playback/<sid>/master.m3u8')
    def master(sid):
        return Response(playback.get(sid)['manifest'], mimetype='application/vnd.apple.mpegurl', headers={'Cache-Control': 'no-store'})

    @routes.get('/playback/<sid>/resource/<int:rid>')
    def resource(sid, rid):
        path = playback.get(sid)['resources'].get(str(rid))
        if not path:
            raise PlexError('Unknown playback resource.', 404)
        content, mime = playback.raw(path, sid)
        if content.startswith(b'#EXTM3U'):
            content, mime = playback.manifest(sid, path, content), 'application/vnd.apple.mpegurl'
        elif mime not in ('video/mp2t', 'video/mp4', 'audio/mp4', 'application/octet-stream', 'audio/aac'):
            raise PlexError('Unsupported playback segment.')
        return Response(content, mimetype=mime, headers={'Cache-Control': 'no-store'})

    app.register_blueprint(routes)
    # A quiet background cleanup also covers clients that disappear without Stop.
    def cleanup():
        while True:
            time.sleep(30)
            playback.reap()
    threading.Thread(target=cleanup, daemon=True, name='vidplex-playback-cleanup').start()
