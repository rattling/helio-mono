# Process Changelog

Tracks durable updates to SDLC/process guidance (not per-run findings).

## 2026-03-06

### Process Audit (Canonicalization + Token Reduction)
- `.github/copilot-instructions.md`
  - Reduced duplicated long-form workflow/mode/rehydration text that was already canonical in `SDLC/agent/*` and `SDLC/WORKFLOW.md`.
  - Preserved Helionyx hard invariants (repo identity, `.venv` enforcement, milestone branch model, required tests, QA gate, PR preflight, escalation, runnable-system posture).
  - Added a compact canonical-reference section to direct operators/agents to single-source docs.
- `.github/ISSUE_TEMPLATE/implementation_issue.yml`
  - Added canonical-source header pointing to `SDLC/agent/templates/ISSUE_TEMPLATE.md`.
- `.github/ISSUE_TEMPLATE/milestone_meta_issue.yml`
  - Added canonical-source header pointing to `SDLC/agent/templates/MILESTONE_META_ISSUE_TEMPLATE.md`.

Intent:
- Reduce token/context waste in high-frequency entrypoint docs.
- Keep `.github` as bridge/discovery surface with explicit links to SDLC canonical ownership.
- Preserve architecture discipline, test rigor, and delivery quality constraints.

### Process Guide Consistency Refresh
- `SDLC/human/SDLC_HUMAN_PROCESS_GUIDE.md`
  - Added explicit pointer to `SDLC/SDLC_GITHUB_BRIDGE_POLICY.md` in the canonical map.
  - Expanded the recommended stale-reference grep to include legacy bridge paths (`.github/WORKFLOW.md`, `.github/agents`, `TWO_PROMPTS`) in addition to template-name drift checks.

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
- Moved engineering constitution to SDLC root and updated all cross-references:
  - `SDLC/ENGINEERING_CONSTITUTION.md`
- Updated process template compliance checks to validate SDLC template paths:
  - `SDLC/scripts/check_workflow_templates.py`

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
- `SDLC/WORKFLOW.md`
  - PR preflight added to PR creation phase
  - CI polling posture documented
