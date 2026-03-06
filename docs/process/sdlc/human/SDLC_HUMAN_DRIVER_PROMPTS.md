# SDLC Human Driver Prompts

These prompts are intentionally short.
They set mode + context for the session; detailed execution rules remain in `.github/copilot-instructions.md` and the mode guides.

Operational companion docs:
- `docs/process/sdlc/agent/SDLC_AGENT_EXECUTION_RUNBOOK.md`
- `docs/process/sdlc/SDLC_PROCESS_CHANGELOG.md`
- `docs/process/sdlc/human/SDLC_HUMAN_PROCESS_GUIDE.md`

---

## Prompt 1 — ARCH (plan the milestone)

```text
MODE: ARCH
MILESTONE: <N + name>

See attached charter.

Do ARCH-mode work per repo instructions:
- restate goal/scope/non-goals
- identify needed contracts/ADRs
- create milestone issues + meta-issue
```

---

## Prompt 2 — DEV → QA (implement, validate, PR)

```text
MODE: DEV then QA
MILESTONE: <N + name>

Input: Use the github milestone meta-issue + all milestone issues listed in it as the source of truth.

Session status context (required - use one of these):
- Starting fresh: "Starting work on Milestone. Dev/test. No work done yet."
- Continuing: "Continuing Milestone <N>. Dev/test. Current focus is issue #<id>. <x>/<total> issues completed."

Issue source-of-truth rule:
- Derive milestone issue list from the meta-issue checklist items only.
- Do not infer full issue set from milestone-title search results.

Do DEV-mode implementation, then switch to QA-mode validation.

Critical QA rule: if you find a bug in QA mode, create a bug issue first; then switch to DEV mode to fix; then return to QA mode to recheck.

If QA passes, create the milestone PR.
```

---

## Prompt 3 — Process Check (audit and tune workflow docs)

```text
MODE: ARCH then DEV
FOCUS: Process docs audit

Goal: Review process documentation chain end-to-end for productivity and consistency.

Scope:
- .github/copilot-instructions.md
- docs/process/sdlc/agent/SDLC_AGENT_AUTHORITY_MAP.md
- docs/process/sdlc/agent/SDLC_AGENT_SESSION_BOOTSTRAP.md
- docs/process/sdlc/agent/SDLC_AGENT_EXECUTION_RUNBOOK.md
- .github/WORKFLOW.md
- docs/process/sdlc/agent/modes/{architect,developer,qa}.agent.md
- docs/process/sdlc/agent/templates/* (especially issue/PR/handoff templates)

Required outcomes:
- identify duplication/conflicts/stale references
- prefer canonical ownership + short cross-links
- preserve feature delivery quality, architecture discipline, and test rigor
- reduce token/context waste from repeated rule text
- update docs/templates as needed and record changes in docs/process/sdlc/SDLC_PROCESS_CHANGELOG.md

Deliverables:
- concise summary of findings
- exact files updated and why
- remaining recommendations (if any)
```
