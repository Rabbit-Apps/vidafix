# Copyright (c) 2026 Vidafix contributors. Licensed under MIT; see LICENSE.
import hashlib
import configparser
import os
from pathlib import Path

from flask import Flask, Response, jsonify, send_from_directory, request
from server.plex_api import PlexClient, PlexError

ROOT = Path(__file__).resolve().parent.parent


def create_app(client=None, config_path=None):
    config = configparser.ConfigParser(interpolation=None)
    config.read(config_path or os.environ.get("VIDAA_CONFIG", str(ROOT / "config.ini")), encoding="utf-8-sig")
    app = Flask(__name__, static_folder=str(ROOT / "app"), static_url_path="/static")
    plex = client or PlexClient(config.get("plex", "server", fallback="http://127.0.0.1:32400"),
                                os.environ.get("PLEX_TOKEN") or config.get("plex", "token", fallback=""))
    app.config["LISTEN"] = config.get("web", "listen", fallback="0.0.0.0")
    app.config["PORT"] = config.getint("web", "port", fallback=8765)

    from server.artwork_cache import ArtworkCache
    namespace = hashlib.sha256((getattr(plex, 'server', '') + ':' + getattr(plex, 'token', '')).encode()).hexdigest()
    cache_path = ':memory:' if client is not None else os.environ.get('VIDAA_ART_CACHE', str(ROOT / '.cache' / 'artwork.sqlite3'))
    art_cache = ArtworkCache(cache_path, namespace)
    app.extensions['artwork_cache'] = art_cache

    from server.playback import install_playback
    install_playback(app, plex)

    @app.get("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    @app.get("/styles.css")
    @app.get("/navigation.js")
    @app.get("/app.js")
    @app.get("/player.js")
    def frontend_asset():
        from flask import request
        return send_from_directory(app.static_folder, request.path.lstrip("/"))

    @app.get("/api/libraries")
    def libraries():
        return jsonify(libraries=plex.libraries(), preferred=config.get("plex", "library", fallback=""))

    @app.get('/api/library/<int:section>/recent')
    def recent_library(section):
        return jsonify(plex.recent_library(str(section)))

    @app.get("/api/library/<int:section>")
    def library(section):
        value = request.args.get('offset', '0')
        if not value.isascii() or not value.isdigit() or len(value) > 10:
            raise PlexError('Invalid library page offset.', 400)
        return jsonify(plex.library_page(str(section), int(value), request.args.get("sort", "title")))

    @app.get('/api/show/<int:key>/episodes')
    def episodes(key):
        if plex.metadata(str(key)).get('type') != 'show':
            raise PlexError('Choose a TV series.', 400)
        value = request.args.get('offset', '0')
        if not value.isascii() or not value.isdigit() or len(value) > 9 or int(value) % 20:
            raise PlexError('Invalid episode page.', 400)
        offset = int(value)
        data = plex.fetch('/library/metadata/' + str(key) + '/allLeaves', {
            'X-Plex-Container-Start': offset, 'X-Plex-Container-Size': 20})
        entries = data.get('Metadata', [])[:20]
        total = data.get('totalSize')
        return jsonify(items=[plex.public(x) for x in entries if x.get('type') == 'episode'],
                       previous=max(0, offset - 20) if offset else None,
                       next=offset + 20 if len(entries) == 20 and (total is None or offset + 20 < int(total)) else None)

    @app.get('/api/show/<int:key>/seasons')
    @app.get('/api/season/<int:key>/episodes')
    def children(key):
        seasons = request.path.startswith('/api/show/')
        parent_type, child_type = ('show', 'season') if seasons else ('season', 'episode')
        if plex.metadata(str(key)).get('type') != parent_type:
            raise PlexError('Choose a valid series or season.', 400)
        value = request.args.get('offset', '0')
        if not value.isascii() or not value.isdigit() or len(value) > 9 or int(value) % 20:
            raise PlexError('Invalid page.', 400)
        offset = int(value)
        data = plex.fetch('/library/metadata/' + str(key) + '/children', {
            'X-Plex-Container-Start': offset, 'X-Plex-Container-Size': 20})
        entries = data.get('Metadata', [])[:20]
        total = data.get('totalSize')
        return jsonify(items=[plex.public(x) for x in entries if x.get('type') == child_type],
                       previous=max(0, offset - 20) if offset else None,
                       next=offset + 20 if len(entries) == 20 and (total is None or offset + 20 < int(total)) else None)

    @app.get("/api/item/<int:key>")
    def item(key):
        return jsonify(plex.public(plex.metadata(str(key))))

    @app.get('/api/feed/<name>')
    def feed(name):
        return jsonify(plex.feed(name))

    @app.get('/api/watchlist')
    def watchlist():
        return jsonify(plex.watchlist())

    @app.get("/art/<int:key>/<kind>")
    def artwork(key, kind):
        if kind not in ('thumb', 'art'):
            raise PlexError('Unknown artwork type.', 404)
        content, mime = art_cache.get(str(key) + '/' + kind, lambda: plex.artwork(str(key), kind))
        response = Response(content, mimetype=mime, headers={"Cache-Control": "private, max-age=3600"})
        response.set_etag(hashlib.sha256(content).hexdigest())
        return response.make_conditional(request)

    @app.errorhandler(PlexError)
    def plex_error(error):
        return jsonify(error=str(error)), error.status

    @app.after_request
    def headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'"
        if response.mimetype == "application/json":
            response.headers["Cache-Control"] = "no-store"
        return response

    return app


if __name__ == "__main__":
    from waitress import serve
    application = create_app()
    serve(application, host=application.config["LISTEN"], port=application.config["PORT"])
