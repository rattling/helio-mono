# Milestone 10 --- Data Explorer (Power-User Interrogation and Traceability)

## Objective

Introduce a dedicated Data Explorer surface that makes Helionyx fully
interrogable for power users.

This milestone provides a first-class way to answer:

- what happened,
- why it happened,
- what state changed,
- and where to inspect the underlying evidence.

The Data Explorer is the deep-inspection companion to Control Room:
Control Room summarizes system behavior; Data Explorer exposes traceable detail.

------------------------------------------------------------------------

## Why This Milestone

Milestone 9 establishes practical UI operation and basic transparency, but
advanced operators still need a direct path from summary signals to underlying
system evidence.

Without an explicit explorer, users can see outcomes but cannot efficiently
trace causality across events, projections, and decision semantics.

Milestone 11 is expected to expand Lab visibility/control and can build on the
traceability foundation established here.

------------------------------------------------------------------------

## What the User Gets

By the end of this milestone, a user should experience:

- A dedicated Data Explorer tab for deep system interrogation
- Fast lookup by entity IDs (task/event/suggestion/reminder/decision)
- Timeline views showing event progression and state transitions
- Side-by-side raw data and interpreted explanation views
- Deep links from Control Room/Lab into relevant explorer context

------------------------------------------------------------------------

## User Experience Over Time

### Week 1: Findability and grounding

- User can open Data Explorer from top navigation
- User can search by known IDs and immediately inspect canonical records

### Weeks 2--4: Causality and state inspection

- User can traverse event timeline and related projection snapshots
- User can inspect why ranking/suggestion/reminder decisions occurred

### Month 2+: Repeatable interrogation workflows

- User can reuse saved query presets for common operational questions
- Control Room and Lab become launch points into deep evidence inspection

------------------------------------------------------------------------

## Core Product Semantics

### Transparency contract

- Every operator-visible summary should have a path to inspect backing evidence
- Explorer must preserve auditable links between event data and read-model state

### Read-first discipline

- Milestone 10 is primarily interrogation and traceability, not broad mutation
- Any write-capable controls remain bounded and explicit via milestone-specific scope

### Human legibility + raw access

- Raw payloads remain available for precision
- Interpreted summaries exist to reduce cognitive load, not hide details

------------------------------------------------------------------------

## Product Acceptance Criteria

- Data Explorer tab is present and discoverable in UI
- User can query by ID and retrieve related canonical records
- User can inspect event timeline and corresponding projection state
- Decision-oriented records include inspectable rationale fields
- Control Room can deep-link into relevant Explorer contexts
- Existing task/control-room/lab surfaces remain non-regressive

------------------------------------------------------------------------

## How to Test (Operator Checklist)

1. Validate entity lookup
	- Search for known task/event IDs
	- Confirm explorer resolves and displays canonical objects

2. Validate timeline interrogation
	- Open an entity timeline and follow event sequence
	- Confirm ordering and timestamps are consistent

3. Validate event-to-state traceability
	- Inspect a projection row and locate contributing events
	- Confirm user can understand what changed and when

4. Validate decision transparency
	- Inspect ranked/suggested/reminder items and rationale fields
	- Confirm deterministic + learned metadata are visible when applicable

5. Validate deep-link flows
	- Navigate from Control Room to Explorer context for a surfaced item
	- Confirm handoff preserves entity/time/filter context

6. Regression sanity
	- Re-run key task/control-room/lab checks
	- Confirm no disruption to existing interaction paths

------------------------------------------------------------------------

## Implementation Scope (Product-Facing)

### Explorer navigation + query shell

- New Data Explorer top-level entry
- Query controls for ID/type/time/source/status filters
- Read-only result panes suitable for power-user debugging

### Traceability views

- Event timeline view for selected entity/context
- Projection/state snapshot view with essential field-level clarity
- Decision/rationale view for ranking/suggestion/reminder artifacts

### Cross-surface linking

- Deep links from Control Room and Lab into Explorer
- Stable URL/query format for reproducible investigation contexts

------------------------------------------------------------------------

## Non-Goals

- No unrestricted operator mutation over core domain state
- No replacement of Control Room with raw explorer-only UX
- No broad analytics warehouse or BI tooling scope in this milestone
- No dilution of contract-first boundaries for convenience coupling
