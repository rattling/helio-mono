# Process Architecture: Operating Profiles + Agentic Posture

**Status**: Proposed direction (post-M13 planning aid)  
**Primary scope**: operating-profile boundaries, invocation model, handoff semantics, and Helionyx posture toward agentic/multi-agent design

## Purpose

Clarify how Helionyx should evolve from:
- a set of explicit domain capabilities over a durable substrate,
- into a broader personal-assistant system with multiple user-facing assistant surfaces,
- without collapsing into vague agent ownership or hidden autonomy.

This document defines:
- what an operating profile is,
- how operating profiles relate to capabilities, workflows, and the durable substrate,
- how scheduled and interactive invocation should work,
- what Helionyx should borrow from emerging agentic paradigms,
- and where future milestone work could operationalize these ideas.

## Why This Doc Exists

Existing architecture docs describe important runtime slices well:
- message ingestion and extraction,
- orchestration and control-plane policy,
- runtime/deployment,
- planned calendar/email integration.

What they do not yet make explicit enough is the stable ownership model for a future system that includes:
- durable personal memory/state,
- multiple specialized domain capabilities,
- interactive general-assistant behavior,
- scheduled digests/reminders,
- explicit role/handoff behavior.

This note is intended to close that gap.

## Core Position

Helionyx is **not** primarily a classic multi-agent system.

Helionyx is a **durable capability substrate** with **bounded agentic orchestration** on top.

User-facing assistants may exist, but internally they should be modeled as
**operating profiles** rather than as hidden autonomous entities with unclear
ownership.

## Architectural Layers

### 1. Durable Substrate

The durable substrate is the system of record.

It owns:
- append-only event history,
- replay/rebuild semantics,
- durable evidence and auditability,
- derived read models,
- explainability surfaces.

Representative anchors:
- `services/event_store/file_store.py`
- `services/query/service.py`
- `shared/contracts/events.py`
- `shared/contracts/tasks.py`

### 2. Domain Capabilities

Domain capabilities are explicit bounded interfaces over a particular domain.

They own:
- domain contracts,
- normalization rules,
- deterministic mutations,
- read/query behavior,
- integration semantics for that domain.

Representative current and planned domains:
- capture/extraction,
- task/execution,
- attention/ranking,
- calendar,
- portfolio,
- delivery/rendering,
- explanation/explorer.

Representative anchors:
- `services/ingestion/service.py`
- `services/extraction/service.py`
- `services/task/service.py`
- `services/attention/service.py`

### 3. Orchestration + Control

This layer coordinates capability usage under explicit policy.

It owns:
- graph structure,
- sequencing/branching,
- checkpoint/resume,
- interrupts and escalation,
- routing across capabilities,
- policy-gated side effects.

Representative anchors:
- `services/orchestration/runtime.py`
- `services/control/policy.py`
- `docs/CONTROL_PLANE_POLICY_CONTRACT.md`

### 4. Interaction Adapters

Adapters receive triggers and present outputs.

They own:
- transport,
- request parsing,
- response rendering at the surface layer,
- adapter-specific command or UI wiring.

Representative anchors:
- `services/api/routes/`
- `services/adapters/telegram/`
- `web/src/`

### 5. Operating Profiles

Operating profiles sit conceptually above orchestration as the internal model
for user-facing assistant behavior.

They do **not** own data or side effects directly.

They own:
- which workflows may be invoked,
- which capabilities are in scope,
- default policy posture,
- interaction mode assumptions,
- routing/handoff behavior,
- explanation style and operator posture.

User-facing surfaces may call these “assistants”, but the internal term should
remain “operating profile” to avoid over-personification and ownership blur.

## Taxonomy

### Capability

A bounded domain interface with explicit contracts and durable evidence
semantics.

Examples:
- ingest message,
- extract objects,
- list tasks,
- fetch calendar events,
- normalize provider payloads,
- render digest,
- send Telegram message.

### Workflow

A bounded orchestration path that sequences capabilities to achieve an outcome.

Examples:
- urgent reminder,
- Monday digest,
- weekday day-ahead summary,
- interactive task update.

### Graph / Subgraph

The runtime structure used to implement a workflow.

Graphs and subgraphs are execution machinery, not user identities.

