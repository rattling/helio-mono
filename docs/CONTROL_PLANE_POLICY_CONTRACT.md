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

## Policy Envelope (v0)

Each run must resolve an effective policy envelope before execution starts.

```json
{
  "policy_version": "0.1",
  "mode": "deterministic|shadow|bounded",
  "allowlisted_tools": ["query", "task", "telegram"],
  "allowlisted_integrations": [],
  "side_effect_scope": {
    "read": true,
    "write": ["notifications"],
    "forbidden": ["task_delete", "external_write"]
  },
  "budgets": {
    "max_runtime_seconds": 60,
    "max_llm_tokens": 12000,
    "max_llm_cost_usd": 0.25,
    "max_tool_calls": 20
  },
  "retry_policy": {
    "max_attempts": 2,
    "backoff": "exponential",
    "fallback": "deterministic_summary"
  },
  "escalation": {
    "on_policy_violation": "hard_stop",
    "on_budget_exceeded": "hard_stop",
    "on_ambiguous_write": "require_human"
  }
}
```

## Deterministic Enforcement Rules

1. Fail closed: missing policy fields default to deny.
2. No direct side effects from agent nodes without policy approval.
3. Write operations require explicit scope match.
4. Out-of-budget execution halts the run.
5. Policy violations are non-retriable unless classified transient by control rules.

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
  `docs/ADR/`.
- Backward-incompatible policy changes should bump contract version and note
  migration requirements in milestone docs.

## Related Docs

- `docs/ARCHITECTURE.md`
- `docs/Milestones/MILESTONE12_CHARTER.md`
- `docs/Milestones/MILESTONE13_CHARTER.md`
- `docs/ADR/`