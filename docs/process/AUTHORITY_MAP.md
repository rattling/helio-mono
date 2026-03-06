# Authority Map

## Purpose

This document defines instruction precedence and conflict handling for Helionyx workflow execution.

For the human-oriented process overview and flow diagrams, see `docs/process/SDLC_PROCESS_GUIDE.md`.

Use this whenever guidance appears to conflict across prompts, role docs, templates, and project docs.

Productivity intent: resolve ambiguity quickly with minimal reading, then continue execution.

## Instruction Precedence (Highest to Lowest)

1. Platform/system safety rules (non-negotiable)
2. Human user explicit request for current session
3. Repository hard rules in `.github/copilot-instructions.md`
4. Workflow and mode operating guides:
   - `.github/WORKFLOW.md`
   - `.github/agents/architect.agent.md`
   - `.github/agents/developer.agent.md`
   - `.github/agents/qa.agent.md`
5. Milestone/issue artifacts:
   - milestone charter
   - milestone meta-issue
   - issue body + acceptance criteria
6. Templates and checklists in `.github/agents/templates/`
7. Agent defaults (when not in conflict with items above)

If two sources at the same precedence conflict, choose the newer, more specific source and record the assumption in issue or PR notes.

## Mode Authority Boundaries

### ADHOC Mode
- Scope: operator help, diagnostics, local edits requested directly by the human.
- No mandatory issue/PR workflow unless explicitly requested.
- Must still respect secrets handling, repo identity checks when relevant, and `.venv` usage.

### ARCH Mode
- Owns: milestone planning, boundary setting, contract evolution, architecture artifacts.
- Must not perform broad implementation unrelated to architecture tasks.

### DEV Mode
- Owns: scoped issue implementation only.
- Must not redesign architecture without escalation.

### QA Mode
- Owns: runnability and acceptance validation, milestone gate validation, PR readiness.
- Must not silently patch defects; must raise bug issue and route through DEV.

## Conflict Resolution Protocol

When conflict/ambiguity appears:

1. Identify all conflicting instructions and their precedence level.
2. Apply higher-precedence source.
3. If still ambiguous, stop and escalate using `BLOCKER_TEMPLATE.md`.
4. Record the decision path in durable artifacts (issue comment, handoff note, or PR note).

Never silently choose a lower-precedence rule when a higher-precedence rule applies.

## Token-Efficient Defaults

Default to the smallest context set that can safely unblock execution:

1. `docs/process/SESSION_BOOTSTRAP.md` (mode + startup checks)
2. Active mode guide (`.github/agents/*.agent.md`)
3. Current issue or milestone meta-issue

Expand context only if one of these is true:
- Contract/interface changes are required
- Invariant or scope conflict is detected
- Verification expectations are unclear

When expansion is needed, read in this order:
1. `.github/WORKFLOW.md`
2. `.github/copilot-instructions.md`
3. Relevant architecture/project docs

## Fast Examples

- If a user asks for a quick one-off operational check, use ADHOC mode even if structured workflow exists.
- If a user asks to "follow workflow" or "architect mode", structured workflow rules apply.
- If an issue lacks required test commands, ARCH/DEV must update issue definition before implementation proceeds.
