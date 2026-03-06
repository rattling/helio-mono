#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


REQUIRED_MARKERS = {
    ".github/agents/templates/ISSUE_TEMPLATE.md": [
        "## Required Tests (must pass)",
        "## Acceptance Criteria",
    ],
    ".github/agents/templates/MILESTONE_META_ISSUE_TEMPLATE.md": [
        "## Milestone Test Gate (must pass before QA sign-off)",
        "## Acceptance Criteria",
    ],
    ".github/agents/templates/ISSUE_HANDOFF_TEMPLATE.md": [
        "## Verification",
    ],
    ".github/agents/templates/PR_REQUEST_TEMPLATE.md": [
        "## Milestone Test Gate",
        "## Issue Test Coverage Confirmation",
    ],
    ".github/copilot-instructions.md": [
        "docs/process/AUTHORITY_MAP.md",
        "docs/process/SESSION_BOOTSTRAP.md",
    ],
}


def main() -> int:
    failures: list[str] = []

    for rel_path, markers in REQUIRED_MARKERS.items():
        path = ROOT / rel_path
        if not path.exists():
            failures.append(f"Missing required file: {rel_path}")
            continue

        content = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in content:
                failures.append(f"{rel_path}: missing marker: {marker}")

    if failures:
        print("Process template validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Process template validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
