# Copyright (c) 2026 Vidafix contributors. Licensed under MIT; see LICENSE.
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock
from server.artwork_cache import ArtworkCache

class CacheTests(unittest.TestCase):
    def test_persistent_hit_expiry_and_identity(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'cache.db'
            loader=Mock(return_value=(b'original', 'image/jpeg'))
            c=ArtworkCache(path,'a'); c.get('1/thumb',loader); c.db.close()
            c=ArtworkCache(path,'a'); self.assertEqual(c.get('1/thumb',loader)[0],b'original')
            self.assertEqual(loader.call_count,1)
            c.ttl=0; c.get('1/thumb',loader); self.assertEqual(loader.call_count,2);c.db.close()
            c=ArtworkCache(path,'b');c.get('1/thumb',loader);self.assertEqual(loader.call_count,3);c.db.close()

    def test_bound_and_concurrent_dedup(self):
        c=ArtworkCache(':memory:','test',max_bytes=10)
        loader=Mock(return_value=(b'123456','image/png'))
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda _:c.get('same',loader),range(8)))
        self.assertEqual(loader.call_count,1)
        c.get('other',loader)
        self.assertLessEqual(c.db.execute('SELECT SUM(length(data)) FROM images').fetchone()[0],10)
        c.get('same',loader);self.assertEqual(loader.call_count,3)
        c.db.close()

    def test_errors_not_cached(self):
        c=ArtworkCache(':memory:','test')
        loader=Mock(side_effect=ValueError('failed'))
        for _ in range(2):
            with self.assertRaises(ValueError):c.get('1',loader)
        self.assertEqual(loader.call_count,2);c.db.close()
