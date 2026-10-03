# Copyright (c) 2026 Vidafix contributors. Licensed under MIT; see LICENSE.
"""Bounded persistent artwork cache. No credentials or upstream URLs stored."""
import hashlib
import sqlite3
import threading
import time
from pathlib import Path


class ArtworkCache:
    def __init__(self, path, namespace, max_bytes=256 * 1024 * 1024, ttl=86400):
        self.path, self.namespace = str(path), namespace
        self.max_bytes, self.ttl = max_bytes, ttl
        self.lock = threading.Lock()
        self.flights = [threading.Lock() for _ in range(32)]
        if self.path != ':memory:':
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path, check_same_thread=False)
        # Reclaim deleted image pages so the database does not grow indefinitely.
        self.db.execute('PRAGMA auto_vacuum=FULL')
        self.db.execute('CREATE TABLE IF NOT EXISTS images (key TEXT PRIMARY KEY, data BLOB, mime TEXT, created REAL, used REAL)')
        self.db.commit()

    def get(self, key, loader):
        key = hashlib.sha256((self.namespace + ':' + key).encode()).hexdigest()
        with self.flights[int(key[:8], 16) % len(self.flights)]:
            now = time.time()
            with self.lock:
                row = self.db.execute('SELECT data,mime,created FROM images WHERE key=?', (key,)).fetchone()
                if row and now - row[2] < self.ttl:
                    self.db.execute('UPDATE images SET used=? WHERE key=?', (now, key))
                    self.db.commit()
                    return bytes(row[0]), row[1]
            data, mime = loader()  # Failures are never cached.
            if len(data) <= self.max_bytes:
                with self.lock:
                    self.db.execute('DELETE FROM images WHERE created<? OR key=?', (now-self.ttl, key))
                    size = self.db.execute('SELECT COALESCE(SUM(length(data)),0) FROM images').fetchone()[0]
                    while size + len(data) > self.max_bytes:
                        oldest = self.db.execute('SELECT key,length(data) FROM images ORDER BY used LIMIT 1').fetchone()
                        if not oldest:
                            break
                        self.db.execute('DELETE FROM images WHERE key=?', (oldest[0],))
                        size -= oldest[1]
                    self.db.execute('INSERT INTO images VALUES (?,?,?,?,?)', (key, data, mime, now, now))
                    self.db.commit()
            return data, mime
