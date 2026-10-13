import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import jogger

class CacheTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.cfg = jogger.Config(cache_dir=self.d)
        os.makedirs(self.d, mode=0o700, exist_ok=True)

    def tearDown(self):
        for f in os.listdir(self.d):
            os.unlink(os.path.join(self.d, f))

    def test_roundtrip_and_permissions(self):
        key = jogger.cache_key("ls files", "m", "http://x/v1", "prompt")
        self.assertTrue(jogger.store_cache(key, "ls files", "ls -la", "m", "http://x/v1", "prompt", max_entries=10, config=self.cfg))
        self.assertEqual(jogger.lookup_cache(key, self.cfg), "ls -la")
        mode = oct(os.stat(jogger.cache_path(self.cfg)).st_mode & 0o777)
        self.assertEqual(mode, "0o600")

    def test_corrupt(self):
        p = jogger.cache_path(self.cfg)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write("{bad json")
        self.assertIsNone(jogger.lookup_cache("nope", self.cfg))
        # recreate store works
        key = jogger.cache_key("a", "m", "u", "p")
        jogger.store_cache(key, "a", "cmd", "m", "u", "p", config=self.cfg)
        self.assertEqual(jogger.lookup_cache(key, self.cfg), "cmd")

    def test_prune(self):
        for i in range(5):
            key = jogger.cache_key(f"desc{i}", "m", "u", "p")
            jogger.store_cache(key, f"desc{i}", f"cmd{i}", "m", "u", "p", max_entries=3, config=self.cfg)
        data = jogger.load_cache(self.cfg)
        self.assertEqual(len(data["entries"]), 3)

    def test_isolation(self):
        k1 = jogger.cache_key("d", "m1", "u", "p")
        k2 = jogger.cache_key("d", "m2", "u", "p")
        self.assertNotEqual(k1, k2)

    def test_key_no_normalization(self):
        k1 = jogger.cache_key("  hello  ", "m", "u", "p")
        k2 = jogger.cache_key("hello", "m", "u", "p")
        # trimming only, so equal descriptions after trim should match; extra internal spaces preserved
        self.assertEqual(k1, k2)
        k3 = jogger.cache_key("hello world", "m", "u", "p")
        k4 = jogger.cache_key("hello  world", "m", "u", "p")
        self.assertNotEqual(k3, k4)

if __name__ == "__main__":
    unittest.main()