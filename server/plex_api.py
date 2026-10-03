# Copyright (c) 2026 Vidafix contributors. Licensed under MIT; see LICENSE.
"""Read-only local media adapter; one fixed account endpoint for Watchlist."""
import math
import ipaddress
import re
import time
import threading
from urllib.parse import urlsplit

import requests


class PlexError(Exception):
    def __init__(self, message, status=502):
        super().__init__(message)
        self.status = status


def public_ratings(item):
    """Keep provider attribution from Plex; never fetch provider sites or icons."""
    entries = item.get('Rating', [])
    entries = entries if isinstance(entries, list) else []
    entries = entries + [
        {'image': item.get('ratingImage'), 'value': item.get('rating'), 'type': 'critic'},
        {'image': item.get('audienceRatingImage'), 'value': item.get('audienceRating'), 'type': 'audience'}]
    result, seen = [], set()
    for entry in entries:
        if not isinstance(entry, dict) or isinstance(entry.get('value'), bool):
            continue
        try:
            value = float(entry.get('value'))
        except (ValueError, TypeError):
            continue
        if not math.isfinite(value) or not 0 <= value <= 10:
            continue
        image = str(entry.get('image') or '').lower()
        provider = image.split('://', 1)[0]
        if provider == 'imdb':
            label, score = 'IMDb', format(value, '.1f') + '/10'
        elif provider == 'rottentomatoes':
            audience = entry.get('type') == 'audience' or 'upright' in image or 'spilled' in image
            label = 'Rotten Tomatoes audience' if audience else 'Rotten Tomatoes critics'
            score = str(int(value * 10 + 0.5)) + '%'
        elif provider == 'themoviedb':
            label, score = 'TMDB', format(value, '.1f') + '/10'
        elif not image:
            label = 'Plex audience' if entry.get('type') == 'audience' else 'Plex rating'
            score = format(value, '.1f') + '/10'
        else:
            continue
        if label not in seen:
            result.append({'label': label, 'score': score})
            seen.add(label)
    return result


def local_server(value):
    url = urlsplit(value)
    try:
        address = ipaddress.ip_address(url.hostname or "")
        port = url.port
    except ValueError:
        raise ValueError("Plex server must use a literal loopback or private LAN IP.") from None
    private = address.is_loopback or any(address in network for network in (
        ipaddress.ip_network("10.0.0.0/8"), ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"), ipaddress.ip_network("fc00::/7")
    ) if address.version == network.version)
    if not private or url.scheme not in ("http", "https") or url.username or url.password or url.path not in ("", "/") or url.query or url.fragment:
        raise ValueError("Plex server must be a local HTTP(S) origin without credentials or a path.")
    return value.rstrip("/")


