# Copyright (c) 2026 Vidafix contributors. Licensed under MIT; see LICENSE.
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location('configure_vidafix', ROOT / 'sideload-addon/configure_vidafix.py')
addon = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(addon)


class SideloadAddonTests(unittest.TestCase):
    def fixture(self, folder):
        (folder / 'server.py').write_text('# Synthetic server; never executed.\n')
        (folder / 'fixture.cert').write_text('fake certificate')
        (folder / 'fixture.key').write_text('fake key')
        original = {'ssl_certfile': 'fixture.cert', 'ssl_keyfile': 'fixture.key',
                    'html_file': 'index-en.html', 'dns_records': [], 'custom_option': True}
        (folder / 'config.json').write_text(json.dumps(original))
        return (folder / 'config.json').read_bytes()

    def test_configuration_backup_and_separate_hosts(self):
        with tempfile.TemporaryDirectory() as target:
            folder = Path(target)
            original = self.fixture(folder)
            server = (folder / 'server.py').read_bytes()
            backup = addon.configure(folder, '192.168.1.20', '192.168.1.21', 9000)
            config = json.loads((folder / 'config.json').read_text())
            page = (folder / 'vidafix-install.html').read_text()
            self.assertEqual(backup.read_bytes(), original)
            self.assertEqual((folder / 'server.py').read_bytes(), server)
            self.assertEqual(config['server_address'], '192.168.1.21')
            self.assertEqual(config['dns_records'][0]['address'], '192.168.1.21')
            self.assertEqual(config['https_port'], 443)
            self.assertTrue(config['enable_dns_server'])
            self.assertFalse(config['enable_http_server'])
            self.assertTrue(config['custom_option'])
            self.assertEqual(config['ssl_keyfile'], 'fixture.key')
            self.assertIn('http://192.168.1.20:9000/', page)
            self.assertNotIn('__VIDAFIX_SETTINGS__', page)
            self.assertIn("'vidplex-local'", page)

    def test_invalid_addresses_do_not_mutate(self):
        with tempfile.TemporaryDirectory() as target:
            folder = Path(target)
            original = self.fixture(folder)
            for ip in ['127.0.0.1', '8.8.8.8', '0.0.0.0', '169.254.1.2',
                       'http://192.168.1.20/', '192.168.1.20:8765', '<script>', '::1']:
                with self.subTest(ip=ip), self.assertRaises(ValueError):
                    addon.configure(folder, ip, '192.168.1.21')
            self.assertEqual((folder / 'config.json').read_bytes(), original)
            self.assertFalse(list(folder.glob('config.before-*')))

    def test_missing_key_and_bad_port_do_not_mutate(self):
        with tempfile.TemporaryDirectory() as target:
            folder = Path(target)
            original = self.fixture(folder)
            with self.assertRaises(ValueError):
                addon.configure(folder, '192.168.1.20', '192.168.1.21', 65536)
            (folder / 'fixture.key').unlink()
            with self.assertRaises(ValueError):
                addon.configure(folder, '192.168.1.20', '192.168.1.21')
            self.assertEqual((folder / 'config.json').read_bytes(), original)
            self.assertFalse(list(folder.glob('config.before-*')))

    def test_existing_page_is_preserved(self):
        with tempfile.TemporaryDirectory() as target:
            folder = Path(target)
            original = self.fixture(folder)
            (folder / 'vidafix-install.html').write_text('keep this page')
            with self.assertRaises(ValueError):
                addon.configure(folder, '192.168.1.20', '192.168.1.21')
            self.assertEqual((folder / 'vidafix-install.html').read_text(), 'keep this page')
            self.assertEqual((folder / 'config.json').read_bytes(), original)
