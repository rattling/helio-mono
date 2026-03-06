Consider complete arch seperation between:

helionyx data substrate and app that allows agents and apis to interact with it to add and query data.
personal assistant service with the various agents and apis that provide helioynx functionality
auditor service 

The separation exists so Helionics can accumulate governed intelligence, not just generate behaviour but.....

# NB - dont let governer become too grand.  Its a governance plane, not a moral OS etc. It shouldnt slow me down. It should help speed up because you know the right gov is there.

# Helionics Governor Architecture Note

## Status

Draft concept note. Early architecture sketch for future implementation. Not an execution plan.

## Purpose

This note captures an emerging three-service architecture for Helionics so the idea is preserved while still fresh. The aim is not to split Helionics into three commercial products, but to enforce clean service boundaries inside one coherent product.

The working architecture separates:

1. **Helionics Substrate** — durable data and event substrate
2. **Helionics Governor** — governance and enforcement plane
3. **Helionics Assistant** — user-facing agentic runtime and orchestration layer

A capable personal/decision agent needs three things:

a way to act
a way to remember
a way to be bounded and reviewable

That is your three-service model.

The separation matters because otherwise governance collapses into ordinary application logic and becomes vague, hard to enforce, and difficult to audit.

## Core Position

Helionics should be built as **one product with three separable services**.

That means:

* one overall product direction
* one monorepo is acceptable
* separate deployment units
* explicit service boundaries
* each service remains operable on its own
* no pretending they are fully independent businesses today

The main reason for treating them as separable is architectural discipline, not premature productisation.

## Why This Exists

The key problem is that agentic systems need more than internal safety checks. They need an explicit governance layer that can:

* define operational protocols
* constrain autonomous behaviour
* require transparency at selected points
* log what happened and why
* eventually intervene or block execution when required

If all of that sits inside the assistant runtime, the result is muddled:

* governance rules become mixed with app logic
* auditability weakens
* enforcement becomes inconsistent
* reuse across assistants becomes harder
* future externalisation becomes painful

The Governor therefore acts as a dedicated governance plane rather than a loose collection of rules buried in assistant code.

## Three-Service Model

### 1. Helionics Substrate

The Substrate is the durable state and evidence layer.

#### Responsibilities

* append-only or ledger-like event storage
* project and task state
* decision records
* evidence objects and references
* query and retrieval APIs
* durable audit records
* provenance and traceability

#### Character

The Substrate should remain relatively boring. It is primarily concerned with storing, retrieving, and exposing structured records.

#### Non-responsibilities

The Substrate should not decide policy. It should not decide whether a behaviour is permitted. It stores what happened, what was known, and what governance decisions were made.

---

### 2. Helionics Governor

The Governor is the governance and enforcement plane.

#### Responsibilities

* protocol definitions
* policy storage and versioning
* policy evaluation
* execution constraints
* disclosure requirements
* approval requirements
* step-level checks at defined control points
* pause, deny, or allow decisions
* override handling
* governance audit generation
* governance telemetry and review state

#### Character

The Governor is not only a registry of policies. It is a runtime authority.

In the earliest milestone it may mostly observe and advise. Over time it should gain enforcement power at selected control points.

#### Important distinction

The Governor should govern behaviour, not absorb every deterministic function already present in the system. It is a governing plane, not a replacement for existing application control logic.

---

### 3. Helionics Assistant

The Assistant is the user-facing orchestration and execution layer.

#### Responsibilities

* user interaction
* workflow planning
* orchestration via LangGraph
* tool invocation
* execution of multi-step tasks
* interaction with Substrate APIs
* surfacing disclosures and approvals
* complying with Governor requirements

#### Character

The Assistant remains the active runtime. It does not become passive just because a Governor exists. It still plans and executes. The Governor constrains and audits where required.

#### Non-responsibilities

The Assistant should not become the ultimate source of governance truth when the Governor is attached. It may keep local safety checks and deterministic guardrails, but the Governor should be authoritative for governance decisions.

## Existing Internal Distinction to Preserve

Helionics already has an internal distinction between:

* an **orchestration plane** using LangGraph
* a more **deterministic control plane** containing operational logic and guardrails