### Operating Profile

A named internal orchestration identity that selects which workflows and
capabilities can be invoked under what policy and interaction posture.

Operating profiles are architectural. Persona or tone alone is not.

## Operating Profile Contract

An operating profile should become a real architectural object only if it
changes execution semantics.

Useful fields could include:
- `profile_id`
- `display_name`
- `description`
- `interaction_modes` (`interactive`, `scheduled`, `api`)
- `allowed_capabilities`
- `workflow_entrypoints`
- `subgraph_allowlist`
- `policy_defaults`
- `delivery_permissions`
- `handoff_targets`
- `default_response_style`
- `explanation_level`

If a profile affects only wording or personality, it belongs in the UI/prompt
layer rather than architecture.

## Likely Near-Term Operating Profiles

These are non-binding but plausible profiles given current and near-future
Helionyx scope.

### 1. Capture Profile

Purpose:
- convert raw user input into durable recorded artifacts/objects.

Likely capabilities:
- message ingestion,
- object extraction,
- lightweight confirmation/explanation.

Likely triggers:
- free-form Telegram or chat input,
- API ingest calls,
- imported conversation history.

### 2. Task / Execution Profile

Purpose:
- manage actionable work as canonical task state.

Likely capabilities:
- task ingest,
- patch/complete/snooze/link,
- review queue,
- suggestions and explicit apply/reject flows.

Likely triggers:
- direct user request,
- follow-on from Capture Profile,
- reminder handling.

### 3. Cadence / Digest Profile

Purpose:
- produce scheduled or on-demand summaries and reminders.

Likely capabilities:
- fetch task/attention context,
- invoke calendar context,
- digest planning,
- render and deliver per channel.

Likely triggers:
- scheduler,
- explicit user request for daily/weekly/day-ahead summary.

### 4. Calendar Profile

Purpose:
- read and normalize calendar context as an explicit reusable domain surface.

Likely capabilities:
- provider fetch,
- normalization,
- degraded-mode reporting,
- event-summary preparation.

Likely triggers:
- Cadence Profile,
- General Chat Profile,
- operator/explanation flows.

### 5. Portfolio Profile

Purpose:
- ingest and interpret portfolio movements over the same substrate model.

Likely capabilities:
- provider/data-source fetch,
- normalization,
- state snapshots,
- movement alerts and summaries.

This should parallel Calendar structurally rather than becoming a bespoke
assistant stack.

### 6. General Chat Profile

Purpose:
- serve as the broad user-facing interactive assistant surface.

Likely capabilities:
- classify user intent,
- answer questions from durable state,
- route to narrower profiles/workflows,
- ask clarifying questions,
- return explanations or proposals.

Important constraint:
- broad read access does not imply unconstrained write authority.

### 7. Operator / Explanation Profile

Purpose:
- explain what the system has done and why.

Likely capabilities:
- control-room views,
- event/evidence lookup,
- orchestration visibility,
- rationale surfacing,
- degradation explanation.

## Invocation Model

### General Rule

Adapters receive triggers.

Triggers activate an operating profile.

The profile selects either:
- a direct bounded capability call, or
- a workflow implemented as a graph/subgraph composition.

Workflows invoke capabilities.

Capabilities operate over the durable substrate and external systems under
policy control.

### Scheduled Invocation

Scheduled flows should usually invoke a narrow operating profile directly
rather than routing through free-form general chat behavior.

Representative pattern:

1. Scheduler fires.
2. Cadence Profile is selected.
3. A workflow entrypoint is chosen (`urgent_reminder`, `weekday_day_ahead`,
   `monday_digest`, etc.).
4. Orchestration runs under policy.
5. The workflow calls task, attention, calendar, rendering, and delivery
   capabilities as needed.
6. Delivery outcomes and policy decisions are durably recorded.

This keeps scheduled behavior narrow, inspectable, and reproducible.

### Interactive Invocation

Interactive chat should usually enter through the General Chat Profile.

Representative pattern:

1. Message arrives through a chat adapter.
2. General Chat Profile classifies intent.
3. It chooses one of four paths:
   - answer directly from durable read/query capability,
   - invoke Capture Profile,
   - invoke a narrower workflow/profile,
   - request clarification or escalate.
