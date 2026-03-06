#!/usr/bin/env python3

from __future__ import annotations

import os


REQUIRED_SECTIONS = [
    "## Summary",
    "## Related Issues",
    "## Verification",
    "## Milestone Test Gate",
    "## Issue Test Coverage Confirmation",
]


def main() -> int:
    body = os.environ.get("PR_BODY", "")

    if not body.strip():
        print("PR body validation failed: empty PR body")
        return 1

    missing = [section for section in REQUIRED_SECTIONS if section not in body]
    if missing:
        print("PR body validation failed. Missing required sections:")
        for section in missing:
            print(f"- {section}")
        return 1

    print("PR body validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
