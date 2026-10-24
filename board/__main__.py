"""python -m board [ROOT] [--html OUT] [--search TEXT]

ROOT defaults to the Claude Code projects folder in your home directory.
"""
import argparse
import os
import sys

from board import core


def main(argv=None):
    ap = argparse.ArgumentParser(prog="board")
    ap.add_argument("root", nargs="?", default=os.path.join(os.path.expanduser("~"), ".claude", "projects"))
    ap.add_argument("--html", help="also write a static board page to this path")
    ap.add_argument("--search", help="only cards whose name, project or step contains this text")
    a = ap.parse_args(argv)
    cards = core.scan(a.root, query=a.search)
    print(core.render_text(cards) or "(no sessions found)")
    if a.html:
        with open(a.html, "w", encoding="utf-8") as fh:
            fh.write(core.render_html(cards))
        print("wrote %s" % a.html)
    return 0


if __name__ == "__main__":
    sys.exit(main())
