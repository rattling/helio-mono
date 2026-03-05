# Milestone 6 --- Attention + Planning Assistant (Merged M6/M7)

**Architecture ADR**: [ADR_M6_BOUNDED_LEARNING_FROM_FEEDBACK.md](ADR_M6_BOUNDED_LEARNING_FROM_FEEDBACK.md)

## Objective

Turn Helionyx from a passive task store into a practical weekly operating
assistant: it should tell the user what matters now, what is blocked,
and what concrete next steps are suggested.

------------------------------------------------------------------------

## What the User Gets

By the end of this milestone, a user should be able to:

- Receive a daily Telegram digest with top priorities and near-term due work
- Receive a weekly Telegram lookahead for upcoming commitments and risk areas
- Get urgent reminders without spammy duplicates
- See stale tasks that need cleanup attention
- Ask for dependency suggestions on a task (proposed, never auto-applied)
- Ask for task-splitting suggestions for vague or oversized tasks
- Explicitly accept or reject suggestions, with rationale preserved in history
- Use plan queues that answer: “What should I do next?”, “What can I unblock?”,
  and “What is waiting/snoozed?”

------------------------------------------------------------------------

## User Experience Scope

### Daily loop

- Morning: user receives a short digest (top actionable items, due soon,
  one cleanup candidate)
- During the day: urgent reminders fire only when threshold conditions are met
- User can review and act without searching across multiple lists

### Weekly loop

- User receives a weekly lookahead covering due-this-week work, high-priority
  undated work, and blocked summary
- User can request planning help (dependencies/split) for tasks that are stuck
  or unclear

### Suggestion safety model

- Suggestions are advisory only
- Nothing changes automatically
- Every applied suggestion is event-logged and explainable

------------------------------------------------------------------------

## Product Acceptance Criteria

- Digests arrive at configured times and match current task state
- Urgent reminders do not repeat duplicate notifications for the same condition
- “Why is this urgent?” is always explainable in user-visible terms
- Suggested dependencies are reasonable and keep the graph acyclic by default
- Suggested task splits for vague tasks produce actionable child steps
- Applying a suggestion requires explicit user acceptance
- Plan views are stable enough for UI/API consumers (predictable filtering,
  ordering, and pagination semantics)

------------------------------------------------------------------------

## How to Test (Operator Checklist)

Use this checklist as milestone verification from a user perspective.

1. Seed a realistic task set
	- Include: due-soon tasks, blocked tasks, stale tasks, and one vague task

2. Verify daily attention output
	- Run attention generation and inspect “today” queue
	- Confirm top actionable ordering and urgency explanations are sensible
	- Confirm digest includes:
	  - Top 5 actionable
	  - Due in next 72h
	  - 1 stale cleanup candidate

3. Verify weekly lookahead output
	- Inspect weekly queue/digest
	- Confirm sections include:
	  - Due this week
	  - High priority without due date
	  - Blocked summary

4. Verify anti-spam reminder behavior
	- Trigger reminder evaluation multiple times with unchanged state
	- Confirm no duplicate reminder spam is emitted

5. Verify planning suggestions
	- Request dependency suggestions and split suggestions for a target task
	- Confirm each suggestion includes rationale
	- Confirm no changes occur until explicit apply
	- Apply one suggestion and verify event log captures the action

6. Verify plan views
	- Confirm “next actions”, “unblock-first”, and “waiting/snoozed” queues
	  are coherent and reproducible across repeated reads

7. Regression sanity check
	- Confirm task lifecycle operations still work after attention/planning runs

------------------------------------------------------------------------

## Implementation Scope (APIs + Jobs)

### Attention APIs

GET /attention/today\
GET /attention/week\
POST /attention/run

### Suggestion APIs

POST /tasks/{id}/suggest-dependencies\
POST /tasks/{id}/suggest-split\
POST /tasks/{id}/apply-suggestion

### Background jobs

- Daily digest generator
- Weekly digest generator
- Urgent threshold detector
- Reminder delivery logging
- Stale review candidate selector

All reminders and suggestions must be reproducible from API-visible state and
event history.

------------------------------------------------------------------------

## Non-Goals

- No autonomous task execution
- No calendar auto-placement or full calendar optimization
- No heavy black-box planning behavior
