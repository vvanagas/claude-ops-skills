<!-- ============================================================================
     TEMPLATE — Internal incident / code-level root-cause write-up
     Location: <templates-dir>/_template_incident_report.md
     Lineage:  formalised 2026-06-27 on the originating estate from a
               poller-stuck-on-immutable-rows incident write-up, which itself
               extended a delta-import OOM write-up.

     HOW TO USE
       1. Copy to  <docs-dir>/incident_<YYYY-MM-DD>_<kebab-slug>.md
       2. Fill every ‹angle-bracket› placeholder. Delete the guidance comments
          as you go, OR keep them — they render invisibly.
       3. Before publishing, run the FEATURE-PARITY CHECKLIST at the bottom.
          Every box is either filled or explicitly marked "N/A — <reason>".
       4. This template pairs with the standalone disciplines below. It is the
          INTERNAL aftermath doc; the external (redacted) sibling goes to
          <reports-dir> (via /ctx-bug), the post-hoc change retro to
          <retros-dir> (via /ctx-retro). Link them in §10.

     CONVENTIONS & DISCIPLINES (apply to every section)
       M1  Never silently omit a section. If a section has nothing, STATE the
           absence and WHY ("N/A — purely a code defect, no data trigger").
       M2  No hallucination. Only assert what was observed/decompiled/queried.
           Anything inferred-but-unverified must be flagged as such inline.
       M3  Record branches considered and REJECTED, not just the path taken —
           ruled-out hypotheses (§2), N/A depth probes (§3), and non-fixes
           (§9 defense-in-depth). Roads-not-taken are the least-recoverable,
           highest-value content.
       M4  Dual timestamps. Quote logs as "HH:MM local (HH:MM UTC)" — container
           clocks are often UTC while the host is +TZ; ambiguity costs hours.
       M5  Confidence flags. Distinguish "verified end-to-end" from "confirmed
           at source but not observed live". Say which.
       M6  Comprehensive in DEBUGGING SUBSTANCE, zero fluff. Capture every fact
           a future debugger would need; write nothing for the sake of looking
           thorough. This is a debugging artefact, not a compliance doc — a
           one-line "N/A — <reason>" beats a padded paragraph, and no section is
           a box to tick. Only the root cause is kept terse in §0 (full chain
           in §4).
     ============================================================================ -->

# Incident — ‹one-line title: component + failure mode›

> **Type:** Incident write-up (Diátaxis: How-to / reference)
> **Date:** ‹YYYY-MM-DD›
> **Scope:** ‹host(s) / container(s) / DB + IPs touched›
> **Status:** ‹Resolved | Mitigated | Partial› (‹active state stopped how›; ‹code fix proposed/shipped?›; ‹recurrence caveat if any›)
> **Triggered by:** ‹how it surfaced — include if it was incidental to another request, and note any unrelated faults the same sweep turned up›

---

## 0. LLM Preamble — pin these facts before reading

<!-- A dense bullet list a future reader/LLM can load in seconds. Mirror the
     report's own conclusions. Include EACH of the following where applicable;
     mark any that don't apply N/A rather than dropping the line. -->

- **Root cause (one line):** ‹exact symbol @ file:line + the thrown/observed error›.
- **Mechanism / why it persists or loops:** ‹the control-flow reason the fault repeats or sticks›.
- **Dead-code / guard / edge observation:** ‹any guard that looks protective but never fires; the precondition that makes this the common path vs an edge case›.
- **Data safety:** ‹is underlying data intact? bookkeeping-only vs data-loss›.
- **Class-of-bug magnitude:** ‹how many rows/values/callers share the trigger — 1 vs N›.
- **Escape hatch (negative control):** ‹the sibling condition that does NOT fail, and why›.
- **Fix applied this session:** ‹one-line of the remediation actually run›.
- **Smoking gun:** ‹the single verbatim decompiled/queried line that proves it›.
- **Cross-incident tie:** ‹shared objects/flow/weakness with a prior incident, or "none"›.
- **Secondary impact:** ‹side effects independent of the headline symptom, e.g. notifications never sent›.
- **Restart / self-recovery characterization:** ‹does a restart clear it or not, and WHY — DB-state-driven vs in-memory. Contrast a sibling incident if relevant›.
- **Operational cost / latent resource risk:** ‹log/disk/CPU/neighbour-service load the fault itself imposes; rotation/quota caps in place or not›.

---

## 1. Symptom (what was reported)

<!-- The verbatim trigger, then what the investigation surfaced. If one sweep
     turned up MULTIPLE unrelated faults, separate them explicitly and scope
     this report to one (link the others in §10). End with the verbatim error
     / stack excerpt — never paraphrase a stack trace. -->

Trigger: *"‹verbatim request / alert›"*

