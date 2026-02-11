#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${ENV:-dev}"
BACKUP_ID="${BACKUP:-}"

if [[ -z "$BACKUP_ID" ]]; then
  echo "Error: BACKUP is required (timestamp id)." >&2
  echo "Example: make restore ENV=${ENV_NAME} BACKUP=20260211T201530Z" >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Error: Python venv not found at .venv/. Run 'make install' first." >&2
  exit 1
fi

umask 077

eval "$(ENV="$ENV_NAME" "$PYTHON_BIN" - <<'PY'
from shared.common.config import Config
import shlex

c = Config.from_env()
print(f"EVENT_STORE_PATH={shlex.quote(c.EVENT_STORE_PATH)}")
print(f"PROJECTIONS_DB_PATH={shlex.quote(c.PROJECTIONS_DB_PATH)}")
print(f"ENV_EFFECTIVE={shlex.quote(c.ENV)}")
PY
)"

BACKUP_ROOT_DEFAULT="${ROOT_DIR}/data/backups/${ENV_EFFECTIVE}"
BACKUP_ROOT="${BACKUP_ROOT:-$BACKUP_ROOT_DEFAULT}"
SRC_DIR="${BACKUP_ROOT}/${BACKUP_ID}"

if [[ ! -d "$SRC_DIR" ]]; then
  echo "Error: backup not found: ${SRC_DIR}" >&2
  exit 1
fi

if [[ ! -f "${SRC_DIR}/manifest.sha256" ]]; then
  echo "Error: backup manifest missing: ${SRC_DIR}/manifest.sha256" >&2
  exit 1
fi

if [[ "$ENV_EFFECTIVE" == "live" ]]; then
  if [[ -t 0 ]]; then
    echo "WARNING: You are about to restore ENV=live from BACKUP=${BACKUP_ID}." >&2
    read -r -p "Type 'yes' to proceed: " answer
    if [[ "$answer" != "yes" ]]; then
      echo "Aborted." >&2
      exit 1
    fi
  else
    if [[ "${CONFIRM_LIVE:-}" != "YES" ]]; then
      echo "Error: non-interactive live restore requires CONFIRM_LIVE=YES" >&2
      exit 1
    fi
  fi
fi

echo "Validating backup integrity..."
(
  cd "$SRC_DIR"
  sha256sum -c manifest.sha256
)

echo "AUDIT restore_validated env=${ENV_EFFECTIVE} backup_id=${BACKUP_ID} backup_dir=${SRC_DIR}" >&2

ROLLBACK_ID="$(date -u +%Y%m%dT%H%M%SZ)"
ROLLBACK_DIR="${ROOT_DIR}/data/rollbacks/${ENV_EFFECTIVE}/${ROLLBACK_ID}"
mkdir -p "${ROLLBACK_DIR}/events" "${ROLLBACK_DIR}/projections"

if [[ ! -d "$EVENT_STORE_PATH" ]]; then
  echo "Error: EVENT_STORE_PATH is not a directory: ${EVENT_STORE_PATH}" >&2
  exit 1
fi

PROJECTIONS_DIR="$(dirname "$PROJECTIONS_DB_PATH")"
if [[ ! -d "$PROJECTIONS_DIR" ]]; then
  echo "Error: projections directory does not exist: ${PROJECTIONS_DIR}" >&2
  exit 1
fi

echo "Creating rollback point: ${ROLLBACK_ID}"
cp -a "${EVENT_STORE_PATH}/." "${ROLLBACK_DIR}/events/"
cp -a "${PROJECTIONS_DIR}/." "${ROLLBACK_DIR}/projections/"

(
  cd "$ROLLBACK_DIR"
  find . -type f ! -name 'manifest.sha256' -print0 | sort -z | xargs -0 sha256sum > manifest.sha256
)

chmod -R u+rwX,go-rwx "$ROLLBACK_DIR"

echo "AUDIT rollback_created env=${ENV_EFFECTIVE} rollback_id=${ROLLBACK_ID} rollback_dir=${ROLLBACK_DIR}" >&2

echo "Restoring events into: ${EVENT_STORE_PATH}"
mkdir -p "$EVENT_STORE_PATH"
find "$EVENT_STORE_PATH" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
cp -a "${SRC_DIR}/events/." "${EVENT_STORE_PATH}/"

echo "Restoring projections into: ${PROJECTIONS_DIR}"
mkdir -p "$PROJECTIONS_DIR"
find "$PROJECTIONS_DIR" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
cp -a "${SRC_DIR}/projections/." "${PROJECTIONS_DIR}/"

echo "Restore complete. Rollback id: ${ROLLBACK_ID}"

echo "AUDIT restore_completed env=${ENV_EFFECTIVE} backup_id=${BACKUP_ID} rollback_id=${ROLLBACK_ID}" >&2
