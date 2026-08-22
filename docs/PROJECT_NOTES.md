# Project Notes — claude-ops-skills

Durable, evolving per-project knowledge note (companion to the `MEMORY.md`
pointer). Update as work lands; do not spawn dated files.

## 1. What this is

Seven generalized, publishable copies of ops skills that run on the origin
fleet, plus two generic transactional handover skills designed in this repo.
The seven live originals stay at `~/.claude/skills/<name>/SKILL.md` on the
hosts; their copies here are the sanitized, estate-agnostic export.
`ctx-internal-bug` additionally bundles its two report templates under
`skills/ctx-internal-bug/templates/` (generalized copies of the host
templates the live skill points at).
`ctx-handoff` and `ctx-accept` have no host-bound origin: they form one
two-party protocol and should be installed, bound, and evolved together.

**The exported copies are one-way.** This repo is downstream for those
skills. A fix made here does not reach the hosts, and a host edit does not
reach here — see §4.

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

The handover pair was authored estate-agnostically: it contains role and path
placeholders, no origin-fleet examples, and an explicit rule never to place
access-granting values in an offer, receipt, or checkpoint.

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
  host's `~/.claude/skills/<name>/SKILL.md` and the exported copies under
  `skills/` here. Improving methodology on a host and forgetting this repo
  (or the reverse) is the expected failure. If the divergence ever matters,
  decide a direction of truth rather than hand-merging.
- **The handover pair is one protocol.** Changing modes, evidence classes,
  drift classes, receipt semantics, or filenames in one skill requires a
  compatibility review of the other.
- **Offers are immutable and non-transferring.** `ctx-handoff` leaves
  ownership with the sender. Only an effective receipt from `ctx-accept`
  commits transfer; `AFTER_CONDITIONS` does not.
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

## 6. policy/ — agent operating policy (added with history.txt #7)

Estate-agnostic abstraction of the fleet global agent-instruction files
(the CLAUDE.md / AGENTS.md near-mirrors). Structure: a platform-neutral
`AGENTS.master.md` + `overlays/{posix.md,windows-user.md}` +
`PLACEHOLDERS.md`. A deployed agent file is a projection: master + platform
overlay + a PRIVATE estate overlay (never in this repo).

Design decisions:
- **No duplication of coding-rules.** TDD Iron Law / secrets-in-code /
  idempotency live canonically in vvanagas/coding-rules; the master points
  there and carries only what that repo does not (ops-git pattern, workflow
  protocol, ledger discipline, docs-follow-code, durable capture, OKF,
  scripting/shell preference). Avoids a 5th synchronized mirror.
- **[admin] tagging.** Rules presuming host-admin authority are tagged so a
  restricted overlay can satisfy them within user scope or mark them N/A —
  silence is not compliance.
- **windows-user overlay = OS x privilege.** A no-admin Windows box deletes
  the host-admin half and keeps the portable project-workflow half. Inferred
  mechanics are marked [unverified] pending validation on a real restricted
  host (schtasks self-scoped, per-user installers — estate-local caveats the
  operator fills in).

Gate: same forbidden-token sweep as the skills (v2 estate pattern), run over
policy/ in scratch AND in-repo — CLEAN. No new token classes were required.

Follow-up (not done): adapt coding-rules `mirror-check.sh` to verify
master <-> overlay <-> fleet-projection drift mechanically, turning the
"matched semantic change in both files" habit into a script.

2026-08-22: `projections/linux-posix.md` is the first rendered projection
(imported on the origin Linux host via `@path` from `~/.claude/CLAUDE.md`
next to a private estate overlay). Rule: generic text lands in the master
first, then the projection — never edited on a host.
