# Project Notes — claude-ops-skills

Durable, evolving per-project knowledge note (companion to the `MEMORY.md`
pointer). Update as work lands; do not spawn dated files.

## 1. What this is

Generalized, publishable copies of five ops skills that run on the origin
fleet. The live originals stay at `~/.claude/skills/<name>/SKILL.md` on the
hosts; this repo is the sanitized, estate-agnostic export.

**The copies are one-way.** This repo is downstream. A fix made here does not
reach the hosts, and a host edit does not reach here — see §4.

## 2. Why the split, and what was scrubbed

The origin skills are host-bound: they name hosts, internal and public
addresses, vhosts, databases, products, a personal DB login, and — in the
excluded one — the estate's open security risks. That last category is why
this is not a straight copy: a private repo is one credential away from
public, and an unremediated-vulnerability inventory is the worst thing to
have there.

Scrub classes applied: host names → role placeholders; addresses → `<...>`;
products/orgs/vendors → generic roles; DB names and logins → placeholders;
estate paths → `<ops-home>/...`; pinned software versions → generic; and
**every statement about a real unremediated vulnerability deleted outright**,
not genericized.

Verified mechanically before the first push with a forbidden-token regex
sweep over `skills/` (see `history.txt` #1 for the pattern). Re-run it before
any future push — it is the gate, not the agents' self-reports.

## 3. Deliberate exclusion — the host-context loader

`ctx-infra` (origin fleet) is NOT here and should not be added. Its value is
precisely its specificity, so a generalized version would be a hollow shell;
and the real one is an attack briefing (topology, ports, open risks). It
stays host-local, tracked only in the local ops git repo.

## 4. Gotchas

- **One-way copies, no sync mechanism.** Nothing detects drift between a
  host's `~/.claude/skills/<name>/SKILL.md` and `skills/<name>/SKILL.md`
  here. Improving methodology on a host and forgetting this repo (or the
  reverse) is the expected failure. If the divergence ever matters, decide a
  direction of truth rather than hand-merging.
- **`ctx-save` is unredacted by design.** The published version makes this an
  explicit two-mode contract with a loud warning. Do not "fix" it into
  silently redacting.
- **The redaction table is the product.** `ctx-bug`'s value is the
  deterministic pattern set. Extend it (never narrow it) when a new
  access-granting token format appears.
- Skill precedence is **personal overrides project** — a vendored copy in a
  repo is inert if a same-named personal skill exists. Silent, no error.

## 5. Open items

See [`../pending/index.md`](../pending/index.md).
