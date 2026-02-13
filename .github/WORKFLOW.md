# Workflow

## 1. Purpose

This document defines **how work is executed** in this repository.

It specifies:
- how projects start
- how milestones are planned and executed
- how issues are worked
- how agents coordinate safely
- how work is handed off and resumed

This document assumes the constraints and posture defined in:
- ENGINEERING_CONSTITUTION.md
- Role charters in `.github/agents/`

All execution artifacts must conform to the templates defined in:
- `.github/agents/templates/`

---

## 1.1 Single Agent, Multiple Modes

This repo is operated as a **single Copilot agent that switches modes**, not three separate agents.

Modes:
- **ARCH mode**: architecture + milestone planning + contract decisions
- **DEV mode**: implementation of scoped issues
- **QA mode**: runnable-system validation + acceptance checks + PR creation

**Mode discipline**:
- The agent must explicitly state its current mode at the start of a working session.
- If switching modes mid-session, the agent must announce the switch and follow that mode’s rules.

### Two-Prompt Cadence (Default)

Milestones are typically executed with **two human prompts**:
1. **Architecture prompt** (ARCH mode): decompose the milestone, create issues/meta-issue, establish/adjust contracts and architecture artifacts.
2. **Implementation prompt** (DEV → QA loop): implement issues, validate end-to-end, raise bug issues as needed, fix them, re-validate, then create the PR.

Canonical prompt templates live in:
- `.github/agents/templates/TWO_PROMPTS.md`

The human intervenes primarily to:
- approve the ARCH output (milestone plan/contracts)
- review and merge the milestone PR

---

## 2. Units of Work

### 2.1 Project
A project is defined by:
- a repository
- a Project Charter
- a set of milestones

### 2.2 Milestone (Primary Unit)
A milestone is the **primary delivery unit**.

A milestone:
- has a clear goal and acceptance criteria
- results in a runnable, integrated system state
- is delivered via a single PR to the main branch (initially)

Each milestone must be tracked using the **Milestone Meta-Issue Template**:
- `.github/agents/templates/MILESTONE_META_ISSUE_TEMPLATE.md`

### 2.3 Issue (Execution Unit)
An issue is the **atomic execution unit**.

An issue must:
- be small enough to complete in a single agent session
- be independently testable
- produce durable artifacts

All issues must be created using:
- `.github/agents/templates/ISSUE_TEMPLATE.md`

If an issue is too large, it must be split.

---

## 3. Project Startup

### 3.1 Required Project Documents
Before implementation begins, the following must exist:
- PROJECT_CHARTER.md (core vision, principles, invariants - milestone-agnostic)
- Current milestone charter (e.g., MILESTONE2_CHARTER.md - goals, deliverables, scope)
- PROJECT_INVARIANTS.md (if applicable)
- ARCHITECTURE.md (baseline, may evolve)

Historical milestone charters (MILESTONE0_CHARTER.md, MILESTONE1_CHARTER.md, etc.) are preserved for reference.

### 3.2 Architecture Baseline (Optional but Recommended)
A project may begin with an explicit **Architecture Baseline milestone**, producing:
- component diagram
- state diagram
- sequence diagram (canonical flow)
- data/ERD diagram (if applicable)

No feature work begins until the baseline is accepted.

---

## 4. Milestone Structure

Each milestone follows the same internal shape.

### 4.1 Milestone Planning
The agent in **ARCH mode**:
- defines milestone scope
- proposes a set of issues
- identifies dependencies and service boundaries
- ensures a runnable spine exists or will be created

The human approves or amends the milestone plan.

### 4.2 Milestone Composition Pattern
Every milestone must include:
1. **Spine / Scaffold work**
   - repo structure
   - service boundaries
   - configuration
   - test harness
   - run commands

2. **Walking Skeleton**
   - at least one end-to-end flow exercising:
     - interfaces
     - persistence
     - contracts
     - runtime behavior

3. **Incremental Feature Work**
   - limited in scope
   - layered onto the spine

4. **User Interaction Preservation**
   - All existing user interaction paths continue to work
   - New interfaces **add to**, not replace, existing entry points
   - Core domain code remains directly callable
   - Examples:
     - Adding API doesn't break direct Python calls to services
     - Adding UI doesn't break CLI/API access
     - Service wrapper doesn't prevent direct module import
   - README.md documents all active interaction methods
   - Makefile provides convenient commands for key paths

A milestone that does not preserve a runnable spine is invalid.  
A milestone that breaks existing user interaction paths is invalid.

