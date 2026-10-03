# Vidafix validation

## Automated checks

Run from the project directory with dependencies installed:

```sh
.venv/bin/python -m unittest discover -s tests -v
node tests/navigation.test.cjs
node tests/player.test.cjs
node tests/subtitle-menu.test.cjs
node tests/sideload-addon.test.cjs
```

Python checks use synthetic metadata and a loopback fake Plex server. They cover
local server validation, authentication headers, library discovery/paging/sorting,
Home feeds, Watchlist matching, seasons, ratings, artwork cache limits/expiry,
playback sessions/progress/HLS resume, subtitle result binding/expiry and next
episode ordering. Service renderer tests cover path quoting and injection rejection.

JavaScript checks exercise remote focus and scrolling, player lifecycle/absolute
progress, natural completion versus manual Stop, and subtitle menu results,
dismissal, selection, late responses, empty results and errors. A DOM stub does
not prove hardware compatibility.

## Observed hardware and live checks

The owner reports library browsing, artwork, navigation, playback and play/pause
working in the installed app on Hisense 55U7HAU / VIDAA 6. Cache reuse and the
corrected subtitle search menu were reported working. The built-in TV browser's
pointer behaviour differs from the installed launcher.

Live Plex subtitle search and next-episode lookup succeeded during development.
Complete subtitle download/rendering, uninterrupted natural-end autoplay,
autoplay Off, last episode/movie completion and Home refresh remain explicit
hardware regression checks. Do not infer them from the offline suite.

## Before a release

1. Install dependencies in a fresh environment; configure with a test server.
2. Verify Home, each library, Title/Recently Added sorting and pages beyond 20.
3. Open series, season, episode; check each Back step and season artwork.
4. Check artwork reuse after changing screens and across helper restarts.
5. Play movie and episode: sound, subtitle download/selection, pause, seek, Stop,
   Resume, natural completion, next episode and autoplay Off.
6. Return Home after stopping; verify current progress and On Deck against Plex.
7. Test missing artwork, empty library, Plex unavailable, bad token and subtitle
   search failure; every error must leave a usable Back/Retry action.
8. Verify app access from a second device, systemd restart and planned reboot.
9. Review the public export and secret scan. Do not publish actual library
   screenshots, cached artwork, private config, credentials or old ZIP files.

The generic Linux service installer requires a Mint/systemd smoke test; rendering
its unit on Windows is not evidence that it has been installed successfully.

## Windows host checks

The Windows helper tests cover configuration preservation, dependency-install
failure, XML escaping for paths with spaces/ampersands, a per-user interactive
logon task with no password and no execution time limit, refusal to replace an
existing task, and Notepad UTF-8 BOM configuration support. No test registers,
starts or removes a real scheduled task or changes the firewall.

Before release, verify fresh Setup-Windows.cmd on a clean Windows installation,
LAN access, task registration/start/stop, sign-out/sign-in startup and updating
in place. Existing development-host success is not a fresh-install certification.

## Portable package verification â€” 2026-10-03

The portable export passed archive integrity, credential/private-key
checks, personal path/address checks and private-file exclusion checks. Linux
launch/setup scripts use LF endings; Windows command launchers use their own
folder instead of a fixed path. All 53 Python tests passed in the working folder
and from a clean extraction using the existing development interpreter and
dependencies. Navigation, player and subtitle-menu JavaScript checks passed.
Task Scheduler previously accepted the generated task XML without registration.
Fresh dependency installation, real scheduled task/sign-in and Linux boot checks
remain manual tests. The package contains source, not bundled Python or packages.

## Owner stability report — 2026-10-03

The owner reports multiple days of use with no issues. This supports a beta
stability claim for that installation; it is not a fresh Windows/Linux install
test or confirmation of every subtitle/autoplay regression case listed above.

## MIT release review - 2026-10-03

Both 53-file source/portable ZIPs passed allowlist, configured-secret/private-key
and archive-integrity checks. All 53 Python tests passed again in the working
folder and from a fresh portable extraction with existing dependencies. All three
JavaScript suites passed. pip check found no broken installed requirements; this
is a dependency consistency check, not a vulnerability audit. Sideloader code and
keys remain excluded. Privacy notice and separate upstream guide are included.
No live host changes, scheduled-task registration, commit or publication occurred.

## Sideload add-on checks

Offline add-on tests use temporary synthetic helper files. They verify distinct
app/installer hosts, private IPv4 validation, config backups, preserved server
and key paths, rejected invalid/missing settings and refusal to replace an
existing generated page. JavaScript checks verify installer arguments, historical
tile ID, local-domain/API checks and arrow/OK focus. No helper was downloaded,
started or installed on a TV by these checks. Real TV installation remains
pending for this new combination.

The add-on change passed all 57 Python tests and the new installer-page
JavaScript checks. The rebuilt 58-file public packages include only the
three generic add-on files, not a downloaded helper or generated settings.
