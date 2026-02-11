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
- PROJECT_CHARTER.md
- PROJECT_INVARIANTS.md (if applicable)
- ARCHITECTURE.md (baseline, may evolve)

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
The Architect agent:
- defines milestone scope
- proposes a set of issues
- identifies dependencies and service boundaries
- ensures a runnable spine exists or will be created

The Product Owner approves or amends the milestone plan.

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

A milestone that does not preserve a runnable spine is invalid.

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
- issue updated with a closing comment using:
  - `.github/agents/templates/ISSUE_HANDOFF_TEMPLATE.md`

This closing comment is the **durable handoff artifact**.

---

## 6. Parallel Agent Work

### 6.1 Branch Discipline
- Each issue is worked on its own branch.
- Agents assume other agents may be working concurrently.
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

### 7.2 Milestone Validation (QA Agent)
The QA agent performs final milestone validation:
- verifies system is runnable end-to-end
- confirms all acceptance criteria met
- validates documented usage paths
- checks issue state and traceability
- produces milestone QA summary

### 7.3 Pull Request Creation (QA Agent)
After successful validation, the QA agent:
- confirms all milestone issues are closed with handoffs
- confirms meta-issue is updated
- confirms branch is mergeable with main
- creates PR using `.github/agents/templates/PULL_REQUEST_TEMPLATE.md`
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
