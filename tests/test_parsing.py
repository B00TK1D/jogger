import os, sys, unittest, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import jogger

class ParsingTests(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(jogger.normalize_base_url("https://api.openai.com/v1/"), "https://api.openai.com/v1")
        self.assertEqual(jogger.normalize_base_url("https://api.openai.com/v1/v1"), "https://api.openai.com/v1")
        self.assertEqual(jogger.normalize_base_url("https://localhost:8080"), "https://localhost:8080/v1")

    def test_extract(self):
        resp = {"choices": [{"message": {"content": "ls -la\n"}}]}
        self.assertEqual(jogger.extract_command(resp), "ls -la")
        fenced = {"choices": [{"message": {"content": "```\nls -la\n```"}}]}
        self.assertEqual(jogger.extract_command(fenced), "ls -la")

    def test_pane_validation(self):
        self.assertTrue(jogger.PANE_ID_RE.match("%1"))
        self.assertFalse(jogger.PANE_ID_RE.match("1"))

    def test_metachar_passed_as_list(self):
        # dry-run by monkeypatching subprocess.run
        import subprocess
        calls = []
        def fake(cmd, **kw):
            calls.append(cmd)
            class R: returncode=0; stdout="%1\n"
            return R()
        orig = subprocess.run
        subprocess.run = fake
        try:
            jogger.insert_command("%1", 'echo "a"; rm -rf / `id` $x')
        except Exception as e:
            print("exc", e)
        subprocess.run = orig
        # second call send-keys
        self.assertTrue(any("send-keys" in " ".join(c) for c in calls))
        sk = [c for c in calls if "send-keys" in c]
        self.assertTrue(sk)
        self.assertEqual(sk[0][-1], 'echo "a"; rm -rf / `id` $x')

if __name__ == "__main__":
    unittest.main()