# Engineering Constitution

## 1. Purpose and Scope

This document defines the **engineering posture, architectural biases, and technical discipline**
under which all projects are built.

It applies across projects and over time.

It intentionally does **not** define:
- workflows or phases
- milestones or delivery mechanics
- branching or PR strategy
- role responsibilities
- acceptance or testing procedures

Those belong in workflow and role documents.

This document exists to prevent drift, accidental complexity, and architectural incoherence.

---

## 2. Core Engineering Values

### 2.1 Pragmatism Over Purity
We favor designs that are:
- understandable
- modifiable
- proportionate to the problem

We value ideas from Clean Architecture, DDD, and layered design, but apply them **lightly and selectively**.

We reject architecture that exists primarily to satisfy theory rather than current needs.

### 2.2 Clarity Over Cleverness
- Prefer explicit code to clever abstractions.
- Prefer readable control flow to meta-programming.
- Prefer boring solutions that fail predictably.

### 2.3 Intentional Tradeoffs
All non-trivial architectural choices involve tradeoffs.
We prefer **conscious compromise** over accidental structure.

---

## 3. Language and Technology Defaults

Defaults are preferences, not mandates. Deviations are allowed when justified.

### 3.1 Backend
- **Primary language:** Python
- Backend services should be:
  - modular
  - self-contained
  - locally runnable
  - testable in isolation

We strongly prefer:
- thin APIs, favouring fastAPI (with room for flexibility e.g. RPC or other paradigms, tools where justified)
- minimal framework surface
- business logic independent of transport and persistence details

### 3.2 Frontend (when applicable)
- **Preferred language:** TypeScript
- **Preferred framework:** React
- **Preferred build tooling:** Vite
- **Preferred UI baseline:** Material UI (or equivalent)

Frontend choices may vary by project, but must remain:
- modular
- testable
- decoupled from backend internals

---

## 4. Architectural Posture (Lightweight, Not Dogmatic)

### 4.1 Monorepo With Service-Grade Boundaries
We default to a **monorepo**, but we structure it as a set of **modular, service-like units**.

A “service” here means:
- a bounded unit of responsibility
- independently runnable (where applicable)
- independently testable
- independently deployable in principle
- owned end-to-end by whichever agent is working on it

This is explicitly intended to support **parallel agents** working safely without constant coordination.

### 4.2 Contract-First Interfaces Between Services
Inter-service integration must be **contract-based**, not “read the other code and hope.”

- Each service exposes explicit interfaces (API/schema/events) treated as contracts.
- Contracts are versioned and documented.
- A change to a contract is a first-class change:
  - it must be visible
  - it must be documented
  - it must be backwards-compatible where practical
  - or it must declare a breaking change clearly

Goal: an agent should be able to implement, test, and deploy a service without needing conversational synchronization with other agents, except when proposing/accepting a contract change.

### 4.3 Explicit Dependency Policy
We prefer:
- dependencies flowing *into* stable contracts and shared libraries
- not into other services’ internal code

Direct code-level imports across service boundaries are discouraged unless explicitly allowed by contract and ownership rules.

### 4.4 Dependency Direction (Bias, Not Law)
We prefer:
- one-way dependency direction where practical
- core logic isolated from infrastructure concerns

However:
- we accept pragmatic violations when cost outweighs benefit
- boundary purity must never obstruct progress

### 4.5 Clean Architecture — Lightly Applied
Where useful, we separate:
- core logic
- adapters (API, persistence, external systems)
- infrastructure concerns

This separation should be:
- obvious in structure
- light in ceremony
- easy to refactor

If maintaining strict layers becomes burdensome, simplify.

---

## 5. Shared Code and Reuse

- Shared functionality must be explicit.
- Shared code lives in clearly named libraries or packages.
- Implicit coupling through copy-paste or hidden imports is discouraged.

Shared libraries should:
- have minimal dependencies
- be usable independently
- avoid entanglement with application-specific logic

Rule of thumb:
- **Shared library** = stable, reusable primitives
- **Service** = behavior, orchestration, integration, and persistence

---

## 6. Deployability and Composition Bias

Even when running locally or in early stages, systems should be designed such that:
- components could be deployed independently if needed
- services do not rely on hidden global state
- configuration is explicit and externalized

This supports future parallel development and multi-agent workflows without committing to distributed systems prematurely.

---

## 7. Runnable Systems and Explicit Entry Points

A system is not considered complete unless it can be **stood up and exercised** in a way that reflects real usage.

Passing tests alone is insufficient.

Every project must provide **explicit, documented entry points** that allow a human or agent to:
- start the system (or relevant services)
- verify that it is running
- exercise representative end-to-end flows

These entry points are a **first-class architectural concern**, not an afterthought.

### 7.1 Explicit Entry Points

Projects must expose clear ways to interact with the system, such as:
- startup commands or scripts
- status or health checks
- example usage flows (API calls, CLI commands, UI access, or domain-level invocation)

The specific mechanism (e.g. Makefile targets, scripts, task runners) is flexible, but:
- the entry points must be explicit
- they must be documented
- they must be kept in sync with the code

A system that “works in theory” but cannot be run and used is incomplete.

### 7.2 Usability as an Engineering Responsibility

Engineering is responsible for ensuring that:
- the system can be launched without hidden knowledge
- configuration is explicit and discoverable
- representative flows can be exercised without manual setup beyond documented steps

This supports:
- effective QA and acceptance validation
- reliable context resets
- onboarding of new engineers or agents
- confidence at milestone boundaries

### 7.3 Alignment With Modularity and Services

For modular or service-like systems:
- each service should have its own runnable entry point where practical
- shared startup or orchestration should remain explicit
- services must not rely on implicit global state to function

This bias supports parallel agent work and future decomposition without premature distribution.

### 7.4 Durability of Operational Knowledge

Operational knowledge (how to run, use, and verify the system) must be:
- versioned with the code
- recoverable from the repository
- reflected in durable artifacts (README, scripts, examples)

If a future agent cannot stand the system up from the repository alone, the engineering discipline has failed.

---

## 8. State, Recording, and Durability Philosophy

- Durable system state must live outside ephemeral execution or agent context.
- Engineering outputs must be reconstructable from the repository and version control history.
- Systems should make state transitions explicit and inspectable.

Event-style recording, logging, or journaling is encouraged where it improves traceability, but should not introduce unnecessary complexity.

---

## 9. Complexity Discipline

### 9.1 Frameworks and Tooling
- Frameworks must earn their inclusion.
- Prefer minimal viable tooling.
- Avoid stacking abstractions unless each layer provides clear value.

### 9.2 Avoid Premature Generalization
- Do not design for hypothetical future requirements.
- Optimize for today’s understanding.
- Leave space to refactor when knowledge improves.

---

## 10. Decision Discipline

- Architectural decisions should be made consciously.
- Non-obvious or impactful decisions should be recorded succinctly.
- Reversibility should be considered explicitly.

We prefer a small number of well-understood decisions over large numbers of implicit ones.

---

## 11. Amendment Philosophy

This constitution is intended to be:
- stable
- rarely changed
- applicable across projects

Project-specific constraints or deviations belong in project documents, not here.

---

### Guiding Principle

> Build systems that a fresh engineer—or agent—can understand, modify, and extend without inheriting hidden assumptions, and where parallel agents can work safely via explicit contracts.
