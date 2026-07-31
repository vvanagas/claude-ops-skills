---
name: doc-this
description: Walk a structured diagnostic on a reported problem (hypothesis ladder, cheapest-distinguishing probes, logs, service/DB/index state) and produce a deep, human+LLM-friendly troubleshooting document under your documentation directory. Use ONLY when the user explicitly invokes /doc-this (optionally with a short symptom hint, e.g. /doc-this search-oom-loop). Save-and-document — it performs the investigation and writes the doc.
---

<!-- WHY (design rationale):
     Three things go wrong with ad-hoc debugging, and this skill is shaped
     against each of them.
     (1) Undisciplined probing. An operator (or an LLM) reaches for whatever
         command comes to mind, collects a pile of output, and never records
         which observation eliminated which cause. The fix is the hypothesis
         ladder: rank the causes FIRST, name the cheapest probe that
         distinguishes each, and stop the moment one is conclusively confirmed.
     (2) Documents written from hypotheses instead of evidence. A write-up that
         asserts a cause nobody actually observed is worse than no write-up — it
         poisons the next incident's pattern-matching. Hence the refuse-guard
         floor (concrete symptom + at least one completed evidence loop + a fix
         or a named next action) and the absolute "never invent evidence" rule.
         Refusing to write is a valid outcome.
     (3) Write-ups optimized only for the author. The output here is read later
         by two different consumers: a human operator under time pressure, and
         an LLM pattern-matching the next similar incident. That is why §0 of
         the template is an LLM preamble — a 30-second briefing pinned above the
         narrative — and why the root-cause section states the mechanism, not
         just the trigger.
     The change/reload discipline (BEGIN/END CHANGE comments, a timestamped
     .bak, an entry in the narrative change log, then the correct reload
     incantation, then a RE-PROBE) exists because a fix that was never verified
     after the process actually picked it up is not a fix — it is a belief.
     Boundaries are deliberate: this is the only skill of its family that RUNS
     the investigation. Siblings named below are load-only, snapshot-only, or
     redact-and-ship-only, and this skill must not absorb their jobs. -->

# doc-this

## Host binding

This skill is host-agnostic. Before first use, bind these placeholders to your
own estate — either by editing this file or by keeping the mapping in your host
primer:

| Placeholder | Meaning |
|---|---|
| `<app-host>` | The host running the application / web tier |
| `<db-host>` | The host running the database (may equal `<app-host>`) |
| `<search-host>` | The host running the search engine, if any |
| `<docker-host>` | The host running containerized services, if any |
| `<web-service>` | Web server service unit name (e.g. the httpd/nginx unit) |
| `<app-service>` | Application worker/pool service unit name |
| `<search-service>` | Search engine service unit name |
| `<db-service>` | Database service unit name |
| `<vhost>` | The virtual host / FQDN the application is served on |
| `<database>` | The application's database name |
| `<db-user>` | The database role used for read-only probes |
| `<app-root>` | Filesystem root of the deployed application source |
| `<log-path>` | Directory holding web/app logs |
| `<doc-dir>` | Where troubleshooting docs are written |
| `<ops-git-dir>` | The local ops git directory that captures `<doc-dir>` |
| `<change-log>` | The narrative change log file |

Runs a structured diagnostic for a problem reported on the host under
investigation and produces an in-depth troubleshooting document under
`<doc-dir>`. Both the procedure AND the resulting document are designed to be
useful for a future human operator and a future LLM.

This is NOT `ctx-bug` (external, redacted bug report from a pre-existing
investigation) and NOT `ctx-save` (internal session snapshot, no redaction, no
investigation) and NOT `ctx-infra` (LOAD-only — primes context, investigates
nothing). `doc-this` is the only skill that performs the investigation itself.

## When to use

- User explicitly invokes `/doc-this` (optionally with a short symptom hint used
  in the filename slug, e.g. `/doc-this search-oom-loop`,
  `/doc-this source-edit-no-effect`, `/doc-this upstream-soap-500`).
- A specific symptom has been described in the conversation OR will be described
  as part of the invocation.

**Do not** invoke without a concrete symptom. If the user invokes `/doc-this`
with no context and no recent symptom in the conversation, ask them once for a
one-line symptom description before proceeding.

## Refuse-guard — check BEFORE writing the doc

The doc is only written when the **investigation floor** is met. Floor:

1. **A concrete symptom** — a specific URL/host/service + a specific observed
   misbehavior (status code, error message, hang, OOM, etc.). Not "something is
   slow."
2. **At least one evidence loop completed** — you ran probes (see §B), read
   logs, or inspected service/DB/index state, and have observations to record.
   Not just hypotheses.
3. **Either a fix has been applied OR a clear next action is identified.**
   "Cause unknown, recommend further work" is acceptable if §1 and §2 are met —
   but say so plainly in the doc.

If the floor is not met, **refuse to write** and tell the user which item is
missing. Do not invent evidence.

## Procedure when invoked

