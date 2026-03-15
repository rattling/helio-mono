# Milestone 15 --- Operating Profiles Foundation

## Objective

Introduce a first-class **operating-profile layer** that makes assistant-like
runtime behavior explicit without turning Helionyx into a vague or unconstrained
multi-agent system.

This milestone introduces:
- operating profiles as explicit internal orchestration identities,
- profile-aware routing at selected adapter entrypoints,
- typed handoff payloads between profiles/workflows,
- profile-level visibility in orchestration and operator surfaces,
- and a clean bridge between current Helionyx capabilities and future
  user-facing assistant experiences.

The target outcome is not “many assistants talking to each other,” but
**clear runtime ownership, explicit routing, and bounded authority**.

------------------------------------------------------------------------

## Why This Milestone

Helionyx already has:
- a durable substrate,
- explicit domain capabilities,
- a control plane,
- and a growing orchestration layer.

What it does not yet make first-class is the internal concept that sits between
user-facing assistant language and actual runtime behavior.

Without that layer, future work risks becoming unclear in several ways:
- user-facing assistants may be described as if they own domain state,
- routing between interactive chat and scheduled flows may remain implicit,
- profile/role handoffs may be buried inside orchestration or prompt logic,
- and broader assistant behavior may drift toward vague “agentic” patterns
  without explicit system boundaries.

Milestone 15 introduces operating profiles to solve that problem.

------------------------------------------------------------------------

## What the User Gets

By the end of this milestone, the user should experience:

- clearer and more consistent behavior across interactive and scheduled flows,
- more legible assistant routing when a request belongs to a specific domain,
- better explanation of which operating mode/profile handled a task,
- and no regression in existing substrate-first durability or control behavior.

User-facing surfaces may still call these profiles “assistants,” but the
internal runtime will use explicit operating-profile boundaries.

------------------------------------------------------------------------

## Core Product Semantics

### Operating profiles are execution identities, not data owners

- Operating profiles decide which workflows and capabilities can be used in a
  given interaction mode.
- They do not own durable state directly.
- They do not bypass domain capability boundaries.

### Capabilities remain explicit and deterministic

- Domain capabilities remain the authoritative owners of domain contracts,
  normalization rules, deterministic mutations, and read-model behavior.
- Operating profiles select and constrain capability usage; they do not replace
  capabilities.

### Orchestration remains bounded under policy

- Operating profiles route into workflows implemented with existing
  orchestration/runtime patterns.
- Profile defaults may influence policy inputs, but the deterministic control
  plane remains authoritative for allow/block/escalate behavior.

### Persona remains a presentation concern

- Internal operating-profile semantics should remain distinct from UI-level tone,
  naming, or branding.
- A user-facing assistant persona may map to an operating profile, but persona
  alone is not architecture.

------------------------------------------------------------------------

## Milestone Scope

### 1) Operating Profile Contract + Registry

- Define an explicit internal contract for operating profiles.
- Introduce a lightweight in-process registry for profile definitions.
- Include at least the fields needed for:
  - interaction mode,
  - allowed capabilities,
  - workflow entrypoints,
  - handoff targets,
  - policy defaults,
  - and explanation posture.

Initial profile candidates:
- `general_chat`
- `capture`
- `task_execution`
- `cadence`
- `operator_explanation`

Calendar and portfolio profiles may remain planned if not yet runtime-ready.

### 2) Profile-Aware Entry Routing

- Make at least one interactive adapter entrypoint profile-aware.
- Make at least one scheduled entrypoint profile-aware.
- Ensure routing logic explicitly selects a profile before invoking workflows or
  direct bounded capability calls.

Representative targets:
- Telegram message handling for interactive capture/general-chat routing
- scheduler-triggered digest/reminder flows for cadence routing

### 3) Typed Handoff Semantics

- Define a typed handoff payload between profiles/workflows.
- Support at least routing handoff and context handoff semantics.
- Optionally support approval/escalation handoff scaffolding where it improves
  future interrupt/resume readiness.

### 4) Visibility and Auditability

- Surface profile invocation metadata in orchestration visibility or control-room
  payloads.
- Make it inspectable which profile handled a run or request.
- Ensure profile routing decisions remain reconstructable from durable evidence
  or explicit event metadata.

### 5) Non-Regressive Integration with Existing Flows

- Preserve existing digest/reminder semantics.
- Preserve existing task/capture behavior where profile routing is introduced.
- Do not force a broad general-chat implementation as part of this milestone.

------------------------------------------------------------------------

## Product Acceptance Criteria

- Operating profiles are represented explicitly in code/config rather than only
  in prompts or docs.
- At least one interactive entrypoint and one scheduled entrypoint are profile-aware.
- Profile selection constrains which workflows/capabilities may be invoked.
- Typed handoff payloads exist for profile/workflow routing.
- Profile invocation is visible in operator-facing surfaces or durable audit data.
- Existing user-visible behavior remains non-regressive.

------------------------------------------------------------------------

## How to Test (Operator Checklist)

1. Validate registry and routing behavior
	- Confirm operating profiles are declared in one explicit runtime location
	- Confirm an interactive request resolves to the expected profile
	- Confirm a scheduled digest/reminder resolves to the expected profile

2. Validate capability/workflow bounds
	- Attempt a profile-incompatible workflow or capability path
	- Confirm it is rejected before execution proceeds
	- Confirm compatible routes continue normally

3. Validate handoff behavior
	- Trigger a request that routes from general chat to a narrower profile
	- Confirm handoff payload shape is explicit and inspectable
	- Confirm result returns through the originating adapter path

4. Validate visibility
	- Inspect control-room or orchestration run output
	- Confirm profile identity is visible for relevant runs/requests
	- Confirm profile-aware routing is reconstructable from durable evidence

5. Validate non-regression
	- Re-run existing digest/reminder and task/capture scenarios
	- Confirm user-visible behavior remains stable

------------------------------------------------------------------------

## Non-Goals

- No broad unconstrained multi-agent conversations
- No profile-owned durable state outside substrate/capability boundaries
- No major persona system or branding framework
- No automatic profile learning/adaptation in this milestone
- No replacement of deterministic policy enforcement with prompt-defined rules

------------------------------------------------------------------------

## Risks and Mitigations

- **Risk: Operating profiles become thin labels with no runtime meaning**
	- Mitigation: Require routing, allowlists, and visibility semantics in the
	  first implementation.

- **Risk: Over-abstracting before enough real use cases exist**
	- Mitigation: Start with a static registry, a small set of profiles, and two
	  concrete entrypoints.

- **Risk: Confusion between persona and execution identity**
	- Mitigation: Keep UI-level assistant naming separate from internal operating
	  profile semantics.

- **Risk: Profile layer bypasses capability boundaries**
	- Mitigation: Treat capabilities as the only valid owners of domain mutations
	  and domain contracts.

------------------------------------------------------------------------

## Forward Path (Post-M15)

After this milestone, Helionyx can safely expand to a follow-on milestone for
bounded agentic maturation, such as:
- reusable critique/verification nodes,
- richer profile-aware subgraph libraries,
- approval/interrupt handoffs,
- typed plan/evidence bundles for interactive chat,
- and more explicit borrowing from multi-agent paradigms where it improves
  bounded orchestration.

Any such expansion should preserve:
- substrate-first durability,
- explicit capability ownership,
- deterministic control-plane authority,
- and inspectable runtime behavior.