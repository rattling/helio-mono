# Helionyx Data Management (Milestone 4)

This runbook documents where Helionyx stores data per environment and how to perform backup/restore safely.

## Data Locations (Environment-Aware)

Helionyx uses two primary storage paths (configured via `.env.{env}`):

- `EVENT_STORE_PATH`: append-only event log (JSONL files)
- `PROJECTIONS_DB_PATH`: SQLite database derived from the event log

Typical same-host conventions:

- dev:
  - `EVENT_STORE_PATH=./data/dev/events`
  - `PROJECTIONS_DB_PATH=./data/dev/projections/helionyx.db`
- staging:
  - `EVENT_STORE_PATH=./data/staging/events`
  - `PROJECTIONS_DB_PATH=./data/staging/projections/helionyx.db`
- live:
  - `EVENT_STORE_PATH=/var/lib/helionyx/live/events`
  - `PROJECTIONS_DB_PATH=/var/lib/helionyx/live/projections/helionyx.db`

Backups / rollbacks (defaults):

- Backups: `data/backups/<env>/<timestamp>/`
- Rollbacks (created on restore): `data/rollbacks/<env>/<timestamp>/`

You can override backup root via `BACKUP_ROOT`.

## Backup

Create a backup:

```bash
make backup ENV=dev
```

Expected behavior:

- Outputs a backup id like `20260211T201530Z`.
- Creates `data/backups/dev/<backup_id>/` containing:
  - `events/` (copy of event log)
  - `projections/` (copy of projections directory)
  - `meta.json`, `config.json`
  - `manifest.sha256` (integrity manifest)

Integrity expectations:

- `manifest.sha256` contains sha256 checksums for all files in the backup.
- A restore will fail closed if any file is missing or checksums mismatch.

## Restore

Restore from a backup:

```bash
make restore ENV=dev BACKUP=20260211T201530Z
```

Expected behavior:

1. Validates backup integrity using `manifest.sha256`.
2. Creates a rollback point of the current state under `data/rollbacks/<env>/<timestamp>/`.
3. Replaces the contents of the configured event store and projections directories with the backup contents.

### Live restore safety

`ENV=live` restore requires explicit confirmation:

- Interactive: you must type `yes`.
- Non-interactive: set `CONFIRM_LIVE=YES`.

## Rollback / Recover from a Bad Restore

If a restore produces an unexpected or broken state:

1. Identify the rollback id printed by the restore script.
2. Treat the rollback directory as a backup artifact.
3. Restore again using the rollback as the source by setting `BACKUP_ROOT` to the rollbacks folder.

Example:

```bash
BACKUP_ROOT=./data/rollbacks/dev make restore ENV=dev BACKUP=<rollback_id>
```

## Notes

- The event log is append-only within a running environment. Restore is an operational action that replaces the environment’s stored files; it does not mutate individual events in place.
- Projections can be rebuilt from the event log if needed (`make rebuild`), but backups include projections for faster recovery.

## Dev Backup/Restore Drill (Evidence)

Performed (UTC):

- Start: `2026-02-11T20:12:57Z`
- Backup: `make backup ENV=dev` → `20260211T201257Z`
- Restore: `make restore ENV=dev BACKUP=20260211T201257Z` → rollback `20260211T201301Z`
- Post-restore verification: `pytest tests/test_api_health.py tests/test_api_ingestion.py tests/test_api_query.py` (23 passed)
- End: `2026-02-11T20:13:11Z`
