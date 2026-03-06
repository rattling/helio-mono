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
- `SDLC/ENGINEERING_CONSTITUTION.md`
- `SDLC/agent/SDLC_AGENT_AUTHORITY_MAP.md`
- `SDLC/agent/SDLC_AGENT_SESSION_BOOTSTRAP.md`
- `SDLC/agent/SDLC_AGENT_EXECUTION_RUNBOOK.md`

In particular:

- **Milestones are the primary delivery unit**
- **One branch per milestone**
- **One PR per milestone**
- **Issues are the atomic execution unit**

### Lean Execution Checklist (Default)

Use this minimal loop before reading deeper sections:

1. Startup: run lean path from `SDLC/agent/SDLC_AGENT_SESSION_BOOTSTRAP.md`.
2. Pre-code: verify issue has `Required Tests (must pass)`.
3. Implement: keep strictly in issue scope and preserve interaction paths.
4. Verify: run required test commands and capture exact results.
5. Close: handoff comment + close issue in GitHub.

Read additional docs only if scope/contract ambiguity blocks progress.
Treat `SDLC/agent/SDLC_AGENT_EXECUTION_RUNBOOK.md` as canonical for the per-issue durable loop and PR preflight details.

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
- Read milestone meta-issue checklist and derive ordered issue list from that checklist only.
- Do not infer the full milestone issue set from search, labels, or title pattern matches.
- Update the milestone meta-issue “Current Focus” to this issue and DEV mode (if the meta-issue uses it).
- Emit a status line (MODE/MILESTONE/ISSUE/STATE) for human visibility.
- For GitHub issue/meta updates, prefer MCP GitHub tools; avoid temp-file body workflows (e.g., `/tmp` + `--body-file`) when an inline/in-memory update path exists.
- Confirm the issue contains **Required Tests (must pass)** with executable commands.

If required tests are missing or unclear:
- update the issue first (or request ARCH clarification)
- do not start implementation until verification criteria are explicit

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
- process issues in checklist order unless the human explicitly reprioritizes
- complete the durable issue loop before moving to next issue:
  1) implement
  2) run required tests
  3) commit and push
  4) post handoff comment
  5) close issue
  6) update milestone meta-issue checklist/current focus

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
- run the issue’s declared **Required Tests (must pass)** command set and capture results

If testing is deferred:
- state this explicitly in the issue closing comment
- explain why

Testing deferral is exceptional and must include:
- a linked blocker issue
- explicit risk statement
- clear follow-up owner/path

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
1. Add closing comment using `SDLC/agent/templates/ISSUE_HANDOFF_TEMPLATE.md`
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

Verification in handoff must include:
- exact test commands run
- pass/fail result summary
- whether the issue’s Required Tests section is fully satisfied

**Do not consider the issue complete until it is closed in GitHub with the handoff comment.**

Before creating/updating milestone PR body, run local preflight validation with the full candidate body:
- `PR_BODY="<body>" .venv/bin/python SDLC/scripts/check_pr_body.py`
- If this check fails, fix missing sections before publishing PR updates.

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
