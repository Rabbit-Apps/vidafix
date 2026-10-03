# Copyright (c) 2026 Vidafix contributors. Licensed under MIT; see LICENSE.
import unittest
from deploy.render_service import render


class ServiceTests(unittest.TestCase):
    def test_config_and_executable_use_same_location(self):
        unit = render('/home/example/Media Apps/vidafix%test', 'example')
        self.assertIn('User=example', unit)
        self.assertIn('WorkingDirectory="/home/example/Media Apps/vidafix%%test"', unit)
        self.assertIn('ExecStart="/home/example/Media Apps/vidafix%%test/.venv/bin/python" -m server.app', unit)
        self.assertNotIn('@APP_DIR@', unit)
        self.assertNotIn('@USER@', unit)

    def test_rejects_unit_injection(self):
        for path in ['relative', '/home/a\nExecStart=bad', '/home/"bad', '/home/a\\bad']:
            with self.assertRaises(ValueError):
                render(path, 'example')
        with self.assertRaises(ValueError):
            render('/home/example/app', 'user\nExecStart=bad')
