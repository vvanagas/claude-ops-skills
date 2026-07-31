---
name: ctx-save
description: Save resumable session context to a markdown file under the host's context store. Use ONLY when the user explicitly invokes /ctx-save (optionally with a short label, e.g. `/ctx-save db-migration`). Captures the minimum state to resume work later — not polished documentation.
---

<!-- WHY: the context store lives in its own directory rather than the
     operator's home dir — the home dir was accreting one-off files and acting
     as a de-facto garbage collector, which made resumable context impossible
     to find. The store is still placed inside the tree the ops-git hook
     covers, so context saves keep auto-committing with no extra wiring. -->

# ctx-save

## Host binding

Fill these in for your host before using the skill; every path below is
written in terms of them.

| Placeholder | Meaning | Example |
|---|---|---|
| `<context-dir>` | Directory the context files and `INDEX.md` live in. Must sit **inside** the tree your ops-git hook (or equivalent snapshotter) covers, and must not be the operator's home dir. | `/var/lib/agent-contexts` |
| `<transcript-dir>` | Directory holding this agent's session transcripts (`*.jsonl`), used only for the session-id fallback. | `~/.claude/projects/<project-key>` |
| `<ops-git-dir>` | The local-only ops git repo that auto-commits changes under the tree. | `/var/lib/ops.git` |
| `<index-script>` | Path to `rebuild-index.py` (ships alongside the context store). | `<context-dir>/rebuild-index.py` |

---

Writes a **session context** file: the minimum state for a future session
(human or agent) to *resume this work*. This is not documentation — favour
"where things stand and what to do next" over narrative polish.

## Redaction stance — READ BEFORE ADOPTING

This skill has two supported modes. **Pick one deliberately; the default is
the unsafe-to-share one.**

**Mode A — verbatim (default as written).** The artifact is **host-local and
unredacted BY DESIGN**: single-operator, single-host, never leaves the box.
Content is written verbatim so a resumer loses nothing. Do not transcribe
gratuitous credential dumps, but do not scrub either; describe credential-
related decisions plainly.

> ⚠ **Because Mode A is unredacted, a context file MUST NOT be committed to a
> shared or remote repository, pushed anywhere, pasted into a ticket/chat, or
> otherwise sent off-host.** The ops-git repo that auto-commits it is
> **local-only and must never gain a remote.** Treat every context file as if
> it contained secrets, hostnames, and internal topology — because it will.

**Mode B — redacted (required if your store syncs anywhere).** If
`<context-dir>` is inside a repo with a remote, a synced/backed-up folder, a
shared filesystem, a cloud drive, or anything replicated off the host, Mode A
is **not** available to you. Turn redaction on: apply the redaction rules from
the sibling externally-shippable skill (`ctx-bug`) to everything you write
here — no credentials, no tokens, no internal IPs/hostnames, no personal
usernames, no customer data — and state `Redaction: on` in the metadata block
so future readers know the file is lossy by policy.

If you are unsure which mode applies, assume Mode B.

## Procedure

### 1. Resolve filename parts (run this)

```bash
DIR=<context-dir>; mkdir -p "$DIR"              # context store (NOT the home dir)
HOST=$(hostname -s)
TS=$(date +%Y%m%d-%H%M%S)                       # sortable, second precision
SID="${CLAUDE_CODE_SESSION_ID:-}"
if [ -z "$SID" ]; then                          # fallback: transcript basename
  SID=$(ls -t <transcript-dir>/*.jsonl 2>/dev/null \
        | head -1 | xargs -r basename -s .jsonl)
fi
SIDSHORT=$(printf '%s' "${SID:-none}" | cut -c1-8)
echo "DIR=$DIR HOST=$HOST TS=$TS SID=${SID:-<none-> F2 recency-only> } SHORT=$SIDSHORT"
```

- **Session id found** → identity mode (R2): files sharing the full `SID`
  are snapshots of one session; newest `TS` wins.
- **No session id** (`SID` empty) → **F2 fallback**: recency-only; omit the
  id segment; resume = newest file by timestamp.

### 2. Label (optional)

If the user passed an argument to `/ctx-save`, slugify it (lowercase,
kebab, alnum+dash) → `LABEL`. If none, omit the label segment entirely.

### 3. LLM slug

You generate a 3–6 word kebab-case summary of what *this session was about*
→ `SLUG` (e.g. `loadtest-a1-json-cache`). Human-readable only — it is **not**
the identifier (the session id is); a different slug per run is harmless.

### 4. Filename

```
<context-dir>/<HOST>-<TS>-<SIDSHORT>[-<LABEL>]-<SLUG>.md
```

Omit `<SIDSHORT>` segment entirely in F2 mode. Omit `[-<LABEL>]` if no label.

