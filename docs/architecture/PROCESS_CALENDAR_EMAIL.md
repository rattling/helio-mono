# Process Architecture: Calendar + Email Digest (Planned M13)

**Status**: Planned  
**Primary scope**: external calendar reads + multi-channel digest delivery

## Purpose

Define the planned M13 process for calendar-aware digest composition and
Telegram/email delivery under bounded orchestration control.

## Planned Boundaries

- Calendar integrations are read-first (Google + Zoho).
- Delivery channels include Telegram and SMTP/Gmail-compatible email.
- External calls are policy-gated through the control plane.
- All outcomes (fetch/compose/deliver) are durably auditable.

## Planned High-Level Flow

1. Orchestration run starts under policy envelope.
2. Calendar adapters fetch and normalize provider events.
3. Digest composer builds Monday weekly+day-ahead or Tue-Fri day-ahead output.
4. Delivery adapter sends to enabled channels.
5. Run + delivery outcomes are emitted for replay/explanation.

## Schedule Semantics (Planned)

- Monday morning: weekly lookahead + day-ahead
- Tuesday-Friday morning: day-ahead

## Related Milestone Docs

- `docs/Milestones/MILESTONE12_CHARTER.md`
- `docs/Milestones/MILESTONE13_CHARTER.md`
- `docs/CONTROL_PLANE_POLICY_CONTRACT.md`
