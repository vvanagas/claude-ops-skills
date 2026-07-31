---
name: ctx-bug
description: Write a redacted, externally-shippable bug report from an investigation already done this session on the current host. Use ONLY when the user explicitly invokes /ctx-bug (optionally with a short bug description, e.g. `/ctx-bug oom-loop`). Save-only — it does NOT run the investigation.
---

<!-- WHY (design rationale): this skill exists because a report that LEAVES the
     machine has different rules from every other note an operator writes. Four
     constraints drive the whole design and should survive any edit:
     (1) It is the *external* sibling of an internal save skill: internal notes
         may carry secrets verbatim, this one may not — so the two are separate
         skills, never chained.
     (2) Redaction is a deterministic regex pass run IN MEMORY before the first
         byte is written, not an LLM judgement call and not a write-then-clean
         step: the output directory is tracked by a local ops git repo, and an
         unscrubbed draft committed once is leaked forever.
     (3) A refuse-guard floor keeps the credibility of this format away from
         bare complaints — a report is only worth an external team's time if it
         carries observed errors, captured infrastructure state, and real log
         lines.
     (4) Fixed section set and fixed ordering, so a receiving maintainer learns
         the shape once; a section with nothing in it says so explicitly rather
         than disappearing.
     Secondary decisions: raw logs are never attached (only inline, scrubbed
     excerpts — no attached file means no separate log-sanitising path to get
     wrong); the redaction table is deliberately BROAD (extend it when a new
     access-granting token shows up, never narrow it); Section 8 carries an
     explicit depth floor because a report can satisfy the refuse-guard and
     still be too shallow to act on. It remains save-only: it formats findings,
     it never investigates. -->

# ctx-bug

Writes a **bug report** for an **external technical team**, from an
investigation that already happened **in this session**. Save-only: it
captures and formats findings — it never performs the investigation.

## Host binding

This skill is written with placeholders. Fill them in for your environment
before use (in this file, or in a per-host copy):

- `<app-host>`, `<db-host>`, `<docker-host>` — the machine roles you run on;
  `HOST` in the procedure resolves to whichever one the report is written on.
- `<vhost>` — the public virtual host / site name whose logs you quote.
- `<database>` — the database name(s) in play.
- `<db-user>` — the database login(s) appearing in evidence.
- `<version>` — package/build versions of the services involved.
- `<reports-dir>` — where reports are written (this file assumes
  `~/bug_reports`; substitute your own and keep it inside the tracked tree).
- `<ops-git-repo>` — the **local-only** ops git repository that tracks host
  config and notes. The skill assumes one exists, that `<reports-dir>` sits
  inside its work-tree, and that writes there auto-commit. If your ops repo
  lives elsewhere, set its path here; if you have no such repo, the
  redaction-before-first-write rule matters *more*, not less — a plain file
  can still be copied, backed up, or synced before anyone re-reads it.

Sibling-skill names (`ctx-save`, `ctx-infra`, `doc-this`, `dig-this`) are the
roles this skill draws boundaries against; rename them to match your own set,
but keep the boundaries.

## Boundaries

