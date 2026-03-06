# Two Prompts (Canonical)

These are intentionally short.
They *only* set mode + context; the detailed rules live in `.github/copilot-instructions.md` and the mode guides.

Operational companion docs:
- `docs/process/MILESTONE_EXECUTION_RUNBOOK.md`
- `docs/process/PROCESS_CHANGELOG.md`

---

## Prompt 1 — ARCH (plan the milestone)

```text
MODE: ARCH
MILESTONE: <N + name>

Input: I will paste the full milestone charter below.

Do ARCH-mode work per repo instructions:
- restate goal/scope/non-goals
- identify needed contracts/ADRs
- create milestone issues + meta-issue

Milestone charter:
<PASTE HERE>
```

---

## Prompt 2 — DEV → QA (implement, validate, PR)

```text
MODE: DEV then QA
MILESTONE: <N + name>

Input: Use the milestone meta-issue + all milestone issues as the source of truth.

Session status context (required):
- Starting fresh: "Starting work on Milestone <N>. Dev/test. No work done yet."
- Continuing: "Continuing Milestone <N>. Dev/test. Current focus is issue #<id>. <x>/<total> issues completed."

Issue source-of-truth rule:
- Derive milestone issue list from the meta-issue checklist items only.
- Do not infer full issue set from milestone-title search results.

Do DEV-mode implementation, then switch to QA-mode validation.

Critical QA rule: if you find a bug in QA mode, create a bug issue first; then switch to DEV mode to fix; then return to QA mode to recheck.

If QA passes, create the milestone PR.
```
