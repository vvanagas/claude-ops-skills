<!-- Projection of policy/AGENTS.master.md + overlays/posix.md for a Linux host
     where the agent administers the machine. Deploy by importing it from
     ~/.claude/CLAUDE.md next to a PRIVATE estate overlay that binds the
     $PLACEHOLDERS (PLACEHOLDERS.md) and names real hosts, paths, logins and
     tools — that overlay never enters a git remote. Edit rules in the master
     first, then re-project; never patch this copy on a host. Publish gate: a
     forbidden-token sweep (no host names, estate paths, logins, internal
     domains) over the staged diff. -->

# Claude Code — operating policy (Linux, host-admin projection)

## Tools

- **ripgrep (`rg`)** — prefer over `grep` for code/content search.
- **bun** — prefer over `node`/`npm`/`npx` for JS/TS. Fall back to node only
  when a package genuinely requires it — and say which.
- The estate overlay names every other CLI, its full path, and any
  authentication it carries.

## Gates are not negotiable

A failing check — linter, type-strictness flag, test, coverage/mutation
floor, review model floor — is fixed at the CAUSE, never by weakening the
check: no relaxed flag, no loosened or deleted assertion, no lowered
threshold, no narrowed pattern, no gate switched off to get green. Cause
unfixable now → record the trade-off where the next person hits it
(`pending/` item + its revisit trigger); never silently.

Downgrading a *dependency* to keep a *gate* running is the correct inverse —
the version is the variable, the gate is the constant. Prefer it to shipping
with the gate off, and say why.

**A gate must be complete, and provably live.** Vendoring a rule set means
configuring EVERY promotion it declares automatic — a subset silently
degrades the rest to human review while still looking like enforcement. A
check never seen to FAIL is not evidence: mutate what it guards, watch it
fire, restore. A rule matching nothing passes forever; a pin nothing enforces
(no CI, no lockfile check) is a preference; a control claiming more scope than
it has is worse than none, because everyone downstream believes it.

A workaround (stated goal unmet, looks done) is never a silent call: surface
it with its cost, let the operator decide.
## Scripting preference

Prefer **TypeScript (via bun)** over Bash for anything beyond trivial
one-liners (shell: no types, no test runner, opt-in error handling — the
exact failure modes `coding-rules` exists to prevent). Bash only for
zero-dependency bootstrapping or simple CLI pipe chains.

## Shell and dependency safety

- Interactive `cp`/`rm`/`mv` aliases can silently consume input. For an
  authorized state-changing action bypass them explicitly (`command cp`,
  `command rm`, `command mv`) with the intended flags. Verify the target side
  effect instead of trusting a chained command's final exit.
- Never install Python packages into the apt-managed system environment.
  Prefer a project `.venv` or a dedicated tool venv under `$VENVS_HOME`. Use
  `pip --user` only for intentionally shared user tooling, with a pinned
  version and documented consumer.

## Change management (ops-git — MANDATORY)

This host tracks config/code changes in a local-only ops git repo.
**Git records WHAT changed; in-file comments record WHY. Both required.**

- Git dir `$OPS_GIT_DIR` (0700), work-tree `$OPS_WORKTREE` (`/`). **Local only
  — never add a remote** (it may hold plaintext secrets).
- Run git ops from `cd /` with
  `G="git --git-dir=$OPS_GIT_DIR --work-tree=/"`; the estate overlay names the
  convenience wrapper and its contract file.
- **Never `git add -A` / `git add .`** — the work-tree is `/`. Always explicit
  `-- <path>` pathspecs.
- Edits via the **Edit / Write / MultiEdit tools** auto-commit (pre/post
  hooks in `~/.claude/settings.json`; hooks and `~/.claude/agents/*.md` are
  read at Claude Code startup — a change needs a restart). Changes made any
  other way (scripts, docker, other users) do NOT auto-commit: the periodic
  snapshot job catches drift under its snapshot roots; anything outside them
  needs a manual `cd / && $G add -f -- <path> && $G commit -m "..."`. Read the
  snapshot's own log, not `git log`, to answer "did the job run" (a quiet
  interval commits nothing). Secrets and session/cache state are excluded
  from the snapshot by pattern.
- In-file comment convention (every edit): comment out the old line in
  place; add `# YYYY-MM-DD: <why — a measurement/constraint, not a
  restatement>`; put the new value under it.