The ‹scan/log review› surfaced:
1. **‹fault A›** — ‹one line; if not this incident, say "handled separately, see §10"›.
2. **‹fault B (this report)›** — ‹frequency + scope, e.g. "240 ERR / 2 h, every 30 s, one job"›.

```
‹verbatim error line + stack, first frames at minimum›
```

---

## 2. Hypothesis ladder

<!-- Every hypothesis tested, INCLUDING the initial lead that proved wrong and
     anything ruled out. The Outcome column is what makes this honest. -->

| Rank | Hypothesis | Probe | Outcome |
|------|-----------|-------|---------|
| 1 | ‹the first/obvious lead, often the reporter's framing› | ‹command/query› | ‹Confirmed / Ruled out — evidence› |
| 2 | ‹…› | ‹…› | ‹…› |
| … | ‹…› | ‹…› | ‹…› |

---

## 3. Evidence collected

<!-- Numbered probes in the order actually run. Each: prose intent (what
     hypothesis it tested) + exact command(s) + a "Finding:" line stating what
     it proved or ruled out. Lead in with constraints (read-only? scratch
     location?). The THREE depth probes below are MANDATORY — include each as a
     real probe OR mark "N/A — <reason>". -->

‹Lead-in: read-only? extraction to <scratch-dir> (not a shared tree)? image/digest pinned?›

**Probe 1 — ‹title›:**
```bash
‹command›
```
Finding: ‹what it proved / ruled out›.

**Probe 2 — ‹title›:** …

<!-- MANDATORY DEPTH PROBES (each present or N/A+reason): -->

**Probe — Live-vs-shipped cross-check (MANDATORY):**
<!-- Prove the LIVE artefact matches what was SHIPPED (decompiled-from-running-
     jar vs repo/migration; live /etc/foo.conf vs repo copy). Rules out an
     out-of-band hot-patch and locates where the fix must land. For a compiled
     artefact extracted from the running container, state "live ≡ shipped by
     construction". -->
Finding: ‹match / differ — and what that means for fix locus›.

**Probe — Class-of-bug count (MANDATORY if data/config-triggered):**
```sql
‹count rows/values that violate the invariant the broken code assumes›
```
Finding: ‹1 vs N — changes urgency and workaround choice›. <!-- or N/A — purely a code defect -->

**Probe — Negative control (MANDATORY):**
<!-- A sibling input/row/endpoint/host that does NOT fail. A failure with no
     contrast is a coincidence, not a localisation. -->
Finding: ‹failing vs passing, side by side›.

**Probe — Provenance / artefact extraction (if a compiled/baked artefact):**
<!-- image + digest, jar path, extraction dir; how the source was reached
     (decompile tool). Underpins §9's grounding map. -->
Finding: ‹image digest, artefact location, decompile method›.

**Probe — Triggering-input provenance (if the fault was data/input-driven):**
<!-- Trace the BAD INPUT back to origin: who/what created it, when, the source
     file/object/row. Different from artefact provenance above. Often names the
     recurrence vector and ties to prior incidents. -->
Finding: ‹what input triggered it, who/what produced it, when, where it lives›.

---

## 4. Root cause

<!-- The full causal chain (kept OUT of §0). Numbered steps from trigger to the
     failing line. Where relevant, the two-sides framing (shared-library
     contract vs application assumption). End by naming the fix LOCUS.
     If root cause is NOT proven: say so plainly and list what was ruled out
     (link §2) — an honest "unknown, here's the evidence" beats a guessed chain. -->

1. ‹step›
2. ‹…›
N. ‹the throw/failure, file:line›.

‹Two-sides framing if applicable: who produces the bad condition vs who trips on it.›
Fix locus: ‹where the patch must land — and why that side is cheapest/correct›.

---

## 5. Fix applied / recommended

<!-- Separate APPLIED (this session) from RECOMMENDED (code/upstream). -->

**Applied this session — ‹data-side / config / restart› (immediate):**
```‹sql|bash›
‹the exact remediation, with backup/guard noted›
```
Result: ‹observable effect›. Reversible: ‹how›.

**Fidelity of the manual fix — what it skipped vs. the code path.**
<!-- MANDATORY when a manual remediation substitutes for a code path: state
     exactly what the app would have done that the manual action did/didn't
     reproduce, and confirm nothing data-integrity-critical was skipped
     (grounded in the decompile/source). -->
‹The manual action reproduced ‹X, Y›; it skipped ‹Z›; ‹Z› is/ isn't data-critical because ‹decompile-confirmed reason›.›

**Recommended — code fix (‹repo/image›), see §9.** ‹One-line pointer + recurrence caveat until shipped.›

---

## 6. Verification

