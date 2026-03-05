# Personal Conversational AI System -- Vision & Architecture

# NB I may need to divide this into a few milestones!
Initally we are just going to capture chatgpt questions from pc or something daily/weekly 
Then I move to my own UI....

## Purpose

Create a personal conversational environment where:

-   High-quality general reasoning comes from frontier LLMs (OpenAI).
-   Domain-specific workflows are handled by specialised personal
    agents.
-   All conversations and thoughts are captured into a personal
    knowledge ledger (Helionyx).
-   The system gradually evolves from simple capture to a full
    conversational operating system.

This allows a **best-of-both-worlds approach**:

-   Use world-class LLM reasoning
-   Retain ownership of personal knowledge and workflows
-   Build specialised agents over time

------------------------------------------------------------------------

# Core Concept

The system has **two intelligence layers**.

## 1. General Cognitive Layer

Powered by:

**OpenAI Responses API / Agents SDK**

Responsibilities:

-   Natural conversation
-   Interpretation of ambiguous questions
-   Reasoning and synthesis
-   Deciding when specialist agents should be consulted
-   Explaining results returned from agents

This layer behaves like a **thinking partner**.

It does not contain domain logic.

## 2. Specialist Agent Layer

Implemented using:

**LangGraph agents**

Responsibilities:

-   Domain workflows
-   Tool orchestration
-   Persistent agent state
-   Structured outputs
-   Multi-step reasoning within a domain

Examples:

-   Trading agent
-   Research agent
-   Writing agent
-   Task / planning agent
-   Data analysis agent

These agents behave like **domain specialists**, not general
conversational partners.

------------------------------------------------------------------------

# Interaction Model

The general assistant acts as a **conductor**.

User message flow:

User → Router → General Assistant → (optional agent consult) → Response

Example:

User: "What's the latest on Nvidia?"

Router decides: - domain: trading - action: consult agent

Flow:

User\
↓\
Router\
↓\
Trading Agent (LangGraph)\
↓\
Structured Result\
↓\
General Assistant explains results conversationally

------------------------------------------------------------------------

# Structured Agent Output

Specialist agents should return structured data rather than prose.

Example:

    {
      "ticker": "NVDA",
      "price": 891.22,
      "change_24h": -1.7,
      "portfolio_exposure": 6.2,
      "risk_flag": "moderate",
      "recommendations": [
        "hold",
        "consider hedge if >7% drawdown"
      ],
      "sources": [...]
    }

The general assistant then converts this into natural dialogue.

This separation keeps:

-   data reliable
-   reasoning clean
-   agent logic deterministic

------------------------------------------------------------------------

# Conversation Modes

The system supports two interaction styles.

## 1. Consult Mode (default)

Specialist agents are used like tools.

No persistent session.

Example:

User: "What's Nvidia doing today?"

The system:

1.  consults trading agent
2.  receives snapshot
3.  explains results

Conversation remains in the **general assistant context**.

## 2. Focus Mode (optional)

When deeper interaction is required, the system enters a **specialist
session**.

Example:

User: "Let's analyse my Nvidia exposure."

Flow:

General assistant\
↓\
Focus session with Trading Agent\
↓\
Multi-turn dialogue

Focus ends via:

-   explicit command ("end trading session")
-   topic change
-   inactivity timeout

------------------------------------------------------------------------

# Session Behaviour

Each specialist agent session uses shared infrastructure:

AgentSession

-   short_term_context (last N turns)
-   structured_state (domain state)
-   history summarisation
-   TTL timeout

This session management logic is **written once** and reused by all
agents.

------------------------------------------------------------------------

# Router

The router determines how each message is handled.

Inputs:

-   user message
-   conversation context

Output example:

    intent: question
    domain: trading
    action: consult_agent
    confidence: 0.87

Possible actions:

-   general_response
-   consult_agent
-   focus_agent
-   workflow_action

Implementation options:

Simple: - LLM classifier

Hybrid: - rule triggers - fallback LLM classification

------------------------------------------------------------------------

# Knowledge Ledger (Helionyx)

All interactions are captured into a personal ledger.

Stored data:

-   raw conversation events
-   summaries
-   topics
-   tasks
-   insights
-   agent outputs

This ledger becomes the **long-term memory substrate**.

Agents and models both retrieve information from it.

------------------------------------------------------------------------

# Early Phase (Before Custom UI)

Until the custom interface exists, conversations occur in **ChatGPT
UI**.

A lightweight capture hook sends valuable conversations to Helionyx.

Approach:

Browser hook / button:

"Send to Helionyx"

Captured data:

-   recent chat turns
-   timestamps
-   source link
-   metadata

This avoids friction while preserving knowledge.

------------------------------------------------------------------------

# Future Phase (Custom Interface)

A personal web interface will replace ChatGPT UI.

Capabilities:

-   direct conversation with Responses API
-   automatic ledger capture
-   routing to specialist agents
-   agent session management
-   multi-agent interaction
-   analytics over personal conversations

------------------------------------------------------------------------

# System Architecture

High level structure:

User Interface ↓ Router ↓ General Assistant (OpenAI Responses API) ↓
Specialist Agents (LangGraph) ↓ Helionyx Ledger

------------------------------------------------------------------------

# Guiding Design Principles

### Use frontier models for thinking

Do not rebuild LLM reasoning.

Use them as cognitive engines.

### Keep workflows deterministic

Agents should execute structured domain logic.

### Separate reasoning from data

Agents return structured outputs.

LLM explains results.

### Capture everything

All conversations feed the personal knowledge ledger.

### Build incrementally

Phase 1 - ChatGPT UI - capture hook

Phase 2 - personal UI - routing - agent sessions

Phase 3 - full conversational operating system

------------------------------------------------------------------------

# Long-Term Vision

A **personal conversational operating system** where:

-   LLMs provide cognition
-   agents perform work
-   Helionyx stores knowledge
-   the interface remains natural conversation

Conceptually:

LLM = Cortex\
Agents = Organs\
Router = Nervous system\
Helionyx = Memory
