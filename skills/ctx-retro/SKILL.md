---
name: ctx-retro
description: Write a comprehensive post-hoc retrospective for one change or incident that has ALREADY been applied/resolved this session — what changed, decisions, verification, blast radius, rollback, prevention. Reconstructs the change-set from the host's local ops git repo rather than from memory. Use ONLY when the user explicitly invokes /ctx-retro (optionally with a short slug, e.g. /ctx-retro disk-pressure). Analyze-and-save — it does NOT investigate root cause or apply the fix.
---

<!-- WHY: ctx-retro is the ANALYZE member of an ops skill family, and it exists to
     fill the one gap the others leave. The usual lifecycle runs orient →
     investigate → save: a context loader gets the operator's bearings, a
     diagnostic skill works an open problem, and a save skill freezes the result
     into a document. Nothing in that chain analyzes the AFTERMATH of a change
     once it has actually been applied. The trigger pattern this was written for:
     a multi-step remediation whose verification, rollback path, and prevention
     lesson end up scattered across a long session and evaporate unless captured
     while still fresh in context.

     Three design commitments hold it together. (1) The change-set is
     RECONSTRUCTED FROM GIT, not recalled — a model narrating "what we changed"
     from memory drifts, so the factual spine is real commits over the incident's
     paths, with the non-git infra actions reconciled in explicitly (they are
     invisible to git and their omission is what makes rollback sections wrong).
     (2) A REFUSE-GUARD FLOOR keeps it post-hoc: no applied change and no
     verification evidence means there is nothing to retro, and the honest answer
     is to refuse and redirect to the investigate skill rather than manufacture a
     narrative. (3) LIGHT REDACTION, not external scrubbing — this document stays
     inside the estate, so it strips access-granting values only and deliberately
     KEEPS the diagnostic detail (internal addresses, hostnames, service and
     database names, paths, versions) that an external-facing report would have to
     destroy. That asymmetry is the point: an internal retro that has been scrubbed
     like a public bug report is worthless six months later.

     Boundary that stops it drifting into the diagnostic skill: it runs ONLY on
     already-applied work, and root cause is delegated via a link, never
     re-derived. Output lives in its own tree, separate from the troubleshooting
     docs, and is auto-committed by the ops-git tooling. -->

# ctx-retro

## Host binding

