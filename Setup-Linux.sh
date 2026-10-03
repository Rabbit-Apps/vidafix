#!/bin/sh
set -eu
app_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$app_dir"
if [ -d .venv ] && [ ! -x .venv/bin/python ]; then
    echo 'This .venv belongs to another platform or Python installation. Recreate it locally.' >&2
    exit 1
fi
if [ ! -x .venv/bin/python ]; then
    python3 -m venv .venv
fi
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -c 'from pathlib import Path; p=Path("config.ini"); p.exists() or p.write_text(Path("config.example.ini").read_text(), encoding="utf-8")'
chmod 600 config.ini
echo 'Setup complete. Edit config.ini locally, then run sh Start-Linux.sh.'
