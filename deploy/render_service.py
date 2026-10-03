# Copyright (c) 2026 Vidafix contributors. Licensed under MIT; see LICENSE.
"""Render a systemd unit without installing it or reading Plex credentials."""
import getpass
from pathlib import Path
import re


def render(app_dir, user):
    app_dir = str(app_dir)
    if not app_dir.startswith('/') or any(c in app_dir for c in '\r\n\x00"\\'):
        raise ValueError('Use an absolute Linux path without quotes, backslashes or line breaks.')
    if not re.fullmatch(r'[a-zA-Z_][a-zA-Z0-9_-]*[$]?', user):
        raise ValueError('Unsupported Linux account name.')
    # systemd interprets percent specifiers even inside quoted values.
    escaped = app_dir.replace('%', '%%')
    template = Path(__file__).with_name('vidplex.service').read_text(encoding='utf-8')
    return template.replace('@APP_DIR@', escaped).replace('@USER@', user)


if __name__ == '__main__':
    print(render(Path(__file__).resolve().parent.parent, getpass.getuser()), end='')
