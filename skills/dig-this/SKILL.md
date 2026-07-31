---
name: dig-this
description: Walk a code-level root-cause investigation on an application host when the bug points at a source-level artefact — a controller/model class in an interpreted-language MVC app, a search-index mapping/setting, or a service config. Locates the live file, reads it where it actually runs (interpreted source needs no decompile), cross-checks live-vs-shipped against the tracking repo, counts the class-of-bug, finds a negative control, and produces an in-conversation synthesis ready for the bug-report skill. Use ONLY when the user explicitly invokes /dig-this (optionally with a short symptom hint). Investigates only — does NOT write a report.
---

<!-- WHY: the four-verb pattern (locate → read where it runs → cross-check →
     quantify) exists because a stack trace names a file but not the *executing*
     file. On hosts running interpreted sources, the "extract the build artefact
     and decompile it" step collapses into "find the live source file and read
     it directly" — which is faster but tempts you to skip the confirmation that
     the on-disk copy is what the daemon is serving. Bytecode caches (e.g. an
     opcode cache with timestamp validation disabled) break that assumption:
     the file can change while behaviour does not, until the worker pool is
     restarted. Hence Step 4 is mandatory and non-obvious. Live-vs-shipped
     (Step 5) exists because out-of-band hot-patching is common on long-lived
     app hosts, and a fix aimed at the repo copy silently misses a hot-patched
     live file. Class-of-bug counting (Step 6) turns "a bug" into "N affected
     rows/docs/call sites", which is what a reader needs to prioritise. The
     negative control (Step 7) is what separates a root cause from a
     coincidence. Boundary is deliberate: investigate-only, read-only, and the
     output is shaped as input for the report-writing skill rather than a file. -->

# dig-this

## Host binding

Fill these in for your environment before using the skill (or let the host
context skill supply them):

| Placeholder | Meaning |
| --- | --- |
| `<app-host>` | Host running the web/app tier (web server + interpreter workers) |
| `<db-host>` | Host running the database, if it is not the app host |
| `<search-host>` | Host/port of the search engine (often `localhost:9200`) |
| `<web-root>` | Filesystem root of the deployed application source |
| `<framework>` | The MVC framework the app is built on (controller/model layout) |
| `<database>` | Database name to query for class-of-bug counts |
| `<index>` | Search index implicated by the symptom |
| `<ops-git-dir>` | Git dir of the repo that tracks deployed config/source |
| `<db-user>` | Database role used for read-only queries |

Drives a **code-level root-cause investigation** on the app host. Locates the
implicated artefact (a controller/model class in the application, a search
index mapping, or a service config), reads it where it actually runs,
cross-checks the live copy against what the repo shipped, and produces findings
shaped for the bug-report skill. Investigation-only — writes no file.

## When to use

- User explicitly invokes `/dig-this`, optionally with a symptom slug
  (e.g. `/dig-this search-missing-hits`).
- The bug points at a source artefact and "look at the logs" is not enough.
  Examples: a stack trace ends in a specific controller/method, a search query
  returns wrong hits (mapping issue), a signing/token defect in an SSO or
  document-signing integration, a config the daemon reads differently from what
  the repo seems to say.

**Do not** invoke for surface issues logs already name (use the diagnostic-doc
skill, `/doc-this`), for saving the report (`/ctx-bug` afterwards), or for
session state (`/ctx-save`).

## Constraints (mandatory)

- **Read-only.** Copy artefacts to `/tmp` and inspect there. Never edit live
  source to "test", never restart the daemon to clear state (it destroys the
  logs the report needs).
- **No fixes.** Localise only; the patch path is separate.
- **No file output.** Findings stay in conversation; chain `/ctx-bug` if wanted.
- **Work from copies in `/tmp`** — never edit under `<web-root>`.

## Procedure

### Step 1 — Pin the symptom

```bash
# application / interpreter errors (paths vary by distro and stack):
sudo tail -200 /var/log/<interpreter>/*error*.log /var/log/<webserver>/*error*.log 2>/dev/null \
  | grep -nE '<error pattern>' | head
# search engine:
curl -fsS 'http://<search-host>/_cat/indices?v' | grep -i <index>
```

