---
name: ctx-internal-bug
description: Write a comprehensive INTERNAL bug report from an investigation already done this session, using the bundled report templates. Light scrub only (access-secrets; internal IPs/hostnames/digests/symbols retained). The internal SAVE sibling of ctx-bug (which is the EXTERNAL, heavily-redacted one). Use ONLY when the user explicitly invokes /ctx-internal-bug (optionally with a short slug, e.g. `/ctx-internal-bug oom-loop`). Save-only — it does NOT run the investigation.
---

<!-- WHY (design rationale): the gap this fills sits between three siblings.
     ctx-bug is EXTERNAL (heavy deterministic redaction, ships outside the
     estate); doc-this/dig-this are INVESTIGATION walkers for open problems;
     ctx-retro requires the fix to be already APPLIED. Nothing produced the
     comprehensive *internal* bug artifact from a finished investigation — the
     full-detail report the estate's own engineers (and future LLM sessions)
     read to understand, fix, and not re-walk a bug. The templates are adopted
     verbatim from the originating estate's practice — they already encode the
     best practices (mandatory ruled-out section, detection-gap analysis,
     rejected fixes, tooling trail). The output dir is deliberately SEPARATE
     from the external reports dir so an unredacted internal doc can never be
     shipped by grabbing the wrong file. Writes auto-commit via the local
     ops-git hook. -->

# ctx-internal-bug

Writes a **comprehensive internal bug report** for **one** bug whose
investigation was **already performed this session**. Internal register: full
diagnostic detail, only access-secrets scrubbed. This is the artifact the
estate's engineers (and future LLM sessions) read to understand, fix, and not
re-walk a bug.

Family position: `doc-this`/`dig-this` INVESTIGATE → **`ctx-internal-bug`
SAVES the internal report** (`ctx-bug` saves the external one) → after the fix
is applied, `ctx-retro` records the aftermath.

## Host binding

This skill is written with placeholders. Fill them in for your environment
before use (in this file, or in a per-host copy):

