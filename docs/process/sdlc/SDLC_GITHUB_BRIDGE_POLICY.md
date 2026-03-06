# SDLC ↔ GitHub Bridge Policy

Purpose: keep SDLC process assets clearly separated from product code while preserving GitHub platform behavior.

## Canonical Ownership

- Canonical SDLC guidance lives under `docs/process/sdlc/`.
- `.github/` contains only files that are required as platform entrypoints or operator entrypoints.

## Why `.github` cannot be fully emptied

Some GitHub capabilities are path-sensitive:

- Issue templates/forms are discovered from `.github/ISSUE_TEMPLATE/` (primary location).
- PR template discovery uses `.github/PULL_REQUEST_TEMPLATE.md` (or limited fallback locations).
- GitHub Actions workflows must be in `.github/workflows/`.

These files remain in `.github` by design.

## Bridge Pattern (Repository Standard)

1. Keep canonical process content in `docs/process/sdlc/`.
2. Keep required GitHub-discovery files in `.github/`.
3. In `.github` docs that duplicate process behavior, prefer concise pointers to canonical SDLC files.
4. When process rules change, update canonical SDLC docs first, then adjust `.github` bridge docs/templates as needed.
5. Record durable changes in `docs/process/sdlc/SDLC_PROCESS_CHANGELOG.md`.

## Practical Scope Boundary

Outside SDLC canonical docs, the process-critical entrypoint is:

- `.github/copilot-instructions.md`

Additional `.github` files are retained only when needed for GitHub discovery/automation compatibility.
