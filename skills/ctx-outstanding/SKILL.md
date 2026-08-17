---
name: ctx-outstanding
description: Review the estate's OUTSTANDING watchlist — report open items, flag date-gated checks that are due/overdue, and (on request) close or add items. The REVIEW sibling of the ctx-* family. Use ONLY when the user explicitly invokes /ctx-outstanding (no args = review; with args = close/add an item, e.g. `/ctx-outstanding done backup-check` or `/ctx-outstanding add <text>`).
---

<!-- WHY (design rationale): born the day the estate got a single OUTSTANDING
     watchlist — before that, open items were scattered across retro sections,
     plan docs, and session memory, and nothing swept them. The design question
     was "make the host-context loader glance at the list vs. give review its
     own skill"; own skill won: the loader's contract is LOAD-only ("does not
     pull files"), and a REVIEW skill works at any time, completing the family:
     load-context=LOAD · ctx-save/ctx-bug/ctx-internal-bug=SAVE ·
     ctx-retro=ANALYZE · ctx-outstanding=REVIEW.
     The watchlist file is the single source of truth; this skill is its only
     maintainer. Writes auto-commit via the local ops-git hook. -->

# ctx-outstanding

Reviews **`<watchlist-file>`** — the estate's living list of open items,
date-gated checks, operator-gated tasks, improvement queue, and standing
canaries. Reports compactly; maintains the file on request. It does NOT do the
work the items describe.

## Host binding

This skill is written with placeholders. Fill them in for your environment
before use (in this file, or in a per-host copy):

| Placeholder | Meaning |
| --- | --- |
| `<watchlist-file>` | The single watchlist file (origin assumes an `OUTSTANDING_watchlist.md` in the ops docs tree). Keep it inside the ops-git work-tree |
| `<change-narrative-log>` | The estate's change-narrative log — named here only to draw the boundary; this skill never writes it |
| `<ops-git-repo>` | The **local-only** ops git repository whose hook auto-commits edits to `<watchlist-file>` |

Sibling-skill names (`ctx-retro`, and your host-context loader if you have
one) are the roles this skill draws boundaries against; rename them to match
your own set, but keep the boundaries.

## When to use

- User explicitly invokes `/ctx-outstanding`.
- Typical: at session start (alongside the host-context loader), or "from time
  to time" as a reminder sweep, or right after finishing something on the list.

**Do not** auto-invoke. Do not use it to plan or execute the items themselves.

## Modes

### 1. Review (no args) — the default

1. Read `<watchlist-file>` and today's date (`date +%F`).
2. Output ONE compact block:
   - **DUE/OVERDUE** — date-gated items whose date ≤ today (with the check command
     if the entry carries one). If none: "no date-gated items due".
   - **UPCOMING** — next 1–2 date-gated items with their dates.
   - **OPEN counts** — one line per section: operator-gated N · improvements N ·
     canaries N (titles only, no full text — the file has the detail).
3. If a DUE item's check is a single read-only command (e.g. "did last night's
   backup pass"), OFFER to run it — run only on user confirmation.
4. Stop. No file edits in review mode.

### 2. Close — `/ctx-outstanding done <hint>`

Find the item matching the hint, move it to the **Done** section with today's date
and a one-line outcome (ask for the outcome if not obvious from the session).
Never delete items — the trail matters.

### 3. Add — `/ctx-outstanding add <text>`

Append to the right section (date-gated if a date is present or derivable —
convert relative dates to absolute; operator-gated if it needs the operator/the
team; otherwise improvements queue). Keep the file's entry style: bold
date/actor prefix, the why, and a check command when one exists.

**Every entry must carry either a date or an explicit trigger** — the event or
condition that makes it actionable ("when the upstream ships the fix", "after
the next cert renewal"). Refuse un-triggered "someday" items: ask for the
trigger before writing. Undated + untriggered is how items rot.

## Output format (review mode)

```
OUTSTANDING — <date>
DUE:
  [!] 2026-08-17 <db-host> nightly backup check — ssh <db-host> 'ls …'   ← run it? (y)
UPCOMING:
  2026-08-22 first dual-write run of the new cleanup job
  2026-08-30 post-cutover cleanup gate
OPEN: operator-gated 5 · improvements 6 · canaries 3
```

## What this skill does NOT do

- Does not execute watchlist items (it reminds; the work happens in the normal flow,
  with the usual confirmations).
- Does not run any command without explicit user confirmation (review mode is
  read-only except the watchlist file itself in done/add modes).
- Does not touch application data — ever (standing operator rule).
- Does not replace `/ctx-retro` (aftermath analysis) or the
  `<change-narrative-log>` (change narrative); it only tracks what is still open.
