#!/bin/sh
set -eu
app_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$app_dir"
if [ ! -x .venv/bin/python ] || [ ! -f config.ini ]; then
    echo 'Run sh Setup-Linux.sh and configure config.ini first.' >&2
    exit 1
fi
echo 'Vidafix: leave this terminal open. Ctrl+C stops the server.'
exec .venv/bin/python -m server.app
