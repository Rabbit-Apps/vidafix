# Copyright (c) 2026 Vidafix contributors. Licensed under MIT; see LICENSE.
"""Build a reviewed source export. Never recursively package the working folder."""
import argparse
import configparser
import getpass
import hashlib
import os
from pathlib import Path
import re
from urllib.parse import urlsplit
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent.parent
TOP = ['README.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md', 'AGENTS.md', 'DESIGN.md',
       'TESTING.md', '.gitignore', '.gitattributes', 'config.example.ini', 'requirements.txt',
       'Setup-Windows.cmd', 'Start-Vidafix.cmd', 'Setup-Linux.sh', 'Start-Linux.sh',
       'QUICK_START.md', 'INSTALL_AND_CONFIGURE.txt', 'PRIVACY.md']
GROUPS = {
    'app': {'.html', '.css', '.js', '.png'},
    'server': {'.py'}, 'tests': {'.py', '.cjs'},
    'deploy': {'.py', '.sh', '.md', '.service'}, 'tools': {'.py'},
}
DOCS = ['docs/REFERENCES.md', 'docs/PUBLISHING.md', 'docs/SIDELOADER_REVIEW.md', 'docs/SIDELOADING.md',
        'sideload-addon/configure_vidafix.py', 'sideload-addon/vidafix-install.template.html',
        'sideload-addon/READ_ME.txt']


def export_files(root):
    files = [root / name for name in TOP + DOCS]
    for folder, suffixes in GROUPS.items():
        files.extend(p for p in (root / folder).iterdir() if p.is_file() and p.suffix in suffixes)
    for path in files:
        if path.is_symlink() or not path.is_file() or root.resolve() not in path.resolve().parents:
            raise ValueError('Missing or unsafe export file: ' + str(path.name))
    return sorted(files)


def sensitive_values(root):
    config = configparser.ConfigParser(interpolation=None)
    config.read(root / 'config.ini', encoding='utf-8-sig')
    values = [config.get('plex', 'token', fallback=''), os.environ.get('PLEX_TOKEN', '')]
    host = urlsplit(config.get('plex', 'server', fallback='')).hostname
    if host and host not in ('127.0.0.1', '::1', 'localhost'):
        values.append(host)
    user = getpass.getuser()
    if len(user) >= 6 and user.lower() not in ('runner', 'ubuntu', 'example'):
        values.append(user)
    return [v.encode() for v in values if len(v) >= 6]


def main():
    parser = argparse.ArgumentParser(description='Build a private-data-free Vidafix package')
    parser.add_argument('--portable', action='store_true', help='Name the output vidafix-portable.zip')
    args = parser.parse_args()
    files = export_files(ROOT)
    private_key = re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----')
    secrets = sensitive_values(ROOT)
    payloads = []
    for path in files:
        data = path.read_bytes()
        if path.suffix == '.sh':
            data = data.replace(b'\r\n', b'\n')
        if private_key.search(data) or any(value in data for value in secrets):
            raise ValueError('Private-data match; export stopped: ' + path.relative_to(ROOT).as_posix())
        payloads.append((path.relative_to(ROOT).as_posix(), data))
    destination = ROOT / 'dist'
    destination.mkdir(exist_ok=True)
    archive = destination / ('vidafix-portable.zip' if args.portable else 'vidafix-source.zip')
    with ZipFile(archive, 'w', ZIP_DEFLATED) as output:
        for name, data in payloads:
            output.writestr('vidafix/' + name, data)
    with ZipFile(archive) as check:
        if check.testzip() is not None:
            raise ValueError('Archive integrity check failed')
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.zip.sha256').write_text(digest + '  ' + archive.name + '\n', encoding='utf-8')
    print('Built', archive.name, 'with', len(payloads), 'reviewed source files; private-data checks passed.')


if __name__ == '__main__':
    main()