Quote one verbatim error line + the first stack frame (file:line) or the search
engine's error body.

### Step 2 — Localise the artefact

From the stack, name the file the fix lands in:

- Application exception → the controller/model class file + method + line.
- Wrong search results → the index `_mapping` / `_settings`, or the
  query-builder source that emits the query.
- Daemon misbehaviour → the config file it actually reads (interpreter ini,
  worker-pool conf, web-server vhost/conf.d, search engine yml).

```bash
# find the live class file under the app root:
sudo find <web-root> -path '*<Namespace path or ClassName>*' 2>/dev/null
```

### Step 3 — Copy the live artefact to /tmp + read it

```bash
sudo cp <web-root>/<path>/<Class>.<ext> /tmp/   # interpreted source: read directly, no decompile
# index mapping/settings (live, authoritative):
curl -fsS "http://<search-host>/<index>/_mapping?pretty"  > /tmp/<index>.mapping.json
curl -fsS "http://<search-host>/<index>/_settings?pretty" > /tmp/<index>.settings.json
# config the daemon reads:
sudo cp /etc/<interpreter>/<worker-pool>.conf /tmp/ 2>/dev/null
```

Read the file (Read tool). Name the **exact file:line** and **symbol** the fix
has to change.

### Step 4 — Confirm the running code path

Interpreted source means the running code is the file on disk — **but** an
opcode/bytecode cache with timestamp validation disabled serves a cached copy:
a live edit is INERT until the worker pool is restarted. Confirm what is
actually live:

```bash
<interpreter> -i 2>/dev/null | grep -E 'opcache.enable|validate_timestamps'
# If validate_timestamps=0, the on-disk file may NOT be what is executing until a restart.
```

State explicitly whether the on-disk artefact is the executing one.

### Step 5 — Live-vs-shipped cross-check (mandatory)

```bash
# live file vs the repo copy tracked by the ops/deploy repo (work-tree /):
git -C / --git-dir=<ops-git-dir> --work-tree=/ show HEAD:<web-root>/<path>/<Class>.<ext> \
  > /tmp/<Class>.shipped 2>/dev/null
diff <(grep -vE '^\s*//|^\s*$' /tmp/<Class>.<ext>) <(grep -vE '^\s*//|^\s*$' /tmp/<Class>.shipped)
```

If they differ: the live file was hot-patched out of band — record both, state
which is authoritative. If they match: the fix ships through the repo. Either
way, state the result.

### Step 6 — Class-of-bug count (mandatory if data-triggered)

Quantify the blast radius — DB rows (if the database lives on another host,
query it read-only via `psql -h <db-host> -U <db-user> <database>`), or indexed
documents matching the bad invariant, or other call sites of the broken method:

```bash
grep -rn '<broken method or pattern>' <web-root> --include='*.<ext>' | wc -l
curl -fsS "http://<search-host>/<index>/_count" -H 'Content-Type: application/json' \
  -d '{"query":{<invariant-violation>}}'
```

If purely a code defect, record `not applicable — purely code defect`.

### Step 7 — Negative control (mandatory)

A sibling input that does **not** fail — same controller with a different
request, same query on a good doc id. Quote failing vs passing side-by-side. If
none reachable, say so and why.

### Step 8 — Synthesise

Short summary in report shape: **Symptom** (verbatim error), **Artefact**
(file:line / index name, and whether it is the executing copy given the opcode
cache), **Root cause** (exact expression + why), **Cross-checks**
(live-vs-shipped diff, class-of-bug count, negative control), **Fix locus**
(repo path + whether a worker-pool restart is required to take effect).

Close with: `Want me to /ctx-bug this with slug <slug>?`

## What this skill does NOT do

- Does not write a file (use `/ctx-bug`, `/doc-this`, or `/ctx-save`).
- Does not edit source, configs, or restart the interpreter/web server/search
  engine.
- Does not modify search indices or DB rows.
- Does not substitute for the host-context skill (`/ctx-infra`) — load that
  first if needed.