4. If a narrower profile/workflow is invoked, it executes with explicit bounds.
5. The result is returned to the user through the original adapter.

This keeps General Chat as a router/synthesizer rather than a hidden owner of
all system behavior.

## Handoff Semantics

Handoffs should be explicit and typed.

Three useful handoff classes:

### 1. Routing Handoff

One profile routes a request to another profile or workflow.

Example:
- General Chat -> Task / Execution
- General Chat -> Cadence

### 2. Context Handoff

One profile or capability gathers structured context that another workflow
consumes.

Example:
- Calendar provides normalized events to Cadence digest planning.

### 3. Approval / Escalation Handoff

A workflow halts or pauses and returns control to another profile or operator
surface for explicit resolution.

Example:
- incomplete provider data,
- policy escalation,
- ambiguous delivery target,
- low-confidence plan quality.

Minimum structured handoff payload fields should likely include:
- `source_profile`
- `target_profile`
- `reason`
- `context_refs`
- `requested_action`
- `confidence`
- `policy_state`

## Relationship to Agentic / Multi-Agent Paradigms

Helionyx should borrow from emerging agentic patterns selectively.

### Recommended Borrowings

Borrow these ideas more aggressively over time:
- role-specialized reasoning,
- supervisor/router pattern,
- reusable subgraphs for common orchestration concerns,
- checkpoint/resume and explicit interrupt points,
- typed intermediate representations,
- explicit handoff contracts and stop conditions,
- critique/verification steps inside bounded workflows where valuable.

### Guardrails Against Over-Borrowing

Avoid making these foundational:
- free-form agent-to-agent conversation as core control flow,
- hidden mutable shared memory owned by agents,
- unconstrained model-owned side effects,
- persona-first decomposition that obscures real domain boundaries,
- vague “agent societies” without typed ownership or replay semantics.

### Practical Stance

Use agentic techniques inside bounded orchestration paths.

Do not let “multi-agent” replace:
- domain contracts,
- durable state authority,
- deterministic write boundaries,
- or explicit policy control.

## Operationalization Ideas

The ideas in this document do not need to be implemented all at once.

Two practical milestone shapes are plausible.

### Option A: One Foundation Milestone

Single milestone focused on introducing the operating-profile layer.

Possible scope:
- add operating-profile registry/config,
- add profile-aware routing at chat and scheduler entrypoints,
- define handoff payload contract,
- make one scheduled path and one interactive path profile-aware,
- expose profile name/routing in Control Room visibility.

Benefits:
- faster end-to-end proof of concept,
- lower process overhead.

Risk:
- may under-specify later agentic maturation concerns.

### Option B: Two Milestones

#### Candidate Milestone 15: Operating Profiles Foundation

Possible scope:
- define operating-profile contract and registry,
- introduce profile selection at adapter entrypoints,
- implement General Chat, Capture, Task / Execution, and Cadence as initial
  profiles,
- add explicit routing and handoff payloads,
- add profile-level policy defaults,
- add visibility for profile invocation/handoff events.

Desired outcome:
- assistants become an explicit internal architecture concept rather than an
  implicit prompt/product concept.

#### Candidate Milestone 16: Bounded Agentic Maturation

Possible scope:
- add reusable critique/verification nodes,
- introduce profile-aware subgraph libraries,
- support approval/interrupt handoffs across profiles,
- add typed plan/evidence bundles for interactive chat,
- formalize what is borrowed from multi-agent patterns and where it is allowed,
- expand operator visibility for pauses, escalations, and handoffs.

Desired outcome:
- Helionyx gains more agentic flexibility without losing durability or explicit
  authority boundaries.

### Recommendation

If calendar/email and other domain integrations remain the near-term priority,
Option B is cleaner.

It allows:
- M13 to finish integration and orchestration maturation,
- a dedicated follow-on milestone to make operating profiles explicit,
- and a subsequent milestone to introduce richer borrowed agentic patterns with
  bounded scope.

## Implementation Posture

The operating-profile layer should initially be light.

Prefer:
- configuration + explicit routing,
- typed handoff payloads,
- clear capability allowlists,
- visibility before heavy autonomy.

Avoid starting with:
- many conversational agents talking to each other,
- prompt-only role definitions with no runtime semantics,
- direct profile ownership of durable writes.

