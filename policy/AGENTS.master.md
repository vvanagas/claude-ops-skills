# Agent operating policy — master

Platform-neutral operating discipline for a coding/ops agent (Claude Code,
Codex, or similar) working on real systems. This master holds the invariants;
an **overlay** binds them to a platform's mechanics (`overlays/posix.md`,
`overlays/windows-user.md`), and a private estate overlay (not in this repo)
binds them to one fleet's paths, hosts, and tools. A deployed agent file is a
*projection*: master + platform overlay + estate overlay, merged.

Placeholders like `$OPS_GIT_DIR` are defined in `PLACEHOLDERS.md`; each
overlay assigns them concrete values.

Rules that presume host-administration authority are marked **[admin]**. In a
restricted environment (no root/admin), an overlay satisfies them within the
user's own scope or marks them N/A explicitly — silence is not compliance.

## Production code

Writing, reviewing, or planning repo-bound code is governed by
**[coding-rules](https://github.com/vvanagas/coding-rules)** — TDD Iron Law,
secrets-in-code, idempotency/retry contracts, layering, generation density.
That repo is the single canonical source of those invariants; this master
deliberately does not duplicate them. Downstream agent files may carry a
verbatim excerpt for always-on enforcement; if they do, they stamp it with a
`mirror-check` line (version + rule ids + content hash) so drift is
mechanically detectable, and an edit to either side lands in both in the same
change.

## Scripting preference

Prefer a typed scripting language with a test runner over shell for anything
beyond trivial one-liners (shell: no types, no test runner, opt-in error
handling — exactly the failure modes coding-rules exists to prevent). Shell
only for zero-dependency bootstrapping or simple CLI pipe chains. The overlay
names the preferred runtime.

## Shell and dependency safety

- Interactive-mode aliases on destructive commands can silently consume input
  or block automation. For an authorized state-changing action, bypass the
  alias explicitly (overlay gives the mechanism) and supply the intended
  flags. Verify the target side effect instead of trusting a chained
  command's final exit code.
- Never install language packages into an OS-managed runtime environment
  **[admin-relevant either way]**: prefer a per-project virtual environment,
  or a dedicated tool environment under `$VENVS_HOME`. A shared user-level
  install is acceptable only for deliberately shared tooling, with a pinned
  version and a documented consumer.

## Change management — the ops-git pattern [admin: scope varies]

Track configuration you are responsible for in a **local-only** version
control repository. **VCS records WHAT changed; in-file comments record WHY.
Both required.**

- Repo at `$OPS_GIT_DIR`, work-tree `$OPS_WORKTREE` (the broadest tree you
  administer: system root with admin authority, your user profile without).
  **Local only — never add a remote.** A config-tracking repo can capture
  secrets; treat its history as sensitive.
- **Never stage with catch-all commands** (`git add -A` / `git add .`) when
  the work-tree is broad — always explicit `-- <path>` pathspecs.
- Automated capture where available (editor/tool hooks that auto-commit
  agent edits) plus a periodic snapshot job for drift made outside the hooks
  (other users, scripts, remote sessions). Anything outside the snapshot
  roots needs a manual add+commit.
- In-file comment convention (every edit): comment the old line out in
  place; add `# YYYY-MM-DD: <why — a measurement or constraint, not a
  restatement>`; put the new value under it.
- Ownership-restore hazard: tracked files may be service-user-owned; VCS
  stores no ownership. **Never restore with checkout** — read the blob,
  write it back as the original owner, then restore ownership.
- Narrative log: record the story of each change in `$NARRATIVE_LOG`
  (VCS = mechanical log; the narrative = why/how/verified).

## Workflow protocol — project work under $CODE_HOME

Host-config changes follow ops-git above; this governs project work.
Projects live one-per-directory under `$CODE_HOME` (git + tests + docs
inside).

1. **Git first.** `git init` + `.gitignore` at project start. Establish a
   scoped pre-change baseline before implementing each request; never absorb
   unrelated or user-authored work into it. Every commit message states what
   AND why.
2. **Plan before execute.** Non-trivial change → numbered plan first: steps,
   files, expected outcome, **Blast Radius**, one-line rollback. Attended →
   present it and wait. Unattended → record it in `history.txt` and proceed,
   EXCEPT destructive / production-facing / access-control work: always stop
   and show the dry-run form first.
3. **`history.txt` — mechanical ledger.** At project root, one entry per
   request: `#N title` · `[REQUEST]` · `[PLAN]` (steps, blast radius,
   rollback) · `[EXECUTED]` verbatim commands + `# → result` (never
   summaries) · `[RESULT]` outcome, numbers, next. Update after each change;
   commit together with it. It records *what ran*; the *why* a future session
   would re-derive goes in `docs/PROJECT_NOTES.md`. Two files, two jobs.
4. **Commit cadence.** One logical unit per commit; one request ≥ one commit;
   never batch unrelated changes. Body = root-cause rationale, not lines
   moved. Amend only pre-push, same logical unit, and say "amending".
5. **Ambiguity.** Attended → ask before writing or committing. Unattended →
   least-surprising assumption, recorded in `[PLAN]` and flagged in the
   summary — a private, unrecorded resolution is unreviewable.
6. **Canonical source before migrations.** Verify the working copy matches
   deployed state (checksum / `git status`); on divergence record which is
   canonical and why in `[EXECUTED]`. Out-of-cycle hotfixes create silent
   divergence; stale source wastes the whole migration.
7. **Session context.** Before migration, architecture, or refactor work,
   read the infra config and the `history.txt`/`PROJECT_NOTES.md` entries
   covering the target — file state alone loses the why.
8. **Definition of done.** Not complete until verified — give the command
   that proves it (test run, HTTP probe, service/process check). A service
   change's `[RESULT]` includes a healthy-startup log snippet. **Evidence
   before assertion**: "should work" is not a result; if not run, say so.
9. **Housekeeping.** Temp scripts deleted or moved to `scripts/internal/`
   before the final commit. The secrets invariant covers `history.txt` too.

## Secrets in operation

(Complements coding-rules' secrets-in-code rules; this is transcript and
session discipline.)

**Never put a secret literal in a command, dispatch prompt, or doc** — it
freezes into the transcript, and the transcript outlives the credential.
Database access prefers ambient/peer authentication, else a mode-restricted
credentials file — never a literal on the command line. Inspecting configs
or environments that hold live tokens: dump names-only (overlay gives the
redaction idiom), never dump raw. Subagents get a pointer, not the value.
A leaked secret is *disclosed* → flag it and rotate. `.env.example` is
committed (keys, no values); `.env` never is.

## Docs travel with the project

Design docs that explain a project — its spec, ADR/decision-record, and any
live review worklist — are part of the deliverable. They live in a `docs/`
directory **inside the project** and move as one unit *with* the code (never
the code alone). A change that invalidates a spec/ADR statement updates the
doc **in the same change**, not later.

Live backlog: `pending/` — sibling of `docs/`, travels with it (same rule).
One file per item with an explicit `state`/`trigger`/`owner`; a short
`index.md` is the only surface read by default — detail enters context only
when an item is opened. Close = set state done + name the closing commit;
never delete items. Keeps `PROJECT_NOTES.md` lean — a dormant backlog inside
an always-read file is a tax paid every session.

## Durable session capture

Substantial project work (multi-task; investigations with non-obvious
findings; anything a future session would re-derive) → record keypoints
(decisions, live findings, gotchas, open follow-ups) in ONE evolving
project note (`docs/PROJECT_NOTES.md`) — update it, don't spawn dated files.
Add/refresh a pointer in the agent's persistent memory index: project docs
are not auto-loaded; memory is the only discovery path. Skip trivial
one-offs.

Continuation pointer: end each project's memory-index line with
`⏸ NEXT: <one action | "Complete — nothing pending">` — the only surface
auto-loaded at resume. Update it last on stop/finish; on resume read it
first and verify against `git log`/state before trusting (point-in-time).
Memory is per project — never hardcode another project's memory path.

## Knowledge documents — OKF

[OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
(Google Cloud, Apache-2.0), **v0.2+**: markdown + YAML frontmatter; `type` is
the only required key, unknown keys tolerated. On any durable doc making a
claim someone will rely on: `type:` always; `verified: {by, at}` when checked
against source rather than recalled (actors `human:<id>` / `process:<id>` /
`<producer>/<version>`; distinct from `generated:`); `stale_after:
YYYY-MM-DD` when version-bound — **absolute date, never a TTL**, so staleness
is a script comparison, not a habit. Full bundle (concept-per-file, reserved
`index.md`/`log.md`) for **new knowledge dirs only** — never retrofit
existing naming. Exempt: agent policy files; skill-owned artifacts (the
skill's format wins — a conflict is a defect in the skill); append-only
ledgers (`history.txt`, `$NARRATIVE_LOG`); code and config. Pin the spec
version in a bundle's root `index.md` (minor spec versions have broken
compatibility within weeks).

## Web research

Native agent web tools are the DEFAULT for search and single-page fetches.
A scraping CLI is for its niche only: JS-heavy pages/SPAs the native tools
render poorly, bot-protected pages, or bulk multi-page crawl/extract.
Never synthesize technical claims from search-result snippets — fetch the
page. A single known static URL needs a plain GET, not a scraping credit.
**Never send internal or sensitive targets** (private address space,
internal hostnames, configs, databases, PII) to an external scraping
service — use in-network fetches for those.

## What stays estate-private

The estate overlay (never published) carries: host topology and addresses,
service inventories and reload conventions, mail/relay configuration, the
operational watchlist and its skills, monitoring endpoints, and anything
naming real systems. A public projection of this master must contain none of
it — verify with a forbidden-token sweep, not by eye.
