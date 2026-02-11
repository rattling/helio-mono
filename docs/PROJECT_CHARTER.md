# Helionyx — Project Charter

## Version
v0.2 — Core Charter (Milestone-Agnostic)

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

## 6. Milestones

Helionyx development is organized into milestones, each with specific goals and deliverables.

### Milestone 0: Architecture Baseline ✅

**Status**: Complete (Feb 10, 2026)  
**Purpose**: Establish foundational architecture with service boundaries, contracts, and working walking skeleton.

**Key Deliverables**:
- Service-oriented monorepo structure
- Event-sourced architecture with file-based event log
- Contract definitions and protocols
- Walking skeleton demonstration
- Comprehensive architecture documentation

**See**: [MILESTONE0_CHARTER.md](MILESTONE0_CHARTER.md) for complete details.

### Milestone 1: Core Functionality and LLM Integration ✅

**Status**: Complete (Feb 11, 2026)  
**Purpose**: Transform baseline into functional system with real LLM extraction, durable persistence, and active user interaction.

**Key Deliverables**:
- OpenAI integration with MockLLM for testing
- SQLite persistence with projection rebuild
- Telegram bot interface with commands and notifications
- ChatGPT import capability
- Comprehensive test suite (31 tests)

**See**: [MILESTONE1_CHARTER.md](MILESTONE1_CHARTER.md) for complete details.

### Future Milestones

Future milestones will be planned and documented as development progresses. Each milestone will have its own charter document following the same pattern.

---

## 7. Forward Directions (Non-Binding)

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
88