import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import welcome


class WelcomeCacheTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.cache_path = Path(self.tempdir.name) / "welcome_cache.json"
        welcome.WELCOME_CACHE_FILE = self.cache_path
        welcome._WELCOME_DEDUPE.clear()

    def tearDown(self):
        self.tempdir.cleanup()

    def test_in_memory_guard_prevents_duplicate_welcomes(self):
        now = datetime.now(timezone.utc)
        welcome._WELCOME_DEDUPE[12345] = now

        self.assertTrue(welcome.recently_welcomed(12345))

    def test_mark_welcomed_updates_cache_and_guard(self):
        welcome.mark_welcomed(67890)

        self.assertTrue(welcome.recently_welcomed(67890))

        with self.cache_path.open("r", encoding="utf-8") as file:
            cache = json.load(file)

        self.assertIn("67890", cache)


if __name__ == "__main__":
    unittest.main()
