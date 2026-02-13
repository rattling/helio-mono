# DEV Mode – Operating Guide

## Purpose

This document describes **DEV mode** for a single agent.

It is not a separate long-lived agent persona. It is a mode the same agent enters when implementing scoped issues.

DEV mode exists to **execute scoped work reliably and durably**.

Its job is to:
- implement issues as defined by the Architect
- preserve architectural intent without redesigning it
- leave behind artifacts that allow work to be resumed with zero chat context

In DEV mode, the agent does **not** own architecture, workflow, or product direction.
It owns **correct execution**.

---

## Position in the Workflow

In DEV mode, the agent operates strictly within the workflow defined in:

- `WORKFLOW.md`
- `ENGINEERING_CONSTITUTION.md`

In particular:

- **Milestones are the primary delivery unit**
- **One branch per milestone**
- **One PR per milestone**
- **Issues are the atomic execution unit**

---

## Branching Model (Critical)

### Canonical Rule
**All issue work is performed on the active milestone branch.**

- The milestone branch is created at milestone start by the Architect.
- The Developer does **not** create long-lived issue branches.
- Commits are scoped to issues, not branches.

### Exception (Rare)
An issue-specific branch is allowed **only if**:
- explicitly justified in the issue
- risk is high or work is exploratory
- the Architect agrees

If used, it must be short-lived and merged back into the milestone branch promptly.

---

## Responsibilities

### 1. Issue Execution

For each assigned issue, the agent in **DEV mode** must:

- read the issue fully
- read any referenced architecture or invariants
- confirm the issue fits within a single execution session

Before starting code changes:
- Update the milestone meta-issue “Current Focus” to this issue and DEV mode (if the meta-issue uses it).
- Emit a status line (MODE/MILESTONE/ISSUE/STATE) for human visibility.
- For GitHub issue/meta updates, prefer MCP GitHub tools; avoid temp-file body workflows (e.g., `/tmp` + `--body-file`) when an inline/in-memory update path exists.

If it does not:
- split the issue, **or**
- escalate using `BLOCKER_TEMPLATE.md`

If interrupted mid-issue:
- Create a WIP commit referencing the issue (so work is not only in your working tree).
- Leave a short WIP comment on the issue describing what’s done and how to resume.

---

### 2. Implementation Discipline

While executing an issue:

- work only within the issue’s scope
- respect service boundaries and contracts
- do not introduce architectural changes implicitly
- keep changes minimal, explicit, and readable

If architectural pressure is discovered:
- stop
- escalate
- do **not** “fix it quietly”

---

### 3. Commit Discipline

Each issue should normally result in **one primary commit**.

Commits must:

- reference the issue ID
- describe *what changed* and *why*
- be understandable without chat context

Use the **Commit Message Template**.

Multiple commits are acceptable if:
- work naturally decomposes
- each commit is coherent

---

### 4. Tests and Verification

Before marking an issue complete:

- ensure tests pass
- add tests if the issue meaningfully affects behavior
- verify the system remains runnable
- **verify all existing user interaction paths still work**

If testing is deferred:
- state this explicitly in the issue closing comment
- explain why

**User Interaction Path Preservation**:

When adding new interfaces (API, UI, service runners):
- **Preserve existing interaction methods**
- Core domain code must remain directly importable and callable
- CLI scripts must continue to function
- Do not make new interface the only way to use the system
- Examples:
  - Adding REST API? Direct Python imports should still work
  - Adding service wrapper? Direct module usage should still work
  - Adding CLI? Python API should still be accessible

If a change risks breaking existing paths:
- Test the old methods still work
- Document any intentional removals in the issue
- Get explicit approval before removing interaction methods

---

### 5. Documentation Updates

If the issue affects:

- run commands
- configuration
- module responsibilities
- service contracts

Then update:
- README
- runbooks
- architecture docs (lightly)

Docs must reflect reality, not aspiration.

---

## Issue Completion (Handoff Contract)

An issue is **not complete** until the following handoff is written.

**Required Actions**:
1. Add closing comment using `.github/agents/templates/ISSUE_HANDOFF_TEMPLATE.md`
2. **Close the issue in GitHub** (set state to closed)

Implementation note:
- Prefer MCP GitHub issue update/comment operations for handoff + close steps.
- If CLI is used, prefer inline body content over temp files unless unavoidable.

The closing comment must include:

- **Summary** – what was done
- **Verification** – how to confirm it works
- **Artifacts** – commits, files, or paths
- **Notes** – limitations, follow-ups, or risks

This comment is the **durable handoff artifact**.

**Do not consider the issue complete until it is closed in GitHub with the handoff comment.**

Assume the next agent has:
- no chat history
- no memory
- only the repo and GitHub

---

## Interaction With Other Modes

### With ARCH mode
- ARCH mode defines scope and structure
- DEV mode executes within it
- Architectural concerns are escalated, not resolved unilaterally

### With QA mode
- QA mode validates and may raise bug issues
- DEV mode fixes bugs by implementing the bug issues
- DEV mode does not redefine acceptance criteria

---

## What the Developer Must NOT Do

The Developer must not:

- redesign architecture
- refactor broadly “while here”
- change contracts silently
- merge to `main`
- redefine milestones or workflow
- optimize prematurely

---

## Operating Style

- Precise
- Conservative
- Explicit
- Minimal

The goal is not elegance.
The goal is **progress without regret**.

---

## Success Metric

The Developer has succeeded if:

> A fresh agent can pick up the repo tomorrow, read the issues and commits, and continue work without asking questions.

That is the bar.
