# Architecture Decision Record

## Title
Milestone 10 Data Explorer: Canonical Deep-Link Context Contract

## Status
Accepted

## Context
Milestone 10 requires Control Room and Lab surfaces to link users into precise
Data Explorer contexts. Without a canonical deep-link contract, each UI area may
encode ad hoc query state differently, causing broken links and non-reproducible
investigation workflows.

## Decision
Define a canonical deep-link context model for Data Explorer navigation.

Deep-link contexts must encode, at minimum:
- entity identifier and type,
- optional time window,
- optional view mode (timeline/state/decision),
- optional filter preset metadata.

Control Room and Lab links must use this contract so investigation states are
reproducible and shareable.

## Rationale
- Makes cross-surface interrogation deterministic.
- Supports saved/reused investigation presets.
- Prevents proliferation of incompatible query string conventions.

## Alternatives Considered
- Surface-specific link/query formats.
- Context transfer only via in-memory state (non-shareable).

## Consequences
- Requires coordinated client + API parsing/validation of link contexts.
- Introduces a small upfront design cost that avoids long-term navigation drift.
- Improves operator ergonomics for audit and debugging workflows.