That distinction should remain.

The Governor should not erase or swallow the existing control plane. Instead, the system should distinguish between:

### Internal control plane

Deterministic internal application logic, such as:

* workflow state handling
* validation
* retries
* idempotency
* local tool wrappers
* domain-specific checks
* safe execution defaults

### Governing plane

Cross-cutting governance logic, such as:

* policy packs
* transparency obligations
* approval requirements
* enforcement at declared control points
* governance attestation
* overrides
* audit-grade records

This distinction is important. Otherwise the Governor becomes a dumping ground for every rule in the system.

## Enforcement Modes

The Governor can operate in more than one mode.

### 1. Observe

The Assistant emits governance-relevant events. The Governor records, evaluates, and reports. It may flag issues but does not stop execution.

Useful for:

* early rollout
* debugging protocols
* friction analysis
* policy design

### 2. Gate

The Assistant must request approval or evaluation before specific actions or steps. The Governor can allow, deny, require disclosure, or require confirmation.

Useful for:

* meaningful control without full mediation
* sensitive actions
* policy enforcement with manageable complexity

### 3. Proxy / Mediate

Certain tool calls or external actions must pass through the Governor directly. The Governor acts as a runtime mediation layer.

Useful for:

* strongest enforcement
* high-risk actions
* externalisable governance model

### Near-term stance

The pragmatic path is **observe first, with some selected teeth early**, rather than jumping directly to full mediation everywhere.

That means:

* meaningful policy storage from the start
* useful evaluation from the start
* some real pre-action checks for sensitive points
* not yet routing every action through a heavy proxy layer

## Control Points

The Governor needs explicit control points. Without them, governance remains vague.

Examples:

* plan created
* plan reviewed against policy
* before reading sensitive data
* before writing to substrate
* before external communication
* before external side effect
* before scheduled autonomous run
* before threshold-triggered action
* before irreversible action
* after a run completes
* when an override is used

These control points should be explicit in the Assistant runtime rather than inferred loosely.

## Key Design Question: How the Three Services Interact

This is the main unresolved area and should stay visible.

### Question 1: Does the Governor write to the Substrate?

Current leaning: **yes**.

Reason:

* governance decisions need durable reviewability
* admin UI will need to inspect enforcement history
* policy friction and effectiveness need analysis
* review of "what policy was in effect when this happened" must be easy

Recommended pattern:

* Governor owns policy definitions and governance decisions
* Governor writes governance events or signed audit records into the Substrate
* Substrate remains the durable system of record

That gives one durable historical trail without moving policy logic into the Substrate.

### Question 2: When the Assistant writes to the Substrate, does it go through the Governor?

Not always.

This should probably depend on action class.

#### Likely model

* ordinary internal state writes: Assistant writes directly to Substrate
* governance-relevant writes: Assistant emits control-point event to Governor first or alongside the write
* high-risk or externally consequential writes: Governor may gate before write occurs

So the Governor should not necessarily sit inline on every single Substrate interaction. That would add too much coupling and operational drag. But selected classes of write may need pre-checks or parallel governance recording.

### Question 3: How is the Governor invoked?

Current best answer: **hooks plus an explicit client contract**.

The Assistant runtime should expose governance hooks at declared control points. These hooks call the Governor through a narrow client interface.

This is cleaner than smearing Governor logic throughout the graph.

A likely pattern is:

* LangGraph nodes or wrappers emit control-point events
* a Governor client evaluates the step
* the step receives a decision and obligations
* the Assistant continues, pauses, or surfaces UX accordingly

This keeps invocation explicit and testable.

## Proposed Interaction Pattern

### Base flow

1. User request enters Assistant
2. Assistant creates or updates a run plan
3. Assistant consults Governor at relevant control points
4. Governor evaluates policies and returns decision plus obligations
5. Assistant continues execution under those constraints
6. Assistant and Governor both emit relevant records to the Substrate
7. Admin and user-facing review surfaces can inspect both runtime and governance history

### What the Governor returns

At minimum:

* decision: allow / allow-with-obligations / require-confirmation / pause / deny
* policy version(s)
* reason codes
* required disclosures
* required confirmations
* required audit obligations

