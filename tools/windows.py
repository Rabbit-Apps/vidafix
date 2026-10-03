# Copyright (c) 2026 Vidafix contributors. Licensed under MIT; see LICENSE.
"""Windows setup, foreground launch and per-user logon task management."""
import argparse
import configparser
import csv
import io
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re
import runpy
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent


def python_path(root=ROOT, windowless=False):
    return root / '.venv' / 'Scripts' / ('pythonw.exe' if windowless else 'python.exe')


def copy_config(root=ROOT):
    """Exclusive creation prevents setup/upgrades from overwriting credentials."""
    try:
        with (root / 'config.ini').open('x', encoding='utf-8') as target:
            target.write((root / 'config.example.ini').read_text(encoding='utf-8'))
    except FileExistsError:
        return False
    return True


def setup(root=ROOT):
    if sys.version_info < (3, 9):
        raise RuntimeError('Install Python 3.9 or later from python.org first.')
    executable = python_path(root)
    if not executable.exists():
        if (root / '.venv').exists():
            raise RuntimeError('An incompatible .venv exists. Use a separate Windows copy of the source.')
        subprocess.run([sys.executable, '-m', 'venv', str(root / '.venv')], check=True)
    subprocess.run([str(executable), '-m', 'pip', 'install', '-r', str(root / 'requirements.txt')], check=True)
    created = copy_config(root)
    print('Created config.ini.' if created else 'Kept your existing config.ini unchanged.')
    print('Edit config.ini with Notepad, set your Plex server/token, then run Start-Vidafix.cmd.')


def validate(root=ROOT):
    if not python_path(root).is_file() or not (root / 'config.ini').is_file():
        raise RuntimeError('Run Setup-Windows.cmd and edit config.ini first.')
    config = configparser.ConfigParser(interpolation=None)
    try:
        config.read(root / 'config.ini', encoding='utf-8-sig')
    except configparser.Error:
        raise RuntimeError('Invalid config.ini syntax. Check its sections and key=value lines locally.') from None
    token = os.environ.get('PLEX_TOKEN') or config.get('plex', 'token', fallback='')
    if not token.strip() or token == 'YOUR_PLEX_TOKEN':
        raise RuntimeError('Set your Plex token in config.ini first. Never share that file.')
    # Offline validation only: no contact with Plex or port binding.
    from server.plex_api import local_server
    local_server(config.get('plex', 'server', fallback='http://127.0.0.1:32400'))
    port = config.getint('web', 'port', fallback=8765)
    if not 1 <= port <= 65535:
        raise RuntimeError('Configure a web port between 1 and 65535.')
    return port


def task_identity():
    result = subprocess.run(['whoami', '/user', '/fo', 'csv', '/nh'], check=True, capture_output=True, text=True)
    rows = list(csv.reader(io.StringIO(result.stdout)))
    sid = rows[0][-1].strip() if rows else ''
    if not re.fullmatch(r'S-1-[0-9-]+', sid):
        raise RuntimeError('Cannot determine the current Windows account SID.')
    return sid, 'Vidafix-' + sid


def task_xml(root, sid):
    """No passwords/tokens in task definitions. XML escapes paths with spaces/&."""
    if not re.fullmatch(r'S-1-[0-9-]+', sid):
        raise ValueError('Invalid Windows SID')
    namespace = 'http://schemas.microsoft.com/windows/2004/02/mit/task'
    ET.register_namespace('', namespace)
    def child(parent, tag, value=None, **attrs):
        node = ET.SubElement(parent, '{' + namespace + '}' + tag, attrs)
        if value is not None:
            node.text = str(value)
        return node
    task = ET.Element('{' + namespace + '}Task', {'version': '1.2'})
    registration = child(task, 'RegistrationInfo')
    child(registration, 'Description', 'Vidafix: start after this user signs in. No stored password.')
    trigger = child(child(task, 'Triggers'), 'LogonTrigger')
    child(trigger, 'Enabled', 'true'); child(trigger, 'UserId', sid)
    principal = child(child(task, 'Principals'), 'Principal', id='User')
    child(principal, 'UserId', sid); child(principal, 'LogonType', 'InteractiveToken')
    child(principal, 'RunLevel', 'LeastPrivilege')
    settings = child(task, 'Settings')
    child(settings, 'MultipleInstancesPolicy', 'IgnoreNew')
    child(settings, 'DisallowStartIfOnBatteries', 'false')
    child(settings, 'StopIfGoingOnBatteries', 'false')
    child(settings, 'StartWhenAvailable', 'true')
    child(settings, 'ExecutionTimeLimit', 'PT0S')
    retry = child(settings, 'RestartOnFailure')
    child(retry, 'Interval', 'PT1M'); child(retry, 'Count', '3')
    action = child(child(task, 'Actions', Context='User'), 'Exec')
    child(action, 'Command', python_path(root, True))
    child(action, 'Arguments', '-m tools.windows background')
    child(action, 'WorkingDirectory', root)
    return ET.tostring(task, encoding='utf-16', xml_declaration=True)


