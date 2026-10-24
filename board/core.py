"""Read Claude Code session transcripts (JSONL) and turn each into a card.

Expected layout: <root>/<project-folder>/<session-id>.jsonl, one JSON object per line:
  {"type": "user", "timestamp": "...", "cwd": "...", "message": {"role": "user", "content": "text"}}
  {"type": "assistant", "timestamp": "...", "message": {"content": [{"type": "text", "text": "..."},
                                                                    {"type": "tool_use", "name": "Bash"}]}}
"""
import datetime as dt
import html
import json
import os

DONE_AFTER_MIN = int(os.environ.get("BOARD_DONE_AFTER_MIN", "30"))


def _text(content):
    if isinstance(content, str):
        return content
    return " ".join(b.get("text", "") for b in content or [] if isinstance(b, dict) and b.get("type") == "text")


def _ts(s):
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None


def read_session(path):
    first_prompt, project, last, last_ts = "", "", None, None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            if ev.get("cwd") and not project:
                project = os.path.basename(ev["cwd"].replace("\\", "/").rstrip("/"))
            msg = ev.get("message") or {}
            if ev.get("type") == "user" and not first_prompt and isinstance(msg.get("content"), (str, list)):
                first_prompt = _text(msg["content"]).strip()
            if ev.get("type") in ("user", "assistant"):
                last, last_ts = ev, _ts(ev.get("timestamp")) or last_ts
    return {"id": os.path.splitext(os.path.basename(path))[0], "project": project or os.path.basename(os.path.dirname(path)),
            "name": (first_prompt[:60] or "(no prompt)"), "last": last, "last_ts": last_ts}


def card(session, now):
    last = session["last"] or {}
    blocks = (last.get("message") or {}).get("content")
    blocks = blocks if isinstance(blocks, list) else []
    tools = [b for b in blocks if isinstance(b, dict) and b.get("type") == "tool_use"]
    idle = (now - session["last_ts"]).total_seconds() / 60 if session["last_ts"] else 1e9
    if idle > DONE_AFTER_MIN:
        state, step = "done", "closed"
    elif last.get("type") == "assistant" and tools:
        state, step = "working", "running " + tools[-1].get("name", "a tool")
    elif last.get("type") == "assistant":
        state, step = "waiting", (_text(blocks).strip()[:70] or "waiting for you")
    else:
        state, step = "working", "thinking about your last message"
    return {"id": session["id"], "project": session["project"], "name": session["name"], "state": state, "step": step,
            "idle_min": int(idle) if idle < 1e8 else None}


def scan(root, now=None, query=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    cards = []
    for proj in sorted(os.listdir(root)):
        pdir = os.path.join(root, proj)
        if not os.path.isdir(pdir):
            continue
        for f in sorted(os.listdir(pdir)):
            if f.endswith(".jsonl"):
                c = card(read_session(os.path.join(pdir, f)), now)
                if query and query.lower() not in (c["name"] + " " + c["project"] + " " + c["step"]).lower():
                    continue
                cards.append(c)
    return cards


def group(cards):
    g = {}
    for c in cards:
        g.setdefault(c["project"], []).append(c)
    return g


def render_text(cards):
    out = []
    for proj, cs in group(cards).items():
        out.append("[%s]" % proj)
        for c in sorted(cs, key=lambda c: ("working", "waiting", "done").index(c["state"])):
            out.append("  %-8s %-40s %s" % (c["state"].upper(), c["name"][:40], c["step"]))
    return "\n".join(out)


def render_html(cards):
    css = ("body{font:14px system-ui;background:#111;color:#e8e8e8;padding:1.5em}h2{font-size:1em;color:#999;margin:1.2em 0 .4em}"
           ".card{border:1px solid #333;padding:.6em .8em;margin:0 0 .4em;display:grid;grid-template-columns:90px 1fr;gap:.6em}"
           ".working{border-left:4px solid #4a8}.waiting{border-left:4px solid #e0a030}.done{opacity:.5}.s{color:#999}")
    body = ""
    for proj, cs in group(cards).items():
        body += "<h2>%s</h2>" % html.escape(proj)
        for c in cs:
            body += '<div class="card %s"><b>%s</b><div>%s<div class="s">%s</div></div></div>' % (
                c["state"], c["state"], html.escape(c["name"]), html.escape(c["step"]))
    return '<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="5"><title>Session board</title><style>%s</style>%s' % (css, body)
