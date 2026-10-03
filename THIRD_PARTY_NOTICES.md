# Vidafix third-party notices

The root LICENSE applies only to project material its contributors can license.
It does not replace the terms of dependencies, Plex/VIDAA services, media,
metadata or artwork. No third-party Python packages are vendored in the public
source ZIP; pip installs them separately with their own notices.

## Runtime dependencies

| Package | Licence | Source |
| --- | --- | --- |
| Flask | BSD-3-Clause | https://github.com/pallets/flask |
| Requests | Apache-2.0 | https://github.com/psf/requests |
| Waitress | ZPL-2.1 | https://github.com/Pylons/waitress |

The installed dependency tree also includes Werkzeug, Jinja2, MarkupSafe, Click,
ItsDangerous, Blinker, certifi, charset-normalizer, idna and urllib3. They retain
their own licences; inspect the exact installed distributions when packaging a
runtime. In particular, certifi declares MPL-2.0. A source-only export does not
bundle its certificate collection or any of these libraries. Version ranges in
requirements.txt are not a reproducible lockfile or a complete software bill of
materials for every future installation.

Python and optional Node runtimes are separately installed and not redistributed.
Technical references are linked in docs/REFERENCES.md, not bundled. PlexAPI's
subtitle endpoint documentation was consulted; the PlexAPI package is not a
runtime dependency.

## Media and branding

The public package contains the Vidafix wordmark icon and compatibility copies
of that same icon, not the original sideload ZIP's Plex image. Library posters,
backgrounds, ratings and media come from the user's configured Plex server at
runtime and remain subject to their respective rights. Do not redistribute the
cache or real library screenshots with the source.

Plex, VIDAA, Hisense, IMDb, Rotten Tomatoes and TMDB names identify interoperable
products or metadata sources; no affiliation, endorsement or trademark licence
is claimed. Vidafix naming has not received trademark clearance.

## Excluded sideloader

The supplied helper's provenance and redistribution rights remain unresolved.
It and its credentials/compiled bytecode are excluded. See
[the source review](docs/SIDELOADER_REVIEW.md). Nothing in Vidafix's licence
purports to license that excluded material.

The included sideload-addon files are original Vidafix material licensed under
MIT. They configure a separately obtained helper; they do not bundle or license
that helper's server, certificates, keys or other upstream assets.
