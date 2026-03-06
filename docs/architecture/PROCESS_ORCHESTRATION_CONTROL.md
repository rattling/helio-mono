# Process Architecture: Orchestration + Control

**Status**: M12 implemented (LangGraph runtime active), M13-ready  
**Primary scope**: bounded agentic orchestration under deterministic policy control

## Purpose

Define how Helionyx combines:
- LangGraph orchestration (agentic sequencing)
- deterministic control policy (guardrails + fail-closed enforcement)
- append-only auditability (event substrate as source of truth)

## Invariants

1. Human authority is absolute.
2. Agent autonomy is valid only in declared bound
s.
3. Out-of-bounds actions fail closed and escalate.
4. Side effects execute through deterministic services/adapters.
5. Every meaningful run and decision is durably reconstructable.

## Planes and Responsibilities

### Orchestration Plane
- Coordinates graph execution (branch/retry/checkpoint/fallback).
- Selects in-bounds paths based on context and policy envelope.
- Delegates side effects to deterministic services.

### Control Plane
- Evaluates tool allowlists, side-effect scope, and budget constraints.
- Produces deterministic allow/deny/escalate outcomes.
- Emits explicit rationale for blocked/escalated actions.

### Data Substrate
- Persists run lifecycle, node transitions, and policy outcomes.
- Supports replay, forensics, and operator-facing explanation surfaces.

## System Relationship

```mermaid
graph TB
        subgraph "Control Plane"
                POL[Responsibility Policy\nrole + bounds + budgets]
                GOV[Guardrails + Escalation Rules]
        end

        subgraph "Orchestration Plane"
                LG[LangGraph Runtime]
                NODES[Agent + Deterministic Nodes]
        end

        subgraph "Data Substrate"
                EV[(Append-Only Event Log)]
                PR[(Derived Projections)]
        end

        subgraph "Execution Adapters (M12)"
            CURR[Current Adapters\nTelegram + API + Query/Task]
        end

        subgraph "Planned External Adapters (M13)"
            CAL[Calendar Adapters\nGoogle + Zoho]
            EMAIL[Email Delivery Adapter\nGmail/SMTP]
        end

        POL --> LG
        GOV --> LG
        LG --> NODES
        NODES --> CURR
        NODES -. planned .-> CAL
        NODES -. planned .-> EMAIL
        NODES --> EV
        EV --> PR
        PR --> LG
```

## Component-Level View

```mermaid
graph TB
    subgraph "Unified Service"
        subgraph "Control Plane"
            POL[Policy + Responsibility Boundaries]
            GATE[Guardrails + Escalation]
        end

        subgraph "Orchestration Plane"
            ORCH[LangGraph Runtime]
        end

        subgraph "Adapter Layer"
            API[FastAPI HTTP Server]
            TG[Telegram Bot]
            CLI[CLI Scripts]
        end

        subgraph "Domain Services"
            ING[Ingestion Service]
            EXT[Extraction Service]
            QRY[Query Service]
        end

        subgraph "Infrastructure"
            EVT[(Event Store\nJSONL Files)]
            PROJ[(Projections DB\nSQLite)]
        end
    end

    API --> ORCH
    TG --> ORCH
    CLI --> ORCH

    POL --> ORCH
    GATE --> ORCH

    ORCH --> ING
    ORCH --> QRY
    ORCH --> EXT

    ING --> EVT
    EVT --> EXT
    EXT --> EVT
    EVT --> QRY
    QRY --> PROJ
```

## Policy Envelope Contract

Policy envelope shape and deterministic enforcement details are versioned in:
- `docs/CONTROL_PLANE_POLICY_CONTRACT.md`

## Audit Event Families (Active in M12)

- Orchestration run lifecycle (start/checkpoint/finish/failure)
- Node transition outcomes (entered/completed/retried/fallback)
- Policy outcomes (allowed/blocked/escalated with reason)
- Delivery outcomes (attempted/succeeded/failed with dedup fingerprint)

Primary contract and implementation anchors:
- `shared/contracts/events.py` (event schemas and types)
- `services/control/policy.py` (deterministic evaluator)
- `services/orchestration/runtime.py` (runtime boundary + event emission)
- `services/api/routes/control_room.py` (operator visibility)

## Operational Rule of Thumb

- Use LangGraph for sequencing and bounded reasoning.
- Use deterministic services for irreversible side effects and hard invariants.
- Ensure each run is explainable from durable evidence.
