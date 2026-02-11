# Helionyx -- Milestone 4 Charter

## Hardening & Security Baseline

**Version:** 0.1\
**Date:** 2026-02-11

**Part of:** Operational Hardening Arc (Milestones 2, 3, 4)

------------------------------------------------------------------------

## 1. Purpose

Milestone 4 hardens Helionyx for **production-ready operation** by establishing data durability and a minimal security posture.

This milestone does **not** expand cognitive features.

Its purpose is to ensure Helionyx is secure and data-durable enough for real daily use.

**Unified Arc Context:**
- **Milestone 2**: Service infrastructure foundation (complete)
- **Milestone 3**: Deployment & CI discipline
- **Milestone 4** (this): Hardening & security baseline

Milestone 4 assumes M2's service foundation and M3's deployment discipline are in place.

------------------------------------------------------------------------

## 2. Scope

### 2.1 Data Hardening

Helionyx stores:

-   Append-only event log
-   Artifacts (messages, LLM responses, structured objects)
-   Projections (SQLite databases)

Requirements:

-   **Storage Location Discipline**: Explicit, environment-aware data paths
-   **Automated Backup**: Scriptable backup procedure
-   **Tested Restore**: Validated restore procedure
-   **Documentation**: Clear data recovery process

Backups must be:

-   Environment-aware (dev/staging/live)
-   Scriptable (`scripts/backup.sh`, `scripts/restore.sh`)
-   Documented in `docs/DATA_MANAGEMENT.md`
-   Tested at least once in dev environment

------------------------------------------------------------------------

### 2.2 Backup & Restore

Introduce backup commands:

    make backup ENV=live
    make restore ENV=dev BACKUP=<timestamp>

Backup must:

-   Capture event log
-   Capture projections
-   Capture configuration (excluding secrets)
-   Include timestamp and environment metadata
-   Store in designated backup location

Restore must:

-   Validate backup integrity
-   Restore to specified environment
-   Preserve current state as rollback point
-   Require explicit confirmation for live environment

------------------------------------------------------------------------

### 2.3 Security Baseline

Introduce minimal but real security posture:

**Secrets Management:**
-   Strict `.env` handling (never committed)
-   Secrets never logged
-   Environment-specific secret files (`.env.dev`, `.env.live`)
-   `.env.template` shows required variables without values

**Runtime Security:**
-   No debug mode in `live` environment
-   Secure Telegram token storage
-   Principle of least privilege for file permissions

**Transport Security (if exposed externally):**
-   HTTPS for external API exposure
-   Telegram webhook uses HTTPS

**Audit Logging:**
-   Security-relevant events logged
-   Log rotation configured
-   Logs captured but secrets redacted

------------------------------------------------------------------------

### 2.4 Encryption at Rest (Where Practical)

Optional but recommended:

-   Event log encryption
-   SQLite database encryption (SQLCipher or equivalent)
-   Environment-specific encryption keys

If implemented:
-   Must not block normal operation
-   Keys must be manageable
-   Recovery process must be documented

If deferred:
-   Document as future work
-   Ensure file permissions are restrictive

------------------------------------------------------------------------

### 2.5 Security Documentation

Create `docs/SECURITY.md` covering:

-   Secrets management procedure
-   Backup/restore procedure
-   Data recovery process
-   Security incident response (basic)
-   Known limitations and accepted risks

------------------------------------------------------------------------

## 3. Non-Goals

Milestone 4 does NOT include:

-   Enterprise IAM
-   Multi-user authentication
-   Role-based access control
-   Container security
-   Network segmentation
-   Intrusion detection
-   SOC 2 compliance
-   New cognitive features

No premature enterprise security theater.

------------------------------------------------------------------------

## 4. Architectural Invariants

The following must remain true:

1.  Event log remains append-only even through backup/restore.
2.  Secrets never appear in repo, logs, or error messages.
3.  Data integrity is verifiable after restore.
4.  Security measures do not break normal operation.
5.  Documentation is sufficient for recovery without agent help.

------------------------------------------------------------------------

## 5. Deliverables

Milestone 4 is complete when:

-   Backup procedure scripted and tested
-   Restore procedure validated in dev environment
-   Security baseline implemented
-   Secrets management disciplined
-   Data and security documentation complete
-   System passes security self-audit (checklist-based)

------------------------------------------------------------------------

## 6. Acceptance Criteria

Milestone 4 is accepted when:

-   `make backup ENV=live` creates valid backup
-   `make restore ENV=dev BACKUP=<timestamp>` restores successfully
-   System operates with no secrets in logs
-   Documentation allows recovery without prior knowledge
-   Live environment runs with hardened configuration

If any of these fail, milestone is incomplete.

------------------------------------------------------------------------

## 7. Forward Pressure (Non-Binding)

Milestone 4 prepares for:

-   **Milestone 5+**: Feature expansion (todos, calendar, etc.)
-   Future: Multi-user support with proper auth
-   Future: Compliance requirements (if needed)
-   Future: Advanced monitoring and alerting

This completes the operational hardening arc. Subsequent milestones can focus on cognitive and functional expansion with confidence in the operational foundation.