class PlexClient:
    def __init__(self, server, token):
        self.server = local_server(server)
        self.token = token
        self._watchlist_cache = None
        self._watchlist_lock = threading.Lock()

    def fetch(self, path, params=None, image=False):
        return self._request(self.server + path, params, image)

    def _request(self, url, params=None, image=False):
        if not self.token:
            raise PlexError("Set PLEX_TOKEN or plex.token in config.ini, then restart the helper.", 503)
        try:
            # Ignore ambient HTTP proxy variables. Never forward credentials on redirects.
            with requests.Session() as session:
                session.trust_env = False
                with session.get(url, params=params,
                                 headers={"X-Plex-Token": self.token, "Accept": "image/*" if image else "application/json"},
                                 timeout=(3, 10), allow_redirects=False, stream=True) as response:
                    if response.status_code in (401, 403):
                        raise PlexError("Plex rejected the configured token. Check server access.", 502)
                    if response.status_code == 404:
                        raise PlexError("This Plex item is no longer available.", 404)
                    if response.status_code != 200:
                        raise PlexError("Plex returned an unexpected response.")
                    limit = 12 * 1024 * 1024 if image else 4 * 1024 * 1024
                    chunks, size = [], 0
                    for chunk in response.iter_content(65536):
                        size += len(chunk)
                        if size > limit:
                            raise PlexError("Plex response exceeded the prototype size limit.")
                        chunks.append(chunk)
                    content = b"".join(chunks)
                    if image:
                        mime = response.headers.get("Content-Type", "").split(";")[0].lower()
                        if mime not in ("image/jpeg", "image/png", "image/webp"):
                            raise PlexError("Plex returned an unsupported artwork format.")
                        return content, mime
                    import json
                    data = json.loads(content)
                    container = data["MediaContainer"]
                    if not isinstance(container, dict):
                        raise ValueError()
                    return container
        except requests.Timeout:
            raise PlexError("Plex timed out. Check that the server is running.", 504) from None
        except requests.RequestException:
            raise PlexError("Cannot reach Plex. Check the local server address and connection.", 502) from None
        except (ValueError, KeyError, TypeError):
            raise PlexError("Plex returned invalid metadata.") from None

    def libraries(self):
        return [{"id": str(x["key"]), "title": x.get("title", "Library"), "type": x["type"]}
                for x in self.fetch("/library/sections").get("Directory", [])
                if x.get("type") in ("movie", "show") and str(x.get("key", "")).isdigit()]

    def items(self, section):
        return self.library_page(section)['items']

    def library_page(self, section, offset=0, sort="title"):
        sorts = {"title": "titleSort:asc", "recent": "addedAt:desc"}
        if sort not in sorts:
            raise PlexError("Invalid library sort.", 400)
        if not isinstance(offset, int) or offset < 0 or offset > 2147483620 or offset % 20:
            raise PlexError('Invalid library page offset.', 400)
        if section not in [x["id"] for x in self.libraries()]:
            raise PlexError("Choose an available movie or TV library.", 404)
        data = self.fetch("/library/sections/" + section + "/all", {
            "X-Plex-Container-Start": offset, "X-Plex-Container-Size": 20, "sort": sorts[sort]})
        entries = data.get('Metadata', [])[:20]
        total = data.get('totalSize')
        total = int(total) if str(total).isdigit() else None
        return {'items': [self.public(x) for x in entries if x.get('type') in ('movie', 'show')],
                'offset': offset, 'total': total, 'previous': max(0, offset - 20) if offset else None,
                'next': offset + 20 if entries and (offset + len(entries) < total if total is not None else len(entries) == 20) else None}

    def recent_library(self, section):
        library = next((x for x in self.libraries() if x['id'] == section), None)
        if library is None:
            raise PlexError('Choose an available movie or TV library.', 404)
        kind = 'movie' if library['type'] == 'movie' else 'episode'
        data = self.fetch('/library/sections/' + section + '/all', {
            'type': 1 if kind == 'movie' else 4, 'sort': 'addedAt:desc',
            'X-Plex-Container-Start': 0, 'X-Plex-Container-Size': 100})
        entries = [x for x in data.get('Metadata', []) if x.get('type') == kind]
        entries.sort(key=lambda x: int(x.get('addedAt') or 0), reverse=True)
        return {'items': [self.public(x) for x in entries[:100]]}

    def metadata(self, key):
        if not re.fullmatch(r"[0-9]+", key):
            raise PlexError("Invalid item ID.", 400)
        data = self.fetch("/library/metadata/" + key).get("Metadata", [])
        if not data or data[0].get("type") not in ("movie", "show", "season", "episode"):
            raise PlexError("Movie, TV show or episode not found.", 404)
        return data[0]

    @staticmethod
    def public(item):
        key = str(item.get("ratingKey", ""))
        if not key.isdigit():
            raise PlexError("Plex returned an invalid item ID.")
        episode = item.get("type") == "episode"
        return {"id": key, "title": item.get("grandparentTitle", item.get("title", "Untitled")) if episode else item.get("title", "Untitled"), "type": item.get("type"),
                "episodeTitle": item.get("title") if episode else None,
                "season": item.get("parentIndex"), "episode": item.get("index"),
                "viewOffset": item.get("viewOffset", 0),
                "year": item.get("year"), "duration": item.get("duration"),
                "ratings": public_ratings(item), "rating": item.get("rating"), "summary": item.get("summary", "No summary available."),
                "cast": [x.get("tag", "") for x in item.get("Role", [])[:8]],
                "poster": "/art/" + key + "/thumb" if item.get("thumb") or item.get("grandparentThumb") else None,
                "background": "/art/" + key + "/art" if item.get("art") or item.get("grandparentArt") else None}

    def artwork(self, key, kind):
        if kind not in ("thumb", "art"):
            raise PlexError("Unknown artwork type.", 404)
        item = self.metadata(key)
        path = (item.get("grandparentThumb") or item.get("thumb", "")) if kind == "thumb" and item.get("type") == "episode" else item.get(kind, "")
        if kind == "art" and not path:
            path = item.get("grandparentArt", "")
        # Only Plex metadata image paths; no arbitrary URLs or user-supplied proxy paths.
        if not re.fullmatch(r"/library/metadata/[0-9]+/(?:thumb|art)(?:/[0-9]+)?", path):
            raise PlexError("Artwork unavailable.", 404)
        return self.fetch(path, image=True)

    def feed(self, name):
        """Bounded local rows, independently requested so one failure is isolated."""
        libraries = self.libraries()
        allowed = {x['id'] for x in libraries}
        if name in ('continue', 'ondeck'):
            data = self.fetch('/hubs/continueWatching', {'X-Plex-Container-Size': 100})
            entries = data.get('Metadata', [])
            for hub in data.get('Hub', []):
                if hub.get('hubIdentifier') == 'continueWatching':
                    entries += hub.get('Metadata', [])
            if name == 'ondeck':
                entries += self.fetch('/library/onDeck', {'X-Plex-Container-Size': 100}).get('Metadata', [])
            entries = [x for x in entries if str(x.get('librarySectionID')) in allowed
                       and x.get('type') in ('movie', 'episode')
                       and ((int(x.get('viewOffset') or 0) > 0) if name == 'continue'
                            else (x.get('type') == 'episode' and not x.get('viewOffset') and not x.get('viewCount')))]
        elif name in ('recent-movies', 'recent-tv'):
            entries = []
            library_type = 'movie' if name == 'recent-movies' else 'show'
            for library in libraries:
                if library['type'] == library_type:
                    batch = self.fetch('/library/sections/' + library['id'] + '/all', {
                        'type': 1 if library_type == 'movie' else 4, 'sort': 'addedAt:desc',
                        'X-Plex-Container-Start': 0, 'X-Plex-Container-Size': 100}).get('Metadata', [])
                    entries.extend(x for x in batch if x.get('type') == ('movie' if library_type == 'movie' else 'episode'))
            entries.sort(key=lambda x: int(x.get('addedAt') or 0), reverse=True)
        else:
            raise PlexError('Unknown Home row.', 404)
        unique = {}
        for entry in entries:
            unique.setdefault(str(entry.get('ratingKey')), entry)
        return {'items': [self.public(x) for x in list(unique.values())[:100]]}

    @staticmethod
    def guids(item):
        return {x for x in [item.get('guid')] + [g.get('id') for g in item.get('Guid', [])] if x}

    def watchlist(self):
        # Cache only resolved local items in memory, never credentials or cloud artwork.
        with self._watchlist_lock:
            if self._watchlist_cache and time.monotonic() - self._watchlist_cache[0] < 60:
                return self._watchlist_cache[1]
            allowed = {x['id'] for x in self.libraries()}
            resolved, seen, scanned, truncated = [], set(), 0, False
            deadline = time.monotonic() + 40
            for offset in range(0, 200, 50):
                data = self._request('https://discover.provider.plex.tv/library/sections/watchlist/all', {
                    'includeGuids': 1, 'sort': 'watchlistedAt:desc',
                    'X-Plex-Container-Start': offset, 'X-Plex-Container-Size': 50})
                entries = data.get('Metadata', [])
                for online in entries:
                    if len(resolved) >= 20 or time.monotonic() > deadline:
                        truncated = True
                        break
                    scanned += 1
                    if online.get('type') not in ('movie', 'show'):
                        continue
                    guid = online.get('guid', '')
                    if not re.fullmatch(r'plex://(?:movie|show)/[a-zA-Z0-9]+', guid):
                        continue
                    matches = self.fetch('/library/all', {
                        'guid': guid, 'type': 1 if online['type'] == 'movie' else 2,
                        'includeGuids': 1, 'X-Plex-Container-Size': 20}).get('Metadata', [])
                    for local in matches:
                        key = str(local.get('ratingKey', ''))
                        if (str(local.get('librarySectionID')) in allowed and local.get('type') == online['type']
                                and self.guids(local).intersection(self.guids(online)) and key.isdigit() and key not in seen):
                            resolved.append(self.public(local))
                            seen.add(key)
                            break
                if truncated or len(entries) < 50:
                    break
                if offset == 150:
                    truncated = True
            result = {'items': resolved, 'message': 'Only titles available on your local server are shown.',
                      'truncated': truncated, 'scanned': scanned}
            self._watchlist_cache = (time.monotonic(), result)
            return result
