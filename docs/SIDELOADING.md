# Optional TV launcher: separate helper plus Vidafix add-on

The public package includes our own `sideload-addon/` configuration script and
installer-page template. It does not include the DNS/HTTPS helper server, its
certificates or private keys. No personal addresses or Plex tokens are included.

The downloadable helper is [trialuser/vidaa-appstore](https://github.com/trialuser/vidaa-appstore).
It is a separate alternative, not a verified source of the helper previously
used with the owner. The owner-tested helper remains excluded. The new add-on
uses the existing `vidplex-local` tile ID but has not yet been tested on a TV.

## Installation

1. Confirm Vidafix opens on the TV at `http://HOST-LAN-IP:8765/`.
2. Obtain the helper using its GitHub Code > Download ZIP menu and extract it
   outside Vidafix. Review its current README and terms.
3. Copy `sideload-addon/configure_vidafix.py` and
   `sideload-addon/vidafix-install.template.html` beside its server.py/config.json.
4. Follow [the add-on's complete instructions](../sideload-addon/READ_ME.txt).
   Run the configuration script and enter the Vidafix app host IP and installer
   computer IP. They can differ; neither field asks for the TV IP or Plex token.
5. Run the separately downloaded server. Use temporary DNS only on the TV,
   install from your local page, restore the original DNS, stop the helper and
   fully restart the TV. Keep the Vidafix app host running.

The script backs up config.json and generates vidafix-install.html. It selects
HTTPS 443, enables DNS for vidaahub.com and disables the unused HTTP listener.
It preserves the helper's server.py and configured TLS file paths. No firewall,
TV settings, key generation, downloads or server startup happen automatically.
To reconfigure or undo changes, see the add-on instructions.

The new installer page is standalone: no external scripts, catalogue or image
CDN. It offers only Install/Remove Vidafix and references the icon on your app
host. The Remove action targets the historical Vidafix tile, not Plex or media.
An accepted API callback is not proof of a working launcher.

## Redistribution and compatibility

The add-on is newly written Vidafix material under MIT; it is not copied helper
server source. No explicit licence file was visible in the reviewed upstream
repository. Source visibility is not redistribution permission: keep that
separate tool and generated settings out of Vidafix releases. Vendor APIs,
domain substitution and TV installation terms still need their own review.

This upstream DNS server returns errors for unmatched queries instead of acting
as a general internet resolver. Restore the TV's original DNS promptly, even
if installation fails. Review local TLS warnings deliberately and keep access
limited to the TV. Firmware may reject this installation path; browser access
is the fallback. The previously supplied helper's distinct instructions remain
in INSTALL_AND_CONFIGURE.txt section E2 for existing owners only.

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
