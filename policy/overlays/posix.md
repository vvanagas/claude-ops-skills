# Overlay — POSIX (Linux/Unix, host-admin)

Binds the master's mechanics for a POSIX host where the agent administers the
system. A private estate overlay layers on top with real paths/hosts/tools.

## Placeholder bindings

See `PLACEHOLDERS.md` "posix example" column. `$OPS_WORKTREE` = `/` (full
admin); `$SCRATCH` = `/tmp` or the session scratch dir.

## Scripting runtime

Preferred typed runtime: whatever the estate standardizes on (e.g. a
JS/TS runtime with a built-in test runner, or Python with pytest). Shell is
POSIX `sh`/`bash` — the fallback for bootstrapping and pipe chains only.

## Shell and dependency safety

- Alias bypass: prefix with `command` (`command cp`, `command rm`,
  `command mv`) and pass explicit flags; the root shell may alias these to
  interactive mode, which can consume EOF and silently skip a state change.
- Language-package isolation: never install into an OS/package-manager-owned
  runtime (e.g. an RPM/DEB-managed Python). Use a project `.venv` or a tool
  venv under `$VENVS_HOME`; `pip --user` only for deliberately shared root
  tooling, pinned + documented.

## Change management

- `G="git --git-dir=$OPS_GIT_DIR --work-tree=/"`; run git ops from `cd /`.
- Auto-commit via editor/tool hooks; periodic drift capture via a cron job
  under `/etc/cron.d/` (roots listed inside it). Outside those roots:
  `cd / && $G add -f -- <path> && $G commit -m "..."`.
- Ownership restore: `$G show HEAD:path > file` then `chown <owner> file` —
  never `git checkout` a service-user-owned tracked file.

## Definition-of-done proofs

Service/health checks use the platform's service manager and network tools:
`systemctl is-active <svc>`, `curl -I <url>`, a port probe
(`</dev/tcp/host/port`). A restart's `[RESULT]` includes a healthy-startup
log snippet (`journalctl`/service log).

## Secrets redaction idiom

`$REDACT` = `sed -E 's/(=|: ).*/\1<redacted>/'`. DB access: peer auth
(`sudo -u <dbuser> psql` locally / over ssh) or a `chmod 600` credentials
file — never a literal on the line.

## Marked N/A

None — POSIX-admin satisfies every master rule directly.
