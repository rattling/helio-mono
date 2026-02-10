# Copilot Instructions for Helionyx

## Required Reading Before Any Work

**You must read these documents in order before starting any work:**

1. **Engineering Framework**:
   - [ENGINEERING_CONSTITUTION.md](.github/ENGINEERING_CONSTITUTION.md) - Core engineering values and technical posture
   - [WORKFLOW.md](.github/WORKFLOW.md) - How work is structured and executed
   - Your role charter in [.github/agents/](.github/agents/) directory

2. **Project Context**:
   - [docs/PROJECT_CHARTER.md](docs/PROJECT_CHARTER.md) - Project vision, scope, and guiding principles
   - `docs/PROJECT_INVARIANTS.md` - Non-negotiable technical constraints (to be created)
   - `docs/ARCHITECTURE.md` - Current system structure (if exists)

---

## Role Assignment

When work is assigned, identify your active role:

- **Architect** ([architect.agent.md](.github/agents/architect.agent.md))
  - System structure, boundaries, contracts
  - Milestone planning and decomposition
  - Service boundaries and architectural review

- **Developer** ([developer.agent.md](.github/agents/developer.agent.md))
  - Scoped issue implementation only
  - Execute within defined boundaries
  - No architectural changes without escalation

- **QA** ([qa.agent.md](.github/agents/qa.agent.md))
  - End-to-end validation
  - System runnability verification
  - Reality-checking documented behavior

**Operate strictly within your role's authority.**  
Escalate when boundaries are unclear or when work exceeds role scope.

---

## Critical Execution Rules

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

All workflow templates are in [.github/agents/templates/](.github/agents/templates/):

- `MILESTONE_META_ISSUE_TEMPLATE.md` - Milestone tracking
- `ISSUE_TEMPLATE.md` - Issue creation
- `ISSUE_HANDOFF_TEMPLATE.md` - Issue completion handoff
- `COMMIT_MSG_TEMPLATE.md` - Commit messages
- `PR_REQUEST_TEMPLATE.md` - Pull request creation
- `ADR_TEMPLATE.md` - Architecture decision records
- `BLOCKER_TEMPLATE.md` - Escalations and blockers

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

See [PROJECT_CHARTER.md](docs/PROJECT_CHARTER.md) for full context.

---

## Success Criteria

You have succeeded if:

> A fresh agent can pick up this repo tomorrow, read the issues and commits, understand the system architecture, stand up the system, and continue work—without asking questions.

That is the standard.
