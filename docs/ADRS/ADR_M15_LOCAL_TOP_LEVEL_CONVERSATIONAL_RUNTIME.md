# Architecture Decision Record

## Title
Milestone 15: Keep the Top-Level Conversational Runtime Local

## Status
Accepted

## Context

As Helionyx evolves toward a broader general-chat surface on top of the durable
substrate, there is a design choice about who should own the top-level
conversational runtime.

Two broad options were considered:

1. Helionyx owns the top-level conversational runtime locally.
2. A managed hosted conversation runtime, such as the OpenAI Responses API,
   becomes the top-level conversational surface, with Helionyx acting more as a
   routed capability substrate beneath it.

This decision matters because Helionyx is intentionally being built as:
- a durable substrate with append-only evidence,
- a system with explicit capability ownership,
- a system with bounded operating profiles and orchestration,
- and a system where policy, side effects, and explainability remain
  first-class.

The more Helionyx grows into a high-trust personal system, the more important
it becomes that routing, memory semantics, capability invocation, policy, and
auditability remain stable and locally owned.

At the same time, there is one possible convenience use case for hosted
conversation runtimes:
- allowing a broad ChatGPT-like conversational mode to sit behind the Helionyx
  front door so a user does not need to switch tools for casual or exploratory
  conversation.

This convenience path is potentially useful, but it is explicitly not the same
question as “who owns the system’s constitutional runtime?”

## Decision

Helionyx will keep the **top-level conversational runtime local**.

This means Helionyx remains authoritative for:
- top-level routing,
- operating-profile selection,
- turn semantics,
- local memory and durable conversation/event recording,
- capability invocation boundaries,
- policy enforcement,
- side-effect control,
- handoff semantics,
- and explanation/audit surfaces.

External model APIs may be used inside bounded nodes, subgraphs, or workflows
as reasoning engines, but they will not become the primary authority for the
top-level conversational loop.

An optional future exception is permitted:

- Helionyx may support a clearly bounded **hosted conversation passthrough
  mode** for low-stakes interaction consolidation.

If such a mode is ever implemented, it must be treated as:
- a convenience surface,
- explicitly non-canonical for system memory/authority,
- and non-core to the main Helionyx architecture roadmap.

It must not replace the local top-level runtime.

## Rationale

- Local ownership preserves stable memory semantics and durable evidence.
- Local ownership preserves explicit capability boundaries.
- Local ownership reduces exposure to behavior drift in a managed conversation
  product.
- Local ownership keeps policy and side-effect control inspectable and
  testable.
- Local ownership aligns with operating profiles, substrate-first durability,
  and bounded orchestration.
- Hosted conversational runtimes are useful as bounded reasoning tools, but are
  a poor constitutional foundation for a high-trust personal system.

The main concern is not only model stochasticity in isolation, but also:
- runtime behavior drift over time,
- opaque internal state handling,
- hard-to-pin-down real-time routing behavior,
- and difficulty guaranteeing stable interaction contracts in a high-stakes
  environment.

For Helionyx, these risks outweigh the convenience of outsourcing the entire
top-level conversation loop.

## Alternatives Considered

- **Managed hosted runtime as primary conversational surface**
  - Faster path to broad free-form conversation quality.
  - Rejected because it weakens local control over memory, routing, policy,
    explainability, and long-term architectural stability.

- **Hybrid system where hosted conversation is a major co-equal top-level path**
  - Could improve conversational breadth while preserving some local routing.
  - Rejected as a primary direction because it still risks ambiguity about who
    owns turn semantics, memory, and live execution behavior.

- **Purely local runtime with no external conversational helper at all**
  - Maximizes control and clarity.
  - Not rejected. This remains the baseline architecture.
  - The ADR simply leaves open a narrow optional passthrough exception for
    low-stakes convenience use cases.

## Consequences

- Helionyx must invest in its own top-level conversational routing and general
  chat profile over time.
- Improvements to general chat should be implemented through local operating
  profiles, bounded workflows, typed handoffs, and reusable orchestration
  patterns.
- External APIs can still be used inside bounded reasoning tasks where useful.
- Any future hosted passthrough mode should be treated as a side quest and kept
  clearly separate from core Helionyx system ownership.
- If hosted passthrough is ever explored, it should likely require:
  - explicit mode switching or conservative routing,
  - clear user-visible signaling,
  - local interception of inbound and outbound turns,
  - minimal but explicit local recording,
  - and no assumption that hosted thread state is canonical Helionyx memory.

Overall consequence:
- Helionyx remains a locally governed conversational system that may borrow
  external conversational power in bounded ways, rather than becoming an
  external conversation shell with a local tool substrate.