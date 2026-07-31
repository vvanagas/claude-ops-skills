---
name: ctx-handoff
description: Prepare and write a transactional handover OFFER for a named receiver, with an explicit ownership mode, authority boundary, evidence-classed state, read-only revalidation procedures, one next control action, contingencies, expiry, and first-checkpoint contract. Use ONLY when the user explicitly invokes /ctx-handoff (optionally with a receiver or short label). Sender-side only — ownership does NOT transfer until the receiver validates the offer and records an effective acceptance.
---

<!-- WHY: a state snapshot is not an ownership transfer. This skill implements
     the PREPARE half of a two-party protocol: the sender offers an evidence-
     backed mandate, but remains responsible until a distinct receiver validates
     it and explicitly commits. The invariant to preserve is OFFERED != ACCEPTED.
     Evidence classes stop prose from flattening observations, reports, and
     assumptions into equal facts. Read-only revalidation procedures let the
     receiver detect drift before acting. Immutable offer/receipt files preserve
     the transaction boundary: material corrections create a revised offer,
     never a silently repaired history. -->

# ctx-handoff

## Host binding

Bind these placeholders before first use, either here or in the local host
primer:

| Placeholder | Meaning |
|---|---|
| `<handover-dir>` | Directory visible to both sender and intended receiver. Keep it inside a deliberately chosen local or shared store. |
| `<ops-git-dir>` | OPTIONAL local-only git store or equivalent snapshotter covering `<handover-dir>`. |
| `<sender-id>` | Stable human or agent identity used in offers. |
| `<redaction-rules>` | Deterministic rules for artifacts that may leave the host; normally the sibling `ctx-bug` pattern table. |

The receiver-side companion is `/ctx-accept`. Adopt both skills with the same
`<handover-dir>`, clock convention (UTC), identity scheme, and redaction
boundary.

## Contract

A handover is a transaction, not a document:

```text
PREPARE       sender writes and delivers an OFFERED artifact
VALIDATE      receiver re-runs critical assertions and reports drift
COMMIT        receiver records a disposition and effective transfer time
POST-COMMIT   receiver announces ownership and performs the first checkpoint
```

The sender owns the work through PREPARE and VALIDATE. An offer, delivery
message, acknowledgement, or timeout is not acceptance. Ownership changes only
when an intended receiver writes an effective `ACCEPTED` receipt, or an
`ACCEPTED WITH CONDITIONS` receipt whose transfer timing is `NOW`.

Expiry aborts an uncommitted transfer. Corrections never rewrite an offered
artifact: issue a higher revision with `Supersedes` pointing to the old offer.
Receipts and checkpoint records are immutable. The newest valid receipt for the
newest valid revision governs.

## Ownership modes

Declare exactly one mode; it controls what can transfer:

| Mode | Ownership effect |
|---|---|
| `TAKEOVER` | Receiver owns the whole stated objective through closure or a later explicit transfer. |
| `RELIEF` | Receiver owns the whole stated objective until the named return condition; return still requires an explicit receipt. |
| `DELEGATION` | Receiver owns only the bounded action/result; sender retains the broader objective. |
| `ESCALATION` | Receiver owns the named blocked decision or exceptional risk; sender retains everything else. |
| `CONSULTATION` | Receiver supplies advice only. Ownership never moves, even after acceptance. |

Never use `CONSULTATION` when the intent is for the receiver to act. Never
describe a bounded delegation or escalation as a full takeover.

## Confidentiality boundary

Choose and record one storage mode before writing:

- `HOST-LOCAL`: preserve operational detail, but never include passwords,
  tokens, private keys, cookies, customer data, or other access-granting values.
  Reference the secret store or access path instead.
- `SHARED`: apply `<redaction-rules>` in memory before the first write.
  Preserve only the identifiers and evidence the receiver is authorized to see.

If the destination is synced, remotely backed up, shared, or uncertain, use
`SHARED`. Never write an unredacted draft and clean it afterward.

## Refuse-guard — check before writing

Refuse to produce an offer unless all of these are known:

1. A named intended receiver or unambiguous receiver role.
2. One ownership mode.
3. An objective with observable completion criteria.
4. Scope, authority, approval requirements, and forbidden actions.
5. Current state reconstructed from authoritative sources.
6. At least one critical claim with a safe read-only revalidation procedure.
7. Exactly one next control action with expected result and stop condition.
8. An expiry, proposed effective time, and first-checkpoint definition.

State every missing item. Do not invent evidence or silently weaken the floor.
If no receiver has been identified, use `/ctx-save` for resumable state instead.

## Evidence classes

Assign every load-bearing claim exactly one class:

| Class | Meaning |
|---|---|
| `OBSERVED` | Directly verified by the sender at the recorded time. |
| `DERIVED` | Concluded from named evidence; record the reasoning. |
| `REPORTED` | Supplied by another party; name the source. |
| `ASSUMED` | Not verified. |
| `STALE` | Previously verified, but its declared freshness limit has elapsed. |

For each critical claim record: claim, class, source, read-only verification
procedure, expected result, observed time, freshness limit, and whether failure
changes or invalidates the next action. A critical `ASSUMED` or `STALE`
claim must be called out as a receiver acceptance risk.

Verification procedures must be read-only, deterministic enough to compare,
bounded in output, and safe to repeat. Never embed credentials or a command
whose execution changes the state being tested.

## Procedure

### 1. Pin the transfer

