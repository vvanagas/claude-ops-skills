#!/usr/bin/env python3
"""Regenerate INDEX.md — the canonical registry of saved session contexts.

Ships with the ctx-save skill. Install into your <context-dir> (it operates on
the directory it lives in), or pass the directory explicitly:

    python3 rebuild-index.py [<context-dir>]

INDEX.md is a DERIVED artifact: it is rebuilt from the context files
themselves, so it cannot drift from them. It is the stable path to refer to
saved contexts (the timestamped filenames change every save; this does not).

Run after every ctx-save (the ctx-save skill does this as its final step).

Reads each `*.md` in the context dir (following symlinks), parses the metadata
table + the "End state" section, groups by Session-ID (newest wins), and emits
INDEX.md. No external dependencies; tolerant of older files.
"""

from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path

CONTEXT_DIR = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent
INDEX_PATH = CONTEXT_DIR / "INDEX.md"

# <HOST>-<TS>-<SIDSHORT?>-<rest>.md  (HOST may contain hyphens; TS is the anchor)
FILENAME_RE = re.compile(
    r"^(?P<host>.+?)-(?P<ts>\d{8}-\d{6})-(?:(?P<sid>[0-9a-f]{8})-)?(?P<rest>.+)\.md$"
)


def table_field(text: str, name: str) -> str:
    m = re.search(rf"^\|\s*{re.escape(name)}\s*\|\s*(.+?)\s*\|\s*$", text, re.M)
    return m.group(1).strip() if m else ""


def end_state_body(text: str) -> str:
    # Section body between the "End state" heading (optionally numbered) and the
    # next "## " heading or EOF.
    m = re.search(
        r"^##\s+(?:\d+\.\s+)?End state\s*$(?P<body>.+?)(?=^##\s|\Z)",
        text,
        re.M | re.S,
    )
    return m.group("body") if m else ""


def end_state_summary(body: str) -> str:
    for line in body.splitlines():
        s = line.strip().lstrip(">").strip().replace("**", "").strip()
        if s and not s.startswith("#"):
            sentence = s.split(". ")[0].rstrip(".")
            if sentence and len(sentence) <= 140:
                return sentence + ("." if "." in s else "")
            return s if len(s) <= 140 else s[:137].rstrip() + "..."
    return ""


def derive_status(declared: str, end_body: str) -> str:
    # Declared status in the metadata table wins — reliable, no guessing.
    d = declared.strip().upper()
    if d in ("ACTIVE", "BLOCKED", "DONE"):
        return d
    # Fallback heuristic, scoped to the End state section ONLY (avoids matching
    # incidental words like "WAF block" elsewhere in the doc).
    low = end_body.lower()
    if "nothing pending" in low or "nothing left" in low or "complete" in low:
        return "DONE"
    if any(k in low for k in ("blocked on", "blocked by", "waiting on", "awaiting")):
        return "BLOCKED"
    return "ACTIVE"


def topic_of(label: str, rest: str) -> str:
    label = label.strip()
    if label and label not in ("-", "—"):
        return label
    return rest


class Ctx:
    def __init__(self, path: Path):
        text = path.read_text(encoding="utf-8", errors="replace")
        fm = FILENAME_RE.match(path.name)
        self.path = path
        self.name = path.name
        self.ts = fm.group("ts") if fm else "00000000-000000"
        rest = fm.group("rest") if fm else path.stem
        self.saved = table_field(text, "Saved") or self.ts
        self.session_id = table_field(text, "Session-ID")
        label = table_field(text, "Label")
        # strip a leading "<label>-" from rest so the slug is clean
        if label and label not in ("-", "—") and rest.startswith(label + "-"):
            rest = rest[len(label) + 1 :]
        self.topic = topic_of(label, rest)
        end_body = end_state_body(text)
        self.summary = end_state_summary(end_body) or "(no End state summary)"
        self.status = derive_status(table_field(text, "Status"), end_body)

    @property
    def group_key(self) -> str:
        sid = self.session_id.lower()
        if sid and not sid.startswith("none"):
            return self.session_id
        return self.topic


def collect() -> list[Ctx]:
    out = []
    for p in sorted(CONTEXT_DIR.glob("*.md")):
        if p.name == "INDEX.md":
            continue
        if not table_field(p.read_text(encoding="utf-8", errors="replace"), "Saved"):
            continue  # not a context file
        out.append(Ctx(p))
    return out


def render(ctxs: list[Ctx]) -> str:
    groups: dict[str, list[Ctx]] = {}
    for c in ctxs:
        groups.setdefault(c.group_key, []).append(c)

    latest, superseded = [], []
    for members in groups.values():
        members.sort(key=lambda c: c.ts, reverse=True)
        latest.append(members[0])
        superseded.extend(members[1:])
    latest.sort(key=lambda c: c.ts, reverse=True)
    superseded.sort(key=lambda c: c.ts, reverse=True)

    now = datetime.now().astimezone().isoformat(timespec="seconds")
    lines = [
        "<!-- WHY: canonical registry of saved session contexts. DERIVED — do",
        f"     NOT hand-edit. Rebuild: python3 {CONTEXT_DIR}/rebuild-index.py",
        f"     (ctx-save runs this as its final step). {now} -->",
        "",
        "# Session Contexts — INDEX",
        "",
        "Canonical, stable entry point for resumable session contexts on this host.",
        f"Refer to **`{INDEX_PATH}`** — it always reflects the newest save",
        "per session. Auto-generated from the context files; do not edit by hand.",
        "",
        "## Active / latest",
        "",
        "| Topic | Status | Saved | File | Summary |",
        "|-------|--------|-------|------|---------|",
    ]
    for c in latest:
        lines.append(
            f"| {c.topic} | {c.status} | {c.saved} | `{c.name}` | {c.summary} |"
        )

    if superseded:
        lines += [
            "",
            "## Superseded snapshots",
            "",
            "Older saves kept for history — resume from the latest above, not these:",
            "",
        ]
        for c in superseded:
            lines.append(f"- `{c.name}` — {c.saved} ({c.topic})")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ctxs = collect()
    INDEX_PATH.write_text(render(ctxs), encoding="utf-8")
    print(f"wrote {INDEX_PATH} ({len(ctxs)} context file(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
