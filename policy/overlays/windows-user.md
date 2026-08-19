# Overlay — Windows, restricted (no admin)

Binds the master for a **non-admin Windows** environment (locked-down
corporate laptop, restricted VM). The defining constraint: no machine-level
authority. That deletes the host-administration half of the policy and keeps
the project-workflow half, which is the portable part anyway.

Shell is **PowerShell** unless noted. Items inferred but not yet validated on
a real restricted host are marked **[unverified]** — confirm in place before
relying on them.

## Placeholder bindings

See `PLACEHOLDERS.md` "windows-user example" column. `$OPS_WORKTREE` =
`%USERPROFILE%` — **never a drive root**; you cannot (and must not) track
what you do not own.

## Scripting runtime

Preferred typed runtime installed per-user (no admin). PowerShell is the
shell fallback; enable local scripts without admin via
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. **[estate-local
caveat: per-user installers and available runtimes vary in a restricted env —
the estate overlay names what is actually installable here.]**

## Shell and dependency safety

- Alias bypass: PowerShell aliases `cp`/`rm`/`mv` to
  `Copy-Item`/`Remove-Item`/`Move-Item`; the hazard is confirmation prompts
  stalling automation, not EOF. For an authorized state change, call the
  cmdlet explicitly with `-Force` (and `-Confirm:$false` where it prompts).
  Verify the side effect, not the pipeline's last exit.
- Language-package isolation: system runtimes may be locked or absent —
  always a per-project virtual environment; a per-user shared install
  (`pip --user` / a per-user tool dir) only for deliberately shared tooling,
  pinned + documented.

## Change management

- `$env:GIT_DIR` / `--git-dir=$OPS_GIT_DIR`, work-tree `%USERPROFILE%`. Run
  git ops from that profile root. Tracks user-owned dotfiles and `AppData`
  configs.
- The "never `git add -A`" rule matters **more** here: a broad work-tree
  under the profile is easy to over-stage. Always explicit `-- <path>`.
- Periodic drift capture = a **user-level scheduled task** (`schtasks
  /create` running as the current user needs no admin) **[unverified in your
  restricted policy — confirm schtasks self-scoped creation is permitted]**.
- Ownership-restore hazard is largely moot (single-user profile), but ACLs
  still are not stored by git; if a tracked file has custom ACLs, reapply
  with `icacls` after a content restore rather than assuming git carried them.

## Definition-of-done proofs

No `systemctl`. Use process/port/HTTP checks: `Get-Process`,
`Test-NetConnection -Port`, `Invoke-WebRequest -Method Head`. A long-running
user process's `[RESULT]` includes its startup output.

## Secrets

DB/credentials via Windows Credential Manager / DPAPI (per-user, no admin)
rather than a `.pgpass`-style file. `$REDACT` =
`-replace '(=|: ).*','$1<redacted>'` over the piped text.

## Restricted-environment gotchas

- **Symlinks need admin or Developer Mode** — for repos that use them,
  `git config core.symlinks false` and expect plain-file placeholders.
- **Long-path support** is an HKLM key you cannot set without admin — use
  `git config core.longpaths true` per-repo as the userland workaround.
- **No hosts-file edits**, no machine env vars — user env vars only
  (`[Environment]::SetEnvironmentVariable(..., 'User')`).
- CRLF: set `git config core.autocrlf` deliberately per project.

## Marked N/A in this environment

System services, a machine-level package manager, `/etc`-style system config
tracking, and machine-wide scheduled jobs are **N/A without admin**. The
master's **[admin]** rules are satisfied within the user profile scope or do
not apply; that is deliberate, not an omission. An admin-Windows deployment
would be a separate overlay, not an edit to this one.