Resolve the sender, intended receiver, ownership mode, objective, and why the
transfer is needed. For `RELIEF`, name the return condition. For
`DELEGATION` or `ESCALATION`, state precisely what remains with the sender.
For `CONSULTATION`, state the expected advice/result and that ownership stays
with the sender.

### 2. Allocate identity

Create:

- `Handover-ID`: `HO-<UTC-YYYYMMDDTHHMMSSZ>-<short-random-suffix>`
- `Revision`: `1`, or one greater than the offer being replaced
- offer path: `<handover-dir>/<Handover-ID>-r<Revision>-offer.md`

A revision keeps the same `Handover-ID`. Never overwrite an existing path.
Record the prior offer under `Supersedes`.

### 3. Reconstruct current state

Use authoritative files, repositories, task trackers, dashboards, service
state, and recent probe results rather than conversation memory. Capture:

- completed work and work in progress;
- exact state left in files, systems, environments, processes, or queues;
- open loops, promises, timers, external dependencies, and pending decisions;
- material decisions, rejected alternatives, and conditions that would reverse
  those decisions;
- resources and access paths the receiver needs;
- unknowns and explicitly unverified assumptions.

Do not investigate a new root cause merely to make the offer look complete.
If missing evidence is load-bearing, stop or mark the offer blocked rather than
manufacturing certainty.

### 4. Define the mandate

Record:

- objective and observable done-when criteria;
- priorities and ordering;
- in-scope and out-of-scope work;
- authority granted by this transfer;
- actions still requiring approval;
- forbidden or irreversible actions;
- parties who must be notified after effective acceptance.

The offer cannot grant authority the sender does not possess.

### 5. Define control

Specify exactly one next control action:

- action;
- expected result;
- stop condition;
- reversible and irreversible effects;
- required approval;
- evidence that would make the action unsafe or obsolete.

Add concise `IF <condition> THEN <action>` contingencies for the important
branches, including evidence mismatch, deadline expiry, and escalation.

Define the first checkpoint as an observable action or review after acceptance,
with an owner, due time or trigger, expected result, and recording location.
The checkpoint is not a vague “continue work” instruction.

### 6. Write the immutable offer

Use this fixed shape:

```markdown
<!-- WHY: transactional handover offer created via /ctx-handoff. -->

# Handover Offer — <short objective>

| | |
|---|---|
| Handover-ID | <ID> |
| Revision | <N> |
| Status | OFFERED |
| Mode | <TAKEOVER / RELIEF / DELEGATION / ESCALATION / CONSULTATION> |
| Sender | <sender> |
| Intended receiver | <receiver> |
| Offered at | <UTC ISO-8601> |
| Expires at | <UTC ISO-8601 or explicit condition> |
| Proposed effective time | <time/condition; subject to receiver receipt> |
| Supersedes | <prior path or —> |
| Storage mode | <HOST-LOCAL / SHARED> |
| Owner before commit | <sender; qualify bounded modes> |

> OFFER IS NOT TRANSFER: ownership remains as stated above until /ctx-accept
> records an effective acceptance for this exact revision.

## 1. Mandate
<objective, done-when, priorities, scope, authority, approvals, forbidden work>

## 2. Current state
<completed, in progress, state left behind, timestamped facts>

## 3. Evidence ledger
| Critical | Claim | Class | Source | Read-only revalidation | Expected | Verified UTC | Freshness | Drift effect |
|---|---|---|---|---|---|---|---|---|

## 4. Decisions and rejected alternatives
<decision, rationale, rejected option, invalidating condition>

## 5. Open loops and dependencies
<owner, item, due/trigger, current status>

## 6. Resources and access
<paths, IDs, systems, people, required permissions; no secret values>

## 7. Next control action
<one action, expected result, stop condition, effects, approval>

## 8. Contingencies
<explicit IF-THEN rules>

## 9. Risks and unknowns
<top three risks, unknowns, unverified assumptions>

## 10. Transfer timing and overlap
<expiry, proposed effective time, sender overlap end, return condition if any>

## 11. First checkpoint
<action/review, owner, due/trigger, expected result, record location>

## 12. Receiver response required
<run /ctx-accept against this path; validate, synthesize, and issue exactly one
disposition: ACCEPTED, ACCEPTED WITH CONDITIONS, or REJECTED>
```

### 7. Deliver without claiming transfer

Write only the already-scrubbed final artifact. Give the intended receiver the
exact path or authorized link and ask them to run `/ctx-accept`. Report to the
sender:

- offer path and revision;
- expiry;
- current owner;
- critical `ASSUMED` or `STALE` claims;
- expected receipt and checkpoint locations.

Remain available for the declared overlap. If the offer expires without an
effective receipt, record it as expired and retain ownership. Do not announce a
transfer from the sender side.

## State model

```text
DRAFT -> OFFERED -> ACCEPTED -> ACTIVE -> CLOSED
                    |            |------> RETURNED
                    |            |------> RE-HANDED
                    |----> REJECTED
                    |----> EXPIRED
```

`ACCEPTED WITH CONDITIONS / AFTER_CONDITIONS` remains uncommitted until a
superseding effective receipt is written.

## What this skill does NOT do

- Does not accept on the receiver's behalf or prove the receiver understood.
- Does not transfer ownership merely by writing or delivering an offer.
- Does not execute the next control action.
- Does not mutate live state while gathering evidence.
- Does not replace `ctx-save`; use that for possible future resumption without
  a named ownership transfer.
- Does not replace `ctx-bug`; use that for an externally shippable incident
  report rather than an operational mandate.
