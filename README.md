# Vidafix

Start here: [step-by-step installation instructions](INSTALL_AND_CONFIGURE.txt) or [portable package quick start](QUICK_START.md). The same source folder supports Windows and Linux; Python is required locally.

An independent, self-hosted Plex client for VIDAA TVs. Browse your own local libraries with a remote, load cached artwork, and play movies and episodes through your Plex Media Server.

**Beta.** Tested by the project owner on a Hisense 55U7HAU running VIDAA 6. Other models and firmware are unverified. Vidafix is not affiliated with, endorsed by, or an official product of Plex, VIDAA or Hisense.

## Features

- Every movie/show library appears under its Plex name, including Anime libraries. Library grids have 20-item pages and Title / Recently Added sorting.
- Home shows Continue Watching, On Deck and Recently Added for each library, up to 100 items per shelf.
- Series open seasons with Plex season artwork, then episodes.
- Details show metadata and provider-labelled ratings supplied by Plex. No ratings websites are queried.
- Play/Resume, audio/subtitle selection, pause and 30-second seeking. Controls hide while playing.
- Find subtitles opens a temporary menu using Plex's subtitle search/download feature. Choose a language, search, choose a result, then select the downloaded track before playing. Back/Cancel dismisses the menu.
- Episode autoplay has an On/Off toggle (default On until changed; resets when the app reloads). Only natural completion starts the next local episode, from the beginning. Movies, manual Stop and playback errors never trigger it.
- Playback completion/Stop refreshes Home progress and On Deck metadata. Plex determines watched thresholds and eligible items.
- Artwork caching on disk and in the browser, deferred poster loading and retained recent screens reduce repeat loads.
- Optional read-only Plex Watchlist, matched to media on your configured local server.

No Discover recommendations, cloud media playback, music, Live TV, rentals, PIN sign-in, full-text search or multiple-server selection. Existing subtitle/audio tracks are selected before playback; stop and resume to change them.

## Requirements

- Linux Mint or Windows 10/11 with Python **3.9+**, venv, pip and access to your Plex server. Use a currently supported Python release; Python 3.12 is the development baseline. Windows 11 is the preferred Windows target.
- One Plex Media Server and its authentication token, with movie/show libraries already configured.
- A TV and host on the same trusted LAN. Keep the host's IP stable with a router DHCP reservation.
- A TV browser/app supporting native HLS and the remote key events used by Vidafix. The built-in browser may use a pointer instead; an installed launcher behaved better on the tested TV.
- Working Plex transcoding where required and enough server capacity. Node is optional for development tests only.

## Install on Windows

