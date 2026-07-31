---
name: ctx-accept
description: Validate a transactional handover OFFER as its named receiver, re-run critical assertions, classify drift, synthesize the mandate, and write exactly one explicit ACCEPTED, ACCEPTED WITH CONDITIONS, or REJECTED receipt with transfer timing and a first-checkpoint record. Use ONLY when the user explicitly invokes /ctx-accept with an offer path or handover ID. Receiver-side only — never treat the existence of an offer as transferred ownership.
---

<!-- WHY: receipt is the commit point missing from ordinary handover notes.
     The receiver must establish present reality independently, prove they
     understand the mandate, and make ownership timing explicit. Validation is
     read-only until acceptance. Drift is classified by operational consequence,
     not hidden by updating the sender's prose. The offer remains immutable and
     every receipt binds to its exact revision and digest, preventing acceptance
     of a moving target. -->

# ctx-accept

## Host binding

Use the same bindings as the sender-side `/ctx-handoff` skill:

| Placeholder | Meaning |
|---|---|
| `<handover-dir>` | Directory containing offers, receipts, and checkpoints. |
| `<receiver-id>` | Stable identity of the human or agent processing the offer. |
| `<notification-channel>` | Authorized place to announce an effective ownership change. |
| `<redaction-rules>` | Deterministic rules used when artifacts may leave the host. |

The offer is authoritative only as a proposal. Live state and the receiver's
fresh observations are authoritative for validation.

## Contract

Run this skill only as the intended receiver. Before an effective disposition,
perform read-only checks only. Do not start the transferred work merely because
the offer exists.

Bind every receipt to the exact offer path, `Handover-ID`, revision, and
SHA-256 digest. Never edit the offer. Never silently repair a material defect
and then accept the old revision; reject it and require a revised offer.

Ownership rules:

- `ACCEPTED`: transfer commits at the recorded effective time.
- `ACCEPTED WITH CONDITIONS` + `NOW`: transfer commits at the recorded
  effective time; the conditions are obligations owned by the receiver.
- `ACCEPTED WITH CONDITIONS` + `AFTER_CONDITIONS`: transfer has not
  committed. The sender retains ownership until the receiver verifies the
  conditions and writes a superseding effective receipt.
- `REJECTED`: no transfer; sender retains ownership.
- `CONSULTATION`: acceptance commits only the consultation obligation;
  ownership of the underlying objective never moves.

Acknowledgement, partial validation, silence, or expiry is not acceptance.

## Input gate

Refuse only when no identifiable offer artifact can be found or read. Once an
offer is identifiable, structural defects, expiry, identity mismatch, unsafe
probes, missing authority, and critical uncertainty produce an explicit
`REJECTED` receipt rather than an ambiguous stop.

Never self-accept an offer whose sender and receiver resolve to the same actor
unless two independently accountable roles are explicitly named and the user
authorized that arrangement.

## Drift classes

Classify each revalidated assertion exactly once:

| Class | Meaning | Default consequence |
|---|---|---|
| `MATCH` | Actual state satisfies the offered expectation. | Continue validation. |
| `BENIGN DRIFT` | State changed, but mandate, authority, next action, and safety are unaffected. | Record; acceptance may proceed. |
| `ACTION-CHANGING DRIFT` | State changes the next action, ordering, condition, or expected result without voiding the mandate. | No unchanged acceptance; condition explicitly or request revision. |
| `INVALIDATING DRIFT` | State contradicts identity, scope, authority, safety, completion criteria, or a critical precondition. | Reject and require a revised offer. |
| `UNVERIFIABLE` | The receiver cannot establish the claim safely and independently. | Reject if critical; otherwise condition and name the owner of verification. |

Do not call drift benign merely because it is easy to fix. Classify by effect on
the mandate and action, not repair cost.

## Procedure

### 1. Resolve and freeze the offer

Locate the exact offer by path or `Handover-ID`. If several revisions exist,
select the highest non-superseded revision and state why. Confirm the artifact is
still `OFFERED`; compute its SHA-256 digest before validation.

