# Milestone Execution Runbook

Purpose: prevent rehydration drift and avoid avoidable CI churn during ARCH/DEV/QA milestone execution.

For human-oriented overview diagrams and update guidance, see `docs/process/SDLC_PROCESS_GUIDE.md`.

## Source of Truth for Milestone Scope

- The milestone issue list is the checklist in the milestone meta-issue body.
- Do not derive the full issue set from title/label search.
- At session start, extract checklist issue IDs and use that ordered list as authoritative scope.

## Required Session Status Line

Emit at start and transitions:

`MODE: <ARCH|DEV|QA> | MILESTONE: <N> | ISSUE: #<id> | STATE: <starting|in-progress|done|blocked>`

Also include one context line:
- Starting fresh: `Starting work on Milestone <N>. DEV/QA. No work done yet.`
- Continuing: `Continuing Milestone <N>. DEV/QA. Current focus: #<id>. <x>/<total> issues complete.`

## Per-Issue Durable Loop (Mandatory)

Complete this full loop before moving to the next issue:

1. Implement scoped changes for the issue.
2. Run issue `Required Tests (must pass)` commands.
3. Commit and push (reference issue number).
4. Post issue handoff comment using template.
5. Close the issue.
6. Update milestone meta-issue checklist and `Current Focus`.

If interrupted mid-issue:
- create WIP commit
- post WIP issue comment with resume/verify commands
- update meta-issue `Current Focus`

## PR Body Preflight (Preventive)

Before creating/updating a PR body, run:

`PR_BODY="<body>" .venv/bin/python scripts/process/check_pr_body.py`

Publish/update PR body only if preflight passes.

Required PR sections:
- `## Summary`
- `## Related Issues`
- `## Verification`
- `## Milestone Test Gate`
- `## Issue Test Coverage Confirmation`

## CI Polling Posture

- Default: do not poll CI in tight loops.
- Prefer prevention first (template compliance + local preflight + targeted local tests).
- Poll CI only when explicitly requested by the human.

## Quick Operator Audit

When reviewing an active milestone:

- Confirm meta-issue checklist matches expected issue set.
- Confirm each closed issue has handoff + test evidence.
- Confirm issue processing appears in-order unless reprioritized by human.
- Confirm PR body preflight-required sections are present before pushing trigger commits.
