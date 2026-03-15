# Milestone 16 --- Bounded Agentic Maturation

## Objective

Expand Helionyx from profile-aware routing into richer **bounded agentic
execution** by introducing reusable orchestration subgraphs, typed
intermediate reasoning artifacts, critique/verification steps, and
approval/interrupt/resume behavior across interactive and scheduled flows.

This milestone introduces:
- profile-aware reusable subgraph libraries,
- typed plan/evidence/handoff bundles,
- bounded critique and verification nodes,
- explicit approval, interrupt, and resume semantics,
- and richer operator visibility into why a workflow proceeded, paused,
  degraded, or escalated.

The target outcome is not “more agents for the sake of it,” but
**better reasoning, better recovery, and better explainability inside explicit
runtime bounds**.

------------------------------------------------------------------------

## Why This Milestone

By the end of Milestone 15, Helionyx should have:
- explicit operating profiles,
- profile-aware routing,
- typed handoff scaffolding,
- and clearer execution ownership.

That solves the “who is acting and what are they allowed to invoke?” problem.

The next problem is different:
- how should these bounded profiles reason more effectively,
- how should they verify output quality,
- how should they pause and recover when context is incomplete,
- and how should they expose those decisions to the user/operator?

Milestone 16 addresses that problem.

It is the place to borrow the most useful ideas from broader agentic and
multi-agent paradigms without giving up Helionyx’s substrate-first,
capability-first architecture.

------------------------------------------------------------------------

## What the User Gets

By the end of this milestone, the user should experience:

- better quality summaries and recommendations,
- fewer brittle one-shot orchestration paths,
- clearer explanation when the system is uncertain or degraded,
- safer escalation when context is missing or risk is elevated,
- and more reliable behavior across interactive and scheduled flows.

The user should also see that Helionyx is becoming more helpful **without**
becoming less bounded or less inspectable.

------------------------------------------------------------------------

## Core Product Semantics

### Agentic behavior remains bounded inside workflows

- Richer reasoning may occur inside explicit graph/subgraph boundaries.
- Free-form autonomous conversation between profiles is not the primary control
  flow.
- Operating profiles remain routing/authority concepts, not hidden autonomous
  data owners.

### Typed intermediate artifacts become first-class

- Plans, evidence bundles, approval requests, degraded-context reports, and
  answer packages should be explicit structured objects.
- Intermediate reasoning should become more composable and inspectable.

### Verification is part of execution, not a post-hoc wish

- Important flows should be allowed to critique, verify, or quality-check
  outputs before irreversible actions or user-visible delivery.
- Critique nodes do not replace deterministic policy; they complement it.

### Interrupt/resume is a product behavior, not just a runtime feature

- When a flow cannot safely continue, Helionyx should pause explicitly,
  preserve state, and expose why.
- Resume behavior should continue from a meaningful checkpoint rather than
  forcing full restart when avoidable.

------------------------------------------------------------------------

## Milestone Scope

### 1) Reusable Profile-Aware Subgraph Library

- Define reusable subgraphs for common orchestration concerns.
- Make them usable across multiple profiles and workflows.
- Avoid one-off workflow logic where a shared bounded pattern should exist.

Representative subgraphs:
- `intent_classification_subgraph`
- `policy_gate_subgraph`
- `context_gather_subgraph`
- `critique_verification_subgraph`
- `approval_interrupt_subgraph`
- `delivery_subgraph`
- `evidence_packaging_subgraph`

### 2) Typed Plan / Evidence / Answer Bundles

- Introduce typed intermediate payloads for workflow reasoning and explanation.
- Use these bundles to improve handoffs, verification, and operator visibility.

Representative bundle types:
- intent decision bundle,
- action plan bundle,
- evidence bundle,
- degraded-context report,
- approval request,
- final answer package.

### 3) Critique and Verification Nodes

- Add bounded critique/verification behavior to workflows where quality matters.
- Ensure verification runs against explicit evidence or deterministic checks.
- Support both scheduled and interactive workflows.

Representative uses:
- digest quality review,
- ambiguous calendar interpretation checks,
- portfolio alert confidence review,
- task recommendation sanity checks.

### 4) Approval / Interrupt / Resume Semantics

- Generalize explicit pause/resume behavior across profile-aware workflows.
- Make approval-worthy conditions first-class runtime events.
- Expose resume points and pause reasons to operator-facing surfaces.

Representative triggers:
- policy escalation,
- degraded provider context with material risk,
- low-confidence plan quality,
- ambiguous delivery or schedule interpretation.

### 5) Operator Visibility and Forensics

- Expand visibility surfaces so operators can inspect:
  - selected operating profile,
  - invoked workflow/subgraphs,
  - critique/verification outcomes,
  - pause/escalation reasons,
  - evidence supporting final responses or deliveries.

------------------------------------------------------------------------

## Concrete Examples of Improvement Over Time

This milestone should improve the system in practical ways, not only in
architectural neatness.

### Example 1: Better Monday Digest Quality

Without this milestone:
- the cadence flow may gather context and render a digest in one largely linear
  path,
- degraded provider context may be handled coarsely,
- and questionable summaries may still be delivered if they pass deterministic
  policy checks.

