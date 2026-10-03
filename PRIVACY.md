# Vidafix privacy notice

Updated 2026-10-03. This notice describes the distributed Vidafix client, not Plex,
subtitle providers, third-party sideloaders or services added by a host operator.

Vidafix has no developer-operated account service, analytics or reporting endpoint.
The project maintainers do not receive your token, library or viewing activity
through the app. It runs on your chosen host and uses the configured Plex account.

## Data used and stored

Your Plex address and token are stored in your private config.ini, or supplied
through local environment variables. The backend uses the token to authenticate
to Plex; it does not send it to the TV/browser in app responses. Protect that file
and any backups. Media titles, artwork, ratings, track information and playback
progress are read from Plex. Playback progress and track/subtitle requests are
sent back to Plex. Subtitle download can change tracks in your Plex library.

Artwork is cached locally in .cache/artwork.sqlite3 by default (256 MiB limit,
24-hour freshness), with a one-hour browser cache. Expired entries can remain
on disk until eviction; freshness is not a deletion guarantee. Browsing screens,
subtitle result identifiers and playback sessions are retained temporarily in
memory. Closing the process clears memory; browser caches have separate controls.
The host can override the artwork location. Stop Vidafix before deleting its
cache; deleting this cache does not delete Plex media.

## Network requests

Library browsing, artwork and playback use the configured local Plex server.
The optional Watchlist feature sends an authenticated request to Plex's account
Watchlist service and matches results to local media. Plex may contact external
subtitle providers when you search/download through it. Those services have
separate policies: [Plex privacy policy](https://www.plex.tv/about/privacy-legal/privacy-policy/).
Installing dependencies requires internet access to package repositories.

The frontend loads app resources from your Vidafix host. There is no bundled
advertising or external ratings lookup. A separately obtained sideloader may
have additional internet/DNS requests; it is outside this package and notice.

## Hosting and logs

Vidafix has no login and uses HTTP by default. Anyone who can reach its port can
access exposed functions using the configured account's permissions. Use only a
trusted LAN; do not expose the port publicly. Host operators control access and
any extra logging. Windows background startup writes rotated local logs under
.logs; Linux service diagnostics may be kept in the system journal. These may
contain request/error context. Review and redact logs before sharing them.

Private config, cached media, logs and screenshots are excluded from public
exports. If you submit an issue, remove credentials, personal addresses and
private library details first. No automatic upload occurs.
