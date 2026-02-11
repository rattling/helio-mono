# QA Mode – Operating Guide

## Purpose

This document describes **QA mode** for a single agent.

It is not a separate long-lived agent persona. It is a mode the same agent enters when validating runnable-system reality and acceptance.

QA mode exists to **establish confidence in reality**, not just correctness.

It validates that:
- the system works end-to-end
- the system can be stood up and used
- documented usage paths are real, not aspirational
- behavior matches architectural and product intent
- regressions and integration failures are visible early

QA explicitly acts as:
- a **technical validator**
- a **user-acceptance surrogate**
- a **deployability sanity check**

Passing tests alone is insufficient.

---

## Position in the Workflow

In QA mode, the agent operates within:

- `WORKFLOW.md`
- `ENGINEERING_CONSTITUTION.md`

Key constraints:
- QA work happens **within a milestone**
- QA runs after issue implementation and before milestone PR merge
- QA does **not** add scope or redesign systems

QA validates what exists.  
It does not invent missing pieces.

---

## Relationship to Other Modes

### With DEV mode
- QA mode verifies delivered behavior
- QA mode reports findings by creating issues; DEV mode fixes
- In QA mode, do not silently patch issues

### With ARCH mode
- QA mode flags architectural drift or contract violations
- QA mode escalates systemic concerns
- QA mode does not resolve architectural trade-offs independently

---

## Core QA Responsibility: Use the System

QA must **actually run and use the system**, as defined by repo artifacts.

This includes, where applicable:
- starting services locally
- running documented commands
- exercising real flows
- inspecting real outputs

If the system cannot be stood up and used, **QA fails**.

---

## What QA Validates

### 1. Runnable System State
QA must confirm that:
- the system can be started using documented mechanisms
- entry points work (e.g. Makefile, scripts, run commands)
- required services come up cleanly
- basic status or health checks succeed

If startup is fragile, unclear, or undocumented, that is a QA finding.

### 1.5 Issue and Milestone State
QA must verify GitHub state before PR creation:
- all milestone issues are closed
- each issue has completion handoff comment
- meta-issue checklist is complete
- no orphaned or incomplete work
- commits properly reference issues
- ADRs created for architectural changes
- branch is mergeable with main

If issue state does not reflect actual delivery, that is a QA failure.

---

### 2. End-to-End Usage Flows
QA exercises representative flows such as:
- API calls (e.g. curl, scripts, tools)
- CLI usage
- UI flows (if applicable)
- direct domain-level invocation (where appropriate)

These flows should reflect **how a real user or operator would engage the system**, not just internal tests.

---

### 3. Functional Correctness
- features behave as described
- happy paths work
- obvious failure modes are handled

---

### 4. Acceptance-Level Behavior
QA checks that:
- outputs are understandable
- configuration is not surprising
- system behavior matches documented intent
- usage does not require hidden knowledge

---

### 5. Regression Safety
- existing functionality still works
- new changes do not break unrelated paths

---

### 6. User Interaction Path Validation

**Critical**: QA must verify all user interaction methods work after milestone changes.

**Core Principle**: New interfaces **add to**, not replace, existing entry points.

**Required Validation Per Milestone**:

1. **Direct Python Access** (if applicable)
   - Import and call domain services directly
   - Example: `from services.ingestion.service import IngestionService`
   - Core domain code must remain callable without framework overhead

2. **CLI/Script Access**
   - All scripts in `scripts/` must work
   - Example: `.venv/bin/python scripts/run_telegram_bot.py`
   - Command-line workflows must not break

3. **API Access** (if exists)
   - HTTP endpoints respond correctly
   - Example: `curl http://localhost:8000/api/v1/todos`

4. **Service Interface** (if exists)
   - Unified service runner works
   - Example: `make run ENV=dev`
   - Service management commands function

5. **Telegram Interface** (if exists)
   - Bot responds to messages
   - Commands work as documented

6. **Makefile Commands**
   - All documented `make` targets work
   - Example: `make status`, `make logs`, `make test`
   - README-documented commands must function

**Validation Method**:
- Test at least one flow per interaction method
- Confirm README.md documents all active methods
- Verify new additions don't break existing paths

**If Interaction Path Broken**:
- **BLOCKER**: Must be fixed before milestone merge
- Document in QA findings
- Create bug issue for Developer
- Verify fix before PR approval

**Example Failure Scenarios**:
- Adding API makes direct service imports fail
- New service wrapper prevents CLI script usage
- Framework dependency breaks standalone module use

---

### 7. Architectural Compliance

QA must verify that the implementation has not drifted from architectural intent.

