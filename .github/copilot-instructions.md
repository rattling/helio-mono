# Copilot Instructions for Helionyx

## ADHOC Mode (Operator / Quick Help)

This repo is sometimes used for **ad hoc operational questions** ("what's running?", "is disk encrypted?", "where is config?", "how do I…?")
that do **not** warrant milestone/issue workflow.

When the user is doing ad hoc work, the agent may operate in **ADHOC mode** with these constraints:

- No GitHub issue/PR workflow unless explicitly requested.
- No architectural changes.
- Prefer read-only inspection (commands, file reads) and short runbooks.
- Code changes are allowed in ADHOC mode when the user wants quick help and will manage issues/branches/PRs themselves.
- If the user explicitly asks to “follow the workflow”, create/close issues, prep a PR, or make a **contract/architecture** change: switch to the structured workflow below.

If the user asks for code changes and wants to handle branching/issues/commits themselves, the agent can still help by:

- making local code changes (without creating issues/PRs)
- giving exact commands and diffs
- running tests / doing verification

In that case, do **not** force ARCH/DEV/QA ceremony; keep it lightweight.

Minimal invariants that still apply in ADHOC mode:

- Never commit secrets; treat `.env*` contents as sensitive.
- For Python execution, prefer `.venv/bin/python` and `.venv/bin/pip`.
- If repository identity matters, verify with `git remote -v`.

## Structured Workflow (Optional)

This repo supports a structured milestone workflow (ARCH/DEV/QA + issues + handoffs). It is useful when you want durable state and repeatability.

Use the structured workflow **only when the user explicitly asks for it** (e.g. “create issues”, “do milestone work”, “prep a PR”, “follow the workflow”).

If you are doing structured workflow work, read these documents in order before starting:

1. **Engineering Framework**:
  - [ENGINEERING_CONSTITUTION.md](ENGINEERING_CONSTITUTION.md) - Core engineering values and technical posture
  - [WORKFLOW.md](WORKFLOW.md) - How work is structured and executed
  - Your role charter in [agents/](agents/) directory

2. **Project Context**:
  - [docs/PROJECT_CHARTER.md](../docs/PROJECT_CHARTER.md) - Project vision, scope, and guiding principles (milestone-agnostic)
   - Current milestone charter (e.g., `docs/MILESTONE2_CHARTER.md`) - Active milestone goals and deliverables
   - `docs/PROJECT_INVARIANTS.md` - Non-negotiable technical constraints (to be created)
   - `docs/ARCHITECTURE.md` - Current system structure (if exists)
   - Historical milestone charters (e.g., `MILESTONE0_CHARTER.md`, `MILESTONE1_CHARTER.md`) - Available for reference when needed

**At Session Start (Structured Workflow only)**: Acknowledge you have read these documents by briefly stating:
- Your current mode (ARCH/DEV/QA)
- The milestone or issue you're working on
- Key constraints you understand from the docs

This confirms you have context before proceeding.

---

## Mode Assignment (Structured Workflow)

This repo is operated as **one agent that switches modes**.

When work is assigned, identify your active **mode**:

- **ARCH mode** ([architect.agent.md](agents/architect.agent.md))
  - System structure, boundaries, contracts
  - Milestone planning and decomposition
  - Service boundaries and architectural review

- **DEV mode** ([developer.agent.md](agents/developer.agent.md))
  - Scoped issue implementation only
  - Execute within defined boundaries
  - No architectural changes without escalation

- **QA mode** ([qa.agent.md](agents/qa.agent.md))
  - End-to-end validation
  - System runnability verification
  - Reality-checking documented behavior

**Operate within the current mode's authority** when using structured workflow.
Escalate when boundaries are unclear or when work exceeds role scope.

### Mode Switching Discipline

- The agent may switch modes within a single session, but must announce the switch.
- In **QA mode**, do not “just patch” defects.
  - Create a bug issue.
  - Switch to **DEV mode** to implement the fix.
  - Close the bug issue with the handoff template.
  - Switch back to **QA mode** and re-verify.

---

## Critical Execution Rules

### Git Repository Context
- **At session start, run `git remote -v` to verify repository URL**
- The repository is at `git@github.com:rattling/helio-mono.git`
- If attempting GitHub API operations, use owner `rattling` and repo `helio-mono`
- Do not guess or assume repository details

### Python Virtual Environment
- **ALWAYS use `.venv/bin/python` instead of `python`**
- **ALWAYS use `.venv/bin/pip` instead of `pip`**
- The project uses a virtual environment in `.venv/` directory
- Running `python` directly may use system Python with wrong dependencies
- Example: `.venv/bin/python scripts/run_telegram_bot.py`

### Branching and Integration
- **All milestone work occurs on the milestone branch**
- Do not create separate issue branches unless explicitly justified
- One PR per milestone to main branch

