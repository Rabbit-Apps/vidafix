VIDAFIX ADD-ON FOR A SEPARATELY DOWNLOADED SIDELOAD HELPER

These are newly written Vidafix files under the project's MIT licence. They
contain no personal host settings, Plex token, server code or TLS credentials.
They are not a repackaged copy of the previously supplied sideloader.

1. Confirm your running Vidafix host works in the TV browser.
2. Download https://github.com/trialuser/vidaa-appstore using Code > Download ZIP.
   Extract it to a SEPARATE folder. Check its current terms and README.
3. Copy configure_vidafix.py and vidafix-install.template.html from this add-on
   into that extracted folder, beside its server.py and config.json.
   Do not replace server.py, index-en.html or its certificate/key files.
4. In a terminal in the helper folder, run:
     Windows: py -3 configure_vidafix.py
     Linux:   python3 configure_vidafix.py
   Enter the Vidafix app host's LAN IPv4 address, then the installer computer's
   LAN IPv4 address. They can be the same, but neither is the TV IP. The default
   app port is 8765; append --port NUMBER if you configured a different app port.
   No Plex token is requested. The script makes vidafix-install.html and backs
   up config.json before selecting the Vidafix page, DNS and HTTPS port 443.
5. Install the helper's dependency using your chosen Python environment:
     Windows: py -3 -m pip install dnslib
     Linux:   python3 -m venv .venv
              .venv/bin/python -m pip install dnslib
   Python already includes ssl. Use the same interpreter to run the helper.
6. Review the helper's certificate/key and local network access before starting.
   The add-on preserves its configured TLS paths; it does not generate or
   redistribute credentials. Do not reuse a public shared key for other services.
   If replacing TLS files, supply your own certificate for vidaahub.com using
   the helper's documented paths. Review the upstream tool's current instructions.
7. Run the helper server from ITS folder:
     Windows: py -3 server.py
     Linux:   .venv/bin/python server.py
   Ports UDP 53 and TCP 443 may need elevated privileges. Do not run the Vidafix
   app as administrator/root. Use your platform's permitted method for this
   temporary helper. On Windows, if access is denied, use an administrator
   PowerShell window in the helper folder. On Linux, if binding is denied, run
   sudo .venv/bin/python server.py from the helper folder. Review the downloaded
   code before granting privileges. Firewall access should be limited to the TV.
   Check BOTH DNS and HTTPS have started; no other service may occupy those ports.
8. Record the TV's ORIGINAL DNS setting. Change only the TV's DNS temporarily to
   the INSTALLER COMPUTER IP. Do not change router DNS or other devices.
9. Visit https://vidaahub.com in the TV browser. Confirm you are using your own
   local helper before deciding to accept its certificate warning. Choose
   Install Vidafix. A successful callback is not proof the tile works.
10. Restore the TV's ORIGINAL DNS immediately, including after failure, then
    stop the helper with Ctrl+C. This upstream DNS server rejects unmatched
    queries, so normal TV internet access may fail during installation.
11. Fully restart the TV and test the Vidafix tile. Keep the app host running.

The page uses the existing vidplex-local tile ID so it can update the launcher
previously used with Vidafix. Its Remove button targets only that tile. It does
not delete media or uninstall Plex. Do not click Remove just to apply an update.

This combination is not yet tested on a real TV. The old helper was tested;
this upstream server with our new page is a separate installation path. Firmware
may reject the API or HTTP allowance. Browser access is the fallback.

To change addresses: stop the helper, retain your generated page privately,
remove vidafix-install.html, then rerun configuration. Each run saves a separate
original-config backup. To undo helper configuration, restore the desired backup
as config.json while the helper is stopped. Configured files/backups contain your
addresses: keep them OUTSIDE the public Vidafix folder and do not upload them.

No helper is automatically downloaded or started. Our licence does not grant
rights over that separate tool or vendor APIs. See docs/SIDELOADER_REVIEW.md.

UNOFFICIAL STATUS AND REVIEW

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
