# M6 Learning Rollout Runbook

## Purpose

Operate Milestone 6 bounded-learning safely: deterministic attention/planning stays authoritative, while model scoring runs in shadow mode and is promoted only after gate checks.

## Preconditions

- Service is runnable (`make run`)
- Task and attention APIs are operational
- Event log is writable
- Telegram configuration is valid for digest/reminder paths (if enabled)

## Key Commands

Set runtime personalization mode (single control):

```bash
export ATTENTION_PERSONALIZATION_MODE=deterministic  # deterministic | shadow | bounded
```

Run replay evaluation report:

```bash
.venv/bin/python scripts/evaluate_attention_replay.py --out data/projections/attention_replay_report.json
```

Run Stage B readiness check (readiness only; no exploration enablement):

```bash
.venv/bin/python scripts/evaluate_attention_replay.py --rollback-verified --out data/projections/attention_replay_report.json
```

Inspect report:

```bash
cat data/projections/attention_replay_report.json
```

## Rollout Stages

### Stage 0 — Deterministic Baseline

- Set `ATTENTION_PERSONALIZATION_MODE=deterministic`
- Confirm `/attention/today` and `/attention/week` outputs are stable and explainable

### Stage 1 — Shadow Mode

- Set `ATTENTION_PERSONALIZATION_MODE=shadow`
- Confirm `model_score_recorded` events are present
- Confirm user-visible ordering is unchanged

### Stage 1.5 — Bounded Stage A

- Set `ATTENTION_PERSONALIZATION_MODE=bounded`
- Confirm ranking changes are limited to deterministic bucket boundaries
- Confirm `personalization_applied` and explanation fields are present in attention payloads

### Stage 2 — Gate Evaluation

Run replay report and verify gates:

- `gate_acceptance_rate_nonzero`
- `gate_duplicate_reminder_rate_below_5pct`
- `gate_shadow_data_present`

All gates must be `true` before any production influence is considered.

### Stage B Readiness (Bandit Not Enabled)

- Inspect `stage_b_readiness` in the replay report
- Confirm checks pass for:
	- interaction volume
	- acceptance/noise non-regression
	- calibration quality
	- rollback verification
- Keep exploration disabled until readiness is explicitly true

## Dry-Run Rollback Procedure

1. Force deterministic mode (single rollback command):

```bash
export ATTENTION_PERSONALIZATION_MODE=deterministic
```

2. Restart service:

```bash
make restart ENV=dev
```

3. Verify fallback:

- Call `/attention/today`
- Confirm deterministic `urgency_score` and explanations are still returned
- Confirm `personalization_policy` is `deterministic_only`
- Confirm `personalization_applied` remains `false`

4. Re-run replay report and verify system remains operational.

## Notes

- Suggestions remain explicit-apply only.
- No model output may mutate task state without user action.
- Event log is source of truth for all replay/evaluation.
