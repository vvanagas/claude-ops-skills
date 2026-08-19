---
type: Pending
title: Adapt mirror-check.sh to verify policy master <-> overlay <-> projection
description: policy/ has no mechanical drift check; the "matched semantic change in both files" rule is a habit, not a script.
status: stable
state: open
trigger: Before the next substantive edit to AGENTS.master.md or either overlay, or when a fleet projection is regenerated.
owner: claude-ops-skills
tags: [policy, drift, tooling]
generated: { by: claude/fable-5, at: 2026-08-19 }
---

# Policy mirror-check

`policy/` (master + `overlays/{posix,windows-user}.md` + `PLACEHOLDERS.md`)
introduced the same multi-file-must-stay-consistent problem that
`coding-rules` already solved for its master/bindings with `mirror-check.sh`
and `projection-check.sh`.

Today nothing detects when:

- a master rule changes but an overlay still binds the old mechanic;
- an overlay marks a rule N/A that the master no longer carries;
- a private fleet projection drifts from `master + overlay` (the projection
  is the deployed agent file — the thing that actually runs).

Adapt the coding-rules scripts to this bundle:

1. **mirror-check** — every `[admin]`/named rule in the master is either bound
   or explicitly marked N/A in each overlay; no overlay binds a rule the
   master dropped. A content-hash stamp (as coding-rules uses) makes an
   unreviewed master edit fail the check.
2. **projection-check** — given a projection + the overlay it claims, assert
   every master rule is represented (bound, inherited, or N/A). Runs
   host-side against the private estate overlay; only the checker ships here.

Cross-ref: coding-rules `mirror-check.sh` / `projection-check.sh` are the
template. Keep the estate projection and its overlay OUT of this repo — the
checker is generic, the inputs are private.