---

## 5. Issue Lifecycle

### 5.1 Start
When starting an issue, the agent must:
- read the issue description
- read relevant docs (architecture, invariants)
- confirm scope is reasonable

If not, the issue must be split or escalated using:
- `.github/agents/templates/BLOCKER_TEMPLATE.md`

### 5.2 Execution
During execution:
- work occurs on a branch
- changes remain within the issue scope
- service boundaries and contracts are respected

If execution is interrupted mid-issue, the agent must leave a durable checkpoint (WIP commit + issue comment) so work can be resumed after a context reset.

All commits must use:
- `.github/agents/templates/COMMIT_MESSAGE_TEMPLATE.md`

If a contract must change:
- the change is made explicit
- downstream impact is documented
- an ADR is created if the change is non-trivial:
  - `.github/agents/templates/ADR_TEMPLATE.md`

### 5.3 Completion (Handoff Bundle)
An issue is complete only when **all** of the following are done:

- code committed and pushed
- tests pass
- docs/runbooks updated if affected
- issue closed in GitHub with handoff comment using:
  - `.github/agents/templates/ISSUE_HANDOFF_TEMPLATE.md`

**The issue must be marked as closed (state=closed) in GitHub.**

This closing comment is the **durable handoff artifact**.

Additionally:
- Do not start the next issue until the current issue has at least one coherent commit referencing the issue number.
- Keep the milestone meta-issue up to date (checkboxes, and “Current Focus” if used).

### 5.4 GitHub Update Method (Automation-Friendly)

When updating GitHub issues/PRs from agent sessions:
- Prefer MCP GitHub tools for issue/PR updates where available.
- Avoid temporary-file body workflows (for example, `/tmp/...` + `--body-file`) unless no practical alternative exists.
- If CLI usage is required, prefer inline/in-memory body updates over filesystem temp files.

Rationale: this improves auto-approval compatibility and reduces friction in non-interactive execution.

---

## 6. Parallel Work (Optional)

### 6.1 Branch Discipline
- Each milestone is worked on a dedicated milestone branch (e.g., `milestone-1`, `milestone-2`).
- All issues within a milestone are completed on that milestone branch.
- The agent in **ARCH mode** creates the milestone branch at the start of milestone setup.
- If multiple agents are used concurrently, assume others may be working and resolve conflicts explicitly.
- Conflicts are resolved explicitly, never silently.

### 6.2 Service Ownership
- An agent working on a service owns it end-to-end for that issue.
- Other agents interact with it only through its published contracts.

### 6.3 Contract Changes
Contract changes must:
- be explicit
- be documented
- identify affected services
- be backwards-compatible where practical

---

## 7. Milestone Integration

### 7.1 Integration Phase
When all milestone issues are complete:
- the milestone branch is integrated
- system is verified as runnable
- milestone acceptance criteria are checked

### 7.2 Milestone Validation (QA mode)
The agent in **QA mode** performs final milestone validation:
- verifies system is runnable end-to-end
- confirms all acceptance criteria met
- validates documented usage paths
- checks issue state and traceability
- produces milestone QA summary

### 7.3 Pull Request Creation (QA mode)
After successful validation, the agent in **QA mode**:
- confirms all milestone issues are closed with handoffs
- confirms meta-issue is updated
- confirms branch is mergeable with main
- creates PR using `.github/agents/templates/PR_REQUEST_TEMPLATE.md`
- includes QA validation summary in PR description
- notifies human for review

### 7.4 Pull Request Review and Merge (Human)
The human reviews and merges:
- reviews QA validation report
- spot-checks key functionality (optional)
- reviews changeset and architectural changes
- approves and merges to main when satisfied

Human authority is absolute for merge decisions.

---

## 8. Context Reset Assumption

Agents must assume:
- no prior chat context
- no shared memory outside the repo and GitHub

All necessary state must be recoverable from:
- repository contents
- commit history
- issue and PR discussions

If work cannot be resumed from these artifacts, the workflow has failed.

---

## 9. Escalation Rules

Agents must stop and escalate when:
- scope is unclear
- invariants conflict
- architectural tradeoffs exceed issue authority
- a decision would affect multiple services or milestones

Escalation must use:
- `.github/agents/templates/BLOCKER_TEMPLATE.md`

---

## 10. Amendments

This workflow may evolve as tooling improves.

However:
- changes must be explicit
- changes must preserve compatibility with the Engineering Constitution
- project-specific deviations belong in project docs, not here