## Rule of Thumb

Use this ordering when making design choices:

1. Substrate first: what is the durable evidence/state model?
2. Capability second: what bounded interface owns the domain action?
3. Workflow third: how is the capability composed into a path?
4. Profile fourth: which operating profile may invoke it, in what mode?
5. Persona last: how should the user-facing surface describe it?

This keeps “assistant” language from distorting system ownership.

## Related Docs

- `docs/ARCHITECTURE.md`
- `docs/architecture/PROCESS_MESSAGE_PIPELINE.md`
- `docs/architecture/PROCESS_ORCHESTRATION_CONTROL.md`
- `docs/architecture/PROCESS_CALENDAR_EMAIL.md`
- `docs/CONTROL_PLANE_POLICY_CONTRACT.md`
- `docs/MILESTONES/MILESTONE13_DESIGN.md`

## Appendix A: Concrete Operating-Profile Contract + Registry Shape

This appendix is intentionally non-binding.

Its purpose is to provide a practical way to begin implementing the
operating-profile layer without forcing premature commitment to a large or
rigid framework.

### Design Goals

The first implementation should:
- be lightweight,
- fit the existing service/orchestration layout,
- make routing explicit,
- support scheduled and interactive invocation,
- and improve observability before adding heavy autonomy.

It should **not** require:
- many profile-specific prompts or model wrappers,
- conversational profile-to-profile exchanges,
- or a large standalone runtime separate from existing orchestration.

### Proposed Contract Shape

An initial internal contract could look conceptually like this:

```python
from dataclasses import dataclass, field
from typing import Literal

InteractionMode = Literal["interactive", "scheduled", "api"]


@dataclass(frozen=True)
class OperatingProfile:
    profile_id: str
    display_name: str
    description: str
    interaction_modes: tuple[InteractionMode, ...]
    allowed_capabilities: tuple[str, ...]
    workflow_entrypoints: tuple[str, ...] = ()
    subgraph_allowlist: tuple[str, ...] = ()
    handoff_targets: tuple[str, ...] = ()
    delivery_permissions: tuple[str, ...] = ()
    default_response_style: str = "direct"
    explanation_level: str = "standard"
    policy_defaults: dict[str, object] = field(default_factory=dict)
```

This structure is enough to support:
- profile selection,
- workflow routing,
- capability allowlisting,
- handoff validation,
- and profile-aware visibility.

### Minimal Companion Types

Two small companion objects would likely be useful immediately.

#### 1. Invocation Request

```python
@dataclass(frozen=True)
class ProfileInvocationRequest:
    profile_id: str
    trigger: str
    interaction_mode: InteractionMode
    requested_workflow: str | None = None
    requested_capability: str | None = None
    input_payload: dict[str, object] = field(default_factory=dict)
    conversation_id: str | None = None
    source_adapter: str | None = None
```

This gives adapters and schedulers a typed way to enter the profile layer.

#### 2. Handoff Payload

```python
@dataclass(frozen=True)
class ProfileHandoff:
    source_profile: str
    target_profile: str
    reason: str
    requested_action: str
    context_refs: tuple[str, ...] = ()
    confidence: float | None = None
    policy_state: dict[str, object] = field(default_factory=dict)
    payload: dict[str, object] = field(default_factory=dict)
```

This is enough to make routing and pause/escalation flows explicit without
needing profile-to-profile free-form chat.

### Registry Shape

An initial registry can stay static and in-process.

Conceptually:

```python
OPERATING_PROFILES: dict[str, OperatingProfile] = {
    "general_chat": OperatingProfile(...),
    "capture": OperatingProfile(...),
    "task_execution": OperatingProfile(...),
    "cadence": OperatingProfile(...),
    "calendar": OperatingProfile(...),
    "operator_explanation": OperatingProfile(...),
}
```

This should be enough for early milestones.

Later, if needed, it could evolve to:
- environment-aware configuration,
- feature-flagged profile availability,
- policy overlay from config,
- or profile metadata surfaced to UI/control-room views.

### Likely Code Placement

To fit the current repo shape with minimal disruption, a reasonable first cut
would be:

