# Milestone 13 Design --- Calendar + Email on Full-Use LangGraph

## Purpose

This document translates the Milestone 13 charter into concrete architectural
choices for implementation.

It focuses on:
- where agentic behavior should live,
- what remains deterministic,
- how LangGraph should be used beyond M12 baseline wiring,
- how existing M12 flows and new M13 flows should converge on shared graph
  patterns.

This is a design companion to `docs/MILESTONES/MILESTONE13_CHARTER.md`, not a
replacement.

------------------------------------------------------------------------

## Design Decision Summary

### 1) LangGraph is the sole agentic orchestrator

- Helionyx should not maintain a permanent split between a “deterministic
  orchestrator” and a “LangGraph orchestrator”.
- LangGraph owns workflow sequencing, branching, interrupts, retries, and
  checkpoint/resume behavior.
- Deterministic code remains in the system as tools, adapters, policy
  enforcement, rendering, normalization, and state persistence.

Reason:
- avoids architectural split-brain,
- keeps future workflows composable,
- aligns implementation with M12/M13 architecture intent.

### 2) Deterministic services remain side-effect authority

- Calendar adapters fetch data.
- Policy evaluator decides allow/block/escalate.
- Renderers produce Telegram/email output.
- Delivery adapters send messages.
- Event store remains durable source of truth.

Reason:
- preserves inspectability,
- keeps irreversible actions bounded and testable,
- prevents hidden model-driven mutation.

### 3) M13 should mature LangGraph usage, not just add integrations

M12 established a working LangGraph runtime boundary.
M13 should make it meaningfully more capable by adding:
- reusable subgraphs,
- explicit interrupt points,
- checkpoint/resume,
- richer branching/fan-out,
- shared graph primitives used across old and new flows.

------------------------------------------------------------------------

## Architectural End State for M13

By the end of M13, Helionyx should have:

- one orchestration plane powered by LangGraph,
- one control plane that remains deterministic and fail-closed,
- one durable event substrate recording run and domain evidence,
- shared graph building blocks reused by:
  - daily digest,
  - weekly digest,
  - urgent reminder,
  - Monday weekly+day-ahead digest,
  - Tuesday-Friday day-ahead digest,
  - Telegram delivery,
  - email delivery.

------------------------------------------------------------------------

## What Becomes More Agentic

The orchestration layer should become more agentic in these areas:

- multi-step planning of digest composition,
- reasoning over multiple context sources,
- deciding what information is important enough to surface,
- choosing escalation vs proceed paths when quality or policy conditions are not met,
- handling interrupted or degraded external-provider flows.

This does **not** mean unconstrained autonomy.
It means agentic reasoning over bounded, deterministic capabilities.

------------------------------------------------------------------------

## What Must Stay Deterministic

These concerns must remain deterministic and outside agent discretion:

- policy enforcement,
- provider auth/config validation,
- provider normalization contracts,
- side-effect execution,
- dedup and cooldown logic,
- durable event persistence,
- read-model projection and replay semantics.

This boundary is non-negotiable.

------------------------------------------------------------------------

## Shared Graph Model

M13 should standardize a reusable graph shape.

### Core reusable subgraphs

1. `policy_gate_subgraph`
- Validates workflow/tool/scope/budget envelope.
- Emits allow/block/escalate evidence.
- Can interrupt on escalation if human approval is required.

2. `context_gather_subgraph`
- Fetches task/attention context.
- Fetches calendar-provider context.
- Handles partial provider failure with explicit degraded-state outputs.

3. `normalize_merge_subgraph`
- Converts provider payloads to a single internal contract.
- Merges calendar and task context into digest/planning state.

4. `digest_plan_subgraph`
- Selects sections, priorities, warnings, conflicts, and summaries.
- Produces structured digest payload before channel-specific rendering.

5. `render_subgraph`
- Produces Telegram and email render payloads from shared structured digest state.

6. `delivery_subgraph`
- Performs deterministic channel send.
- Records attempts, success, failures, dedup, and terminal outcomes.

------------------------------------------------------------------------

## Representative M13 Flow: Monday Digest

The Monday digest should be the flagship M13 graph.

### Proposed node sequence