Record:

- offer path and digest;
- handover ID and revision;
- sender and intended receiver;
- ownership mode;
- offered time, expiry, and proposed effective time;
- storage/redaction mode.

A changed digest means the target moved: classify `INVALIDATING DRIFT` and
reject. A higher revision appearing during validation also invalidates the older
one.

### 2. Validate the envelope

Check all of these before running state probes:

1. `<receiver-id>` matches the intended receiver or authorized receiver role.
2. The offer is unexpired.
3. Exactly one known ownership mode is declared.
4. Objective, observable done-when, scope, and authority are present.
5. Approval requirements and forbidden actions are explicit.
6. A single next control action and first checkpoint are defined.
7. The sender actually possesses the authority being transferred.
8. Required resources can be accessed without receiving secret values in the
   artifact.

Any blocking failure becomes `INVALIDATING DRIFT`.

### 3. Apply mode-specific boundaries

Restate what would and would not become yours:

- `TAKEOVER`: the full stated objective.
- `RELIEF`: the objective until the explicit return transaction.
- `DELEGATION`: only the bounded action/result.
- `ESCALATION`: only the named decision or exceptional risk.
- `CONSULTATION`: advice/result only; no ownership movement.

Reject if the offer's scope is broader than its granted authority or if the
return boundary is ambiguous.

### 4. Revalidate critical assertions

Re-run every critical read-only procedure from the evidence ledger. Re-run
non-critical assertions when they affect understanding or are past freshness.
Use a safe equivalent only when the original procedure cannot be run, and record
the substitution and why it proves the same claim.

For each assertion record:

| Claim | Offered class | Procedure | Expected | Actual | Checked UTC | Drift class | Consequence |
|---|---|---|---|---|---|---|---|

Do not execute a mutating, unbounded, credential-exposing, or unauthorized
procedure. Mark it `UNVERIFIABLE`. Do not repair drift during validation:
repair changes the evidence target and requires a new validation cycle or offer
revision.

### 5. Validate capability and control

Confirm independently that the receiver has:

- access to all required artifacts and systems;
- authority for the next control action and first checkpoint;
- sufficient information to meet the done-when criteria;
- explicit stop, escalation, approval, and irreversible-action boundaries;
- capacity to own open loops for the relevant mode and time window;
- an authorized path to notify affected parties.

Missing capability is not a promise to “figure it out later”; it is a condition
or rejection.

### 6. Synthesize without copying

In the receiver's own words, state:

1. the objective and done-when;
2. current state after revalidation;
3. exactly what ownership would transfer under the mode;
4. the exact next control action and expected result;
5. primary risk;
6. most important contingency;
7. first checkpoint;
8. what remains with the sender.

If this synthesis cannot be made concise and unambiguous, reject for insufficient
understanding.

### 7. Choose exactly one disposition

Use these rules:

#### ACCEPTED

Use only when no blocking drift or missing capability remains. Record an
effective UTC time. It may be immediate or a future time, but it must be
unambiguous.

#### ACCEPTED WITH CONDITIONS

List every condition, its owner, deadline/trigger, and proof of satisfaction.
Also choose exactly one transfer timing:

- `NOW`: conditions are non-blocking obligations accepted by the receiver.
- `AFTER_CONDITIONS`: ownership remains with the sender. After satisfying and
  revalidating the conditions, issue a superseding effective receipt.

Never hide `INVALIDATING DRIFT` inside conditions.

#### REJECTED

State each blocking deficiency, required correction, and whether a revised offer
is needed. Ownership remains with the sender. Expired, wrong-recipient, excess-
authority, moving-target, and critical-unverifiable offers are rejected.

### 8. Write the immutable receipt

Create:

`<handover-dir>/<Handover-ID>-r<Revision>-receipt-<UTC-YYYYMMDDTHHMMSSZ>.md`

