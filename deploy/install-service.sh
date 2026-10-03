#!/bin/sh
# Vidafix: run as the normal account that owns this app, not as root.
set -eu
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
app_dir=$(CDPATH= cd -- "$script_dir/.." && pwd)
if [ "$(id -u)" -eq 0 ]; then
    echo 'Run as the normal app account, without sudo; the installer requests sudo when needed.' >&2
    exit 1
fi
if [ ! -x "$app_dir/.venv/bin/python" ] || [ ! -f "$app_dir/config.ini" ]; then
    echo 'Create .venv, install requirements and configure config.ini first.' >&2
    exit 1
fi
command -v systemctl >/dev/null
"$app_dir/.venv/bin/python" -c 'import flask, requests, waitress'
unit_file=$(mktemp)
trap 'rm -f -- "$unit_file"' EXIT HUP INT TERM
"$app_dir/.venv/bin/python" "$script_dir/render_service.py" > "$unit_file"
chmod 600 "$app_dir/config.ini"
sudo install -m 644 "$unit_file" /etc/systemd/system/vidplex.service
sudo systemctl daemon-reload
sudo systemctl enable vidplex.service
sudo systemctl restart vidplex.service
sudo systemctl --no-pager --full status vidplex.service
echo 'Vidafix is enabled at boot. Check its LAN URL from another device.'