- ⚠ Ownership-restore hazard: tracked files may be service-user-owned; git
  stores no ownership. **Never restore with `git checkout`** — read the blob,
  write it back, restore owner and mode (the overlay names the wrapper
  subcommand that does this).
- Narrative log: record the story of each change in `$NARRATIVE_LOG` (git =
  mechanical log; that file = why/how/verified).
- **Never put a secret literal in a command, dispatch prompt, or doc** — it
  freezes into the transcript, and the transcript outlives the credential.
  DB access: peer auth over ssh/sudo, else a mode-600 credentials file —
  never a literal on the line. Inspecting a config/env/`docker inspect` with
  live tokens: dump names-only (`$REDACT`), never `cat` raw. Subagents get a
  pointer, not the value. A leaked secret is disclosed → flag + rotate.

## Open items — pending bundles

- Host-level open items live in an OKF Pending bundle at `$PENDING_HOST_DIR`
  (`index.md` is the only default-read surface); project items in
  `<project>/pending/`. Glance with `/ctx-start` (top-5 per scope);
  review/close/add only through `/ctx-outstanding`, which drives the
  `pending` CLI — the sole writer. Otherwise leave a note for the operator.
- Point-in-time host state, DR and remediation docs live under `$HOST_DOCS`
  (the overlay names the files).

# Workflow protocol — projects under $CODE_HOME (mandatory)

Host config changes = ops-git above; this governs project work. New
projects go under `$CODE_HOME/<project>`; the overlay lists any grandfathered
project dirs elsewhere. Loose work artifacts (scripts, outputs, reports) go
in `$CODE_HOME` subdirectories too — never `$HOME`, desktop or temp unless
told; throwaway session scratch → `$SCRATCH`.

1. **Git first.** `git init` + `.gitignore` at project start. Commit current
   state BEFORE implementing each request. Every message: what AND why.
