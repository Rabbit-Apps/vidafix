# Vidafix interface design

Vidafix is a dark, remote-operated interface for viewing from a sofa. The header
uses purple Vida and white fix, with no tagline. Metadata and artwork are from
the configured Plex server; provider ratings are labelled without external logos.

- Navigation shows Home, every movie/show library by its Plex name, Watchlist and
  Refresh. Wrapped buttons form separate focus rows.
- Home uses horizontal shelves of up to 100 cards. Library grids show six columns
  with 20-item pages, Title/Recently Added sorting and Previous/Next buttons.
- Series open seasons with individual season posters, then paged episodes.
- Details place a poster beside title, ratings, playback actions and synopsis.
- Find subtitles opens a temporary full-screen vertical menu. Results, empty and
  error states appear there. Back/Cancel restores focus; selecting a result closes
  the menu and requests a Plex download. Dismissed searches cannot reopen it.
- Left/Right follows visible action rows; Up/Down changes rows. Focus uses a
  yellow border. Back restores the previous level or originating card.
- Playback covers the viewport. Controls hide after four seconds while playing;
  pause, buffering and errors keep them visible. First OK while hidden reveals
  controls. Audio and subtitles are chosen in details before playing.
- Episode autoplay defaults On, can be disabled for the current app session, and
  only advances after natural completion. Stop refreshes Home metadata.

Use ES5, XMLHttpRequest, basic DOM APIs, inline-block layouts and system fonts.
No frontend framework, external fonts, CSS grid or animation dependency. Root
font size is 16px, 11px up to 800px viewport height, and 8px up to 600px. Posters
use percentage widths; this is not a guarantee of Full HD/4K TV rendering.

The artwork cache, near-viewport image loading and retained recent screens reduce
repeat download/decode work. Scrolling must keep focused controls reachable above
the footer. Preserve loading, empty, missing-artwork and retry states. Verify
overscan, long text, wrapped buttons and keys on real hardware before claiming
compatibility with another VIDAA model.
