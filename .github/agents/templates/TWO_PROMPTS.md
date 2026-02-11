# Two Prompts (Canonical)

These are intentionally short.
They *only* set mode + context; the detailed rules live in `.github/copilot-instructions.md` and the mode guides.

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

Do DEV-mode implementation, then switch to QA-mode validation.

Critical QA rule: if you find a bug in QA mode, create a bug issue first; then switch to DEV mode to fix; then return to QA mode to recheck.

If QA passes, create the milestone PR.
```