def manage_task(action, root=ROOT):
    sid, name = task_identity()
    if action == 'install-startup':
        validate(root)
        if not python_path(root, True).is_file():
            raise RuntimeError('Missing pythonw.exe; recreate the Windows virtual environment.')
        # Refuse to silently replace an existing task/installation.
        existing = subprocess.run(['schtasks', '/Query', '/TN', name], capture_output=True)
        if existing.returncode == 0:
            raise RuntimeError('A Vidafix task already exists. Remove it before changing its installation.')
        import tempfile
        with tempfile.TemporaryDirectory(prefix='vidafix-task-') as folder:
            path = Path(folder) / 'task.xml'
            path.write_bytes(task_xml(root, sid))
            subprocess.run(['schtasks', '/Create', '/TN', name, '/XML', str(path)], check=True)
        print('Installed startup for this account at sign-in. It has not been started now.')
        print('Close any manual Vidafix server before using startup-start or signing in again.')
    elif action == 'remove-startup':
        # Stop only this account-specific task. Never kill unrelated Python processes.
        subprocess.run(['schtasks', '/End', '/TN', name], capture_output=True)
        subprocess.run(['schtasks', '/Delete', '/TN', name, '/F'], check=True)
    else:
        flag = {'startup-start': '/Run', 'startup-stop': '/End', 'startup-status': '/Query'}[action]
        subprocess.run(['schtasks', flag, '/TN', name], check=True)


class LogStream:
    def __init__(self, logger):
        self.logger = logger
    def write(self, message):
        for line in message.rstrip().splitlines():
            self.logger.info(line)
        return len(message)
    def flush(self):
        pass


def run(background=False):
    validate()
    os.chdir(ROOT)
    os.environ['VIDAA_CONFIG'] = str(ROOT / 'config.ini')
    if background:
        log_dir = ROOT / '.logs'; log_dir.mkdir(exist_ok=True)
        handler = RotatingFileHandler(log_dir / 'vidafix.log', maxBytes=1024 * 1024, backupCount=3, encoding='utf-8')
        logging.basicConfig(level=logging.INFO, handlers=[handler], format='%(asctime)s %(levelname)s %(message)s', force=True)
        sys.stdout = sys.stderr = LogStream(logging.getLogger('vidafix.console'))
    runpy.run_module('server.app', run_name='__main__')


def main():
    parser = argparse.ArgumentParser(description='Vidafix Windows host tools')
    parser.add_argument('action', choices=['setup', 'run', 'background', 'check', 'install-startup',
                                         'remove-startup', 'startup-start', 'startup-stop', 'startup-status'])
    action = parser.parse_args().action
    try:
        if os.name != 'nt':
            raise RuntimeError('These helpers are for Windows. Use the Linux README instructions.')
        if action == 'setup':
            setup()
        elif action in ('run', 'background'):
            run(action == 'background')
        elif action == 'check':
            validate(); print('Local configuration and environment check passed (Plex not contacted).')
        else:
            manage_task(action)
    except KeyboardInterrupt:
        pass
    except Exception as error:
        if action == 'background':
            # A config failure may precede log initialization; report without secrets.
            log_dir = ROOT / '.logs'; log_dir.mkdir(exist_ok=True)
            with (log_dir / 'startup-error.log').open('w', encoding='utf-8') as log:
                log.write('Vidafix startup failed. Run Start-Vidafix.cmd to inspect configuration/dependencies.\n')
        else:
            print('Vidafix could not complete the action:', error, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