Never overwrite a prior receipt. If superseding an `AFTER_CONDITIONS` receipt,
link it explicitly.

Use this fixed shape:

```markdown
<!-- WHY: receiver validation receipt created via /ctx-accept. -->

# Handover Receipt — <short objective>

| | |
|---|---|
| Handover-ID | <ID> |
| Offer revision | <N> |
| Offer path | <path/link> |
| Offer SHA-256 | <digest> |
| Receiver | <receiver> |
| Validated at | <UTC ISO-8601> |
| Disposition | <ACCEPTED / ACCEPTED WITH CONDITIONS / REJECTED> |
| Transfer timing | <NOW / AFTER_CONDITIONS / NEVER> |
| Effective time | <UTC ISO-8601 / pending conditions / —> |
| Mode | <mode> |
| Owner after receipt | <receiver/sender; qualify bounded modes> |
| Supersedes receipt | <path or —> |

## 1. Envelope and authority checks
<result of every check>

## 2. Revalidation and drift
| Claim | Offered class | Procedure | Expected | Actual | Checked UTC | Drift class | Consequence |
|---|---|---|---|---|---|---|---|

## 3. Receiver synthesis
<objective, state, ownership boundary, next action, risk, contingency,
done-when, first checkpoint, sender-retained work>

## 4. Capability
<access, authority, information, capacity, notification path>

## 5. Conditions or rejection reasons
<condition + owner + deadline + proof, or blocking deficiency + correction>

## 6. Commit statement
<plain statement of whether ownership transfers, exactly what transfers, and
the effective time; for AFTER_CONDITIONS/REJECTED state that sender retains it>

## 7. Notification
<affected parties, channel, sent/pending, time>

## 8. First checkpoint contract
<action/review, due/trigger, expected result, record path>
```

The commit statement must agree with disposition and transfer timing. If it
does not, the receipt is invalid and ownership remains with the sender.

### 9. Commit and announce

For an effective receipt:

1. Recompute the offer digest immediately before writing; reject if it changed.
2. Write the already-scrubbed receipt.
3. Announce the ownership change to affected parties through
   `<notification-channel>` when authorized; otherwise record who must send it
   and by when.
4. State the sender overlap end.
5. Move to the first checkpoint.

For `AFTER_CONDITIONS` or `REJECTED`, deliver the receipt to the sender and
state plainly that ownership did not transfer.

The skill does not grant permission to send external messages. Use only channels
and recipients already authorized by the user and environment.

### 10. Execute or schedule the first checkpoint

After effective acceptance, execute the offered checkpoint when it is within
ordinary authorization and safe to do. Otherwise schedule it through an
authorized mechanism and record the trigger. The checkpoint is a post-commit
control, not a second acceptance.

Write:

`<handover-dir>/<Handover-ID>-checkpoint-<UTC-YYYYMMDDTHHMMSSZ>.md`

with:

- receipt path and offer digest;
- action taken or exact schedule;
- expected and observed result;
- new drift, if any;
- whether the handover assumptions still hold;
- next action and current owner.

If the checkpoint invalidates assumptions, stop the affected action and
escalate, return, or re-hand ownership explicitly. Acceptance does not silently
revert; the receiver remains owner until a recorded ownership transaction says
otherwise.

## State model

```text
OFFERED -> ACCEPTED -> ACTIVE -> CLOSED
    |          |------> RETURNED
    |          |------> RE-HANDED
    |------> REJECTED
    |------> EXPIRED
```

An `AFTER_CONDITIONS` receipt records validation progress but leaves the offer
in `OFFERED`.

## What this skill does NOT do

- Does not accept merely because the offer is detailed or delivered.
- Does not mutate operational state during validation.
- Does not expand authority beyond the offer, user instruction, or platform
  policy.
- Does not fix a materially invalid offer in place.
- Does not treat `ACTION-CHANGING DRIFT` as a match.
- Does not release the receiver after acceptance without an explicit return,
  closure, or successor handover.
