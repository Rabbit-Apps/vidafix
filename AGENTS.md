# Vidafix

Read the original specification when available locally, [README.md](README.md), [DESIGN.md](DESIGN.md), and [TESTING.md](TESTING.md) before changing this app.

## Scope and source of truth

- The user's current instructions take precedence. The supplied specification defines the product. The user has expanded Phase 1 to include Home rows and a read-only, locally resolved Plex Watchlist.
- Phase 1: connect to one configured local Plex server, select a movie/TV library, show up to 20 proxied posters, explicit D-pad/OK/Back navigation, and details.
- Approved extension: Continue Watching, On Deck, Recently Added Movies/TV episodes, episode details/progress display, and Watchlist. The user has now authorized Phase 2 playback; Watchlist mutations remain unimplemented.
- Library grids now use bounded 20-item pages with Previous/Next controls; 20 is a page size, not a library-wide cap. Home shelves show up to 100 items each; Watchlist retains its existing limit. The user confirmed Mint hosting and TV artwork; TV app navigation and playback have been reported working; built-in browser pointer behaviour differs.
- Do not advance to full Home/Movies/TV/Search/Watchlist UI, Plex PIN sign-in, or installation packaging without a request to expand scope.
- Never add Discover, Plex-hosted content, music, Live TV, rentals, social features, or automatic server roaming.

## Implementation

- Prefer Python with Flask. Use plain HTML/CSS/JavaScript, with no Node requirement for normal deployment.
- Target Hisense 55U7HAU, VIDAA 6, firmware V0000.06.29X.P0813. Preserve ES5-style JavaScript, XMLHttpRequest and conservative CSS unless hardware testing supports a change.
- Keep focus navigation explicit and predictable. Preserve focus on return from details and keep the focused card above the footer.
- All artwork must pass through the helper. Keep Plex tokens exclusively on the backend and out of browser responses, URLs, logs and Git.
- Keep the server destination fixed to the configured local origin. Reject arbitrary proxy URLs and redirects; retain timeouts and response-size limits.
- Watchlist is the sole account-service exception: read only `https://discover.provider.plex.tv/library/sections/watchlist/all`, match exact GUIDs against the configured local server, and return local metadata/artwork only. Do not add Discover browsing or cloud playback.
- Render Plex text as text, never raw HTML. Retain readable loading, empty, missing-artwork and error states.
- Development previews use synthetic data and must remain clearly distinguishable from live Plex access.

## Verification and delivery

- Follow TESTING.md. Run relevant backend and navigation checks after behaviour changes, and inspect rendered UI after visual changes.
- Never describe desktop browser success as proof of VIDAA compatibility. Record live-server and hardware checks separately.
- Keep Linux Mint setup instructions accurate. Users should open the helper URL, not the HTML file directly.
- Do not commit or push unless the user explicitly requests it. The user approved MIT licensing, including commercial use and sale; preserve LICENSE and source notices.
- Preserve synced project reference files, including anything under the parent project's `sources/` directory. The specification in `docs/` is a reference copy; record decisions separately rather than rewriting its original requirements.

## Optional design references

The parent workspace contains Impeccable and Create DESIGN.md reference skills under `reference-materials/hardware-monitor/`. They are optional references, not installed dependencies of this app. Read their instructions before invoking them. TV compatibility, minimal animation and the user's brief take precedence over generic web design suggestions. WinUI skills do not apply to this HTML client.

Library sorting: Title A–Z (default) or Recently added (newest first). Applies to all movie/show libraries, including Anime. Changing sort returns to page one; the choice persists per library until the page reloads. TV libraries sort series by their Plex added date, while the Home recent-TV shelf lists episodes.

Playback uses native HLS with a bounded same-origin resource proxy, stream-selection validation, timeline reporting and transcode cleanup. Keep credentials server-side. Consult README playback limitations and TESTING.md; desktop success does not prove TV support.

Plex now chooses Direct Stream or conversion within the conservative HLS profile; never claim original-file Direct Play or change global server settings. Controls hide after four seconds while playing and remain reachable via OK/arrows/pointer.

Resume HLS is trimmed to the containing segment. Keep timelineBase accounting consistent in progress and seeking, and preserve restart-based rewind before the playlist origin. Do not revert to requesting all earlier segments.

## Approved playback extras

The user authorized subtitle search/download through the configured Plex server. Plex may contact its subtitle provider; the helper must not fetch arbitrary provider URLs directly. Provider keys remain backend-only, bound to the item and short-lived opaque IDs. Episode autoplay triggers only on natural completion after final progress reporting; manual Stop and movies never autoplay. Refresh Home metadata after playback while retaining artwork caching.

## Public source export

Use tools/build_public_release.py. The local sideload helper, private config, screenshots, original supplied specification, keys, cache and deployment archives are excluded. Retain legacy protocol identifiers and service names for compatibility; all visible product branding is Vidafix. See docs/PUBLISHING.md and docs/SIDELOADER_REVIEW.md.

Only the original, generic sideload-addon source files are approved for public
export. Do not bundle helper servers, credentials or generated installer settings.
Test the new add-on separately; do not claim the old helper's hardware results
as evidence of this downloaded-server/new-page combination.
