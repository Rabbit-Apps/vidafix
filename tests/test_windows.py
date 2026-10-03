# Copyright (c) 2026 Vidafix contributors. Licensed under MIT; see LICENSE.
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from tools import windows


class WindowsHostTests(unittest.TestCase):
    def test_setup_keeps_private_config(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'config.example.ini').write_text('[plex]\ntoken =\n')
            self.assertTrue(windows.copy_config(root))
            (root / 'config.ini').write_text('existing private config')
            self.assertFalse(windows.copy_config(root))
            self.assertEqual((root / 'config.ini').read_text(), 'existing private config')

    def test_failed_dependency_install_does_not_replace_config(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            exe = windows.python_path(root); exe.parent.mkdir(parents=True); exe.touch()
            (root / 'config.ini').write_text('keep me')
            with patch('tools.windows.subprocess.run', side_effect=RuntimeError('pip failure')):
                with self.assertRaises(RuntimeError): windows.setup(root)
            self.assertEqual((root / 'config.ini').read_text(), 'keep me')

    def test_logon_task_is_scoped_hidden_and_unlimited(self):
        root = Path('C:/Users/Example/Media & Apps/Vidafix')
        xml = windows.task_xml(root, 'S-1-5-21-123-456-789-1001')
        tree = ET.fromstring(xml); ns = {'t':'http://schemas.microsoft.com/windows/2004/02/mit/task'}
        def value(path): return tree.find(path, ns).text
        self.assertEqual(value('t:Principals/t:Principal/t:LogonType'), 'InteractiveToken')
        self.assertEqual(value('t:Principals/t:Principal/t:RunLevel'), 'LeastPrivilege')
        self.assertEqual(value('t:Settings/t:ExecutionTimeLimit'), 'PT0S')
        self.assertEqual(value('t:Settings/t:MultipleInstancesPolicy'), 'IgnoreNew')
        self.assertEqual(value('t:Actions/t:Exec/t:WorkingDirectory'), str(root))
        self.assertEqual(value('t:Actions/t:Exec/t:Command'), str(windows.python_path(root, True)))
        self.assertEqual(value('t:Actions/t:Exec/t:Arguments'), '-m tools.windows background')
        self.assertNotIn('Password', xml.decode('utf-16'))
        self.assertNotIn('PLEX_TOKEN', xml.decode('utf-16'))

    def test_refuses_to_replace_existing_task(self):
        with patch('tools.windows.task_identity', return_value=('S-1-5-21-1', 'Vidafix-test')), \
             patch('tools.windows.validate'), patch('pathlib.Path.is_file', return_value=True), \
             patch('tools.windows.subprocess.run') as run:
            run.return_value.returncode = 0
            with self.assertRaisesRegex(RuntimeError, 'already exists'):
                windows.manage_task('install-startup')
            self.assertEqual(run.call_count, 1)
            self.assertNotIn('/Create', run.call_args.args[0])

    def test_validation_accepts_notepad_bom_and_rejects_missing_token(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'PLEX_TOKEN':''}):
            root = Path(folder); exe = windows.python_path(root)
            exe.parent.mkdir(parents=True); exe.touch()
            path = root / 'config.ini'
            path.write_text('[plex]\nserver=http://127.0.0.1:32400\ntoken=synthetic-token\n', encoding='utf-8-sig')
            self.assertEqual(windows.validate(root), 8765)
            path.write_text('[plex]\ntoken=\n', encoding='utf-8-sig')
            with self.assertRaisesRegex(RuntimeError, 'Set your Plex token'):
                windows.validate(root)
