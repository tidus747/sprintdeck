from pathlib import Path
import subprocess
import sys
import unittest


class StyleTests(unittest.TestCase):
    def test_repository_text_style(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable, "scripts/check_style.py"], cwd=root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_session_text_is_not_rendered_as_html(self):
        root = Path(__file__).resolve().parents[1]
        for path in (root / "sprintdeck/static").glob("*.js"):
            content = path.read_text()
            self.assertNotIn("innerHTML", content)
            self.assertNotIn("localStorage", content)
