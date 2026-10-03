# Vidafix publication audit

Reviewed 2026-10-03. Nothing has been committed, pushed or published by this audit.

## What is ready

- A rewritten README covers prerequisites, tokens/configuration, Linux startup,
  LAN access, systemd, updates, controls, cache, limitations and troubleshooting.
- Product-facing names use Vidafix. Historical protocol headers, JavaScript
  identifiers, launcher/icon aliases and the vidplex service name are retained
  for compatibility, not advertised as alternate product names.
- Generic service setup derives the account and path; no personal deployment
  path is embedded in the distributable unit template.
- tools/build_public_release.py creates a source-only ZIP using an allowlist,
  scans it against local configured credentials and private-key markers, and
  writes a SHA-256 file. Ignore rules provide a second layer of protection.

## Private data findings and treatment

| Finding | Treatment |
| --- | --- |
| Real Plex token in local config.ini | Preserved locally; never printed, ignored and excluded |
| Local TLS private key/certificate in sideload helper | Whole helper excluded; personal files preserved |
| Old sideload archives containing a private key | Remain outside public package; never upload them |
| Personal server addresses and Linux paths in setup docs/service | Removed from public instructions; installer now derives its path/account |
| Helper-specific personal host settings | Preserved only in the ignored local helper |
| Logs, cached artwork/database, virtual environment and bytecode | Excluded |
| Real-library screenshots and historical viewing/count details | Screenshots excluded; testing notes rewritten without private library history |
| Original supplied project specification | Preserved as a local reference; omitted from public export |

The configured Plex token was checked against current app files and existing
project deployment/sideload ZIP contents. It was found in the private config,
not those ZIPs. This is an exact-token and pattern/provenance review, not a
claim that no possible unknown secret exists. The export scanner also checks
a configured environment token, private-key markers, the current Windows user
path/name and the configured non-loopback Plex host. It prints file names only.

No Git repository was present in the app folder or its parent chain during the
review, so there was no Git history to inspect. If publishing from another
repository or importing previous history, scan that history separately. Ignore
rules do not remove already-tracked files.

## Licence choice

The owner approved replacing the custom no-sale licence with standard MIT,
including permission for commercial use and sale. LICENSE now contains MIT;
README, installation instructions and project rules agree. Original source
files carry copyright/licence notices. Dependencies retain their own licences.
[MIT licence text](https://opensource.org/license/mit).

A new PRIVACY.md describes storage, LAN access, logs, optional Watchlist requests
and Plex-mediated subtitle downloads. It is linked from README and included in
both release ZIPs. No developer analytics endpoint is present in reviewed source.

[Plex's current terms](https://www.plex.tv/about/privacy-legal/plex-terms-of-service/)
define clients as Interfacing Software and require a privacy notice and source
copyright notice. Their redistribution provision includes sale and sublicensing;
MIT removes the former no-sale mismatch. This does not establish compliance with
all Plex restrictions: its separate functionality, acceptable-use and security
clauses still warrant review for the actual client. No vendor clearance or
legal opinion is claimed, and no request has been sent to Plex.

## Branding review

Public visible branding is Vidafix, with a non-affiliation statement. Vendor
names identify compatibility, and no official vendor logo is bundled as the app
icon. Legacy identifiers remain solely for existing installations.

The name is not unique: [Gips markets Vidafix building products](https://gips-ad.com/en/products/vida)
and [an independent store uses Vidafix](https://vidafix.store/pages/contact).
[WIPO's historical gazette](https://www.wipo.int/edocs/madgdocs/en/2008/madrid_g_2008_25.pdf)
records VIDAFIX for GIPS, international registration 965375, with class 1
chemical/building adhesive products. Historical records do not establish current
registration status or a software conflict. No current jurisdiction/class
clearance search has been completed. Keep Vidafix as the working name, without
claiming trademark ownership, registration or clearance. Seek trademark advice
or choose a more distinctive name before making branding commitments.

## Remaining publication limits

1. The sideload helper cannot be represented as cleared for redistribution;
   it is excluded. See SIDELOADER_REVIEW.md. The public client can be served in a
   TV browser; installation/remote behaviour there varies by firmware.
2. The generic systemd installer needs a fresh Linux Mint install/reboot check.
   Windows unit-renderer tests do not replace that check.
3. Complete the hardware playback/subtitle/autoplay checks in TESTING.md.
4. The name and vendor API terms have not received legal clearance. Review
   [Plex trademarks](https://www.plex.tv/about/privacy-legal/plex-trademarks-and-guidelines/)
   and [Plex terms](https://www.plex.tv/about/privacy-legal/plex-terms-of-service/)
   for the actual intended distribution. A disclaimer is not a permission grant.
5. Dependency ranges remain unpinned; a reproducible lock and dependency-security
   review are separate follow-up work, not completed by this private-data audit.

## Creating the reviewed public source ZIP

```sh
.venv/bin/python tools/build_public_release.py
```

Output is dist/vidafix-source.zip and its SHA-256 file. Extract it into a clean
folder and inspect it before creating the GitHub repository. It contains source,
docs, tests and original app icons; no installer helper, real config, cache or
screenshots. Publish from that clean folder, **not the parent ChatGPT workspace**.
No command here creates a repository, commits, pushes or changes the live server.

## Verification recorded for this export

Current validation is recorded in TESTING.md. Tests use synthetic data and do
not certify fresh installations or all TV firmware. The source export excludes
private config, keys, helper files, cache, logs and original reference material.
No live-server upgrade, commit or push was performed by this review.

## Windows hosting addition

The source export now also includes Setup-Windows.cmd, Start-Vidafix.cmd and
tools/windows.py. They contain no credentials or personal paths. Optional
automatic startup uses a current-user Task Scheduler logon trigger, not a
password-bearing Windows service. The task name is derived locally from the
account SID. Logs stay in the ignored .logs folder. Fresh Windows setup and
actual task registration/sign-in verification remain release checks.

## Portable archive — 2026-10-03

Use `.venv/bin/python tools/build_public_release.py --portable` (or the Windows
virtual-environment interpreter) to produce dist/vidafix-portable.zip with the
same reviewed source plus QUICK_START.md and both platforms' setup/launchers.
The archive requires Python and dependency installation on its destination.
It excludes local credentials/settings, personal deployment paths, screenshots,
cache/logs, virtual environments and the sideload helper. Distribute the clean
archive rather than a folder after it has been configured for private use.

## Separate sideloader guidance

SIDELOADING.md links one upstream alternative and documents the app/icon entries
without copying or bundling that tool. No explicit licence file was visible in
the reviewed upstream repository. It is not verified as the supplied helper's
source, nor tested here. Exclusion removes that material from our distribution;
it does not settle vendor terms for end-user installation.

## Public Vidafix add-on - 2026-10-03

The public export now includes sideload-addon/configure_vidafix.py, an original
standalone installer-page template and READ_ME.txt under MIT. These are newly
written files, not a redistributed copy of the supplied/upstream server. The
configuration script backs up a separately downloaded tool's config, preserves
server.py/TLS paths and generates only a Vidafix page/settings. Generated personal
files belong outside this public source folder. The DNS/HTTPS server and all
credentials remain excluded. Offline checks do not prove this combination works
on the TV; the previous helper's hardware result does not transfer to this one.

## Public review statement - 2026-10-03

README, installation instructions and add-on instructions now identify the
method as unofficial and summarize reasonable review steps. This describes the
bounded work actually performed; it does not claim a lawyer's review, vendor
approval or compliance certification. Published VIDAA terms were consulted,
but the contract applicable to each owner's device/region has not been verified.
Firmware support status does not itself establish installation permission.
