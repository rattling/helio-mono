# Process Changelog

Tracks durable updates to SDLC/process guidance (not per-run findings).

## 2026-03-06

### Renamed / Reorganized
- Moved SDLC process docs into audience-based structure:
  - Agent docs: `SDLC/agent/SDLC_AGENT_{AUTHORITY_MAP,SESSION_BOOTSTRAP,EXECUTION_RUNBOOK}.md`
  - Human docs: `SDLC/human/SDLC_HUMAN_{PROCESS_GUIDE,DRIVER_PROMPTS}.md`
- Replaced `.github/agents/templates/TWO_PROMPTS.md` with `SDLC/human/SDLC_HUMAN_DRIVER_PROMPTS.md`.
- Added `SDLC/README.md` as audience/naming index.

### Added
- Milestone execution runbook with mandatory source-of-truth and progression loop:
  - `SDLC/agent/SDLC_AGENT_EXECUTION_RUNBOOK.md`
- Human-oriented SDLC process guide with flow diagrams, key file map, and update procedure:
  - `SDLC/human/SDLC_HUMAN_PROCESS_GUIDE.md`
- SDLC↔GitHub bridge policy defining path-sensitive `.github` entrypoints and canonical SDLC ownership:
  - `SDLC/SDLC_GITHUB_BRIDGE_POLICY.md`

### Updated
- `.github/copilot-instructions.md`
  - checklist-derived milestone issue set is authoritative
  - mandatory per-issue durable loop
  - PR body preflight requirement
  - no-default CI polling posture
- `SDLC/agent/SDLC_AGENT_SESSION_BOOTSTRAP.md`
  - explicit checklist extraction during rehydration
  - explicit starting/continuing status context
- `SDLC/agent/modes/developer.agent.md`
  - in-order issue execution and mandatory durable loop
  - PR-body preflight before publish/update
- `SDLC/human/SDLC_HUMAN_DRIVER_PROMPTS.md`
  - required session status context
  - explicit checklist-source rule
  - added reusable "Prompt 3 — Process Check" audit prompt
- `SDLC/agent/SDLC_AGENT_AUTHORITY_MAP.md`
  - links to SDLC process guide for human-oriented orientation
- `SDLC/agent/SDLC_AGENT_EXECUTION_RUNBOOK.md`
  - links to SDLC process guide for diagrams/update guidance
- `.github/WORKFLOW.md`
  - PR preflight added to PR creation phase
  - CI polling posture documented