<!-- Evidence PER change. Command + the relevant result line, before/after.
     Dual timestamps (M4). State explicitly anything NOT verified end-to-end
     (M5) — e.g. "confirmed at source, not observed on the next live trigger". -->

```bash
‹before: command + result›
‹after:  command + result›
```
Confirmed: ‹what the result proves›.
Not verified end-to-end: ‹what remains to confirm, and when it can be›.

---

## 7. Generalization — when else does this fire?

<!-- Include each applicable angle as its own bullet; this is where altitude
     lives. Mark N/A rather than dropping. -->

- **Recurrence cadence / trigger:** ‹what set of inputs re-triggers it, how often›.
- **Cross-incident / historical recurrence:** ‹prior rows/incidents that exercised the same path›.
- **Class-wide latent generalization:** ‹other callers/columns/endpoints with the same shape›.
- **Secondary-impact generalization:** ‹e.g. notification silence affecting all imports›.
- **Shared systemic weakness:** ‹a design weakness common to related incidents, e.g. bucket-vs-content-type scoping›.
- **Restart-persistence + resource growth:** ‹does it survive restarts; unbounded log/disk while it runs›.
- **Systemic signal:** ‹if this is the Nth bug in one subsystem in a short window, SAY SO and recommend a dedicated hardening review rather than another point fix›.

---

## 8. Durable mitigation

<!-- Numbered, ordered roughly by leverage. Cover code, library, observability,
     enabling infra, upstream/data hygiene, resource bounding, tests, and the
     subsystem review. Drop the ones that don't apply; don't pad. -->

1. **Ship the code fix (§9 Fix 1).** ‹…›
2. **Class-wide / library fix (§9 Fix N).** ‹weigh blast radius›.
3. **Observability / alerting.** ‹the signal that would have caught it: stuck-row query, repeated-ERROR alert, missing positive signal›.
4. **Enabling infra / operational.** ‹e.g. a dedicated scratch LV created this session — record it›.
5. **Upstream-process / data hygiene.** ‹e.g. content-type-scope a workflow; split buckets›.
6. **Bound the resource.** ‹log rotation cap, disk quota, memory limit — close the latent-growth risk from §7›.
7. **Add a regression test.** ‹the exact case that ships broken today, as an assertion›.
8. **Schedule a subsystem hardening review.** ‹if §7 systemic signal fired›.

---

## 9. Prevention code patterns (‹decompile|source›-confirmed)

<!-- The concrete fix menu, best-first, GROUNDED. Lead with the grounding note.
     Each Fix: locus + risk annotation, Before/After in the project's language,
     a closing character line. Include the central/entity option WITH caveats
     if the accessor/mapper path is generated or unverified. Then "Which to
     use", then the defense-in-depth NON-fix, then the provenance map.
     If the fix is NOT code (infra-rooted incident: memory cap, log rotation,
     config, capacity) say so — "No code fix: <why>; the fix is operational,
     see §8" — and don't invent code to fill this section. -->

‹Grounding lead-in: verified against ‹artefact›; every snippet maps to a method actually decompiled — see provenance map; nothing assumes a field/method/column not present in the decompiles or live schema. Which fixes are app-owned vs shared-library.›

**Fix 1 — ‹title› (`Class:line`) — RECOMMENDED, ‹risk/impact annotation›**
```‹lang›
// Before
‹exact current code›
// After
‹concrete change›
```
‹Closing line: minimum necessary change / guarantees the crashing path regardless of internals.›

**Fix 2 — ‹title› (`Class`) — ‹annotation›** … <!-- repeat per fix, ranked -->

**Fix N — central/entity option (`Entity.setter`) — centralizes the invariant (READ CAVEATS)**
<!-- Use when a single choke point (setter/mapper) could fix the class, but its
     effectiveness depends on generated accessors or an unverified mapper path.
     State the caveats explicitly; do NOT over-promise. -->
‹Before/After + caveats: (a) generated accessor must be opted out; (b) only fixes the load path IF the mapper goes through the setter — UNVERIFIED. Therefore a complement, not a replacement.›

**Which to use:** ‹rank with the trade-offs — "Fix 1 now (guaranteed), Fix N if confirmed, library fix later"›.

**Defense-in-depth — observation, NOT a standalone code fix.**
<!-- A robustness gap adjacent to the bug (e.g. an unbounded catch/retry). If a
     proper fix would need a SCHEMA or DESIGN change (e.g. no attempt-counter
     column exists), say so and DO NOT fabricate a one-liner against fields that
     don't exist. This is the M2/M3 discipline made visible. -->
‹The adjacent gap, why a real fix needs a design/schema decision, and that it is out of scope for a code-only change.›

