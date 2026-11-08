"""Optional documentation build checks; app tests still need no third-party packages."""

from html.parser import HTMLParser
import importlib.util
import json
import subprocess
from pathlib import Path
import tempfile
import unittest
from urllib.parse import unquote, urlsplit

from scripts.build_site import ROOT, build, pages


class PageLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids = [], set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        for key in ("href", "src"):
            if attrs.get(key):
                self.links.append(attrs[key])


@unittest.skipUnless(importlib.util.find_spec("markdown"), "Install website/requirements.txt for documentation checks")
class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temp.name) / "site"
        build(cls.output, "/sprintdeck")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_all_documentation_is_included_and_searchable(self):
        included = {source for _, source, _, _ in pages()}
        self.assertTrue({path.relative_to(ROOT).as_posix() for path in (ROOT / "docs").glob("*.md")} <= included)
        index = json.loads((self.output / "assets/search-index.json").read_text())
        self.assertEqual(len(index), len(pages()))
        self.assertTrue(any("Markdown recap" in page["text"] for page in index))
        self.assertTrue(all(page["url"].startswith("/sprintdeck/docs/") for page in index))
        # A local build can otherwise pass while a source page is accidentally ignored by Git.
        result = subprocess.run(["git", "-c", f"safe.directory={ROOT.as_posix()}", "check-ignore", *sorted(included)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, "Documentation sources must be committable: " + result.stdout + result.stderr)

    def test_internal_links_assets_and_anchors_exist_under_pages_base(self):
        parsed = {}
        for path in self.output.rglob("*.html"):
            parser = PageLinks(); parser.feed(path.read_text(encoding="utf-8")); parsed[path] = parser
        for source, parser in parsed.items():
            for link in parser.links:
                url = urlsplit(link)
                if url.scheme or url.netloc:
                    continue
                if not url.path:
                    target = source
                else:
                    self.assertTrue(url.path.startswith("/sprintdeck/"), f"Incorrect base in {source.name}: {link}")
                    target = self.output / unquote(url.path.removeprefix("/sprintdeck/"))
                    if target.is_dir():
                        target /= "index.html"
                self.assertTrue(target.is_file(), f"Broken link from {source}: {link}")
                if url.fragment and target in parsed:
                    self.assertIn(url.fragment, parsed[target].ids, f"Broken anchor: {link}")

    def test_build_does_not_copy_sessions_profiles_or_demo_fixture_source(self):
        paths = [path.relative_to(self.output).as_posix() for path in self.output.rglob("*")]
        for path in paths:
            self.assertFalse(any(part in {".session", ".git", ".venv", "sessions", "imports", "exports", "demo", "profile"} for part in Path(path).parts), path)
            self.assertFalse(path.endswith(".session.json"), path)
        demo = json.loads((self.output / "downloads/demo-session.json").read_text())
        self.assertEqual([value["name"] for value in demo["members"]], [f"Engineer {letter}" for letter in "ABCDE"])

    def test_output_guard_preserves_unrelated_content(self):
        protected = Path(self.temp.name) / "unrelated"
        protected.mkdir()
        (protected / "keep.txt").write_text("Keep this file")
        with self.assertRaisesRegex(ValueError, "not generated"):
            build(protected)
        self.assertEqual((protected / "keep.txt").read_text(), "Keep this file")
        with self.assertRaises(ValueError):
            build(ROOT)
        with self.assertRaises(ValueError):
            build(Path(self.temp.name) / "invalid", "/../private")

    def test_build_is_repeatable(self):
        before = {p.relative_to(self.output).as_posix(): p.read_bytes() for p in self.output.rglob("*") if p.is_file()}
        build(self.output, "/sprintdeck")
        after = {p.relative_to(self.output).as_posix(): p.read_bytes() for p in self.output.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
