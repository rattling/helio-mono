# Architecture Decision Record

## Title
Milestone 4: Encryption-at-Rest Decision (Defer)

## Status
Accepted

## Context
Milestone 4 calls out encryption-at-rest as optional-but-recommended for:
- event logs
- SQLite projections

However, M4’s primary acceptance criteria are backup/restore durability and a minimal, real security posture.
Adding encryption-at-rest introduces operational complexity:
- key management and recovery procedures
- integration complexity (event log + SQLite)
- increased risk of blocking core deliverables

We still need an explicit decision and compensating controls.

## Decision
Defer application-level encryption-at-rest in M4.

Compensating controls in M4:
- Restrictive filesystem permissions for runtime data and backups (umask 077 for backup/restore artifacts).
- Keep secrets out of the repo and logs (redaction filter + `.env` discipline).
- Prefer host-level / volume-level encryption where available (e.g., encrypted disk, LUKS) as an operational choice outside the application.

## Rationale
- Meets M4 acceptance without introducing fragile crypto/key pathways.
- Host-level encryption is simpler and typically already present in production setups.
- Deferring keeps the backup/restore contract stable and inspectable.

## Alternatives Considered
- Implement SQLCipher for SQLite projections
  - Rejected for M4: adds dependency and key handling, complicates recovery.
- Encrypt event log files with an application-managed key
  - Rejected for M4: key management/recovery is non-trivial and easy to get wrong.

## Consequences
- Backups are plaintext; operators must treat backup directories as sensitive.
- Security posture relies on OS hardening and permissions.
- Encryption-at-rest can be revisited in a future milestone with a dedicated ADR and recovery runbook.