Treat this as a rigid checklist. Track each step with TodoWrite if the
investigation spans more than a couple of probes.

### Step 1 — Read the room

If a context-loading skill (`ctx-infra` or equivalent) has not been invoked this
session, read your host primer yourself (do not output it to the user — just
load it into your context). This gives you the topology, addresses, conventions,
the command cheat-sheet, and the known failure modes. For a cross-host problem,
also read the primer of the other host involved.

### Step 2 — Pin the symptom

Restate the symptom back to the user in one sentence and list the explicit
unknowns (URL? vhost? service? expected vs observed code? time of last working
state? does it correlate with a deploy/edit/restart?). Get answers before
probing further if any unknown is load-bearing.

### Step 3 — Hypothesis ladder

Write a short ranked list of possible causes (3–5 items, most likely first). For
each, name **the cheapest probe that distinguishes it** from the others. Output
this ladder to the user before starting probes so they can redirect.

### Step 4 — Probe

Walk the ladder top-to-bottom. After each probe, record:
- the exact command run,
- the relevant excerpt of output (not the whole dump),
- which hypothesis it confirmed or eliminated.

Use the commands in your host primer's cheat-sheet and failure-mode table —
they are tuned to your stack. Do not invent novel diagnostic commands unless the
standard ones fail. Two traps that recur on almost every stack and are worth
keeping in mind while probing:

- **A TLS-only vhost lies to a plain localhost fetch.** If the application vhost
  listens on 443 only, `curl http://127.0.0.1/...` silently hits the *default*
  vhost and returns a misleading result. Always probe with
  `--resolve <vhost>:443:127.0.0.1`.
- **An opcode/bytecode cache can make your edit inert.** Where the runtime caches
  compiled source and does not re-stat files (e.g. timestamp validation disabled
  for performance), a source change you made earlier may not be live at all —
  which can itself be the symptom, or can mask one.

### Step 5 — Form the diagnosis

Once one hypothesis is conclusively confirmed, stop probing. State the root cause
in one sentence and the mechanism in one paragraph.

### Step 6 — Apply the fix (if the user asked for it)

If the user is debugging in real time, propose the fix and apply it after
confirmation. Wrap config edits with `# BEGIN CHANGE YYYY-MM-DD — why` /
`# END CHANGE YYYY-MM-DD` (operator convention), keep a `.bak.<timestamp>`, and
log the change in `<change-log>`. Then reload with the correct incantation for
the thing you changed — a config file on disk is not a running config:

| Change made | Correct action |
|---|---|
| Web server vhost / `.conf` | Run the web server's config test, then reload the service — never restart blind on a config you have not validated |
| Application source under `<app-root>` | **Invalidate the opcode/bytecode cache** (reset call via a dropped script, or restart the worker pool) — with timestamp validation disabled, a plain reload will NOT pick the edit up |
| Application worker pool config | Reload `<app-service>` |
| Database server config (`postgresql.conf` or equivalent) | On `<db-host>`: reload config in-session for SIGHUP-class params, or restart `<db-service>` for the rest. If the file is service-user-owned, **commit it to ops-git manually** — editor hooks usually do not cover it |
| Database auth/ACL config (`pg_hba.conf` or equivalent) | On `<db-host>`: reload config — no restart needed |
| Search engine config / heap | Restart `<search-service>` (typically no live reload). Check free memory first if the box is memory-tight |

Verify with a **re-probe**. After a fix to cached application source, re-verify
only AFTER invalidating the cache — an un-flushed edit will make a working fix
look broken. Where the symptom is intermittent (upstream jitter, connection-pool
churn), re-probe several times rather than once; a single green probe does not
close an intermittent fault.

### Step 7 — Write the doc

Slug = the hint passed to `/doc-this` (or a derived 2–4 word slug).
Filename = `<doc-dir>/troubleshooting_<slug>.md` for general-purpose
investigations, OR `<doc-dir>/incident_YYYY-MM-DD_<slug>.md` if it is a one-off
incident write-up.

Use the template in §A. Write it directly — if your ops-git hook covers
`<doc-dir>`, the file lands in version control automatically; if not, commit it
explicitly with a pathspec. The local ops git store is the only store and
nothing pushes anywhere.

### Step 8 — Hand off

Tell the user the filename, give a one-paragraph summary of what was found and
what was fixed, and stop. Do not propose unrelated next steps.

## §A — Document template

The output document follows this shape. Sections marked OPTIONAL can be omitted
if not applicable; everything else must be present.

