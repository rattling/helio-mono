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

Canonical process references (single source of truth):
- `SDLC/agent/SDLC_AGENT_AUTHORITY_MAP.md` (instruction precedence, mode authority, conflict handling)
- `SDLC/agent/SDLC_AGENT_SESSION_BOOTSTRAP.md` (startup + rehydration checklist)
- `SDLC/agent/SDLC_AGENT_EXECUTION_RUNBOOK.md` (canonical per-issue execution loop and PR preflight)
- `SDLC/SDLC_GITHUB_BRIDGE_POLICY.md` (what stays in `.github/` for platform discovery vs what stays canonical in SDLC)

Use the structured workflow **only when the user explicitly asks for it** (e.g. “create issues”, “do milestone work”, “prep a PR”, “follow the workflow”, "architect mode", "developer mode", "qa mode").

Productivity default:
- Start with the lean path in `SDLC/agent/SDLC_AGENT_SESSION_BOOTSTRAP.md`.
- Expand context only when required by scope, contracts, or verification ambiguity.
- Prefer linking to canonical docs over re-stating long rule text in new artifacts.
- Treat `SDLC/agent/SDLC_AGENT_EXECUTION_RUNBOOK.md` as the canonical execution-loop reference; avoid duplicating that loop text in new docs/comments unless customization is required.

## Critical Execution Rules

Hard-rule precedence and conflict handling live in `SDLC/agent/SDLC_AGENT_AUTHORITY_MAP.md`.
Startup and rehydration sequence lives in `SDLC/agent/SDLC_AGENT_SESSION_BOOTSTRAP.md`.
Mode-specific execution details live in `SDLC/agent/modes/` and `SDLC/WORKFLOW.md`.
The rules below are the Helionyx-specific invariants that remain non-negotiable.

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
- Issues are atomic units of work and should be completed in a single session when feasible.
- Every issue must define **Required Tests (must pass)** with explicit commands.
- Issue closure must report exact test commands run and results.
- For milestone execution, derive issue scope from the milestone meta-issue checklist only (not title/label searches).
- Process issues in checklist order unless the human explicitly reprioritizes.
- Mandatory loop: implement -> run required tests -> commit -> push -> handoff comment -> close issue -> update milestone meta-issue status/current focus.

### Test Discipline
- Milestone meta-issues must define a **Milestone Test Gate** with explicit commands
- DEV must run the issue-level required tests before closing an issue
- QA must block PR creation if issue-level required tests or milestone test gate are missing/unverified
- If tests cannot be run, open/link a blocker issue and record risk explicitly
- Before creating/updating a PR body, run local preflight: `PR_BODY="<body>" .venv/bin/python SDLC/scripts/check_pr_body.py` and only publish if it passes.
- Avoid polling CI/check status loops by default. Prefer preflight prevention (template + local validation); only poll when explicitly requested by the human.

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

## Canonical References (Use Instead of Duplicating Rules)

- Startup/rehydration: `SDLC/agent/SDLC_AGENT_SESSION_BOOTSTRAP.md`
- Per-issue loop + PR preflight: `SDLC/agent/SDLC_AGENT_EXECUTION_RUNBOOK.md`
- Instruction precedence and mode authority: `SDLC/agent/SDLC_AGENT_AUTHORITY_MAP.md`
- Workflow lifecycle: `SDLC/WORKFLOW.md`
- Mode constraints: `SDLC/agent/modes/`
- Human prompts: `SDLC/human/SDLC_HUMAN_DRIVER_PROMPTS.md`
- Templates/checklists: `SDLC/agent/templates/`

## Durable-State Minimum (Structured Workflow)

- Assume zero chat memory; state must be recoverable from repo + GitHub artifacts.
- Before moving to next issue: commit(s), verification evidence, handoff comment, and issue closed.
- If interrupted mid-issue: leave a WIP commit and WIP issue comment with resume commands.

## Helionyx Posture

- Human authority is absolute.
- Contracts and architecture are explicit, versioned, and reviewed.
- Runnable system behavior is required; tests alone are not sufficient.
