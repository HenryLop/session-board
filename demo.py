"""One-command demo: python demo.py
Renders the sample sessions in tests/fixtures as a board (text + a static page in a temp folder).
"""
import datetime as dt
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from board import core  # noqa: E402

fixtures = os.path.join(ROOT, "tests", "fixtures", "projects")
now = dt.datetime(2026, 10, 24, 10, 2, tzinfo=dt.timezone.utc)  # fixed clock so the sample states are stable
cards = core.scan(fixtures, now)
print(core.render_text(cards))
out = os.path.join(tempfile.mkdtemp(prefix="board-demo-"), "board.html")
with open(out, "w", encoding="utf-8") as fh:
    fh.write(core.render_html(cards))
print("\nsearch 'dark mode':", [c["name"] for c in core.scan(fixtures, now, query="dark mode")])
print("page written to", out)
print("\nOn your own sessions: python -m board --html board.html")