```markdown
# Troubleshooting — <one-line title>

> **Type:** Troubleshooting reference (Diátaxis: How-to)
> **Date:** YYYY-MM-DD
> **Scope:** <which host(s)/service(s)>
> **Status:** <Resolved | Mitigated | Open — root cause unknown>
> **Triggered by:** <user-facing symptom, one line>

---

## 0. LLM Preamble — pin these facts before reading

<3–5 bullets that a future LLM can use as a 30-second briefing. The mechanism,
the smoking-gun signal, the fix in one sentence. Optimized for skim, not depth.>

---

## 1. Symptom (what was reported)

<Verbatim or near-verbatim user report. Include the URL/vhost, the error code or
log line, the time window, the source where relevant.>

## 2. Hypothesis ladder

<The ranked list from Step 3 above, with the probe used to test each.>

## 3. Evidence collected

<Per-probe output. Command on one line, then a small excerpt of the result, then
one line interpreting it. No raw dumps; trim to what mattered.>

## 4. Root cause

<One sentence statement of the cause. Then one paragraph explaining the mechanism
— why this configuration produces this symptom. This is the section a future LLM
will read first when pattern-matching the next similar incident.>

## 5. Fix applied (or recommended)

<Exact change made. If a config file was edited, show the diff and the reload
command used. If the fix is not yet applied, mark the section "RECOMMENDED" and
describe what to do.>

## 6. Verification

<The re-probe(s) confirming the fix. Same command shape as §3. For a fix to
cached application source, note explicitly that the opcode cache was invalidated
before re-probing.>

## 7. Generalization — when else does this fire?  (OPTIONAL)

<If this failure pattern can recur elsewhere in the stack, list the other places.
Typical examples: an "edit had no effect" trap caused by a disabled-timestamp
opcode cache fires for EVERY source file under `<app-root>`, not just the one you
touched; a heap-larger-than-available-RAM OOM pattern recurs for any JVM-style
service tuned past a safe fraction of RAM on a memory-tight box.>

## 8. Durable mitigation  (OPTIONAL)

<Config changes that would prevent the whole class of failure. Not applied;
recorded for a future session.>

## 9. Cross-references

<Other `<doc-dir>` files that touch the same component. At minimum, link to the
host primer and any other troubleshooting_*.md / incident_*.md that covers the
same family of failures.>
```

## §B — Pre-loaded probe vocabulary

This is a **template**, not a host inventory. Fill the placeholders from your own
host primer's cheat-sheet — that primer, not this file, is the source of truth
for real service names, addresses, database names, and log paths. Drop the
categories that do not exist on your stack (a host with no search tier has no
index probes) and keep the ordering: cheap and local first, remote and expensive
last.

```bash
# Service state — adapt to your init system / container runtime
systemctl status <web-service> <app-service> <search-service>

# Database connectivity + size. Prefer peer/socket auth over TCP+password.
ssh <db-host> sudo -u <db-user> psql -d <database> -c '\l+'
ssh <db-host> sudo -u <db-user> psql -d <database> -c '\dt+'

# Search engine indices + live heap usage
curl -s 'http://<search-host>:9200/_cat/indices?v&s=store.size:desc'
curl -s 'http://<search-host>:9200/_nodes/stats/jvm?pretty' | grep heap_used_percent

# Web server config test + a fetch of the real vhost
# (--resolve is mandatory for a TLS-only vhost: plain http hits the default vhost)
apachectl configtest ; apachectl -S      # or: nginx -t ; nginx -T
curl -sk --resolve <vhost>:443:127.0.0.1 \
  https://<vhost>/ -o /dev/null -w "%{http_code}\n"

# Application worker pool + slow-request log
systemctl status <app-service> | grep -i tasks
tail -n 40 <log-path>/app-slow.log

# Slowest endpoints from the access log (request time is the last field here —
# check your own log format before trusting the column indices)
awk '{print $7,$9,$NF}' <log-path>/<vhost>-access.log | head

# Memory pressure + OOM-killer history
free -h ; ps aux --sort=-%mem | head -15
dmesg | grep -i "oom\|killed process"

# What is actually containerized (vs what you assume is)
docker ps
```

Note on credentials: a probe over plain TCP to the database
(`psql -h <db-host> -U <db-user> -d <database>`) needs a password — prefer
peer/socket auth on the database host, which needs none. Never put a password on
the command line, in a prompt, or in the written doc; see your platform's
secrets rule.

## §C — Example output

Keep one prior write-up in `<doc-dir>` as the shape template — same preamble
style, same section ordering, similar level of density. Use the incident shape
(`incident_YYYY-MM-DD_<slug>.md`) for one-off events, and
`troubleshooting_<slug>.md` for general-purpose investigations. Do not copy the
example's content; copy its structure.

## What this skill does NOT do

- Does not load infra context preemptively (that's `/ctx-infra`).
- Does not capture an internal session snapshot (that's `/ctx-save`).
- Does not redact secrets (that's `/ctx-bug` for outgoing reports). Docs written
  here are internal — but per the platform rule, never put a credential, key, or
  secret config value into the doc regardless.
- Does not write outside `<doc-dir>`. The doc lives there and is captured by the
  `<ops-git-dir>` ops-git store.
- Does not push to any remote. Local git only.
- Does not invent evidence to satisfy the refuse-guard. If the floor is not met,
  the skill refuses.
