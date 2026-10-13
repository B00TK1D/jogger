import os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import jogger

class HistoryTests(unittest.TestCase):
    def test_persist_across_runs(self):
        d = tempfile.mkdtemp()
        cfg = jogger.Config(cache_dir=d)
        st = jogger.AppState(cfg, "%1")
        st.on_input_change("list files")
        st.on_input_change("disk usage")
        # simulate a fresh run
        st2 = jogger.AppState(cfg, "%1")
        self.assertEqual(st2.history, ["list files", "disk usage"])

if __name__ == "__main__":
    unittest.main()