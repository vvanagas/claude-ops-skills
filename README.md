# claude-ops-skills

Estate-agnostic Claude Code skills for **operating a server**: investigate a
problem, dig to the code-level root cause, write it up internally, ship a
redacted report outside, save resumable session state, and transfer active
ownership through a verifiable two-party handover.

The seven host-bound skills are generalized copies of skills that run on a
live fleet.
Every host name, address, product, database and path has been replaced with a
placeholder — each host-bound skill opens with a **Host binding** table listing
what to fill in. The two handover skills are generic additions designed around
the same evidence-first and explicit-boundary conventions.

## Operating policy

[`policy/`](policy/) holds the estate-agnostic **agent operating policy** these
skills assume: a platform-neutral [`AGENTS.master.md`](policy/AGENTS.master.md)
plus overlays for [POSIX-admin](policy/overlays/posix.md) and
[restricted Windows](policy/overlays/windows-user.md), with symbolic
[`PLACEHOLDERS.md`](policy/PLACEHOLDERS.md). A deployed agent file is a
projection of master + a platform overlay + a private estate overlay (not in
this repo). Production-code invariants (TDD, secrets-in-code) are not
duplicated here — the master points at
[coding-rules](https://github.com/vvanagas/coding-rules) as their canonical
source.

## The skills

| Skill | Invocation | What it does |
|---|---|---|
| [`doc-this`](skills/doc-this/SKILL.md) | user | Runs a structured diagnostic (hypothesis ladder → probes → diagnosis) and writes a deep troubleshooting doc. The only one that *investigates and saves*. |
| [`dig-this`](skills/dig-this/SKILL.md) | user | Code-level root-cause investigation when the bug points at a source artefact. Read-only; locates the *executing* file, cross-checks live-vs-shipped, counts the class-of-bug, finds a negative control. Investigates only — writes nothing. |
| [`ctx-bug`](skills/ctx-bug/SKILL.md) | user | Turns an investigation already done this session into a **redacted, externally-shippable** bug report. Carries the deterministic redaction pattern table. Save-only. |
| [`ctx-internal-bug`](skills/ctx-internal-bug/SKILL.md) | user | The **internal** sibling of `ctx-bug`: writes a comprehensive, full-diagnostic-detail internal bug report (light scrub — access-secrets only; IPs/hostnames/digests/symbols retained) from an investigation already done this session, using two bundled report templates. Save-only. |
| [`ctx-retro`](skills/ctx-retro/SKILL.md) | user | Post-hoc retrospective for a change or incident already resolved — reconstructs the change-set from the ops git repo. Analyze-and-save. |
| [`ctx-save`](skills/ctx-save/SKILL.md) | user | Minimum state to resume work later. **Read its redaction stance before adopting** — the artifact is unredacted by design and host-local. |
| [`ctx-outstanding`](skills/ctx-outstanding/SKILL.md) | user | The REVIEW member of the family: sweeps the estate's OUTSTANDING watchlist — flags due/overdue date-gated checks, reports open counts, and (on request) closes or adds items. Sole maintainer of the watchlist file; never executes the items. |
| [`ctx-handoff`](skills/ctx-handoff/SKILL.md) | user | Sender-side PREPARE: writes an immutable, evidence-classed handover offer for a named receiver. The sender remains owner. |
| [`ctx-accept`](skills/ctx-accept/SKILL.md) | user | Receiver-side VALIDATE/COMMIT: re-runs critical assertions, classifies drift, synthesizes the mandate, and explicitly accepts with an effective time or rejects. |

The operational-documentation path composes as: `doc-this` or `dig-this`
investigates → `ctx-internal-bug` writes the full-detail internal report →
`ctx-bug` ships the redacted one out → `ctx-retro` writes the post-mortem →
`ctx-save` parks the session. Between sessions, `ctx-outstanding` sweeps the
standing watchlist so open items and date-gated checks don't silently age out.

The ownership-transfer path is deliberately separate:
`ctx-handoff` **offers** → `ctx-accept` **validates and commits or rejects** →
the receiver records the first checkpoint. An offer is never evidence that
ownership moved.

## Design commitments

- **Refuse-guard floors.** Each save-skill states what must be true before it
  will write, and refuses otherwise. Never invent evidence.
- **Deterministic redaction, not judgement.** `ctx-bug` redacts via a fixed
  pattern table — zero LLM discretion on whether a token is a secret.
- **Asymmetric redaction.** Internal docs keep diagnostic detail (addresses,
  service names, versions) because stripping it guts them; only outbound
  reports are scrubbed hard. The boundary is the skill, not the habit.
- **Investigate/save separation.** A skill either runs the investigation or
  writes the artifact, never both by accident.
- **Transactional ownership.** `OFFERED` is not `ACCEPTED`. Handover claims
  carry evidence classes and receiver-side revalidation; ownership changes only
  through an explicit receipt with an effective time.
- **Immutable audit.** Material corrections create a new offer revision.
  Receipts bind to the exact offer digest, and first checkpoints get their own
  record.

## Install

Copy a skill directory into `~/.claude/skills/` (personal, loads everywhere)
or `.claude/skills/` in a repo (project-scoped). Personal overrides project
when names collide. Then fill in its Host binding table.

Install `ctx-handoff` and `ctx-accept` together and bind them to the same
handover store, identity scheme, UTC clock convention, and redaction boundary.

## Not included

The host-context loader (`ctx-infra` on the origin fleet) is deliberately
absent. Its entire value *is* the specifics — topology, addresses, open
risks — so a generalized version would be an empty shell, and the real one
does not belong in a git remote. Write your own; keep it local.

`ctx-save` artifacts are unredacted by design: keep the context store on the
host, out of any repo with a remote. Handover artifacts may be shared with a
named receiver, so the pair requires an explicit `HOST-LOCAL` or `SHARED`
storage mode and never carries access-granting values.