This is NOT `ctx-save`. `ctx-save` is internal, for the operator, and writes
secrets verbatim. `ctx-bug` leaves the host and goes to an outside party, so
it **must scrub every value that grants access** before the file is written.
The two are unrelated tools — do not chain them, do not assume one ran. It is
also distinct from `ctx-infra` (LOAD-only context) and `doc-this` (which writes
*internal*, unredacted troubleshooting docs into the operator's own docs tree).

## When to use

- User explicitly invokes `/ctx-bug` (optionally with a short bug
  description argument).
- An investigation with real evidence happened this session and a report
  is going to an external team.

**Do not** invoke for internal session state (that is `/ctx-save`), and do
not run an investigation just to satisfy this skill.

<!-- WHY: explicit pointer to the investigation companion. ctx-bug is save-only
     and refuses below the floor; the investigation skill is the right tool to
     *reach* a code-level root cause first. Pair, do not chain — the user
     invokes both explicitly. If your set has no dig-this equivalent, repoint
     this line at whatever investigation walker you do have. -->
If the investigation has not reached a code-level root cause yet (a database
function/view, an application class, a baked config value), invoke `/dig-this`
first to extract and inspect the artefact, then return here to save the report.

## Refuse-guard — check BEFORE writing anything

The skill **refuses** and tells the user to investigate first unless the
**floor** is met. The floor is checkable without the user:

1. **Symptoms with real observed errors** — concrete error text, status
   codes, or observed misbehavior. Not "it's broken."
2. **Captured infrastructure state / configuration** — the actual services
   in question (e.g. the web server, the application runtime, the database,
   the search engine) and their relevant config, gathered this session.
3. **Relevant log excerpts** — real log lines seen this session, to be
   quoted inline (see Logs below).

Root cause need **not** be established — "unknown; here is what we ruled
out, with evidence" is a legitimate, shippable external report.
Reproduction need **not** exist — "not yet reproduced" is shippable.

Below the floor → **refuse**: state which of the three is missing and stop.
A bare complaint must not receive the credibility of this format.

## Redaction — mandatory, deterministic, in-memory

**What is scrubbed:** any value that grants access — passwords (e.g. a
database password in a framework config file), bearer tokens, API keys, bare
`Basic <token>` proxy strings, inline DB-URL credentials, PEM private keys
(e.g. SOAP/TLS signing keys on disk, or a hardcoded private key embedded in a
controller), and backup-encryption passphrases.

**What is preserved:** internal IPs, hostnames, DB usernames, package/build
versions, file paths, config structure. Stripping these would leave abstract
prose, not an actionable bug report.

**How:** a deterministic regex pass over the **entire final report body**.
Zero LLM judgement, zero extra tokens. Minimum pattern set (extend if a
clearly-access-granting token appears, never narrow):

| Pattern (regex, case-insensitive) | Replace with |
|---|---|
| `Authorization:\s*Basic\s+\S+` | `Authorization: Basic ‹redacted›` |
| `Authorization:\s*Bearer\s+\S+` | `Authorization: Bearer ‹redacted›` |
| `(password|passwd|pwd)\s*[=:]\s*\S+` | `\1=‹redacted›` |
| `jdbc:[a-z]+://[^ \n]*:[^@ \n]+@` | `jdbc:…://…:‹redacted›@` |
| `://[^/:@\s]+:[^@\s]+@` (creds in any URL) | `://‹redacted›@` |
| `\bBasic\s+[A-Za-z0-9+/=]{12,}\b` (bare Basic-auth token) | `Basic ‹redacted›` |
| `(api[_-]?key|secret|token)\s*[=:]\s*\S+` | `\1=‹redacted›` |
| `-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z0-9 ]*PRIVATE KEY-----` (PEM / OPENSSH private keys, any type) | `-----BEGIN PRIVATE KEY----- ‹redacted› -----END PRIVATE KEY-----` |
| `AWS_ACCESS_KEY_ID\s*[=:]\s*\S+` and `AWS_SECRET_ACCESS_KEY\s*[=:]\s*\S+` and `\bAKIA[0-9A-Z]{16}\b` | `AWS_…=‹redacted›` / `‹redacted›` |
| `\bgh[posru]_[A-Za-z0-9]{20,}\b` and `\bgithub_pat_[A-Za-z0-9_]{20,}\b` (GitHub tokens) | `‹redacted-gh-token›` |
| `\bsk-[A-Za-z0-9_-]{20,}\b` (OpenAI-style secret keys, incl. `sk-proj-`) | `‹redacted-api-key›` |
| `\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b` (JWT: header.payload.sig) | `‹redacted-jwt›` |
| `(Set-Cookie\|Cookie):\s*\S.*` (cookie headers, value to end of line) | `\1: ‹redacted›` |
| `(client-key-data\|client-certificate-data\|token)\s*:\s*\S+` (kubeconfig / `.kube/config` material) | `\1: ‹redacted›` |

**When:** redaction happens **in memory, before the first write**. The only
bytes ever written to disk are already scrubbed. No raw draft, no
write-then-sanitize, no unredacted twin. `<reports-dir>` auto-commits to the
ops git repo (`<ops-git-repo>`); an unscrubbed draft would leak into git
history permanently.

**Accepted residual risk:** the deterministic pass catches known patterns
only. A credential in an unanticipated format inside an inline log excerpt
can slip through, and there is no human-reviewed twin. This is the price of
the no-LLM constraint. **Mitigation (mandatory):** at the end of the run,
print the list of patterns that matched and this exact line to the operator:
`Review inline log excerpts for non-standard credentials before sending.`

## Logs

**Never attach raw log files.** Quote only the **relevant log lines inline**
in the report (in Symptoms / Root cause), at the density of a good incident
write-up: the two or three lines that carry the evidence, with enough
surrounding context to be readable, and nothing else. The inline excerpts are
scrubbed by the same regex pass as all body text. There is no log parser
because there is no attached log file. (Typical sources to quote from: the web
server's `<vhost>` access/error logs, the application runtime's slow/error log,
the datastore or search-engine logs, and `dmesg`/`journalctl` for kernel-level
events such as OOM-killer lines.)

## Procedure

### 1. Resolve filename parts (run this)

```bash
DIR=<reports-dir>; mkdir -p "$DIR"
HOST=$(hostname -s)
DATE=$(date +%Y%m%d-%H%M%S)
SID="${CLAUDE_CODE_SESSION_ID:-}"
if [ -z "$SID" ]; then
  SID=$(ls -t "$HOME"/.claude/projects/*/*.jsonl 2>/dev/null \
        | head -1 | xargs -r basename -s .jsonl)
fi
SEED=$(printf '%s' "${SID:-none}" | tr -dc 'a-z0-9' | tail -c 6)
echo "DIR=$DIR HOST=$HOST DATE=$DATE SEED=${SEED:-none}"
```

`SEED` = last 6 alphanumerics of the session id, used only to make the
filename unique — it carries no resume semantics (this is an external doc).
`HOST` resolves to the short hostname of the machine the report is written on.

### 2. Bug short description

If the user passed an argument to `/ctx-bug`, slugify it (lowercase,
kebab, alnum+dash) → `SLUG`. If none, generate a 3–6 word kebab-case
summary of the bug → `SLUG`.

### 3. Filename

```
<reports-dir>/<HOST>-<DATE>-<SEED>-<SLUG>.md
```

### 4. Build the report in memory, then scrub, then write

Assemble all sections, run the deterministic regex pass over the **whole
text**, and only then write the file. Start with the ops-git WHY header
(an HTML comment — invisible in rendered markdown, satisfies the
change-management convention for tracked files). Do **not** include a
RESUME DISCIPLINE header — this document leaves the building.

```markdown
<!-- WHY: external bug report generated via /ctx-bug. Auto-committed via the
     ops-git hook. Access-secrets scrubbed deterministically. <ISO datetime> -->

# Bug Report — <human title>

| | |
|---|---|
| Host | <HOST> |
| Generated | <ISO datetime> |
| Status | <open / root-caused / fix-proposed> |
```

Then the **8 mandatory sections, always in this order**. A section with no
content states the absence explicitly and *why* — never omit it. The skill
may **add** bug-specific sections (e.g. Timeline, Related issues) but never
drop one of these 8:

1. **Summary** — one paragraph: what breaks, severity, current status.
   Lets the external team triage without reading further.
2. **Symptoms & impact** — observed behavior, exact errors/status codes,
   and who/what is affected (blast radius).
3. **Reproduction** — exact steps/commands/inputs and preconditions. If
   not reproduced, say so explicitly ("not yet reproduced — <why>").
4. **Affected infrastructure & configuration** — services/daemons in
   question, package/build version (e.g. `<service> <version>`), relevant
   config. Access-secrets are scrubbed; IPs/hostnames/usernames/paths/
   versions are kept.
5. **Root cause** — the call/event/flow chain to the failing path. If
   unknown, state "unknown" and list what was ruled out, with evidence.
6. **Possible fixes** — format strictly as follows so an external
   maintainer can act without re-deriving context:
   - One preamble line scoping all fixes (e.g. "All fixes require a code
     change in `<repo/image>`.").
   - Then one `### Fix N — <short title> (<impact/risk annotation>)`
     subsection per fix, ranked best-first. Each subsection contains, in
     order: (a) prose naming the **exact symbol/file/line** of the current
     behavior and **why it is wrong**; (b) a fenced code block showing the
     concrete change — prefer a `// Before` / `// After` contrast in the
     project's own language; (c) a closing sentence stating the fix's
     character ("minimum necessary change", "architecturally cleanest",
     trade-off).
   - Code blocks here are illustrative source, not secrets — the redaction
     pass does not alter them; never put a real credential in an example.
   - If genuinely none: a single line `**No code fix identified** — <why,
     with what was considered and rejected>`. Do not fabricate fixes to
     fill the section.
7. **Possible workarounds** — non-code, operational mitigations the
   receiving team or operator can apply *now*, before the code fix lands.
   Format strictly as follows:
   - One preamble line stating these are stopgaps that do not resolve the
     defect.
   - Then one `### Workaround N — <short title> (<effect annotation, e.g.
     "immediate" / "prevents recurrence" / "data-side">)` subsection per
     workaround, ranked by usefulness/safety. Each contains, in order:
     (a) prose: what it does and when to reach for it; (b) a fenced block
     with the **exact config/command change** (real file names, real
     directives); (c) the **exact activate/apply command** in its own
     fenced block (`apachectl configtest && systemctl reload <web-server>`,
     a bytecode/opcode cache flush, a database config reload such as
     `SELECT pg_reload_conf();`, `systemctl restart <service>`, etc.);
     (d) a closing line stating what it preserves and its
     limitation/blast-radius.
   - Config/command blocks are illustrative ops content, not secrets — the
     redaction pass does not alter them; never embed a real credential.
   - If genuinely none: a single line `**No workaround identified** —
     <why>`. Do not invent a stopgap to fill the section.
8. **Tooling & approach used** — the investigation narrative, detailed
   enough that the external team can trust the conclusion and re-run the
   path. Format strictly as follows:
   - One lead-in line stating scope/constraints (e.g. "conducted read-only
     from `<host>`; no service restarted, no data modified").
   - Then ordered `### Step N — <short title>` subsections in the sequence
     the investigation actually happened. Each contains, in order:
     (a) prose: what was done and *why* (what hypothesis it tested);
     (b) the **exact command(s)** run, in a fenced block; (c) a **Finding:**
     line stating what it proved, ruled in, or ruled out — including dead
     ends and retracted theories (they show rigor and save the reader
     repeating them).
   - **Command blocks here are REAL executed commands, not illustrative —
     they pass through the redaction scrub like all body text.** A probe
     command that carried an access token (e.g. `-H "Authorization: Basic
     <token>"`, or a `psql "postgresql://user:pw@host/db"` connection
     string) MUST appear scrubbed. This is the one place command examples
     are NOT exempt; section 6/7 code is illustrative and exempt, section 8
     commands are not.
   <!-- WHY: depth floor for Section 8. Without these, a report that meets
        the refuse-guard floor (symptoms + infra + logs) can still be too
        shallow to act on — depth otherwise ends up sample-dependent, present
        only when the investigator happened to work that way. Each item has an
        explicit "not applicable" escape so the skill stays save-only rather
        than mandating investigation steps that may not fit every bug. -->
   - **Depth requirements (each must appear as a Step or be explicitly
     marked `not applicable — <reason>`):**
     - **Live-vs-shipped cross-check** — when a SQL function/view, migration,
       or baked config is implicated, one Step must show the **live**
       definition matches the **shipped** one (e.g. `pg_get_functiondef(...)`
       vs. the migration file; the live web-server conf or interpreter setting
       vs. the version checked into `<ops-git-repo>`). Rules out an
       out-of-band hot-patch and locates where the fix has to land.
     - **Class-of-bug count** — when a bad data row or config value triggers
       the defect, one Step must quantify how many similar rows/values exist
       DB-wide (or repo-wide). One row vs. thousands changes both workaround
       choice and fix urgency.
     - **Negative control** — every report must include one Step showing the
       failure does **not** occur under a contrast condition (a sibling row
       that processes cleanly, a sibling endpoint that returns 200, a sibling
       vhost/host that is unaffected). A failure without a contrast is a
       coincidence, not a localisation.
   - Never omit this section — an external team will not act on a
     conclusion whose derivation it cannot see.

### 5. Confirm

Print the written path. Print the list of redaction patterns that matched.
Print verbatim: `Review inline log excerpts for non-standard credentials
before sending.`

## Notes

- New file every invocation (never overwrite/append).
- Save-only skill. It formats and ships; it does not investigate.
- Lives under `<reports-dir>` → inside the ops-git work-tree → auto-commits
  to `<ops-git-repo>` via the hook; the WHY header satisfies the in-file
  convention. No narrative change-log entry (that logs system changes, not
  report generation).
- Unrelated to `ctx-save`. Do not assume `ctx-save` ran; do not chain them.