2. **Plan before execute.** Non-trivial change → plan first: numbered steps,
   files, expected outcome, **Blast Radius**, one-line rollback. Attended →
   present it and wait. Unattended → record in `history.txt` and proceed,
   EXCEPT destructive / prod-facing / IAM-firewall-deletion: always stop and
   show the `--dry-run` command first. **High cost of being wrong →
   `grill-me` first** ([vvanagas/agent-skills](https://github.com/vvanagas/agent-skills)).
   Reviews check work against the plan, never the plan against reality.
3. **`history.txt` — mechanical ledger.** At project root, one entry per
   request: `#N title` · `[REQUEST]` · `[PLAN]` (steps, blast radius,
   rollback) · `[EXECUTED]` verbatim commands + `# → result` (never
   summaries of commands) · `[RESULT]` outcome, numbers, next. Update after
   each change; commit together with it. It records *what ran*; the *why* a
   future session would re-derive goes in `docs/PROJECT_NOTES.md`. Two
   files, two jobs — don't merge them.
4. **Commit cadence.** One logical unit per commit; one request ≥ one
   commit; never batch unrelated changes; reference the `history.txt` entry
   number where relevant. Body = root-cause rationale, not lines moved.
   Amend only pre-push, same logical unit, and say "amending".
5. **Ambiguity.** Attended → ASK before writing/committing. Unattended →
   least-surprising assumption, recorded in `[PLAN]` and flagged in the
   summary — a private, unrecorded resolution is unreviewable.
6. **Canonical source before migrations.** Verify working copy matches
   deployed state (checksum / `git status`); on divergence record which is
   canonical and why in `[EXECUTED]`. Out-of-cycle hotfixes (ssh, scp)
   create silent divergence; stale source wastes the whole migration. **A
   format's cheap moment is before its first real write** — after that you
   own a migration forever: land semantics changes ahead of first use; check
   whether real data exists before assuming the window is still open. **An
   unbound invariant is literature**: a rule with no gate binding it is not
   a control yet — say so rather than filing it as done.
7. **Session context.** Before migration/architecture/refactor work, read
   the infra config and the `history.txt`/`PROJECT_NOTES.md` entries
   covering the target — file state alone loses the why (OOM fixes, SSH
   workarounds, version pins).
8. **Definition of done.** Not complete until verified — give the command
   that proves it (`bun test`, `curl -I`, `systemctl is-active`). Service
   change → `[RESULT]` includes a healthy-startup log snippet. **Evidence
   before assertion**: "should work" is not a result; if not run, say so.
   **A test that already passes proves nothing until you break what it
   guards** — mutate, watch it fail, restore: RED covers new code; mutation
   covers guards, gates and drift checks. **Green ≠ correct** when tests and
   code share one misunderstanding — verify by deriving or executing the
   claim, never by reading it back.
9. **Housekeeping.** Temp scripts deleted or moved to `scripts/internal/`
   before the final commit. The secrets invariant covers `history.txt` too.

# Subagent dispatch — model floors (overrides superpowers "Model Selection")

Definitions live in `~/.claude/agents/` (precedence: project `.claude/agents/`
> user `~/.claude/agents/` > plugin agents). When a skill says "choose the model
per Model Selection", use these instead — user instructions beat skill text:

- implementation → `implementer` (sonnet, xhigh). Never below.
- per-task review (spec + quality) → `task-reviewer` (opus, medium — task diffs
  are small).
- whole-branch / final review → `branch-reviewer` (fable, xhigh); if fable is
  unavailable, re-dispatch it with `model: opus` at xhigh — never lower.
- fix-loop escalation (rounds 4–5): sonnet → opus → fable.
- **Never haiku** for any role. **Never `subagent_type: fork`** for plan
  execution (it inherits the controller's context and model; fresh eyes are the
  point of the review seats).
- Give reviewers sources, not paraphrases. A dispatch outside these
  definitions names its model explicitly — omitted inherits the session's.
- The agent bodies preload `coding-rules` (`skills:`) and say which binding to
  read; the dispatch prompt still pastes the plan's Global Constraints.
- Set because the skill's default routed "mechanical" tasks to the cheapest
  tier, below the bar for committed code.

# Production Code

Writing/reviewing/planning repo-bound code → load the `coding-rules` skill
first. Exempt only: ephemeral scratch under `$SCRATCH`. Committed = meets
standard or deleted; no "clean up later."

The invariants below are non-negotiable, not tool-enforced, and apply
**always** even without the skill loaded. Deliberately mirrored in the
`coding-rules` master: an edit to any lands here AND in the skill in the
same change.

**CLIs — classify before design.** Any new or materially changed CLI, git
hook, cron job, or daemon → the `cli-archetypes` skill *during design, before
any code*: archetype → card defaults → four seams → a present / absent /
floor-dropped checklist in the spec; `branch-reviewer` re-runs it against the
code. Designed without it = re-designed, not patched — its controls
(exit-code contract, child-output trust boundary, bounds, secret masking) are
what a green suite structurally misses. The overlay names the corpus clone.

## The Iron Law of TDD (no `[advisory]` escape)

1. No production code without a failing test first.
2. Watching the test fail is mandatory; record the observed failure mode. A
   test that passed the first time it ran proves nothing.
3. The failure must be for the *right reason* — the asserted behavior, not a
   typo, import error, or unrelated exception.
4. Code written before its failing test is **deleted**, not adapted, not kept
   "for reference", not commented out. Start over test-first.
Also always (TDD CR-3.6, separate from the Iron Law): no horizontal slicing —
each task decomposes into vertical RED→GREEN slices, one behavior per slice.
Refactor only when GREEN.

Proof, not narration: captured RED and GREEN runs go in `history.txt`
`[EXECUTED]`. No captured RED = the law was not followed, whatever the
summary claims.

## Secrets

No secret in version control, logs, tracebacks, responses, event stream, or
history. Secrets are read once at startup via the settings module and never
leave the process. `.env.example` is committed (keys, no values); `.env`
never is.

## Idempotency

Retrying a non-idempotent operation is a correctness bug. Where retry is
legal: full jitter — `Math.random() * min(base * 2^n, max)` — with named max
attempts, backoff, and retryable error classes. A create/migrate/sync run
twice converges: no duplicates, no error on the second run.

## Docs travel with the project

Design docs that explain a project — its spec, its ADR/decision-record, and any
live grill worklist — are part of the deliverable. They live in a `docs/`
directory **inside the code project** and move as one unit *with* the code (never
the code alone, e.g. when migrating to another host/repo). Keep them true to the
code: a change that invalidates a spec/ADR statement updates the doc **in the
same change**, not later. Docs follow code.

**Private repo → SDD task records are tracked** (superpowers ignores and
deletes them by default; override it). CR-3 puts the captured RED/GREEN there,
so an ignored record proves nothing and dies with the container. Handling
rules live in the repo's own `docs/task-records/README.md`. Public repos:
decide at the first that uses SDD.

**Rulings made while executing a plan go in the project, not the scratch.**
Subagent-driven execution keeps its ledger in `.superpowers/`, which is
git-ignored and deleted at branch close — so every ruling taken on the
operator's behalf (plan-vs-spec conflict, finding overridden, scope added or
refused, floor accepted) dies with it unless it is tracked. Append each to
`docs/adr/log.md` (OKF reserves `log.md` for exactly this) with trigger,
decision, and cost-if-wrong; promote long-lived ones to numbered ADRs. A
ruling that survives only in the transcript was made in private.

Live backlog: `pending/` — sibling of `docs/`, travels with it (same rule).
OKF bundle: one file per item, `type: Pending` + `state`/`trigger`/`owner`
producer extensions; `index.md` (a dozen lines) is the only surface read by
default — detail enters context only when an item is opened. Close = set
`state: done` + name the closing commit; never delete items. Keeps
`PROJECT_NOTES.md` lean — a dormant backlog inside an always-read file is a
tax paid every session.

## Durable session capture

Substantial project work (multi-task; investigations with non-obvious findings;
anything a future session would re-derive) → record keypoints (decisions,
live/infra findings, gotchas, open follow-ups) in ONE evolving project note
(`docs/PROJECT_NOTES.md`; lives in-project per "Docs travel with the
project") — update it, don't spawn dated files. Skip trivial one-offs;
coverage is not value. It records *what was learned and decided*, where
`history.txt` records *what ran*. Complements /ctx-save (resume state) +
/ctx-retro (retros); don't duplicate.

### Memory — the only auto-loaded surface

`docs/` isn't auto-loaded; memory is the sole discovery path at resume, so
every project-note change MUST add/refresh the project's `MEMORY.md` line.
Memory is **per project**: `~/.claude/projects/<slug>/memory/`, `<slug>`
derived from the project path by the harness. **Never hardcode one project's
dir** — the session's own instructions name the current one; a pointer written
into another project's memory is a pointer nobody will ever find.

End each project's `MEMORY.md` line with a continuation pointer —
`⏸ NEXT: <one action | "Complete — nothing pending">`. Update it last on
stop/finish; on resume read it first and verify vs `git log`/state before
trusting it (point-in-time; can be stale).

# Knowledge documents — OKF

[OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
(Google Cloud, Apache-2.0), **v0.2+**: markdown + YAML frontmatter; `type` is
the only required key, unknown keys tolerated. On any durable doc making a
claim someone will rely on: `type:` always; `verified: {by, at}` when checked
against source rather than recalled (actors `human:<id>` / `process:<id>` /
`<producer>/<version>`; distinct from `generated:`); `stale_after: YYYY-MM-DD`
when version-bound — **absolute date, never a TTL**, so staleness is a script
comparison, not a habit. New/re-verified host docs under `$HOST_DOCS` get
these fields too. Full bundle (concept-per-file, reserved `index.md`/`log.md`)
for **new knowledge dirs only** — never retrofit existing naming. Exempt: this
file; skill-owned artifacts (the skill's format wins — a conflict is a defect
in the skill); append-only ledgers (`history.txt`, `$NARRATIVE_LOG`); code and
config. On a client project with its own documentation conventions, theirs
win — record that once, don't argue per file. **Enforcement is `[review]`
until a mechanical check exists** (every file in a knowledge dir has `type`;
no `stale_after` has passed) — a compulsory rule with nothing checking it is
policy without mechanism. Pin the spec version in the bundle's root
`index.md` (v0.1→v0.2 broke in six weeks).

## Web research

Native `WebSearch`/`WebFetch` are the DEFAULT for search and single-page
fetches. A scraping CLI is for its niche only: JS-heavy pages/SPAs the native
tools render poorly, bot-protected pages, or bulk multi-page crawl/extract —
the overlay names the tool, its credentials file and any shared credit pool.
Never synthesize technical claims from search-result snippets — fetch the
page. A single known static URL needs a plain GET, not a scraping credit.
**Never send internal or sensitive targets** (loopback, private address
space, internal hostnames, configs, databases, PII) to an external scraping
service — fetch in-network.

## Email

Send through the local MTA the overlay names; body on stdin. Verify
`status=sent` in the mail log before claiming sent — expect failures to
external domains until a relayhost is configured. Never a hosted-mail MCP for
policy mail.

<!-- mirror-check: v0.10 CR-3.1-3.4,3.6,4.4-4.5,8.5 sha256:f53670c6 -->
