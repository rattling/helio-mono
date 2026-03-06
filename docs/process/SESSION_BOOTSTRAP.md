# Session Bootstrap

## Purpose

This document provides the minimum startup and rehydration sequence for reliable continuation after context reset.

## Step 0: Choose Operating Mode

Use this decision rule:

- **ADHOC mode** when user asks for quick operational help, diagnostics, or targeted edits without issue/PR workflow.
- **Structured workflow** when user asks to create/close issues, perform milestone work, prep a PR, or make contract/architecture changes.

If unclear, ask one direct clarification question before proceeding.

## Universal Startup Checks (Always)

Run:

1. `git remote -v`
2. `git status --short`
3. `git branch --show-current`

Confirm expected repo identity and working-tree cleanliness before significant work.

## Python Environment Standard (Always)

For all Python commands in this repository:

- Use `.venv/bin/python` (never bare `python`).
- Use `.venv/bin/pip` (never bare `pip`).

This avoids accidental system-Python usage and keeps dependency behavior consistent
across local execution, automation, and CI.

## Lean Startup Path (Default)

For most sessions, stop after these reads:

1. `docs/process/AUTHORITY_MAP.md`
2. Active mode guide in `.github/agents/`
3. Current issue or milestone meta-issue

This is the default path for high productivity and low token usage.

Token-efficiency rule:
- Do not re-read the full process corpus on every issue.
- Re-read only when mode changes, conflict appears, or requirements become ambiguous.

## Structured Workflow Startup

When in ARCH/DEV/QA mode, execute in order:

1. Read:
   - `.github/ENGINEERING_CONSTITUTION.md`
   - `.github/WORKFLOW.md`
   - active mode guide in `.github/agents/`
   - `docs/process/AUTHORITY_MAP.md`
2. Read project context:
   - `docs/PROJECT_CHARTER.md`
   - active milestone charter in `docs/MILESTONES/`
   - `docs/ARCHITECTURE.md` and relevant deep docs in `docs/architecture/`
3. Rehydrate milestone state from GitHub:
   - open active milestone meta-issue
   - extract checklist issue IDs from the meta-issue body and use that set as source of truth for milestone scope
   - do not rely on issue title/label search alone to determine the milestone issue set
   - find first unchecked issue (or meta “Current Focus”)
   - inspect most recent closed issue handoff for verification commands/results
4. If uncertain, re-run the most recent verification command before starting new work.

### Context Expansion Triggers (Only if Needed)

Read additional docs only when:
- A contract change is required
- Scope/invariant conflict appears
- Rehydrated issue context is insufficient to proceed safely
- Required tests or milestone gate commands are unclear

If triggered, expand in order:
1. `.github/copilot-instructions.md`
2. `docs/PROJECT_CHARTER.md`
3. `docs/ARCHITECTURE.md` and targeted files under `docs/architecture/`

## ADHOC Startup

When operating in ADHOC mode:

1. Confirm current working directory and target files.
2. Execute only the minimum reads/commands needed.
3. Avoid issue/PR ceremony unless the user asks.
4. Keep edits narrow and immediately verifiable.

## Required Status Line (Structured Workflow)

At start and major transitions, emit:

`MODE: <ARCH|DEV|QA> | MILESTONE: <N> | ISSUE: #<id or n/a> | STATE: <starting|in-progress|done|blocked>`

At session start, include one of:
- `Starting work on Milestone <N>. DEV/QA. No work done yet.`
- `Continuing Milestone <N>. DEV/QA. Current focus: #<id>. <x>/<total> issues complete.`

## Interruption Safety Checkpoint

If interrupted mid-issue:

1. Create WIP commit referencing issue.
2. Leave WIP issue comment with current state, files touched, next steps, and verification command.
3. Update meta-issue Current Focus.

If these are missing, resuming agent must treat state as uncertain and re-verify before continuing.
