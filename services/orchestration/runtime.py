"""Deterministic orchestration runtime boundary for M12 flows."""

from __future__ import annotations

from inspect import isawaitable
from typing import Any, Callable
from uuid import uuid4

from shared.contracts import (
    OrchestrationDeliveryAttemptedEvent,
    OrchestrationDeliveryFailedEvent,
    OrchestrationDeliverySucceededEvent,
    OrchestrationNodeCompletedEvent,
    OrchestrationNodeEnteredEvent,
    OrchestrationNodeFallbackEvent,
    OrchestrationPolicyAllowedEvent,
    OrchestrationPolicyBlockedEvent,
    OrchestrationPolicyEscalatedEvent,
    OrchestrationRunCheckpointEvent,
    OrchestrationRunFailedEvent,
    OrchestrationRunFinishedEvent,
    OrchestrationRunStartedEvent,
)
from services.control import ControlPolicyEvaluator, PolicyOutcome
from services.event_store.file_store import FileEventStore


class OrchestrationRuntime:
    """Runtime adapter that emits orchestration transparency events around flow execution."""

    def __init__(
        self,
        event_store: FileEventStore,
        policy_evaluator: ControlPolicyEvaluator | None = None,
    ):
        self.event_store = event_store
        self.policy_evaluator = policy_evaluator or ControlPolicyEvaluator()

    async def run_flow(
        self,
        workflow_name: str,
        reminder_type: str,
        execute: Callable[[], Any],
        envelope: dict[str, Any],
        trigger: str = "scheduler",
        delivery_channel: str = "telegram",
        fingerprint: str | None = None,
    ) -> dict[str, Any]:
        run_id = str(uuid4())

        await self.event_store.append(
            OrchestrationRunStartedEvent(
                run_id=run_id,
                workflow_name=workflow_name,
                trigger=trigger,
                metadata={"reminder_type": reminder_type},
            )
        )

        await self.event_store.append(
            OrchestrationNodeEnteredEvent(
                run_id=run_id,
                workflow_name=workflow_name,
                node_id="policy_evaluation",
            )
        )
        policy_result = self.policy_evaluator.evaluate(envelope)
        await self.event_store.append(
            OrchestrationNodeCompletedEvent(
                run_id=run_id,
                workflow_name=workflow_name,
                node_id="policy_evaluation",
                result={
                    "outcome": policy_result.outcome.value,
                    "reason": policy_result.reason,
                    "details": policy_result.details,
                },
            )
        )

        if policy_result.outcome == PolicyOutcome.ALLOWED:
            await self.event_store.append(
                OrchestrationPolicyAllowedEvent(
                    run_id=run_id,
                    workflow_name=workflow_name,
                    reason=policy_result.reason,
                    envelope=envelope,
                )
            )
        elif policy_result.outcome == PolicyOutcome.BLOCKED:
            await self.event_store.append(
                OrchestrationPolicyBlockedEvent(
                    run_id=run_id,
                    workflow_name=workflow_name,
                    reason=policy_result.reason,
                    envelope=envelope,
                )
            )
            await self.event_store.append(
                OrchestrationRunFailedEvent(
                    run_id=run_id,
                    workflow_name=workflow_name,
                    reason=policy_result.reason,
                    details={"policy_outcome": policy_result.outcome.value},
                )
            )
            return {
                "run_id": run_id,
                "status": PolicyOutcome.BLOCKED.value,
                "reason": policy_result.reason,
            }
        else:
            await self.event_store.append(
                OrchestrationPolicyEscalatedEvent(
                    run_id=run_id,
                    workflow_name=workflow_name,
                    reason=policy_result.reason,
                    envelope=envelope,
                )
            )
            await self.event_store.append(
                OrchestrationRunFailedEvent(
                    run_id=run_id,
                    workflow_name=workflow_name,
                    reason=policy_result.reason,
                    details={"policy_outcome": policy_result.outcome.value},
                )
            )
            return {
                "run_id": run_id,
                "status": PolicyOutcome.ESCALATED.value,
                "reason": policy_result.reason,
            }

        await self.event_store.append(
            OrchestrationNodeEnteredEvent(
                run_id=run_id,
                workflow_name=workflow_name,
                node_id="delivery_execution",
            )
        )
        await self.event_store.append(
            OrchestrationRunCheckpointEvent(
                run_id=run_id,
                workflow_name=workflow_name,
                checkpoint="delivery_attempt",
                details={"reminder_type": reminder_type, "delivery_channel": delivery_channel},
            )
        )
        await self.event_store.append(
            OrchestrationDeliveryAttemptedEvent(
                run_id=run_id,
                workflow_name=workflow_name,
                reminder_type=reminder_type,
                delivery_channel=delivery_channel,
                fingerprint=fingerprint,
            )
        )

        try:
            result = execute()
            if isawaitable(result):
                result = await result
        except Exception as exc:
            await self.event_store.append(
                OrchestrationNodeFallbackEvent(
                    run_id=run_id,
                    workflow_name=workflow_name,
                    node_id="delivery_execution",
                    fallback_node_id="delivery_failure",
                    reason=str(exc),
                )
            )
            await self.event_store.append(
                OrchestrationDeliveryFailedEvent(
                    run_id=run_id,
                    workflow_name=workflow_name,
                    reminder_type=reminder_type,
                    delivery_channel=delivery_channel,
                    reason="delivery_exception",
                    fingerprint=fingerprint,
                    details={"exception": str(exc)},
                )
            )
            await self.event_store.append(
                OrchestrationRunFailedEvent(
                    run_id=run_id,
                    workflow_name=workflow_name,
                    reason="delivery_exception",
                    details={"exception": str(exc)},
                )
            )
            return {
                "run_id": run_id,
                "status": "failed",
                "reason": "delivery_exception",
            }

        sent = bool((result or {}).get("sent"))
        if sent:
            await self.event_store.append(
                OrchestrationDeliverySucceededEvent(
                    run_id=run_id,
                    workflow_name=workflow_name,
                    reminder_type=reminder_type,
                    delivery_channel=delivery_channel,
                    fingerprint=fingerprint,
                    details=result or {},
                )
            )
            await self.event_store.append(
                OrchestrationNodeCompletedEvent(
                    run_id=run_id,
                    workflow_name=workflow_name,
                    node_id="delivery_execution",
                    result=result or {},
                )
            )
            await self.event_store.append(
                OrchestrationRunFinishedEvent(
                    run_id=run_id,
                    workflow_name=workflow_name,
                    status="completed",
                    output=result or {},
                )
            )
            return {"run_id": run_id, "status": "completed", "result": result or {}}

        reason = (result or {}).get("reason") or "delivery_not_sent"
        await self.event_store.append(
            OrchestrationDeliveryFailedEvent(
                run_id=run_id,
                workflow_name=workflow_name,
                reminder_type=reminder_type,
                delivery_channel=delivery_channel,
                reason=str(reason),
                fingerprint=fingerprint,
                details=result or {},
            )
        )
        await self.event_store.append(
            OrchestrationRunFailedEvent(
                run_id=run_id,
                workflow_name=workflow_name,
                reason=str(reason),
                details=result or {},
            )
        )
        return {"run_id": run_id, "status": "failed", "reason": str(reason), "result": result or {}}