With this milestone:
- the cadence profile can gather context,
- produce a typed digest plan,
- run a critique/verification step,
- attach an explicit degraded-context report if provider data is incomplete,
- and either deliver, degrade gracefully, or pause for approval.

User benefit:
- higher quality digest output,
- clearer disclosure when information is partial,
- lower chance of misleading summaries.

### Example 2: Better Interactive Calendar Support

Without this milestone:
- a general chat flow may answer based on incomplete context with weak internal
  structure.

With this milestone:
- General Chat can route to a bounded day-ahead planning workflow,
- receive a typed evidence bundle from calendar and task context,
- verify whether a conflict or ambiguity exists,
- and either answer directly or ask for clarification with evidence-backed
  rationale.

User benefit:
- better answers to questions like “what do I have tomorrow?”
- fewer overconfident but weakly grounded responses.

### Example 3: Safer Portfolio Alerts

Without this milestone:
- future portfolio workflows might either over-alert or require hardcoded logic
  that becomes brittle as scope grows.

With this milestone:
- a portfolio profile can generate a candidate alert,
- run a bounded critique step against thresholds, confidence, and supporting
  evidence,
- and only then decide whether to notify, defer, or escalate.

User benefit:
- more useful alerts,
- less noise,
- better trust in proactive behavior.

### Example 4: Better Recovery When External Systems Fail

Without this milestone:
- provider failures may cause whole-run failure or simplistic degraded output.

With this milestone:
- a workflow can pause at an explicit interrupt node,
- record a degraded-context or approval request bundle,
- and resume from checkpoint when the operator approves or the provider recovers.

User benefit:
- fewer full restarts,
- clearer recovery posture,
- better continuity for long-running or multi-provider workflows.

### Example 5: Better Explanations and Debuggability

Without this milestone:
- users/operators may know that a run succeeded or failed, but not how quality
  checks or intermediate decisions affected the outcome.

With this milestone:
- Control Room or Explorer can show the profile, subgraphs used,
  critique results, evidence bundle, and pause/escalation path.

User benefit:
- stronger trust,
- easier debugging,
- easier iterative improvement of workflows over time.

------------------------------------------------------------------------

## Product Acceptance Criteria

- Reusable bounded subgraphs exist for at least several shared orchestration
  concerns.
- Typed intermediate bundles are used in at least one scheduled and one
  interactive workflow.
- At least one workflow includes an explicit critique/verification step.
- At least one workflow supports explicit interrupt/resume semantics.
- Operator-facing visibility exposes critique/verification and pause/escalation
  evidence.
- Existing control-plane and capability boundaries remain non-regressive.

------------------------------------------------------------------------

## How to Test (Operator Checklist)

1. Validate reusable subgraph behavior
	- Confirm multiple workflows use shared subgraph patterns rather than
	  independent one-off logic
	- Confirm subgraph boundaries are visible in execution evidence

2. Validate typed bundle flow
	- Trigger one interactive and one scheduled workflow
	- Confirm plan/evidence/degraded/answer bundles are explicit and inspectable

3. Validate critique/verification behavior
	- Induce a questionable or partial-context scenario
	- Confirm verification step runs
	- Confirm workflow either proceeds, degrades, or escalates explicitly

4. Validate interrupt/resume behavior
	- Trigger a pause-worthy condition
	- Confirm pause reason and checkpoint are visible
	- Resume the workflow and confirm continuity rather than full restart when applicable

5. Validate operator visibility
	- Inspect control-room or explorer output
	- Confirm profile, subgraphs, critique outcomes, and evidence are inspectable

6. Validate non-regression
	- Re-run representative digest/reminder and interactive flows
	- Confirm richer reasoning behavior does not weaken policy or substrate guarantees

------------------------------------------------------------------------

## Non-Goals

- No unconstrained many-agent conversation as primary runtime control flow
- No hidden mutable shared state owned by profiles or agents
- No replacement of deterministic policy with prompt-only critique logic
- No broad autonomous write authority expansion in this milestone
- No abandonment of explicit domain capability ownership

------------------------------------------------------------------------

## Risks and Mitigations

- **Risk: Critique/verification adds complexity without clear value**
	- Mitigation: Apply it first to high-value flows where output quality and
	  trust matter most.

- **Risk: Typed bundles become over-engineered**
	- Mitigation: Start with a small set of high-value bundle types and extend
	  only when needed.

- **Risk: Interrupt/resume becomes operationally confusing**
	- Mitigation: Require explicit pause reasons, resume semantics, and operator
	  visibility from the start.

- **Risk: “Agentic maturation” is misread as license for loose multi-agent design**
	- Mitigation: Keep reusable subgraphs, typed bundles, and profile-aware
	  workflows as the preferred implementation model.

------------------------------------------------------------------------

## Forward Path (Post-M16)

After this milestone, Helionyx should be in a strong position to expand into:
- richer interactive general-assistant behavior,
- deeper domain-specific profiles such as calendar and portfolio,
- approval-gated proactive support,
- and broader tool ecosystems under the same substrate-first, bounded-control
  architecture.

Further growth should continue to preserve:
- durable replayable evidence,
- explicit capability ownership,
- deterministic control-plane authority,
- and operator-visible reasoning boundaries.