1. `run_start`
2. `policy_gate`
3. `fetch_tasks`
4. `fetch_attention`
5. `fetch_google_calendar`
6. `fetch_zoho_calendar`
7. `normalize_calendar`
8. `merge_context`
9. `plan_weekly_digest`
10. `quality_or_policy_checkpoint`
11. `render_telegram`
12. `render_email`
13. `deliver_telegram`
14. `deliver_email`
15. `run_finish`

### Important branching behaviors

- Provider read failure:
  - continue in degraded mode if policy permits,
  - otherwise escalate/interrrupt.
- Poor digest confidence or missing critical context:
  - interrupt for approval or produce reduced deterministic digest.
- Channel-specific failure:
  - allow partial success if one channel succeeds and policy permits.

------------------------------------------------------------------------

## Interrupt and Approval Model

M13 should introduce explicit operator-visible interrupt points.

Interrupts are appropriate when:
- policy outcome is `escalated`,
- external provider data is incomplete in a materially risky way,
- output quality gate fails,
- delivery would proceed with ambiguous or conflicting schedule interpretation.

Expected behavior:
- run enters paused/interrupted state,
- reason is recorded durably,
- Control Room can expose the pause reason and resume action,
- resume continues from checkpoint rather than restarting full flow.

------------------------------------------------------------------------

## Checkpoint and Resume

M13 should use LangGraph checkpointing for at least one representative flow.

Checkpointing is valuable for:
- long-running multi-provider fetches,
- human approval pauses,
- partial recovery after transient provider or delivery failures,
- deterministic replay boundary alignment.

Checkpointing does not replace the event log.
The event log remains the durable system-of-record; checkpointing is runtime
continuation state.

------------------------------------------------------------------------

## Delivery Model

M13 introduces multi-channel delivery.

Design rule:
- planning is channel-agnostic,
- rendering is channel-specific,
- delivery is deterministic per channel.

This means the graph should produce a shared digest structure first, then branch
to Telegram/email renderers and adapters.

Benefits:
- fewer duplicated planning paths,
- clearer parity between channels,
- easier future addition of other delivery surfaces.

------------------------------------------------------------------------

## Event and Visibility Expectations

M13 should extend visibility, not hide graph complexity.

At minimum, users/operators should be able to inspect:
- run started / interrupted / resumed / finished / failed,
- provider fetch outcomes,
- normalization/merge degradation states,
- policy outcomes and escalation reasons,
- delivery attempts and per-channel results.

Control Room should remain the main operator-facing transparency surface.

------------------------------------------------------------------------

## Implementation Boundaries

### Orchestration layer owns
- graph structure,
- node transitions,
- branch selection,
- interrupt/resume mechanics,
- orchestration event emission.

### Domain services own
- provider calls,
- normalization,
- task and attention retrieval,
- rendering,
- deterministic delivery.

### Control plane owns
- safety envelope validation,
- allow/block/escalate decisions,
- budget/tool/scope limits.

------------------------------------------------------------------------

## Acceptance-Driven Design Checks

M13 should not be considered complete unless all of these are true:

- Existing M12 digest/reminder flows run through shared M13 graph primitives.
- At least one representative flow supports interrupt + resume from checkpoint.
- Calendar-aware digest planning uses multi-source branching/merge structure.
- Telegram and email delivery share planning state but use separate deterministic
  render/delivery nodes.
- Control Room can expose pause/failure/degraded reasons clearly.

------------------------------------------------------------------------

## Explicit Non-Goals

M13 should not introduce:
- broad unconstrained multi-agent systems,
- model-controlled irreversible writes,
- hidden autonomous behavior outside policy and audit surfaces,
- separate competing orchestration engines.

------------------------------------------------------------------------

## Open Questions for Implementation Planning

These should be resolved when creating the M13 issue set:

1. What runtime checkpoint store should back LangGraph in this repo?
2. What exact interrupt/resume operator surface should be exposed first?
3. Should degraded calendar-provider reads still permit Telegram delivery by default?
4. What minimal confidence/quality gate should block or escalate digest delivery?
5. Should email delivery success be required for a run to count as fully successful,
   or can it be partial success with explicit evidence?