| Placeholder | Meaning |
| --- | --- |
| `<internal-bugs-dir>` | Where internal reports are written (origin assumes `~/bugs`). Keep it inside the ops-git work-tree, and **separate** from the external `<reports-dir>` |
| `<reports-dir>` | The EXTERNAL reports dir `ctx-bug` writes to — named here only to draw the boundary; this skill never writes there |
| `<templates-dir>` | Where the two report templates live on the host. Reference copies ship in [`templates/`](templates/) next to this file |
| `<docs-dir>` | The internal troubleshooting-docs tree (where `doc-this` and incident write-ups go) |
| `<retros-dir>` | Where post-hoc change retrospectives live (`ctx-retro`'s output) |
| `<scratch-dir>` | Scratch area for extracted artefacts (jars, `.class` files, decompiles) — a dedicated scratch volume or `/tmp` |
| `<ops-git-repo>` | The **local-only** ops git repository whose hook auto-commits writes under `<internal-bugs-dir>` |

Sibling-skill names (`ctx-bug`, `doc-this`, `dig-this`, `ctx-retro`) are the
roles this skill draws boundaries against; rename them to match your own set,
but keep the boundaries.

## When to use

- User explicitly invokes `/ctx-internal-bug` (optionally with a slug argument).
- The investigation happened **this session**: root cause identified (or honestly
  bounded), evidence in hand.

**Do not** invoke to *start* an investigation (that is `/doc-this` or `/dig-this`).
**Do not** use for reports leaving the estate (that is `/ctx-bug`).

## Refuse-guard — check BEFORE writing

1. **An investigation exists in this session** — concrete evidence: log excerpts,
   probes, source references. If the session only *mentions* a bug, refuse and
   point to `/doc-this`.
2. **One bug per invocation.** Multiple bugs → multiple runs.

Never invent evidence; every claim in the report must trace to something observed
this session.

## Procedure

### 1. Resolve filename (run this)

```bash
DIR=<internal-bugs-dir>; mkdir -p "$DIR"
HOST=$(hostname -s); DATE=$(date +%Y%m%d-%H%M%S)
SEED=$(printf '%s' "${CLAUDE_CODE_SESSION_ID:-$RANDOM}" | tr -dc 'a-z0-9' | tail -c 6)
# SLUG: the argument slugified, else a 2-4 word kebab summary of the bug
echo "$DIR/$HOST-$DATE-$SEED-<SLUG>.md"
```

New file every invocation; never overwrite/append.

### 2. Load the template and fill EVERY section

Template: **`<templates-dir>/_bug-report-template.md`** (reference copy ships
in [`templates/`](templates/) next to this file — if the host copy and the
shipped copy ever diverge, reconcile before writing). Fill all 10 sections +
the header table. A section with nothing to report states the absence and why
("no clean workaround exists — the failing path has no bypass") — never
silently omit, never stub with "N/A" alone.

**Two templates, pick by bug state** (both in `<templates-dir>`):
- Bug **not yet fixed** → `_bug-report-template.md` (fix-pending advocacy: possible
  fixes ranked, workarounds, who fixes).
- Bug **resolved in-session** → prefer `_template_incident_report.md`'s extra
  sections (Hypothesis ladder · Fix applied · Verification · Generalization ·
  Durable mitigation · Prevention code patterns) grafted onto the base — or, if
  the resolution was a substantial *change*, hand off to `/ctx-retro` instead and
  keep this report to the bug mechanics.

Enhancements over the raw template (apply when they earn their place):

- **`Hypothesis ladder`** — when the investigation walked multiple theories, show
  the ordered ladder (theory → probe → verdict), not just the §6.1 outcomes; it
  preserves WHY the order was chosen.
- **`Generalization — when else does this fire?`** — the class-of-bug expansion:
  grep/count the same defect pattern across the tree/estate and say where else it
  bites (e.g. a wrong-case identifier bug → search all identifiers; a guard added
  in one cron feed → check sibling feeds). One of the highest-value sections in
  the originating corpus.
- **`Durable mitigation`** distinct from the fix — the lasting operational guard
  (retention policy, proxy rule, cron guard) that outlives the code change.
- **`Prevention code patterns`** — a source-confirmed reusable idiom for the
  developers ("do X, never Y"), when the bug class has one.

- **`## 0. LLM Preamble — pin these facts before reading`** — for multi-host or
  easily-misread bugs: 3–6 bullet facts a reader must hold to not go wrong.
- **Cross-links row** in the header table: related watchlist item, retro,
  dev-request entry, sibling reports — the report should plug into the ops
  ecosystem, not float.
- **Fix-ownership clarity:** if the fix is code, name the file:line and note the
  standing rule (app code/data changes arrive from developers or with explicit
  operator approval).

### JVM / container bugs — evidence standard (when the report contains a JVM stack trace)

JVM-based container services deserve their own reporting discipline, distilled
from code-level investigation practice on the originating estate:

1. **Stack traces verbatim and COMPLETE** — the full frame list plus every
   `Caused by:` and `Suppressed:` chain (the real cause is usually the innermost
   one). Never elide frames with `…` inside the implicated region; trimming is
   allowed only below the last app-owned frame.
2. **Attribute each implicated frame to its owning artifact** — app fork vs
   framework vs library (package prefix → jar). The §5 table must carry: image
   `repo:tag`, **image id/digest**, build date, and the jar path inside the
   container. "latest" alone is not a version.
3. **Capture the log line's context markers** — timestamp, thread name, request-id
   (e.g. `[virtual-executor…]`, `[http-nio…]`) — they let upstream correlate.
4. **Code-level claims need code-level evidence.** If §6 asserts a mechanism inside
   a class, cite decompile/bytecode proof obtained per `/dig-this` (fat-JAR extract
   to `<scratch-dir>`, decompile via the *container's* own JRE, cross-checked with
   `javap -verbose` constants). If that step was NOT done, draw the honest
   boundary explicitly and point to `/dig-this <hint>`. Never present a
   stack-frame guess as a verified mechanism.
5. **JVM runtime context when relevant** — heap flags (`-Xmx…`), and the service's
   own telemetry lines (memory/HTTP/GC stats) for OOM- or resource-shaped bugs;
   cadence counted by log grep, not estimated.
6. **Extracted artifacts** (jars, `.class`, decompiles) live under `<scratch-dir>`
   — reference their paths in §9 and treat them as reproducible scratch, not part
   of the report.
7. **Cross-estate repro check is cheap and decisive for JVM bugs** — the same
   image digest often runs on a test host; one grep of the test-side log can
   convert "prod anomaly" into "reproducible upstream". Record the result
   either way.

### 3. Light scrub

Redact **access values only**: passwords, tokens, secret keys, credentials
(pointer to where they live instead). **Keep** internal IPs, hostnames, usernames,
paths, image digests, source symbols, SQL — diagnostic, not secret. This is the
internal register ("Access-secrets scrubbed"), NOT `ctx-bug`'s external scrub.

### 4. Confirm

Print the written path. One-paragraph summary. If the bug is unfixed, state the
fix locus and who owns it; if a workaround was applied, say which section records
it. Stop — do not propose unrelated work.

## What this skill does NOT do

- Does not investigate or re-derive root cause (link the session's evidence).
- Does not apply fixes, workarounds, or data changes.
- Does not redact for external shipping — **never hand an `<internal-bugs-dir>`
  file to an outside party; produce a `/ctx-bug` version instead.**
- Does not cover more than one bug per invocation.
- Does not write to `<reports-dir>`, `<templates-dir>`, `<docs-dir>`, or any
  shared tree.
- Does not push to any remote. Local git only (ops-git hook auto-commits).
