---
okf_version: "0.2"
---

# Pending

Open work for `claude-ops-skills`. An
[OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
bundle: one file per item, `type: Pending`, with `state`/`trigger`/`owner` as
producer extensions. Numbers are creation order and permanent. Closing an item
= set `state: done` and name the closing commit; never delete the file.

* [0001 — Decide the drift policy vs the live hosts](0001-drift-policy.md) — copies are one-way with no sync mechanism; decide a direction of truth before the first real divergence.
* [0002 — Self-review the generalized text for lost meaning](0002-generalization-review.md) — five agents each flagged places where removing specifics cost teaching value; read them end-to-end once with fresh eyes.
* [0003 — Adapt mirror-check.sh to the policy master/overlays](0003-policy-mirror-check.md) — policy/ has no mechanical drift check yet; reuse the coding-rules mirror/projection scripts before the next master or overlay edit.
