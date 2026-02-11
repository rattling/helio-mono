# Helionyx — Project Charter

## Version
v0.1 — Initial Charter (Milestone 1 Focus)

## 1. Purpose

Helionyx is a **personal decision and execution substrate** designed to support **human decision-making** with strong guarantees around control, traceability, and durability.

It is not an LLM wrapper.

It is a system that:
- records human and agent cognition
- makes decision surfaces explicit
- enforces clear authority boundaries
- accumulates durable, inspectable state over time

LLMs are used as tools within the system, not as the system itself.

---

## 2. Core Intent

Helionyx aims to establish a **brain and nervous system** independent of any specific LLM or UI.

It defines:
- how information enters the system
- how it is interpreted and categorized
- how decisions are proposed, reviewed, and recorded
- how outcomes and follow-ups are tracked over time

The system is designed to grow in capability and autonomy **only as control and clarity increase**, not before.

---

## 3. Scope and Users

### 3.1 Initial Scope
- **Single-user system** (initially the author)
- Designed from the outset with **multi-user support as a first-class future concern**

### 3.2 Authority Model
- The **human user is the sole source of authority**
- LLMs never have implicit or autonomous authority
- All LLM actions occur within **explicitly bounded decision surfaces**

Bounded autonomy may expand over time, but:
- bounds must always be explicit
- bounds must be inspectable
- bounds must be revisable

---

## 4. Decision Surfaces as First-Class Objects

Decisions are the central organizing concept of Helionyx.

The system explicitly supports:
- **human decisions**
- **agent proposals**
- **review, acceptance, or rejection**
- **recorded rationale and context**
- **observable outcomes**

Decisions and decision workflows are **first-class objects**, not implicit behavior.

This applies both to:
- decisions *within* the system (e.g. categorization, reminders)
- decisions *supported by* the system (human planning, tracking, prioritization)

---

## 5. Recording, State, and Durability Invariants

The following are **hard invariants** of Helionyx.

### 5.1 Append-Only Event Log
- All meaningful system activity is recorded as events
- Events are **append-only**
- Historical events are never mutated
- Corrections occur via new events, never edits

### 5.2 Artifacts
Artifacts recorded by the system include (at minimum):
- raw user messages and inputs
- extracted structured objects
- LLM prompts and responses
- system-generated summaries or interpretations
- decision records and rationales

The artifact model is expected to expand over time.

### 5.3 Projections
- Read models, indexes, and databases are **derived from the event log**
- Projections may evolve or be rebuilt
- The event log remains the source of truth

---

## 6. Interfaces and Interaction Model

### 6.1 Input Streams
Initial input consists of:
- conversational data
- messages exchanged between the user and LLMs

For Milestone 1:
- ingestion of ChatGPT conversation dumps is used as a **temporary bootstrap mechanism**
- this is not a long-term interaction strategy

### 6.2 Active Interaction Surface
For Milestone 1:
- **Telegram** is the primary active interface
- it is treated as an adapter, not a core dependency

Future interfaces (native UI, alternate channels) are anticipated.

### 6.3 Push vs Pull
In Milestone 1:
- **Push**: reminders and summaries only
- **Pull**: conversational queries about recorded items

No autonomous task execution occurs in Milestone 1.

---

## 7. Core Object Types (Milestone 1)

Helionyx initially supports three first-class tagged object types:

- **Todo**
  - explicit actions or commitments
- **Note**
  - noteworthy information worth retaining
- **Track**
  - declarative intent to monitor something over time

Properties:
- objects may carry multiple tags (e.g. note + track)
- tags represent interpretation, not irreversible classification

---

## 8. Milestone 1 Goals

Milestone 1 exists to prove that:

- an ongoing information stream can be ingested
- structured meaning can be extracted reliably
- decisions and interpretations are explicit and inspectable
- durable state accumulates coherently over time
- the system can push and answer basic questions meaningfully

Milestone 1 prioritizes:
- correctness
- traceability
- controllability

It explicitly deprioritizes breadth, automation, and sophistication.

### 8.1 User Interaction Requirements

Milestone 1 must provide **clear, documented pathways** for the business user to:

1. **Bring up the system** and keep it running in a "live" state
2. **Ingest new messages** through multiple channels:
   - Interactive CLI scripts
   - Telegram bot interface
   - ChatGPT conversation imports
3. **Trigger and verify extraction** of structured objects from messages
4. **Query the system** for todos, notes, and tracks with tag filtering
5. **View raw event log** and extracted objects for inspection
6. **Interact via Telegram** for all core operations

**Acceptance Criterion**: The QA agent (simulating the human user) must be able to perform all workflows above using only:
- Scripts in `scripts/`
- Telegram bot commands
- Documentation in `docs/` and `README.md`

No chat history or undocumented steps should be required.

---

## 9. Explicit Non-Goals (Milestone 1)

The following are **out of scope** for Milestone 1:

- autonomous task execution
- complex planning or scheduling
- agent self-improvement
- learning across users
- rich UI beyond Telegram
- deep integrations (email, calendar, external systems)

These may appear in future milestones, but are intentionally excluded now.

---

## 10. Forward Directions (Non-Binding)

Anticipated future directions include:
- native chat and decision UIs
- richer decision and policy layers
- long-horizon planning support
- controlled increases in agent autonomy
- multi-agent orchestration
- integrations with external systems (calendar, email, documents)
- multi-user support with clear authority boundaries

These are directional signals, not commitments.

---

## 11. Guiding Principle

> Helionyx should make it easier for a human to understand what has happened, what decisions were made, why they were made, and what remains unresolved — even months later — without trusting any single model, interface, or session.

That principle governs all future work.