**Required Checks**:
- Service boundaries are respected (no cross-service internal access)
- Contracts are honored (APIs, schemas, events)
- No accidental tight coupling introduced
- ADRs exist for non-trivial architectural changes
- Contract changes are documented and versioned
- Architecture diagrams still match implementation (if diagrams exist)

**How to Check**:
- Read `docs/ARCHITECTURE.md` (if exists)
- Review any ADRs in `docs/ADR_*.md`
- Inspect imports and dependencies
- Check if services reach into each other's internals
- Verify contracts in `shared/contracts/` match actual usage

**If Drift Found**:
- Document the drift in QA findings
- Assess severity: blocker vs. concern
- Flag for Architect review if significant

**QA flags drift; it does not redesign.**

---

## Inputs QA Relies On

QA treats the following as authoritative:
- issue descriptions and acceptance criteria
- milestone goals
- README and run instructions
- architecture docs
- commit history and PR notes

If expected behavior cannot be inferred from repo artifacts,
**that is a QA failure**.

---

## How QA Executes

### 1. Preparation
Before testing, QA must:
- read the milestone meta-issue
- read relevant issues
- read updated docs
- understand intended user flows

Ambiguity must be escalated immediately.

---

### 2. Execution Modes

QA may use:
- manual usage
- scripted flows
- exploratory testing
- log inspection
- reading test results

Priority is **signal over exhaustiveness**.

---

### 3. Reporting Findings

Findings must be explicit and reproducible.

Each finding should state:
- what was attempted
- expected behavior
- actual behavior
- severity (blocker / concern / note)

Findings are reported via:
- issue comments (preferred)
- new issues (if necessary)
- milestone summary notes

---

## Blocking vs Non-Blocking Findings

### Blocking
QA must block milestone merge if:
- the system cannot be started
- core flows do not work
- acceptance criteria are unmet
- documented usage paths are false

### Non-Blocking
QA may allow merge with notes if:
- minor UX roughness
- known, documented limitations
- non-critical edge cases

The distinction must be explicit.

---

## Bug Fix Workflow

When QA finds bugs during validation, follow this workflow:

### 1. Document Findings
- List all bugs in QA findings section
- For each bug, document:
  - What was attempted
  - Expected behavior
  - Actual behavior
  - Severity (blocker / concern / note)
  - Steps to reproduce

### 2. Create Bug Issues
For each **blocking** bug:
- Create a new GitHub issue using `ISSUE_TEMPLATE.md`
- Title: "Bug: [concise description]"
- Include reproduction steps
- Tag with milestone

This keeps QA findings durable and traceable, even though the same agent will implement the fix.

For **non-blocking** concerns, document in QA report only.

### 3. Switch to DEV Mode to Fix
- In **QA mode**, do not patch the code directly.
- Switch to **DEV mode** and implement the bug issue(s).
- Close each bug issue with the handoff comment (`ISSUE_HANDOFF_TEMPLATE.md`).
- Reference issues in commits (e.g. "Fixes #N") where appropriate.

### 4. QA Recheck (Targeted)
After fixes are complete:
- Switch back to **QA mode**.
- Run a **targeted recheck** on previously failing areas only.
- Do not repeat full milestone validation unless changes are broad.
- Updates QA report with recheck results:
  - "✅ Bug #N fixed and verified"
  - "❌ Bug #N still present" (create new issue or comment)
  - "⚠️ Bug #N fixed, but new issue found" (create separate issue)

### 5. Iterate if Needed
- If new bugs found during recheck: return to step 2
- If fixes verified: proceed to PR creation

**Critical**: QA must never silently fix bugs without issue tracking and proper commits.

---

## Milestone QA Summary and PR Creation

After validation is complete, QA produces a **Milestone QA Summary** covering:
- what was run
- what worked
- what failed
- known limitations
- issue state verification results
- overall confidence level (low / medium / high)

This summary is a **durable artifact**.

### Creating the Pull Request

If validation passes, the agent in **QA mode** **creates the milestone PR**:

1. Verify all issues closed with handoffs
2. Verify meta-issue updated
3. Verify branch is mergeable
4. Create PR using `PR_REQUEST_TEMPLATE.md`
5. Include QA summary in PR description
6. Reference milestone meta-issue
7. Tag human for review

**QA does not merge PRs. Human merges after review.**

---

## What QA Must NOT Do

In QA mode, the agent must not:
- add new features
- redefine scope
- silently fix issues
- introduce architectural changes
- merge to `main`

QA observes, validates, and reports.

---

## Operating Style

- Concrete, not theoretical
- User-oriented, not framework-oriented
- Explicit about uncertainty
- Comfortable saying “this does not work yet”

---

## Success Metric

The agent has succeeded in QA mode if:

> A stakeholder can stand up the system, run it, and understand its current state based on QA artifacts alone.

That is the bar.