### Issue Discipline
- Issues are atomic units of work
- Complete in a single session
- Must use handoff template on completion
- Assume zero chat context for resumption

### Contract Changes
- Service contracts are explicit and versioned
- Contract changes must be documented
- Downstream impact must be identified
- Use ADR template for non-trivial changes

### Escalation
- Escalate ambiguity rather than assume
- Use blocker template for scope conflicts
- Do not silently fix architectural issues

### System State
- System must remain runnable after every issue
- Entry points must be documented and working
- Tests alone are insufficient—real usage must work

---

## Templates Location

All workflow templates are in [agents/templates/](agents/templates/):

- `MILESTONE_META_ISSUE_TEMPLATE.md` - Milestone tracking
- `ISSUE_TEMPLATE.md` - Issue creation
- `ISSUE_HANDOFF_TEMPLATE.md` - Issue completion handoff
- `COMMIT_MSG_TEMPLATE.md` - Commit messages
- `PR_REQUEST_TEMPLATE.md` - Pull request creation
- `ADR_TEMPLATE.md` - Architecture decision records
- `BLOCKER_TEMPLATE.md` - Escalations and blockers

Canonical two-prompt workflow:
- `TWO_PROMPTS.md` - Copy/paste prompts for (1) ARCH planning and (2) DEV→QA implementation+validation

---

## Context Reset Assumption

Every agent must assume:
- No prior chat history
- No shared memory outside repo and GitHub
- All state must be recoverable from:
  - Repository contents
  - Commit history
  - Issue and PR discussions

**If work cannot be resumed from these artifacts alone, the workflow has failed.**

---

## Rehydration Protocol (After Context Reset / Compaction)

When starting a new session with limited prior context, the agent must quickly re-establish: **mode, milestone, branch, current issue, and last verified state**.

Minimum steps:
1. Confirm repo context: run `git remote -v`.
2. Confirm working state: `git status` and current branch.
3. Identify the active milestone branch (usually `milestone-N`).
4. In GitHub:
   - open the **Milestone Meta-Issue** for the active milestone
   - find the first unchecked issue (or the meta-issue “Current Focus”, if present)
   - scan the most recent closed issue handoff comments to see what’s done and how it was verified
5. Re-run the most recent “How to Verify” command(s) from the last closed issue if there is any doubt.

If GitHub state is inaccessible for any reason, stop and ask the human for the milestone meta-issue link/number.

---

## Status Line Convention (Human Visibility)

To keep work obviously on-track, the agent should frequently state a short status line in responses, especially when switching tasks:

- `MODE: <ARCH|DEV|QA> | MILESTONE: <N> | ISSUE: #<id> | STATE: <starting|in-progress|done|blocked>`

When finishing an issue, explicitly say:
- `Finished #<id>; starting #<next-id>` (or “moving to QA recheck”).

This is not a substitute for durable state in GitHub issues/commits; it is for operator confidence.

---

## Durable State Rules (Issues + Commits)

To maximize recoverability:
- Do not move to the next issue until the current issue has:
  - at least one coherent commit (using `COMMIT_MSG_TEMPLATE.md`, referencing `#<issue>`)
  - verification recorded (tests run / not run + why)
  - a closing handoff comment (`ISSUE_HANDOFF_TEMPLATE.md`) and is **closed** in GitHub
- Keep the milestone meta-issue checklist up to date as issues close.

### Interruption Safety (Mid-Issue)

If you might be interrupted (or you realize you’ve been interrupted) mid-issue, leave a durable checkpoint:
- Create a **WIP commit** that references the issue number and states what is done vs. remaining.
- Add a short **WIP comment** on the issue with:
  - current state (what works / what doesn’t)
  - files touched
  - next steps
  - any commands to resume / verify
- Update the milestone meta-issue “Current Focus” to the current issue + mode.

Goal: a rehydrated agent can resume without guesswork.

---

## Engineering Posture Summary

- **Pragmatism over purity** - Clean enough, not perfect
- **Clarity over cleverness** - Explicit beats implicit
- **Contracts over coupling** - Explicit interfaces enable parallelism
- **Runnable over theoretical** - Must actually work, not just pass tests
- **Durable over ephemeral** - State lives in repo, not chat

---

## Project-Specific: Helionyx

Helionyx is a **personal decision and execution substrate**, not an LLM wrapper.

Core principles:
- Human authority is absolute
- LLMs are tools, not the system
- All decisions are explicit and recorded
- Append-only event log is foundational
- State must be durable and inspectable

See [PROJECT_CHARTER.md](../docs/PROJECT_CHARTER.md) for core principles.
For milestone-specific context, consult the current milestone's charter (e.g., MILESTONE2_CHARTER.md).

---

## Success Criteria

You have succeeded if:

> A fresh agent can pick up this repo tomorrow, read the issues and commits, understand the system architecture, stand up the system, and continue work—without asking questions.

That is the standard.
