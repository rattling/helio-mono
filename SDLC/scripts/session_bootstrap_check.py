#!/usr/bin/env python3

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run(cmd: list[str]) -> str:
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return f"<error: {' '.join(cmd)}>\n{result.stderr.strip()}"
    return result.stdout.strip()


def main() -> int:
    print("Session Bootstrap Check")
    print("=======================")
    print(f"repo: {ROOT}")
    print()

    print("git remote -v")
    print(run(["git", "remote", "-v"]))
    print()

    print("git status --short")
    status = run(["git", "status", "--short"])
    print(status or "<clean>")
    print()

    print("git branch --show-current")
    print(run(["git", "branch", "--show-current"]))
    print()

    process_docs = [
        ROOT / "SDLC/agent/SDLC_AGENT_AUTHORITY_MAP.md",
        ROOT / "SDLC/agent/SDLC_AGENT_SESSION_BOOTSTRAP.md",
    ]
    missing = [str(path.relative_to(ROOT)) for path in process_docs if not path.exists()]
    if missing:
        print("Missing required process docs:")
        for path in missing:
            print(f"- {path}")
        return 1

    print("Process docs present.")
    print("Next: open milestone meta-issue and resume from Current Focus.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