- `services/orchestration/profiles.py`
  - `OperatingProfile`
  - `ProfileInvocationRequest`
  - `ProfileHandoff`
  - static registry

- `services/orchestration/router.py`
  - profile selection helpers
  - validation of requested workflow/capability against the selected profile
  - handoff validation

- `services/orchestration/runtime.py`
  - continue owning graph execution
  - remain profile-agnostic where possible
  - optionally accept profile metadata for audit/visibility

- `services/control/policy.py`
  - remain the deterministic policy authority
  - optionally consume profile defaults as inputs, not as replacements for
    policy evaluation

- `services/adapters/telegram/message_handler.py`
  - likely first interactive adapter entrypoint to become profile-aware

- `services/adapters/telegram/scheduler.py`
  - likely first scheduled entrypoint to become profile-aware

- `services/api/routes/`
  - API-triggered workflows or chat endpoints can adopt the same invocation
    path later

This keeps profile selection near orchestration and adapters, rather than
burying it inside domain services.

### Capability Naming Posture

Capabilities should be named explicitly and independently of profiles.

Representative capability names could look like:
- `capture.ingest_message`
- `capture.extract_objects`
- `task.ingest`
- `task.patch`
- `task.complete`
- `task.snooze`
- `attention.get_today`
- `attention.get_week`
- `calendar.fetch_google`
- `calendar.fetch_zoho`
- `calendar.normalize_events`
- `digest.plan_day_ahead`
- `digest.plan_weekly`
- `delivery.telegram.send`
- `delivery.email.send`
- `explorer.lookup`
- `control.explain_run`

This matters because profiles should allowlist capabilities, not own them.

### Example Initial Registry Entries

#### General Chat

```python
OperatingProfile(
    profile_id="general_chat",
    display_name="General Chat",
    description="Broad interactive assistant surface over durable state.",
    interaction_modes=("interactive",),
    allowed_capabilities=(
        "explorer.lookup",
        "attention.get_today",
        "attention.get_week",
        "task.ingest",
        "task.patch",
        "capture.ingest_message",
        "capture.extract_objects",
    ),
    workflow_entrypoints=(
        "interactive_task_update",
        "interactive_day_ahead_summary",
    ),
    handoff_targets=(
        "capture",
        "task_execution",
        "cadence",
        "calendar",
        "operator_explanation",
    ),
    default_response_style="direct",
    explanation_level="standard",
)
```

#### Cadence

```python
OperatingProfile(
    profile_id="cadence",
    display_name="Cadence",
    description="Scheduled and on-demand digest/reminder flows.",
    interaction_modes=("scheduled", "interactive", "api"),
    allowed_capabilities=(
        "attention.get_today",
        "attention.get_week",
        "calendar.fetch_google",
        "calendar.fetch_zoho",
        "calendar.normalize_events",
        "digest.plan_day_ahead",
        "digest.plan_weekly",
        "delivery.telegram.send",
        "delivery.email.send",
    ),
    workflow_entrypoints=(
        "urgent_reminder",
        "weekday_day_ahead",
        "monday_digest",
    ),
    handoff_targets=("calendar", "operator_explanation"),
    delivery_permissions=("telegram", "email"),
    default_response_style="concise",
    explanation_level="high",
)
```

These examples are intentionally narrow and concrete.

### First Implementation Moves

The smallest useful implementation path would likely be:

1. Add static registry and contract types.
2. Make `scheduler.py` invoke the Cadence profile explicitly.
3. Make `message_handler.py` invoke the Capture profile explicitly.
4. Add profile metadata to orchestration/control-room visibility.
5. Add typed handoff payloads before adding richer interrupt/resume behavior.

That sequence provides architectural clarity early without requiring a large
rewrite.

### What Can Wait

These ideas are useful, but should probably wait until the first profile layer
is proven valuable:
- dynamic profile loading,
- profile-specific prompt stacks,
- profile-to-profile model conversations,
- automatic profile learning/adaptation,
- deep profile hierarchies.

### Implementation Rule of Thumb

If a new behavior can be expressed as:
- existing substrate,
- explicit capability,
- bounded workflow,
- selected by a profile,

then it fits the operating-profile model.

If it requires a profile to own hidden state, hidden writes, or unbounded
cross-domain authority, it is probably violating the intended architecture.