This skill is estate-agnostic; the adopter fills in the placeholders below
once (in this file, or in the host's `CLAUDE.md`) before first use:

| Placeholder | Meaning | Example shape |
|---|---|---|
| `<retro-dir>` | Directory retrospectives are written to. Its own tree — **not** the troubleshooting-doc tree. | `<ops-home>/retros` |
| `<ops-git-dir>` | The host's local-only ops git dir tracking config/code changes (work-tree usually `/`). | `<ops-home>/.opsgit` |
| `<snapshot-repo>` | OPTIONAL second repo on hosts that keep a separate snapshot/deployment git (e.g. a container host). Declare *which repos exist on this host* — if there is only one, say so explicitly so the skill never hunts for a repo that isn't there. | a repo under the deploy tree |
| `<doc-dir>` | Where the investigate/diagnostic skill writes its troubleshooting docs, so retros can link to them. | `<ops-home>/docs` |

Also note the sibling skills by their local names: the **investigate** skill
(open problems), the **external bug report** skill (heavily-redacted, ships
off-host), and the **session save** skill (resume state). This skill's
boundaries are defined against them.

---

Writes a **comprehensive post-hoc retrospective** for **one** change or
incident that has **already been applied/resolved this session**. It
reconstructs the change-set from real git history, then layers the
session's intent, evidence, and lessons on top. Analyze-and-save: it never
performs the investigation and never applies the fix.

This is NOT the **investigate** skill (which works an **open** problem and
writes a troubleshooting runbook) and NOT the **external bug report** skill
(which ships an **external**, heavily-redacted report). `ctx-retro` is the
**internal aftermath** doc: *we changed X — here is exactly what, why, the
proof it works, what's left, how to undo it, and what would have caught it
earlier.*

**Comprehensive, not lean.** A retrospective is written once, while the
session is fresh; anything dropped now is expensive or impossible to
reconstruct later. The ONLY thing kept terse is root cause — that is
delegated to a linked troubleshooting/bug-report doc. Every other dimension
(decisions, blast radius, open questions, detection, lessons) gets full depth.

## When to use

- User explicitly invokes `/ctx-retro` (optionally with a short slug
  argument naming the incident, e.g. `/ctx-retro cache-eviction`).
- A change or incident was **applied/resolved this session** — there are
  real commits and/or infra actions to reconstruct.

**Do not** invoke to analyze something still open or not yet applied — that
is the investigate skill. **Do not** run an investigation to satisfy this
skill.

## Refuse-guard — check BEFORE writing anything

The skill **refuses** unless the **floor** is met. The floor enforces the
boundary (this is a *post*-hoc tool):

1. **The change is actually applied.** There is concrete evidence the work
   landed: commits in `<ops-git-dir>` for the incident's paths, and/or
   applied infra actions run this session (volume/filesystem changes,
   mounts, permission changes, container deploys). If nothing has been
   applied, the work is still open.
2. **Verification evidence exists.** At least one observation this session
   showing the change does what it should (a probe result, a health check,
   a log going quiet). Not just "I made the edit."

Below the floor → **refuse**: state which item is missing. If the change is
not yet applied, redirect to the investigate skill — do not retro an open
problem. Never invent evidence.

## Procedure when invoked

Treat as a rigid checklist; track with TodoWrite if the change-set spans
more than a couple of files.

### Step 1 — Resolve filename parts (run this)

```bash
DIR=<retro-dir>; mkdir -p "$DIR"
HOST=$(hostname -s)
DATE=$(date +%Y%m%d-%H%M%S)
SEED=$(printf '%s' "${CLAUDE_CODE_SESSION_ID:-$RANDOM}" | tr -dc 'a-z0-9' | tail -c 6)
echo "DIR=$DIR HOST=$HOST DATE=$DATE SEED=${SEED:-none}"
```

### Step 2 — Establish the diff window, then CONFIRM it with the user

The change-set is reconstructed from git, **not** from memory. Identify the
incident's file paths (from the slug + the session), then auto-propose the
matching commits and let the user trim before anything is written.

**Know which repos exist on this host.** The primary source is always
`<ops-git-dir>` (work-tree `/`). Some hosts additionally carry a separate
snapshot/deployment repo (`<snapshot-repo>`) — query both and merge only
where that repo genuinely exists; never assume a second repo on a host that
has only one. Query the ops repo for the incident paths:

```bash
SINCE="6 hours ago"        # or a baseline the user gives (SHA / time)
# work-tree is /, so paths are root-relative without a leading slash:
git -C / --git-dir=<ops-git-dir> --work-tree=/ log --since="$SINCE" \
  --pretty='%h %ad %s' --date=format:'%H:%M' -- <incident-paths> | cat
```

Note: edits made OUTSIDE the agent (ssh, `sed`, scripts, another user) are
not caught by the editor hook — only by the periodic ops-git snapshot job.
If a change you applied this session isn't in the log yet, reconcile it via
Step 3 (non-git change-set).

Show the combined, de-duplicated commit list to the user. **Wait for
confirmation or a trim** ("drop the fstab commit", "add …") before
proceeding. Path-filtering keeps unrelated session commits (other skills,
docs) out automatically — verify nothing unrelated slipped in.

For the actual diffs in §A.2, use `git show <sha> -- <path>` against the
repo that holds each commit.

### Step 3 — Reconcile the NON-git change-set

Git captures **file** changes only. Infra actions leave no commit: volume
and filesystem creation, mounts, permission/ownership changes, container
recreates and redeploys, package installs, one-off SQL. Harvest these from
the session and list them alongside the git changes — the retrospective's
"What changed" (§A.2) is **git diffs ∪ applied infra actions**. Missing them
makes the rollback section (§A.7) wrong.

### Step 4 — Build the document in memory, light-scrub, write

Assemble all 9 sections (§A), run the **light redaction** pass (below) over
the whole text, then write to:

```
<retro-dir>/<HOST>-<DATE>-<SEED>-<SLUG>.md
```

`SLUG` = the `/ctx-retro` argument slugified, else a 2–4 word kebab summary
of the incident. New file every invocation; never overwrite/append.

### Step 5 — Confirm and hand off

Print the written path. Give a one-paragraph summary. Surface §A.6's dated
follow-ups explicitly as **scheduling candidates** if any carry a date or
condition. Stop — do not propose unrelated next steps.

## Light redaction

Internal doc; it lands in `<ops-git-dir>`, which has no remote. Redact only
**access-granting values** — passwords, tokens, secret keys, bearer/Basic
strings. Typical categories worth calling out because they recur: a database
password sitting in a framework config file, SOAP/TLS signing keys held on
disk, a private key hardcoded into an application controller, service
account credentials in an environment file.

**Keep** internal IPs, hostnames, usernames, database names, service names,
file paths, package/build versions, storage volume names — they are
diagnostic, not secret, and stripping them would gut the doc. This is the
core of the skill: the value of an internal retrospective is precisely the
concrete detail that lets a future reader re-find the thing being described.

Note *where* a redacted secret lives (e.g. "the DB password in the framework
config file, mode 640") rather than the value itself. This is a lighter pass
than the external bug-report skill's scrub — do not import that machinery;
a retro never leaves the host.

## §A — Document template

Comprehensive. A section with nothing to report states the absence and why
— never silently omit. Add incident-specific sections freely; never drop
one of these 9.

```markdown
<!-- WHY: post-hoc retrospective generated via /ctx-retro. Auto-committed via
     the ops-git hook. Access-secrets redacted; diagnostic detail retained.
     <ISO datetime> -->

# Retrospective — <one-line title>

| | |
|---|---|
| Host | <HOST> |
| Date | <ISO datetime> |
| Trigger | <what kicked this off, one line> |
| Status | <Resolved | Mitigated | Partial> |
| Severity | <low | medium | high> |
| Impact | <who/what was affected, and for how long> |
| Outcome | <one-line end state> |

## 1. What happened
<2–4 sentences. TERSE. Root cause is NOT re-derived here — link to the
troubleshooting / bug-report / findings doc that owns it. If none exists, one
sentence of mechanism, then move on.>

## 2. What changed
<The applied change-set: git diffs ∪ non-git infra actions (Step 3). List
each file with its commit(s), and each infra action with the exact command.
This is the factual spine — grounded in git, not narrative.>

## 3. Decisions & alternatives considered
<Each material choice: what was decided, WHY, and what was rejected and why.
The roads not taken are the highest-value, least-recoverable content here.>

## 4. Verification
<Evidence-per-change: the proof each piece works, consolidated from probes
scattered across the session. Command + the relevant result line. State
explicitly anything NOT verified end-to-end.>

## 5. Side effects & blast radius
<What the change itself touched and could have broken: downtime from a
recreate, caches invalidated, dependents affected. The risk of the FIX, not
the original fault.>

## 6. Residual risk, open questions & follow-ups
<What is not done: deferred hardening, known gaps, unknowns. Date items
where possible — these are scheduling candidates. Be honest about what was
left unverified or unfinished.>

## 7. Rollback
<How to undo each change. git-tracked changes: the revert command(s). Non-git
actions: the manual reversal (unmount + remove the volume, restore the
previous mode, redeploy the previous container spec). Must cover the full §2
set, including the non-git actions.>

## 8. Detection & prevention
<Two distinct things: (a) DETECTION — how would we KNOW if this regresses?
(a monitor, a health-check signal, a log line). (b) PREVENTION — the systemic
change that stops the whole class (a startup check, a default, a guard).>

## 9. Lessons / action items
<Concrete, separate from prevention. What this taught us; the specific TODOs
worth carrying forward. Link related <doc-dir> or <retro-dir> files.>
```

## What this skill does NOT do

- Does not investigate or re-derive root cause (that's the investigate skill;
  link to its output instead).
- Does not apply or re-run the fix — it analyzes work already applied.
- Does not run on open/unapplied work — the refuse-guard redirects to the
  investigate skill.
- Does not cover more than one incident per invocation (run it again).
- Does not redact for external shipping (that's the external bug-report
  skill); the light pass here only hides access-granting values.
- Does not push to any remote. Local git only.
- Does not write to `<doc-dir>` or any deployment tree — retrospectives live
  in `<retro-dir>`.
