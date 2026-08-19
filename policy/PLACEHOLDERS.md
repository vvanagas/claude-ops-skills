# Placeholders

The master and overlays refer to these by name; each overlay (and the private
estate overlay) assigns concrete values. Keeping them symbolic is what lets
one master project onto many environments and keeps estate paths out of the
public tree.

| Placeholder | Meaning | posix example | windows-user example |
|---|---|---|---|
| `$OPS_GIT_DIR` | local-only config-tracking git dir | `~/.ops-vcs.git` | `%USERPROFILE%\.ops-vcs.git` |
| `$OPS_WORKTREE` | its work-tree (broadest tree you administer) | `/` (admin) | `%USERPROFILE%` (restricted) |
| `$NARRATIVE_LOG` | change-story log (why/how/verified) | `~/changed_in_details.md` | `%USERPROFILE%\changed_in_details.md` |
| `$CODE_HOME` | root for one-dir-per-project work | `~/code` | `%USERPROFILE%\code` |
| `$VENVS_HOME` | dedicated tool virtual-environments dir | `~/.local/share/venvs` | `%LOCALAPPDATA%\venvs` |
| `$SCRATCH` | ephemeral scratch dir (never committed) | `/tmp` (or the session scratch dir) | `%TEMP%` |
| `$PKG_USER` | per-user package installer | `--user` / project venv | per-user installer (see overlay note) |
| `$REDACT` | names-only redaction idiom for configs | `sed -E 's/(=|: ).*/\1<redacted>/'` | `-replace '(=|: ).*','$1<redacted>'` |

Values above are **illustrative defaults**, not an estate's real layout. A
private estate overlay may override any of them and adds its own bindings
(host names, service commands, mail transport, watchlist location) that never
appear in this repo.