### What the Assistant sends

At minimum:

* run ID
* agent ID
* user ID
* workflow type
* control point
* action summary
* intended side effects
* evidence refs
* protocol context
* risk or sensitivity class

## Responsibility Split

This needs to stay sharp.

### Substrate

* durable facts
* event history
* evidence
* state retrieval
* audit persistence

### Assistant

* planning
* execution
* tool orchestration
* user-facing interaction
* local operational controls

### Governor

* policy evaluation
* governance decisions
* transparency obligations
* approvals and overrides
* governance telemetry and attestation

## Local Safeguards vs Governor Authority

Duplication is acceptable only if the roles differ.

### Assistant local safeguards

* ordinary safe defaults
* validation
* retry rules
* basic self-checking
* execution hygiene
* bounded autonomy within app logic

### Governor authority

* whether an action class is allowed under current protocol
* what must be surfaced to the user
* whether human confirmation is required
* whether an override is valid
* what governance record must exist

The rule should be simple: local safeguards are convenience and safety hygiene; Governor decisions are governance authority.

## Data Model Concepts for Governor

The Governor likely needs a few first-class objects.

### Protocol

Named governance package or mode, such as a user or task-specific governance profile.

### Policy Rule

Concrete machine-evaluable rule attached to one or more control points.

### Control Point

Named stage in execution where governance can inspect or intervene.

### Governance Decision

Allow, deny, require disclosure, require confirmation, pause, or similar.

### Obligation

What must happen next, such as surface rationale, request approval, or record a particular event.

### Override

Explicit exception granted by an authorised actor and logged.

### Attestation

Durable statement that a run or step complied with required governance obligations.

## What the Governor Should Already Be Useful For Early

This matters because the Governor should not exist as empty ceremony.

Even early on it should provide real value:

* central storage for policy packs
* evaluation of which policy applies to which task/run/page/action
* reusable governance logic for the Assistant
* observability into how agentic execution is behaving
* friction analysis: where the policies are too heavy or too weak
* admin inspection of whether governance is actually helping

That makes it useful even before it becomes fully hard-edged enforcement infrastructure.

## Failure Semantics

This needs explicit policy later.

### Fail open

If Governor is unavailable, Assistant continues with local safeguards only.

### Fail closed

If Governor is unavailable, governed actions cannot proceed.

This should probably be configurable per protocol or action class rather than global.

## Questions To Keep Open

These should remain active design questions rather than being prematurely flattened.

1. Which exact Substrate writes are governance-relevant enough to require Governor involvement?
2. Which control points should exist in LangGraph execution versus deterministic internal control logic?
3. Should governance checks happen only around external effects, or also around sensitive reads and internal state transitions?
4. What is the minimum useful set of policy semantics for early versions?
5. How much micro-transparency is useful before it becomes friction and noise?
6. How should policy scope work: by user, workflow, task type, page, tool, or action class?
7. How should the admin UI inspect governance history and policy effectiveness?
8. Should the Governor emit its own signed events into the Substrate, or ordinary durable records with versioned provenance?
9. Where exactly do overrides live and who can invoke them?
10. Which parts of the present control plane remain strictly internal and should never be migrated into the Governor?

## Initial Architectural Stance

The most pragmatic stance for now is:

* one Helionics product
* three separate deployable services
* one monorepo is acceptable
* Substrate as durable record and retrieval layer
* Assistant as orchestration and execution runtime
* Governor as governance plane with early practical value
* hooks-based invocation from Assistant into Governor
* Governor writes governance outcomes to Substrate
* selective governance teeth early, not full mediation everywhere
* keep internal control plane distinct from governance plane

## Milestone Path

This is not immediate work. It is a future architecture direction.

### Milestone 0 — note and boundaries

Capture concepts, responsibilities, contracts, and open questions.

### Milestone 1 — policy store plus observability

Governor stores policy packs and evaluates selected control-point events. Assistant can consult it. Results are reviewable in Substrate and admin UI.

### Milestone 2 — selective gating

Sensitive actions require Governor approval before execution.

### Milestone 3 — disclosure and confirmation model

Governor can require specific transparency or user approval patterns at defined points.

