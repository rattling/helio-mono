# M6-M8 Learning Rollout Runbook

## Purpose

Operate bounded-learning safely across Milestones 6-8: deterministic attention/planning stays authoritative, while model scoring runs in shadow mode and is promoted only after gate checks.

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

Inspect per-target diagnostics (Milestone 8):

```bash
jq '.target_diagnostics' data/projections/attention_replay_report.json
```

## Milestone 8 Interpretation Model

Milestone 8 upgrades learning semantics from a single coarse signal to three explicit targets:

- `usefulness_score`: whether the reminder meaningfully helped progress
- `timing_fit_score`: whether the reminder arrived at the right moment
- `interrupt_cost_score`: whether the reminder was disruptive

These targets are interpreted together:

- High usefulness + low timing fit + high interrupt cost -> prefer `retime`
- Low usefulness + high interrupt cost -> prefer `deprioritize`
- High usefulness + high timing fit + low/medium interrupt cost -> `keep`

Guardrail remains unchanged: deterministic priority buckets stay authoritative.

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

Milestone 8 diagnostics should also be present:

- `target_diagnostics.usefulness`
- `target_diagnostics.timing_fit`
- `target_diagnostics.interrupt_cost`

If replay data is insufficient, diagnostics may report `insufficient_data`; this is acceptable for cold-start windows.

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

## QA Checklist (Ambiguous Feedback Scenarios)

Run these checks in order and record outputs for reproducibility:

1. Contract + semantic rule checks:

```bash
.venv/bin/python -m pytest -q tests/test_contract_feedback_events.py tests/test_learning_semantics.py
```

2. Attention API + policy integration checks:

```bash
.venv/bin/python -m pytest -q tests/test_api_attention.py
```

3. Replay diagnostics checks (including per-target metrics):

```bash
.venv/bin/python -m pytest -q tests/test_attention_replay_eval.py
```

4. Full regression suite:

```bash
.venv/bin/python -m pytest -q
```

Manual interpretation checklist for ambiguous reminder actions:

- Dismiss + quick follow-up activity is interpreted as likely useful
- Snooze favors timing-mismatch interpretation over pure negative usefulness
- Attention ordering changes stay within deterministic bucket boundaries
- Candidate explanations include target-aware rationale and recommended action

## Notes

- Suggestions remain explicit-apply only.
- No model output may mutate task state without user action.
- Event log is source of truth for all replay/evaluation.
