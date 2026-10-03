# Copyright (c) 2026 Vidafix contributors. Licensed under MIT; see LICENSE.
"""Configure a separately obtained trialuser/vidaa-appstore; no server code bundled."""
import argparse
import ipaddress
import json
from pathlib import Path
import uuid


def lan_ip(value):
    try:
        address = ipaddress.IPv4Address(value.strip())
    except ipaddress.AddressValueError:
        raise ValueError('Enter a private LAN IPv4 address, without a URL or port.') from None
    if not any(address in ipaddress.ip_network(network) for network in
               ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16')):
        raise ValueError('Use a private LAN IPv4 address reachable by the TV.')
    return str(address)


def configure(folder, app_ip, installer_ip, port=8765):
    app_ip, installer_ip = lan_ip(app_ip), lan_ip(installer_ip)
    if not 1 <= port <= 65535:
        raise ValueError('The app port must be between 1 and 65535.')
    folder = Path(folder).resolve()
    config_path = folder / 'config.json'
    if not (folder / 'server.py').is_file() or not config_path.is_file():
        raise ValueError('Run in the extracted trialuser/vidaa-appstore folder with server.py and config.json.')
    if config_path.is_symlink():
        raise ValueError('Use an ordinary config.json file, not a symbolic link.')
    original = config_path.read_bytes()
    try:
        config = json.loads(original.decode('utf-8-sig'))
    except (ValueError, UnicodeError):
        raise ValueError('The helper config.json is not valid UTF-8 JSON.') from None
    if not isinstance(config, dict) or not all(key in config for key in
                                              ('ssl_certfile', 'ssl_keyfile', 'html_file', 'dns_records')):
        raise ValueError('The helper configuration does not match the supported upstream format.')
    for key in ('ssl_certfile', 'ssl_keyfile'):
        if not isinstance(config[key], str) or not (folder / config[key]).is_file():
            raise ValueError('The helper certificate/key files must exist before configuration.')
    page_path = folder / 'vidafix-install.html'
    if page_path.exists():
        raise ValueError('vidafix-install.html already exists; keep a copy and remove it before reconfiguring.')
    settings = {'host': app_ip, 'url': 'http://%s:%s/' % (app_ip, port),
                'icon': 'http://%s:%s/static/vidafix.png' % (app_ip, port)}
    template = Path(__file__).with_name('vidafix-install.template.html').read_text(encoding='utf-8')
    if template.count('__VIDAFIX_SETTINGS__') != 1:
        raise ValueError('The Vidafix page template is missing or invalid.')
    page = template.replace('__VIDAFIX_SETTINGS__', json.dumps(settings))
    config.update(server_address=installer_ip, enable_dns_server=True,
                  enable_https_server=True, enable_http_server=False,
                  https_port=443, html_file=page_path.name,
                  dns_records=[{'hostname': 'vidaahub.com', 'type': 'A', 'address': installer_ip}])
    # Validate everything before mutation; never replace the helper's server or keys.
    backup = folder / ('config.before-vidafix-' + uuid.uuid4().hex + '.json')
    with backup.open('xb') as output:
        output.write(original)
    try:
        with page_path.open('x', encoding='utf-8') as output:
            output.write(page)
        config_path.write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')
    except OSError:
        config_path.write_bytes(original)
        raise
    return backup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--helper', default='.', help='Extracted upstream helper folder; defaults to current folder')
    parser.add_argument('--app-ip')
    parser.add_argument('--installer-ip')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    try:
        app_ip = args.app_ip or input('Vidafix app host LAN IPv4 address: ')
        installer_ip = args.installer_ip or input('This installer computer LAN IPv4 address: ')
        backup = configure(args.helper, app_ip, installer_ip, args.port)
        print('Configured. Original config saved as ' + backup.name)
        print('No server, key, firewall or TV settings were changed. See READ_ME.txt for installation.')
    except (ValueError, OSError, EOFError) as error:
        print('Configuration failed: ' + str(error))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
