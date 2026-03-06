# Process Changelog

Tracks durable updates to SDLC/process guidance (not per-run findings).

## 2026-03-06

### Added
- Milestone execution runbook with mandatory source-of-truth and progression loop:
  - `docs/process/MILESTONE_EXECUTION_RUNBOOK.md`

### Updated
- `.github/copilot-instructions.md`
  - checklist-derived milestone issue set is authoritative
  - mandatory per-issue durable loop
  - PR body preflight requirement
  - no-default CI polling posture
- `docs/process/SESSION_BOOTSTRAP.md`
  - explicit checklist extraction during rehydration
  - explicit starting/continuing status context
- `.github/agents/developer.agent.md`
  - in-order issue execution and mandatory durable loop
  - PR-body preflight before publish/update
- `.github/agents/templates/TWO_PROMPTS.md`
  - required session status context
  - explicit checklist-source rule
- `.github/WORKFLOW.md`
  - PR preflight added to PR creation phase
  - CI polling posture documented
