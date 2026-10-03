# Vidafix automatic startup on Linux

Finish the [main setup](../README.md) and confirm the manual server works first.
Stop it with Ctrl+C. Run `sh deploy/install-service.sh` from the app directory
as its normal owner, not root. The installer derives the app path and account,
protects config.ini, renders the unit template, then uses sudo to install and
start it. An interactive PLEX_TOKEN is not inherited: configure config.ini.

The retained service name is `vidplex` for upgrade compatibility. Its display
description is Vidafix. Re-running replaces that unit with the current account
and path; only do so for the installation you intend to serve. It never modifies
Plex Media Server. Do not start a manual copy while this service owns the port.

```sh
sudo systemctl status vidplex --no-pager
sudo systemctl restart vidplex
sudo journalctl -u vidplex -n 50 --no-pager
sudo systemctl disable --now vidplex
```

The last command stops Vidafix and disables startup; it leaves files and Plex
intact. Test startup after a planned reboot. Keep the app directory at the same
path, writable by the service account (including .cache), and outside temporary
folders. If you move it, rerun the installer there. Paths containing quotes,
backslashes or line breaks are rejected. Spaces and literal percent signs are
handled by the renderer.

For updates: stop the service, copy source into its existing directory without
overwriting config.ini, update dependencies with `.venv/bin/python -m pip install
-r requirements.txt`, then start the service. See the main README for copying a
public package into an older directory layout.

An address-in-use error usually means a duplicate foreground process. Stop
that process before restarting. For other errors, inspect the journal locally;
redact credentials, server addresses and library metadata before sharing logs.
The template is not an installable unit until render_service.py substitutes it.
