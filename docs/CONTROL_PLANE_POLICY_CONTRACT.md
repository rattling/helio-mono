# Helionyx Control-Plane Policy Contract

**Version**: 0.1 (Living Draft)  
**Last Updated**: March 5, 2026  
**Status**: Active (M12 Baseline)

## Purpose

Define the deterministic policy envelope that governs agentic orchestration runs.
This contract is intentionally versioned and expected to evolve frequently during
M12+ development.

## Scope

This contract applies to all orchestration runs that may perform bounded
reasoning, call tools, or trigger side effects through Helionyx adapters.

It governs:
- tool/integration allowlists
- side-effect scope
- budget constraints (time/tokens/cost)
- retry/fallback posture
- escalation behavior
- audit artifact requirements

## Policy Envelope (v0, M12 runtime)

Each run must resolve an effective policy envelope before execution starts.

```json
{
  "workflow_name": "daily_digest|weekly_digest|urgent_reminder",
  "reminder_type": "task_daily_digest|task_weekly_digest|task_urgent_reminder",
  "tool_name": "telegram.send_message",
  "side_effect_scope": "telegram:notify",
  "budgets": {
    "runtime_seconds": 20,
    "tool_calls": 1,
    "estimated_tokens": 250,
    "estimated_cost_usd": 0.02
  }
}
```

## Deterministic Enforcement Rules

1. Fail closed: missing policy fields default to deny.
2. No direct side effects from agent nodes without policy approval.
3. Write operations require explicit scope match.
4. Out-of-budget execution halts the run.
5. Policy violations are non-retriable unless classified transient by control rules.

Deterministic evaluator reason codes (non-exhaustive):
- Blocked: `missing_field:*`, `workflow_not_allowed`, `reminder_type_not_allowed`, `tool_not_allowed`, `scope_not_allowed`
- Escalated: `runtime_budget_exceeded`, `tool_call_budget_exceeded`, `token_budget_exceeded`, `cost_budget_exceeded`

## Required Audit Artifacts

Every orchestration run must produce enough artifacts/events to reconstruct:
- who/what initiated the run
- effective policy envelope used
- tools attempted and outcomes
- blocked actions and reasons
- delivery attempts and dedup fingerprints
- terminal run status (succeeded/failed/escalated)

## Change Management

- Treat this document as a living contract during M12.
- Any non-trivial policy field addition/removal should include an ADR in
  `docs/ADRS/`.
- Backward-incompatible policy changes should bump contract version and note
  migration requirements in milestone docs.

## Related Docs

- `docs/ARCHITECTURE.md`
- `docs/MILESTONES/MILESTONE12_CHARTER.md`
- `docs/MILESTONES/MILESTONE13_CHARTER.md`
