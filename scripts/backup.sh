#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${ENV:-dev}"

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
print(f"API_HOST={shlex.quote(c.API_HOST)}")
print(f"API_PORT={shlex.quote(str(c.API_PORT))}")
print(f"LOG_LEVEL={shlex.quote(c.LOG_LEVEL)}")
print(f"ENV_EFFECTIVE={shlex.quote(c.ENV)}")
PY
)"

BACKUP_ROOT_DEFAULT="${ROOT_DIR}/data/backups/${ENV_EFFECTIVE}"
BACKUP_ROOT="${BACKUP_ROOT:-$BACKUP_ROOT_DEFAULT}"

BACKUP_ID="$(date -u +%Y%m%dT%H%M%SZ)"
DEST_DIR="${BACKUP_ROOT}/${BACKUP_ID}"

mkdir -p "${DEST_DIR}/events" "${DEST_DIR}/projections"

if [[ ! -d "$EVENT_STORE_PATH" ]]; then
  echo "Error: EVENT_STORE_PATH is not a directory: ${EVENT_STORE_PATH}" >&2
  exit 1
fi

PROJECTIONS_DIR="$(dirname "$PROJECTIONS_DB_PATH")"
if [[ ! -d "$PROJECTIONS_DIR" ]]; then
  echo "Error: projections directory does not exist: ${PROJECTIONS_DIR}" >&2
  exit 1
fi

cp -a "${EVENT_STORE_PATH}/." "${DEST_DIR}/events/"
cp -a "${PROJECTIONS_DIR}/." "${DEST_DIR}/projections/"

GIT_COMMIT=""
if command -v git >/dev/null 2>&1 && [[ -d "${ROOT_DIR}/.git" ]]; then
  GIT_COMMIT="$(git -C "$ROOT_DIR" rev-parse HEAD 2>/dev/null || true)"
fi

"$PYTHON_BIN" - <<PY
import json
from pathlib import Path

dest = Path(${DEST_DIR@Q})
meta = {
    "env": ${ENV_EFFECTIVE@Q},
    "backup_id": ${BACKUP_ID@Q},
    "created_at_utc": ${BACKUP_ID@Q},
    "git_commit": ${GIT_COMMIT@Q} or None,
}
config = {
    "ENV": ${ENV_EFFECTIVE@Q},
    "EVENT_STORE_PATH": ${EVENT_STORE_PATH@Q},
    "PROJECTIONS_DB_PATH": ${PROJECTIONS_DB_PATH@Q},
    "API_HOST": ${API_HOST@Q},
    "API_PORT": int(${API_PORT@Q}),
    "LOG_LEVEL": ${LOG_LEVEL@Q},
}

(dest / "meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
(dest / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True) + "\n")
PY

(
  cd "$DEST_DIR"
  # Integrity manifest: relative paths, excluding the manifest itself.
  find . -type f ! -name 'manifest.sha256' -print0 | sort -z | xargs -0 sha256sum > manifest.sha256
)

chmod -R u+rwX,go-rwx "$DEST_DIR"

echo "AUDIT backup_created env=${ENV_EFFECTIVE} backup_id=${BACKUP_ID} backup_dir=${DEST_DIR}" >&2

echo "$BACKUP_ID"