1. Install Python from [python.org](https://www.python.org/downloads/windows/), including pip and the Python launcher (`py`). If the launcher is unavailable, make `python` available on PATH instead.
2. Extract the source ZIP fully into a permanent folder you own, such as a Vidafix folder under your user directory. Do not run inside the ZIP, put the app in Program Files, or reuse a Linux `.venv` on Windows. Avoid shared/cloud-synced folders because config.ini contains a credential.
3. Double-click **Setup-Windows.cmd**. It creates `.venv`, installs requirements from pip, and creates config.ini only if absent. Keep internet access available during setup; read any error before closing the window.
4. Open **config.ini** in Notepad. Set your Plex server and token using the shared configuration instructions below. Use `http://127.0.0.1:32400` if Plex is on this Windows PC, or the Plex host's private LAN address otherwise.
5. Double-click **Start-Vidafix.cmd**. Leave its window open; Ctrl+C stops it. Open `http://127.0.0.1:8765/` on this PC, then `http://WINDOWS-LAN-IP:8765/` on the TV. Use `ipconfig` to find the active Ethernet/Wi-Fi IPv4 address.

Neither script changes firewall settings or installs a scheduled task automatically. If Windows Firewall asks, allow this app on your trusted **Private** home network only. If LAN access is blocked, use Windows Defender Firewall's advanced settings to allow inbound TCP on the configured port (default 8765), restricted to Private and Local subnet or the TV IP. Do not enable Public-network access, disable the firewall or forward the port on your router.

For command-line use, open PowerShell in the app folder:

```powershell
# Equivalent setup when the Python launcher is installed:
py -3 -m tools.windows setup
# Offline configuration/environment check (does not contact Plex):
.\.venv\Scripts\python.exe -m tools.windows check
# Run manually:
.\.venv\Scripts\python.exe -m tools.windows run
```

Keep Windows awake while watching. Locking the desktop is fine; sleep, shutdown and signing out can interrupt hosting. Windows hosting does not add HLS support to desktop browsers: the TV remains the intended playback client.

### Windows automatic startup (after sign-in)

After verifying manual operation, close the foreground server with Ctrl+C. In PowerShell from the app folder:

```powershell
.\.venv\Scripts\python.exe -m tools.windows install-startup
.\.venv\Scripts\python.exe -m tools.windows startup-start
.\.venv\Scripts\python.exe -m tools.windows startup-status
```

This creates an account-specific **Vidafix-...** Task Scheduler task, with no stored password and no elevated runtime privileges. It runs hidden through pythonw.exe, starts when **that account signs in**, and retries a failed process up to three times. It does not provide unattended startup before sign-in. Windows policy may require an elevated terminal to register a task: if access is denied, retry from an administrator terminal using the **same account**, not a different administrator's account.

Registration alone does not start the server immediately; `startup-start` does. Do not run the task and Start-Vidafix.cmd at the same time. Background logs are in `.logs/vidafix.log` (rotated); an early failure creates `.logs/startup-error.log`. Inspect them locally, and redact private details before sharing. Store your token in config.ini for predictable background startup; shell-only environment overrides are not inherited by the scheduler.

```powershell
# Stop the scheduled server for an update:
.\.venv\Scripts\python.exe -m tools.windows startup-stop
# Remove automatic startup and stop its task:
.\.venv\Scripts\python.exe -m tools.windows remove-startup
```

Keep the app and Python installation at their original paths. To move the app, remove its task first, move source/config, recreate `.venv` with setup in the new location, and register again. Registration refuses to overwrite an existing Vidafix task. Removal affects only this account's Vidafix task, not Plex or unrelated Python processes.

## Install on Linux Mint

Download/extract the reviewed source package (or clone this repository after it is published). The source package contains a `vidafix` folder. Run the following inside that folder:

```sh
sudo apt update
sudo apt install python3 python3-venv python3-pip
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp config.example.ini config.ini
chmod 600 config.ini
nano config.ini
```

Do not copy the example over an existing configured `config.ini` during an upgrade.

### Configuration (both platforms)

Set the following locally:

```ini
[plex]
server = http://127.0.0.1:32400
token = YOUR_PLEX_TOKEN
library =

[web]
listen = 0.0.0.0
port = 8765
```

Use `127.0.0.1` for Plex on the same host. For a separate Plex host, use its literal private LAN IP and port. Hostnames, public IPs, credentials in the URL and URL paths are rejected. HTTPS requires a certificate trusted by Python; certificate verification is not disabled. Leave `library` blank; Home is the default view and all supported libraries are discovered.

Get your token using [Plex's official instructions](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/). Never post it in issues, screenshots or URLs. The `PLEX_TOKEN` environment variable overrides the INI token; `VIDAA_CONFIG` can select a different config path. For automatic startup, storing the token in the protected INI file is simplest: interactive shell environment variables do not automatically reach systemd.

Start Vidafix:

```sh
.venv/bin/python -m server.app
```

Open `http://127.0.0.1:8765/` on the host. On another PC or the TV, open `http://HOST-LAN-IP:8765/`, replacing `HOST-LAN-IP` with the Linux host's address. Use `hostname -I` on Linux to help identify it. Do **not** open `app/index.html` directly or use `127.0.0.1` from the TV.

Check the page from another device before attempting TV installation. If a firewall is enabled, allow TCP 8765 only from your TV or trusted LAN. Do not disable the firewall or forward this port through the router.

## Linux automatic startup at boot

After a successful manual run, stop it with Ctrl+C. From the app folder, as your normal Linux account:

```sh
sh deploy/install-service.sh
```

The installer uses the current app location and account, requires an existing `.venv` and `config.ini`, and asks sudo to install/start the service. It neither configures Plex nor changes the firewall. The service keeps the historical name **vidplex** so existing installations upgrade without a second competing service.

```sh
sudo systemctl status vidplex --no-pager
sudo systemctl restart vidplex
sudo journalctl -u vidplex -n 50 --no-pager
```

Keep the folder at the same path after installation. Verify startup after your next planned reboot. To stop and disable startup: `sudo systemctl disable --now vidplex`. More details: [service setup](deploy/README.md).

## TV access and launcher

Open `http://HOST-LAN-IP:8765/` in the TV browser first. The public package includes our own [sideload add-on](sideload-addon/READ_ME.txt): copy its two files into a separately downloaded helper and enter your host addresses. The helper server and its TLS credentials are **not** bundled; the previously supplied helper has unresolved redistribution provenance. The new add-on/helper combination still needs a TV test. See [separate sideloader sourcing and configuration](docs/SIDELOADING.md) and the [sideload review](docs/SIDELOADER_REVIEW.md). This is not a VIDAA Store release, and installing a TV tile is not guaranteed on other firmware.

An existing Vidafix tile continues to work as long as its server address and port stay the same. Normal server updates do not require reinstalling that tile. The historical `vidplex-local` launcher ID and old icon URLs are compatibility aliases, not current product branding.

## Controls

| Control | Action |
| --- | --- |
| D-pad / arrows | Move between buttons, posters and rows |
| OK / Enter | Open the focused item or activate a button |
| Back / Escape / Backspace | Close a subtitle menu, return through seasons/details, or stop playback |
| Play / Pause | Toggle playback on supported remotes |
| Onscreen Back/Forward | Seek 30 seconds |

Find subtitles has a vertical results menu: Up/Down and OK select a download. Error/empty states remain dismissible. At playback completion the next episode starts only when autoplay is On. The last episode returns to details.

## Playback and network limitations

Native HLS is proxied through Vidafix. The current profile requests H.264/AAC stereo, up to 1080p at 8 Mbps. Plex can Direct Stream compatible streams or transcode as necessary; this is not original-file Direct Play. Selected subtitles are burned in by Plex and can require video conversion. Global Plex settings are not changed. Only the first media version and single-part items are supported.

Progress is reported every 10 seconds and on pause, seek and Stop. Closing the app abruptly can lose recent progress. Resume starts at the containing media segment; seeking before that starting point creates a new session. Compatibility and buffering depend on the TV, file and server.

The helper has **no login**. Anyone able to reach it can use the configured Plex account's exposed library/playback functions, including subtitle downloads. Keep it on a trusted LAN; do not publish it to the internet. Plex credentials remain on the backend.

Local browsing/playback use the configured server. Optional Watchlist contacts Plex's account service and requires an account-capable token and internet access. Subtitle search/download is delegated to Plex, which contacts its provider and also needs internet. These features can fail independently of local playback.

## Artwork cache

`.cache/artwork.sqlite3` stores up to 256 MiB of original image payload (database overhead is extra), with a 24-hour expiry and least-recently-used eviction. The folder must be writable by the service account. `VIDAA_ART_CACHE` can override the database path. The cache separates server/token identities without storing the token itself.

Browser artwork caches last one hour; recent screens retain poster elements for five minutes, with up to two inactive views. Artwork changes can take the server and browser cache lifetimes to appear. To clear the server cache, stop Vidafix, remove only `.cache/artwork.sqlite3` inside its app directory, then restart. Never include this cache or library screenshots in a source release.

## Updating an existing installation

### Windows

Stop the foreground server or use `startup-stop`. Copy updated source into the existing folder, preserving config.ini, .venv and .cache. Run Setup-Windows.cmd to update dependencies; it keeps your configuration. Restart with Start-Vidafix.cmd or `startup-start`, then fully reopen the TV app. Do not copy a Linux virtual environment onto Windows.

### Linux

Back up your private config securely. Stop the service, copy the new source files into the **existing app directory**, preserving `config.ini`, `.venv` and `.cache`, then run from that directory:

```sh
.venv/bin/python -m pip install -r requirements.txt
sudo systemctl start vidplex
```

Run `sudo systemctl stop vidplex` before copying. The reviewed public ZIP has a `vidafix/` top-level folder; copy its contents into the existing app directory if that directory has a different name. Do not nest it inside the current app. Fully close/reopen the TV app; on desktop use Ctrl+F5. Do not run a second manual server alongside systemd.

## Troubleshooting

- **Works on host, not TV:** use the host's LAN address, check TCP 8765/firewall, and ensure neither device uses guest Wi-Fi/client isolation or a conflicting VPN.
- **Connection refused:** confirm the service is running. **Address already in use:** stop the duplicate foreground process before restarting systemd.
- **No libraries / authentication error:** check the server address, token and token owner's library access. Do not share your config while requesting help.
- **No playback:** confirm native HLS support and Plex transcoding. Some desktop browsers cannot play native HLS even when the TV can.
- **No subtitles found:** try another language/title and confirm Plex's own subtitle search works. After a successful download, allow Plex time to add the track, then reopen details if necessary.
- **Remote Back/arrows not received:** try the installed app if available; `/?debug=1` shows received key codes. Firmware can intercept keys before the page sees them.
- **Old UI after update:** restart the helper and fully exit/reopen the TV app.

## Development and validation

```sh
.venv/bin/python -m unittest discover -s tests -v
# Optional JavaScript tests, with Node installed:
node tests/navigation.test.cjs
node tests/player.test.cjs
node tests/subtitle-menu.test.cjs
```

On Windows, replace `.venv/bin/python` in these commands with `.\.venv\Scripts\python.exe`.

Run `.venv/bin/python -m tests.preview` for synthetic browsing data at `http://127.0.0.1:8766/` without a token. This fixture is not a live playback test. See [testing notes](TESTING.md) for verified and pending hardware checks.

Structure: `app/` frontend; `server/` Flask, Plex adapter, playback and artwork cache; `deploy/` systemd setup; `tests/` offline checks; `tools/` reviewed source packaging. No build step or Node runtime is required to run Vidafix.

## Unofficial status and review

Vidafix and its optional sideload installation method are unofficial and are
not affiliated with, endorsed by or approved by Plex, VIDAA or Hisense.

Reasonable steps have been taken to review publication-related legal questions:
we reviewed the publicly available vendor terms, checked the helper's available
licensing information, adopted MIT for our own code, documented privacy practices,
and excluded third-party helper code, credentials and personal settings from the
release. These checks are documented in docs/PUBLISHING.md and
docs/SIDELOADER_REVIEW.md.

This is a limited project review, not legal advice, a legal opinion or confirmation
that every use or installation method is permitted. Vendor authorization for the
DNS-based installation method has not been established. Applicable terms and laws
may differ by location and device. Users should review the terms applicable to
their own equipment and use only media they are entitled to access.

## Licence and publication

Vidafix is licensed under the [MIT License](LICENSE), allowing use, modification, redistribution and sale with its copyright and permission notices retained. Third-party software retains its own terms; see [third-party notices](THIRD_PARTY_NOTICES.md). See the [privacy notice](PRIVACY.md) for local storage and network requests.

Publish only the reviewed source export, not the working folder or old deployment/sideload ZIPs. See [publication audit](docs/PUBLISHING.md). The licence and review do not provide trademark clearance or authorization for vendor APIs/sideloading.