### 5. Write the file

Start with the change-convention WHY header and a machine-readable metadata
block (so a future reader can group by session id and pick the newest):

```markdown
<!-- WHY: resumable session context saved via /ctx-save. Auto-committed via
     the ops-git hook. <ISO datetime> -->

# Session Context — <SLUG>

| | |
|---|---|
| Host | <HOST> |
| Saved | <ISO datetime> |
| Session-ID | <full SID, or "none (recency-only)"> |
| Label | <LABEL or —> |
| Redaction | <off (host-local, verbatim) \| on (redacted per ctx-bug rules)> |
| Status | <ACTIVE \| BLOCKED \| DONE — declare it; this drives INDEX.md> |

> RESUME DISCIPLINE: to continue this work, open the **newest** file whose
> Session-ID matches this one (or, if Session-ID is "none", the newest
> `<HOST>-*` file in the context store). Older files are stale snapshots —
> do not act on them.
```

Then the body. **Mandatory sections (always present, even if short):**

1. **Start state** — what the session began from / the problem or goal.
2. **End state** — where it stands now, AND the resume pointer: the explicit
   next action, or `Complete — nothing pending` (this assertion is load-
   bearing; a resumer relies on it). This section must answer "what do I do
   next?" — never omit the next-step.
3. **Key decisions + rationale** — each material decision and *why*; include
   rejected alternatives where the reasoning matters.
4. **Artifacts** — files created/modified/relevant, with paths and one-line
   purpose; commands or IDs needed to resume.

Set the `Status` row honestly: `DONE` only if End state is "Complete — nothing
pending"; `BLOCKED` if the next action is waiting on something/someone external;
else `ACTIVE`. INDEX.md reads this row verbatim, so a wrong value mislabels the
context for every future reader.

**Optional sections** — include only when they carry real content; omit
entirely otherwise (do not stub with "N/A"):

- **State left on the box** — encouraged whenever the session mutated system
  state a resumer must know about: services restarted, configs/policies
  changed, processes started, temp files/artifacts left, anything not pristine.
  (E.g.: a system-wide policy was changed, an application service was
  restarted, credentials/keys were staged but not yet activated.)
  Without it a resumer assumes the box is untouched.
- Goal/context (if not obvious from Start state)
- Pitfalls / do-not-repeat (retracted theories, dead ends, gotchas)
- Open questions / blocked-on
- References (tickets, dashboards, related context files)

### 6. Rebuild the canonical index

```bash
python3 <index-script>
```

This regenerates `<context-dir>/INDEX.md` from all context files. Always run it
after writing — it is the one stable path to refer to (filenames change every
save; INDEX.md does not). Never hand-edit INDEX.md; it is derived.

### 7. Confirm

Print the written path. State which mode was used (identity vs F2), the
mandatory sections written, and that INDEX.md was rebuilt.

## Notes

- **`<context-dir>/INDEX.md` is the canonical, referenceable entry point** —
  a single stable path to point others (or a future session) at. It is a
  DERIVED registry: rebuilt from the context files by `rebuild-index.py`
  (groups by session, newest wins, reads the `Status` row). Do not hand-edit it
  — edits are wiped on the next rebuild. To correct a status/summary, fix the
  source context file's `Status` row / End state, then re-run the script.
- New file every invocation (never overwrite/append). Multiple saves of one
  session are versioned by `TS` and grouped by `SID`.
- Save-only skill. The RESUME DISCIPLINE line in each file *is* the read-side
  contract — keep it verbatim; without it stale snapshots get acted on.
- Saved under `<context-dir>/` (keeps the operator's home dir uncluttered). It
  is still inside the tracked tree, so it auto-commits to `<ops-git-dir>` via
  the hook; the WHY header satisfies the in-file convention. No
  `changed_in_details.md` entry (that logs system changes, not context saves).

## Boundaries vs sibling skills

- **This skill is save-only.** It does not investigate, diagnose, or apply
  anything — it records the state of work already done this session.
- **Not `ctx-bug`** — that writes a *redacted, externally-shippable* bug
  report about one investigated defect. ctx-save is host-local resume state,
  not a shippable artifact. (Its redaction rules are what Mode B above
  borrows.)
- **Not `ctx-retro`** — that writes a post-hoc retrospective for a change or
  incident already applied/resolved (decisions, verification, blast radius,
  rollback, prevention), reconstructed from git. ctx-save is forward-looking
  resume state, not backward-looking analysis.
- **Not a project note / handover** — a durable per-project note that evolves
  across sessions (keypoints, decisions, open follow-ups, continuation
  pointer) lives with the project's code. ctx-save writes a new dated
  snapshot per invocation; it never edits the project note.