**Grounding & provenance** (so a maintainer trusts these come from their bytecode, not inference):
- Fix 1 — `‹File.java:lines›` (‹what was read›).
- Fix N — `‹File.java:lines›`.
- Reached via `‹entry point›`; classes extracted from ‹image + digest›, retained under `‹<scratch-dir>/…›`.

---

## 10. Cross-references

- **External (redacted) bug report:** `‹<reports-dir>/…›` (or "not filed").
- **Post-hoc change retrospective:** `‹<retros-dir>/…›` (or "not filed").
- **Related incident(s):** `‹<docs-dir>/incident_…›` — ‹shared objects/weakness›.
- **Parallel findings this session (not this incident):** ‹one line + where handled›.
- **Host topology / reload conventions:** ‹your host-primer / infra-brief docs›.
- **Evidence artefacts retained:** `‹<scratch-dir>/…›` (jar, decompiles, dumps).
- **Alert / dashboard / ticket** (only if one exists): ‹link to the signal or issue — skip the line otherwise›.

---

<!-- ============================================================================
     FEATURE-PARITY CHECKLIST — tick each before publishing.
     Every item is FILLED or "N/A — <reason>". This guarantees 1:1 conceptual
     parity with the reference report. Delete this block after self-review, or
     keep it (renders invisibly).

     FRONT MATTER
       [ ] Title states component + failure mode
       [ ] Diátaxis Type / Date / Scope / Status (with recurrence caveat)
       [ ] Triggered-by notes how it surfaced + any unrelated co-findings

     §0 PREAMBLE (each present or N/A)
       [ ] root-cause one-liner (symbol@file:line)   [ ] mechanism/why-it-persists
       [ ] dead-code/guard/edge observation          [ ] data-safety statement
       [ ] class-of-bug magnitude                     [ ] escape hatch / negative control
       [ ] fix applied (one line)                     [ ] smoking gun (verbatim)
       [ ] cross-incident tie                         [ ] secondary impact
       [ ] restart/self-recovery characterization     [ ] operational cost / latent resource risk

     §1 SYMPTOM
       [ ] verbatim trigger   [ ] multiple faults separated & scoped   [ ] verbatim error/stack

     §2 HYPOTHESIS LADDER
       [ ] table incl. the initial/wrong lead   [ ] Outcome column (ruled in/out)

     §3 EVIDENCE
       [ ] constraints lead-in (read-only / scratch / digest)
       [ ] numbered probes: intent + command + Finding
       [ ] MANDATORY live-vs-shipped cross-check (or N/A)
       [ ] MANDATORY class-of-bug count (or N/A)
       [ ] MANDATORY negative control
       [ ] provenance / artefact extraction (if compiled/baked)
       [ ] triggering-input provenance (if data/input-driven)

     §4 ROOT CAUSE
       [ ] numbered causal chain   [ ] two-sides framing (if applic.)   [ ] fix locus named

     §5 FIX APPLIED / RECOMMENDED
       [ ] applied remediation + backup/guard + reversibility
       [ ] FIDELITY of manual fix vs code path (data-integrity check)
       [ ] recommended code fix pointer + recurrence caveat

     §6 VERIFICATION
       [ ] before/after command+result   [ ] dual timestamps   [ ] explicit NOT-verified-end-to-end

     §7 GENERALIZATION
       [ ] recurrence cadence       [ ] cross-incident/historical
       [ ] class-wide latent        [ ] secondary-impact generalization
       [ ] shared systemic weakness [ ] restart-persistence + resource growth
       [ ] systemic signal -> hardening-review recommendation (if Nth bug in subsystem)

     §8 DURABLE MITIGATION
       [ ] code fix  [ ] library fix  [ ] observability  [ ] enabling infra
       [ ] upstream/data hygiene  [ ] resource bounding  [ ] regression test  [ ] subsystem review

     §9 PREVENTION CODE PATTERNS
       [ ] grounding lead-in (verified vs inferred; no nonexistent fields)
       [ ] Fix 1..N best-first: locus + Before/After + character
       [ ] central/entity option WITH explicit caveats
       [ ] "Which to use" ranking
       [ ] defense-in-depth NON-fix (schema/design decision, not fabricated)
       [ ] grounding & provenance map (file:line + artefact + image digest)

     §10 CROSS-REFERENCES
       [ ] external bug report  [ ] retro  [ ] related incident(s)
       [ ] parallel findings    [ ] host docs  [ ] evidence artefacts

     DISCIPLINES (M1–M6)
       [ ] no section silently omitted (absence stated + why)
       [ ] no hallucination; unverified flagged
       [ ] rejected branches recorded (hypotheses / N/A probes / non-fixes)
       [ ] dual timestamps where logs are quoted
       [ ] confidence flags (verified vs source-confirmed)
       [ ] comprehensive (only root cause kept terse in §0)
     ============================================================================ -->
