# Architecture Decision Record

## Title
Milestone 4: Backup/Restore Artifact Format and Semantics

## Status
Accepted

## Context
Milestone 4 requires environment-aware backup/restore with integrity validation, rollback semantics, and explicit confirmation for live restores.

Helionyx has three key kinds of durable state:
- Append-only event log (source of truth)
- Projections (SQLite DB derived from the event log)
- Non-secret configuration needed to interpret the backup and restore safely

We need an explicit, scriptable contract so that:
- `scripts/backup.sh` output is predictable and verifiable
- `scripts/restore.sh` can fail closed on invalid inputs
- docs and QA drills can be written against stable behavior

## Decision
Backups are stored as a timestamped directory tree under an environment-scoped backup root.

### Naming + location
- Backup root default: `data/backups/<env>/`
- Backup identifier: `<timestamp>` in UTC, format `YYYYmmddTHHMMSSZ` (example: `20260211T201530Z`)
- Backup directory: `data/backups/<env>/<timestamp>/`

### Backup directory layout
Each backup directory contains:
- `meta.json`
  - `env`
  - `backup_id` (timestamp string)
  - `created_at_utc`
  - `git_commit` (best-effort; may be null)
- `config.json` (non-secret, restore-relevant settings)
  - `ENV`
  - `EVENT_STORE_PATH`
  - `PROJECTIONS_DB_PATH`
  - `API_HOST`, `API_PORT`
  - `LOG_LEVEL`
- `events/` (copy of the event store directory)
- `projections/` (copy of the projections directory containing the SQLite DB)
- `manifest.sha256` (integrity manifest)

### Inclusion / exclusion
Included:
- All files under `EVENT_STORE_PATH`
- All files under the directory containing `PROJECTIONS_DB_PATH`
- Non-secret config snapshot (`config.json`)

Excluded:
- Any `.env*` files
- Any secret values (OpenAI keys, Telegram tokens, etc.)

### Integrity validation
`manifest.sha256` is generated for all files in the backup directory (relative paths), excluding the manifest file itself.

Restore must validate integrity before applying changes by running `sha256sum -c manifest.sha256` and failing closed if any file is missing or mismatched.

### Restore semantics
Restore is environment-targeted:
- `make restore ENV=<env> BACKUP=<timestamp>` restores from `data/backups/<env>/<timestamp>/` into the target environment’s configured paths.

Before applying restore:
- Create a rollback point of the current state at `data/rollbacks/<env>/<timestamp>/` using the same layout + integrity manifest.

Applying restore:
- Replace the contents of the target event store directory with the backup’s `events/` contents.
- Replace the contents of the target projections directory with the backup’s `projections/` contents.

### Live restore confirmation
Restoring `ENV=live` requires explicit confirmation.

- If running interactively (TTY): prompt and require the user to type `yes`.
- If non-interactive: require environment variable `CONFIRM_LIVE=YES`.

## Rationale
- Directory-based artifacts are easy to inspect and recover from manually.
- A sha256 manifest is portable, deterministic, and fail-closed.
- Rollback points provide safety against a bad backup or operator error.
- Live confirmation reduces accidental production destruction.

## Alternatives Considered
- Tarball-based artifacts (`.tar.gz`) with embedded manifest
  - Rejected for now: harder to inspect and do partial recovery without tooling.
- Backing up only the event log and always rebuilding projections
  - Rejected: projections restore is faster for practical recovery; rebuilding can remain a fallback.
- Adding encryption-at-rest in M4 scripts
  - Deferred to a separate decision ADR to avoid blocking core durability deliverables.

## Consequences
- Restore is an operational action that replaces environment state; it is not an event-log append.
- Projections in the backup are treated as a convenience; rebuilding projections remains viable if needed.
- Operators must ensure backup directories are protected by filesystem permissions.
