# Milestone 7 --- Planning Aids + Dependency Suggestions + UI Readiness

## Objective

Introduce constrained intelligent planning features and stabilize APIs
for UI integration.

------------------------------------------------------------------------

## Core Capabilities

-   Dependency suggestions (proposed, not automatic)
-   Task splitting suggestions
-   Blocked/unblock workflow
-   Agent-first plan views
-   UI-compatible stable filtering & pagination
-   Optional UI BFF layer

------------------------------------------------------------------------

## Suggestion APIs

POST /tasks/{id}/suggest-dependencies\
POST /tasks/{id}/suggest-split\
POST /tasks/{id}/apply-suggestion

All suggestions must: - Include rationale - Require explicit
acceptance - Be event-logged

------------------------------------------------------------------------

## Plan Views

-   Next actions queue
-   Unblock-first queue
-   Waiting/snoozed queue

------------------------------------------------------------------------

## UI Considerations

-   Domain APIs remain stable
-   Optional BFF composes domain endpoints
-   Event stream for task changes

------------------------------------------------------------------------

## Acceptance Criteria

-   System proposes reasonable splits for vague tasks
-   Dependency graph remains acyclic unless explicitly overridden
-   UI can be built without introducing new domain semantics

------------------------------------------------------------------------

## Non-Goals

-   Autonomous task execution
-   Full calendar optimization
-   Heavy AI black-box planning
