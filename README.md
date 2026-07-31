# claude-ops-skills

Estate-agnostic Claude Code skills for **operating a server**: investigate a
problem, dig to the code-level root cause, write it up internally, ship a
redacted report outside, and save resumable session state.

These are generalized copies of skills that run on a live fleet. Every host
name, address, product, database and path has been replaced with a
placeholder — each skill opens with a **Host binding** table listing what to
fill in.

## The skills

| Skill | Invocation | What it does |
|---|---|---|
| [`doc-this`](skills/doc-this/SKILL.md) | user | Runs a structured diagnostic (hypothesis ladder → probes → diagnosis) and writes a deep troubleshooting doc. The only one that *investigates and saves*. |
| [`dig-this`](skills/dig-this/SKILL.md) | user | Code-level root-cause investigation when the bug points at a source artefact. Read-only; locates the *executing* file, cross-checks live-vs-shipped, counts the class-of-bug, finds a negative control. Investigates only — writes nothing. |
| [`ctx-bug`](skills/ctx-bug/SKILL.md) | user | Turns an investigation already done this session into a **redacted, externally-shippable** bug report. Carries the deterministic redaction pattern table. Save-only. |
| [`ctx-retro`](skills/ctx-retro/SKILL.md) | user | Post-hoc retrospective for a change or incident already resolved — reconstructs the change-set from the ops git repo. Analyze-and-save. |
| [`ctx-save`](skills/ctx-save/SKILL.md) | user | Minimum state to resume work later. **Read its redaction stance before adopting** — the artifact is unredacted by design and host-local. |

They compose: `doc-this` or `dig-this` investigates → `ctx-bug` ships it out →
`ctx-retro` writes the post-mortem → `ctx-save` parks the session.

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

## Install

Copy a skill directory into `~/.claude/skills/` (personal, loads everywhere)
or `.claude/skills/` in a repo (project-scoped). Personal overrides project
when names collide. Then fill in its Host binding table.

## Not included

The host-context loader (`ctx-infra` on the origin fleet) is deliberately
absent. Its entire value *is* the specifics — topology, addresses, open
risks — so a generalized version would be an empty shell, and the real one
does not belong in a git remote. Write your own; keep it local.

`ctx-save` artifacts are unredacted by design: keep the context store on the
host, out of any repo with a remote.
