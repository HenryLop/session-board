import datetime as dt
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from board import core  # noqa: E402

FIX = os.path.join(ROOT, "tests", "fixtures", "projects")
NOW = dt.datetime(2026, 10, 24, 10, 2, tzinfo=dt.timezone.utc)


def by_id():
    return {c["id"]: c for c in core.scan(FIX, NOW)}


class Tests(unittest.TestCase):
    def test_states(self):
        c = by_id()
        self.assertEqual(c["s1"]["state"], "working")
        self.assertEqual(c["s1"]["step"], "running Edit")
        self.assertEqual(c["s2"]["state"], "waiting")
        self.assertIn("write the migration", c["s2"]["step"])
        self.assertEqual(c["s3"]["state"], "done")

    def test_grouped_by_project(self):
        g = core.group(core.scan(FIX, NOW))
        self.assertEqual(sorted(g), ["notes-app", "webshop"])
        self.assertEqual(len(g["webshop"]), 2)

    def test_search_history(self):
        hits = core.scan(FIX, NOW, query="dark mode")
        self.assertEqual([c["id"] for c in hits], ["s3"])

    def test_html_escapes_and_has_cards(self):
        cards = core.scan(FIX, NOW)
        cards[0]["name"] = "<img src=x onerror=alert(1)>"
        out = core.render_html(cards)
        self.assertNotIn("<img src=x", out)
        self.assertIn('class="card', out)

    def test_bad_lines_are_skipped(self):
        import tempfile
        d = tempfile.mkdtemp()
        os.makedirs(os.path.join(d, "p"))
        with open(os.path.join(d, "p", "x.jsonl"), "w", encoding="utf-8") as fh:
            fh.write("not json\n" + '{"type":"user","timestamp":"2026-10-24T10:00:00Z","message":{"content":"hi"}}\n')
        self.assertEqual(core.scan(d, NOW)[0]["name"], "hi")


if __name__ == "__main__":
    unittest.main()
