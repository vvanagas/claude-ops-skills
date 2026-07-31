---
type: Pending
title: Read the generalized skills end-to-end for lost teaching value
description: Each generalizing agent flagged spots where replacing a concrete example with a category cost vividness or a load-bearing fact.
status: stable
state: open
trigger: Before recommending these skills to anyone else, or on first real use of one.
owner: claude-ops-skills
tags: [quality, review]
generated: { by: claude/fable-5, at: 2026-07-31 }
---

# Generalization review

Known soft spots, self-reported at export time:

- **ctx-bug** — the log-density exemplar was a pointer to a real incident
  doc; replaced with a prose spec of the same density. Prose only
  approximates what the example taught.
- **ctx-retro** — the "this host has one repo, the other has two" fact was
  operationally load-bearing (it stops the agent hunting for a repo that
  does not exist). Now an instruction to declare which repos exist.
- **doc-this** — §B probe vocabulary lost its factual payload (which
  database is real, exact grep targets); it is now a template. Also the two
  gotchas read as "check this" rather than "this is true here".
- **dig-this** — generalized further than briefed (interpreter and search
  engine became placeholders too); concreteness now carried by API shapes
  rather than product names. Reversible if it reads as over-abstracted.

The check: read each file as an adopter with none of the origin context and
ask whether the procedure is still executable.