### Milestone 4 — mediated execution for selected actions

Some tool calls or action classes are routed through Governor-mediated paths.

### Milestone 5 — externalisable architecture if ever needed

Only if it proves genuinely useful inside Helionics first.

## Non-goals For Now

* designing a complete policy language
* building a universal external governance product
* routing every system action through Governor
* collapsing existing control logic into governance logic
* finalising data schemas prematurely

## One-Paragraph Summary

Helionics should be structured as one product composed of three separable services: a Substrate that stores durable state, evidence, and event history; an Assistant runtime that plans and executes agentic workflows; and a Governor that defines and enforces governance protocols at declared control points. The Governor should begin as a practical policy and observability service with selected enforcement teeth, not as a fully general standalone product, while still being designed with strong service boundaries. Governance outcomes should be durably written into the Substrate so that policy effectiveness, friction, and compliance can be reviewed over time. The internal distinction between orchestration and deterministic control logic should remain intact, with the Governor handling cross-cutting governance rather than absorbing all application rules.



# Helionics Service Separation (Early Architecture)

## Core Structure

Helionics will be structured as **three top-level services**:

1. **Helionics Assistant**
2. **Helionics Governor**
3. **Helionics Substrate**

Each service is treated as an independent runtime unit.

### Service Rules

Each service will have:

* its **own FastAPI application**
* its **own API surface**
* its **own deployment unit**
* its **own schema in the database**
* its **own internal domain logic**

Services interact **only through APIs**, not by importing each other's internal code or directly accessing each other's database tables.

This keeps the architecture clean while still allowing a single repository and shared infrastructure early on.

---

# Database Strategy (Initial Phase)

Initially the system will use **one physical database** with **separate schemas**.

Example:

```
postgres
 ├─ assistant_schema
 ├─ governor_schema
 └─ substrate_schema
```

Rules:

* Each service **owns its schema**
* Services **only read/write their own schema**
* Cross-service data access happens **via API calls**, not SQL

This allows strong logical separation without operational complexity.

---

# Service Responsibilities

## Helionics Assistant

User-facing agent runtime and orchestration layer.

Responsibilities:

* user interaction
* workflow planning
* LangGraph orchestration
* tool execution
* scheduling
* runtime state

Persistence includes:

* run state
* orchestration checkpoints
* scheduling metadata
* execution logs

Writes durable artifacts and events to **Substrate** when needed.

---

## Helionics Governor

Governance and policy enforcement layer.

Responsibilities:

* policy definitions
* protocol configuration
* governance evaluation
* control point checks
* approvals and overrides
* governance decisions

Persistence includes:

* policy definitions
* policy versions
* governance configuration
* evaluation metadata

Writes governance outcomes and attestations to **Substrate**.

---

## Helionics Substrate

Durable memory and evidence layer.

Responsibilities:

* system event ledger
* durable artifacts
* decisions and evidence
* run history
* audit records
* cross-system query surface

Substrate should remain **implementation-agnostic** and not depend on assistant or governor internals.

---

## Interaction Model

High-level flow:

```
User → Assistant

Assistant
   ↓ (governance check)
Governor

Assistant
   ↓ (durable event / artifact)
Substrate
```

Substrate acts as the **durable shared memory plane**.

Governor and Assistant both publish relevant records into it.

---

## Architectural Principle

The system is designed as **three services inside one product**, not three separate products.

Early stage goals:

* strong service boundaries
* minimal operational overhead
* clear ownership of data and logic

---

## Future Evolution (If System Grows)

Possible later steps:

* separate databases per service
* independent deployments
* separate repositories
* independent scaling

Example future structure:

```
assistant-service → assistant DB
governor-service  → governor DB
substrate-service → substrate DB
```

The current architecture is intentionally compatible with that evolution.

---

## Guiding Rule

**Substrate stores durable system memory.
Assistant and Governor manage their own operational state.**

Not all internal data belongs in the Substrate.

Only records that matter for **history, evidence, or cross-system visibility** should be written there.

---

If you want, I can also give you a **very small repo layout** (about 10 lines) that fits this architecture cleanly. It will save you pain once the FastAPI apps start growing.
