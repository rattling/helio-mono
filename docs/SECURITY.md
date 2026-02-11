# Helionyx Security Baseline (Milestone 4)

This document describes Helionyx’s minimal security posture for daily use.

## Scope

- Secrets discipline (`.env` handling)
- Log redaction baseline
- Audit logging baseline
- Log retention/rotation baseline (systemd/journald)
- Encryption-at-rest decision

Non-goals:
- AuthN/AuthZ/RBAC
- Rate limiting
- Network segmentation
- Enterprise security tooling

## Secrets Discipline

- Never commit `.env`, `.env.dev`, `.env.staging`, `.env.live`.
- Use [.env.template](../.env.template) to enumerate required variables (no secret values).
- For node1 deployments, create `.env.{env}` from `.env.{env}.example` and set strict permissions:

```bash
cp .env.live.example .env.live
chmod 600 .env.live
```

### What counts as a secret

- `OPENAI_API_KEY`
- `TELEGRAM_BOT_TOKEN`

Treat these as secrets even in dev.

## Logging Redaction

Helionyx applies a best-effort redaction filter to log messages via [shared/common/logging.py](../shared/common/logging.py).

Redaction targets:
- OpenAI-style keys (e.g. `sk-...`)
- Telegram bot token format (e.g. `123456:ABC...`)
- Common env-var key/value patterns

This is a pragmatic baseline, not a guarantee. Avoid logging secrets in the first place.

## Audit Logging (Baseline)

Helionyx emits basic audit logs for security-relevant actions:
- Config loaded (environment)
- Extraction triggers (API)
- Backup/restore scripts print `AUDIT ...` lines for operator visibility

Audit logs are intended to help answer “what happened” during operations without including sensitive content.

## Log Rotation / Retention

Production services log to `journald` (systemd journal). Journal retention is configured globally.

This repo provides a baseline snippet:
- [deployment/systemd/journald.conf.d/helionyx.conf](../deployment/systemd/journald.conf.d/helionyx.conf)

Install (recommended):

```bash
sudo mkdir -p /etc/systemd/journald.conf.d
sudo cp deployment/systemd/journald.conf.d/helionyx.conf /etc/systemd/journald.conf.d/
sudo systemctl restart systemd-journald
```

Inspect logs:

```bash
sudo journalctl -u helionyx -n 200
sudo journalctl -u helionyx -f
```

## Encryption at Rest

M4 decision: defer application-level encryption-at-rest.

See ADR:
- [docs/ADR_M4_ENCRYPTION_AT_REST.md](ADR_M4_ENCRYPTION_AT_REST.md)

Compensating controls:
- Restrictive filesystem permissions for runtime data and backups
- Host-level disk encryption where applicable

## Incident Response (Minimal)

If you suspect a credential leak:

1. Rotate the compromised secret (OpenAI key, Telegram bot token).
2. Stop the impacted service (`sudo systemctl stop helionyx`).
3. Check recent logs for suspicious activity (`journalctl -u helionyx -n 500`).
4. Verify `.env.*` permissions and that no secrets were committed.
