# Issue Template

## Title
```
[<Service/Area>] <Action-oriented description>
```

## Objective
<1–3 sentences describing the outcome this issue should achieve.>

## Context
- Links: <related issues, PRs, docs>
- Constraints: <invariants, contracts, assumptions>

## Acceptance Criteria
- [ ] <criterion 1>
- [ ] <criterion 2>

## Required Tests (must pass)
- [ ] New/updated tests:
	- `<tests/path_or_name>`
- [ ] Regression tests:
	- `<tests/path_or_name>`
- [ ] Command(s):
	- `.venv/bin/python -m pytest -q <tests...>`

Rules:
- Every issue must include this section before implementation starts.
- If behavior changes and no new test is added, explain why under Implementation Notes.
- An issue is not complete unless its listed test command(s) pass or a blocker issue is explicitly created.

## Non-goals
- <explicitly out of scope items>

## Implementation Notes (optional)
- <hints, file paths, contracts touched>

## Verification Notes (optional)
- Runtime/manual checks to run in addition to tests:
	- `<command + expected outcome>`

## Size
S / M / L

Guidance:
- S: trivial, low risk
- M: normal issue
- L: too large — must be split
