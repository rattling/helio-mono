"""LangGraph-backed orchestration runtime boundary for M12 flows."""

from __future__ import annotations

from inspect import isawaitable
from typing import Any, Callable, NotRequired, TypedDict
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

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


class FlowState(TypedDict):
    workflow_name: str
    reminder_type: str
    envelope: dict[str, Any]
    trigger: str
    delivery_channel: str
    fingerprint: NotRequired[str | None]
    run_id: str
    execute: Callable[[], Any]
    status: NotRequired[str]
    reason: NotRequired[str]
    result: NotRequired[dict[str, Any]]
    policy_outcome: NotRequired[str]


class OrchestrationRuntime:
    """Runtime adapter that emits orchestration transparency events around flow execution."""

    def __init__(
        self,
        event_store: FileEventStore,
        policy_evaluator: ControlPolicyEvaluator | None = None,
    ):
        self.event_store = event_store
        self.policy_evaluator = policy_evaluator or ControlPolicyEvaluator()
        self._graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(FlowState)
        graph.add_node("policy_evaluation", self._policy_evaluation_node)
        graph.add_node("delivery_execution", self._delivery_execution_node)
        graph.add_node("delivery_success", self._delivery_success_node)
        graph.add_node("delivery_failure", self._delivery_failure_node)

        graph.add_edge(START, "policy_evaluation")
        graph.add_conditional_edges(
            "policy_evaluation",
            self._policy_route,
            {
                "continue": "delivery_execution",
                "halt": END,
            },
        )
        graph.add_conditional_edges(
            "delivery_execution",
            self._delivery_route,
            {
                "success": "delivery_success",
                "failure": "delivery_failure",
            },
        )
        graph.add_edge("delivery_success", END)
        graph.add_edge("delivery_failure", END)
        return graph.compile()

    @staticmethod
    def _policy_route(state: FlowState) -> str:
        if state.get("status") in {PolicyOutcome.BLOCKED.value, PolicyOutcome.ESCALATED.value}:
            return "halt"
        return "continue"

    @staticmethod
    def _delivery_route(state: FlowState) -> str:
        return "success" if state.get("status") == "completed" else "failure"

    async def _policy_evaluation_node(self, state: FlowState) -> FlowState:
        run_id = state["run_id"]
        workflow_name = state["workflow_name"]

        await self.event_store.append(
            OrchestrationNodeEnteredEvent(
                run_id=run_id,
                workflow_name=workflow_name,
                node_id="policy_evaluation",
            )
        )
        policy_result = self.policy_evaluator.evaluate(state["envelope"])
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
                    envelope=state["envelope"],
                )
            )
            return state

        if policy_result.outcome == PolicyOutcome.BLOCKED:
            await self.event_store.append(
                OrchestrationPolicyBlockedEvent(
                    run_id=run_id,
                    workflow_name=workflow_name,
                    reason=policy_result.reason,
                    envelope=state["envelope"],
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
            state["status"] = PolicyOutcome.BLOCKED.value
            state["reason"] = policy_result.reason
            return state

        await self.event_store.append(
            OrchestrationPolicyEscalatedEvent(
                run_id=run_id,
                workflow_name=workflow_name,
                reason=policy_result.reason,
                envelope=state["envelope"],
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
        state["status"] = PolicyOutcome.ESCALATED.value
        state["reason"] = policy_result.reason
        return state

    async def _delivery_execution_node(self, state: FlowState) -> FlowState:
        run_id = state["run_id"]
        workflow_name = state["workflow_name"]
        reminder_type = state["reminder_type"]
        delivery_channel = state["delivery_channel"]
        fingerprint = state.get("fingerprint")

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
            result = state["execute"]()
            if isawaitable(result):
                result = await result
            state["result"] = result or {}
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
            state["status"] = "failed"
            state["reason"] = "delivery_exception"
            state["result"] = {"exception": str(exc)}
            return state

        sent = bool((state.get("result") or {}).get("sent"))
        if sent:
            state["status"] = "completed"
            return state

        state["status"] = "failed"
        state["reason"] = str((state.get("result") or {}).get("reason") or "delivery_not_sent")
        return state

    async def _delivery_success_node(self, state: FlowState) -> FlowState:
        run_id = state["run_id"]
        workflow_name = state["workflow_name"]
        reminder_type = state["reminder_type"]
        delivery_channel = state["delivery_channel"]
        fingerprint = state.get("fingerprint")
        result = state.get("result") or {}

        await self.event_store.append(
            OrchestrationDeliverySucceededEvent(
                run_id=run_id,
                workflow_name=workflow_name,
                reminder_type=reminder_type,
                delivery_channel=delivery_channel,
                fingerprint=fingerprint,
                details=result,
            )
        )
        await self.event_store.append(
            OrchestrationNodeCompletedEvent(
                run_id=run_id,
                workflow_name=workflow_name,
                node_id="delivery_execution",
                result=result,
            )
        )
        await self.event_store.append(
            OrchestrationRunFinishedEvent(
                run_id=run_id,
                workflow_name=workflow_name,
                status="completed",
                output=result,
            )
        )
        return state

    async def _delivery_failure_node(self, state: FlowState) -> FlowState:
        run_id = state["run_id"]
        workflow_name = state["workflow_name"]
        reminder_type = state["reminder_type"]
        delivery_channel = state["delivery_channel"]
        fingerprint = state.get("fingerprint")
        reason = str(state.get("reason") or "delivery_not_sent")
        result = state.get("result") or {}

        details = result
        if reason == "delivery_exception":
            details = {"exception": result.get("exception", "unknown")}

        await self.event_store.append(
            OrchestrationDeliveryFailedEvent(
                run_id=run_id,
                workflow_name=workflow_name,
                reminder_type=reminder_type,
                delivery_channel=delivery_channel,
                reason=reason,
                fingerprint=fingerprint,
                details=details,
            )
        )
        await self.event_store.append(
            OrchestrationRunFailedEvent(
                run_id=run_id,
                workflow_name=workflow_name,
                reason=reason,
                details=details,
            )
        )
        return state

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

        final_state = await self._graph.ainvoke(
            {
                "workflow_name": workflow_name,
                "reminder_type": reminder_type,
                "execute": execute,
                "envelope": envelope,
                "trigger": trigger,
                "delivery_channel": delivery_channel,
                "fingerprint": fingerprint,
                "run_id": run_id,
            }
        )

        status = final_state.get("status")
        reason = final_state.get("reason")
        result = final_state.get("result") or {}

        if status in {PolicyOutcome.BLOCKED.value, PolicyOutcome.ESCALATED.value}:
            return {
                "run_id": run_id,
                "status": str(status),
                "reason": str(reason or "policy_blocked"),
            }

        if status == "completed":
            return {"run_id": run_id, "status": "completed", "result": result}

        return {
            "run_id": run_id,
            "status": "failed",
            "reason": str(reason or "delivery_not_sent"),
            "result": result,
        }
