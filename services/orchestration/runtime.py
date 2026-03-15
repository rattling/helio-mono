"""LangGraph-backed orchestration runtime boundary for M13 flows."""

from __future__ import annotations

from dataclasses import dataclass
from inspect import isawaitable
from pathlib import Path
from typing import Any, Callable, NotRequired, TypedDict
from uuid import uuid4

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

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
from services.orchestration.checkpoints import PersistentInMemorySaver


@dataclass(slots=True)
class FlowCallbacks:
    gather_context: Callable[[], Any] | None = None
    prepare_delivery: Callable[[], Any] | None = None
    execute: Callable[[], Any] | None = None


class FlowState(TypedDict):
    workflow_name: str
    reminder_type: str
    envelope: dict[str, Any]
    trigger: str
    delivery_channel: str
    fingerprint: NotRequired[str | None]
    run_id: str
    status: NotRequired[str]
    reason: NotRequired[str]
    result: NotRequired[dict[str, Any]]
    policy_outcome: NotRequired[str]
    failure_stage: NotRequired[str]
    context: NotRequired[dict[str, Any]]
    prepared_delivery: NotRequired[dict[str, Any]]
    interrupt_before_delivery: NotRequired[bool]
    interrupt_on_policy_escalation: NotRequired[bool]
    interrupt_payload: NotRequired[dict[str, Any]]
    interrupt_decision: NotRequired[Any]


class OrchestrationRuntime:
    """Runtime adapter that emits orchestration transparency events around flow execution."""

    def __init__(
        self,
        event_store: FileEventStore,
        policy_evaluator: ControlPolicyEvaluator | None = None,
        checkpoint_path: str | None = None,
    ):
        self.event_store = event_store
        self.policy_evaluator = policy_evaluator or ControlPolicyEvaluator()
        self.checkpoint_path = checkpoint_path or self._default_checkpoint_path()
        self.checkpointer = PersistentInMemorySaver(self.checkpoint_path)
        self._callbacks: dict[str, FlowCallbacks] = {}
        self._graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(FlowState)
        graph.add_node("context_gather", self._context_gather_node)
        graph.add_node("policy_evaluation", self._policy_evaluation_node)
        graph.add_node("interrupt_gate", self._interrupt_gate_node)
        graph.add_node("delivery_prepare", self._delivery_prepare_node)
        graph.add_node("delivery_execution", self._delivery_execution_node)
        graph.add_node("terminal_success", self._terminal_success_node)
        graph.add_node("terminal_failure", self._terminal_failure_node)

        graph.add_edge(START, "context_gather")
        graph.add_edge("context_gather", "policy_evaluation")
        graph.add_conditional_edges(
            "policy_evaluation",
            self._policy_route,
            {
                "interrupt": "interrupt_gate",
                "continue": "delivery_prepare",
                "failure": "terminal_failure",
            },
        )
        graph.add_conditional_edges(
            "interrupt_gate",
            self._interrupt_route,
            {
                "continue": "delivery_prepare",
                "failure": "terminal_failure",
            },
        )
        graph.add_edge("delivery_prepare", "delivery_execution")
        graph.add_conditional_edges(
            "delivery_execution",
            self._delivery_route,
            {
                "success": "terminal_success",
                "failure": "terminal_failure",
            },
        )
        graph.add_edge("terminal_success", END)
        graph.add_edge("terminal_failure", END)
        return graph.compile(checkpointer=self.checkpointer, name="helionyx_orchestration")

    def _default_checkpoint_path(self) -> str:
        event_data_dir = Path(self.event_store.data_dir)
        return str(event_data_dir.parent / "orchestration" / "langgraph_checkpoints.pkl")

    @staticmethod
    def _graph_config(run_id: str) -> dict[str, Any]:
        return {"configurable": {"thread_id": run_id, "checkpoint_ns": "orchestration"}}

    def _register_callbacks(
        self,
        run_id: str,
        *,
        gather_context: Callable[[], Any] | None = None,
        prepare_delivery: Callable[[], Any] | None = None,
        execute: Callable[[], Any] | None = None,
    ) -> None:
        callbacks = self._callbacks.get(run_id, FlowCallbacks())
        if gather_context is not None:
            callbacks.gather_context = gather_context
        if prepare_delivery is not None:
            callbacks.prepare_delivery = prepare_delivery
        if execute is not None:
            callbacks.execute = execute
        self._callbacks[run_id] = callbacks

    def _callback_bundle(self, run_id: str) -> FlowCallbacks:
        return self._callbacks.get(run_id, FlowCallbacks())

    def _clear_callbacks(self, run_id: str) -> None:
        self._callbacks.pop(run_id, None)

    @staticmethod
    async def _resolve_callback(callback: Callable[[], Any] | None) -> dict[str, Any]:
        if callback is None:
            return {}
        result = callback()
        if isawaitable(result):
            result = await result
        if isinstance(result, dict):
            return result
        return {"value": result}

    @staticmethod
    def _policy_route(state: FlowState) -> str:
        if state.get("status") == PolicyOutcome.BLOCKED.value:
            return "failure"
        if state.get("status") == PolicyOutcome.ESCALATED.value and state.get(
            "interrupt_on_policy_escalation"
        ):
            return "interrupt"
        if state.get("interrupt_before_delivery"):
            return "interrupt"
        return "continue"

    @staticmethod
    def _interrupt_route(state: FlowState) -> str:
        return "failure" if state.get("status") == "failed" else "continue"

    @staticmethod
    def _delivery_route(state: FlowState) -> str:
        return "success" if state.get("status") == "completed" else "failure"

    async def _context_gather_node(self, state: FlowState) -> FlowState:
        run_id = state["run_id"]
        workflow_name = state["workflow_name"]

        await self.event_store.append(
            OrchestrationNodeEnteredEvent(
                run_id=run_id,
                workflow_name=workflow_name,
                node_id="context_gather",
            )
        )
        context = await self._resolve_callback(self._callback_bundle(run_id).gather_context)
        state["context"] = context
        await self.event_store.append(
            OrchestrationNodeCompletedEvent(
                run_id=run_id,
                workflow_name=workflow_name,
                node_id="context_gather",
                result=context or {"skipped": True},
            )
        )
        return state

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
            state["policy_outcome"] = policy_result.outcome.value
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
            state["status"] = PolicyOutcome.BLOCKED.value
            state["reason"] = policy_result.reason
            state["failure_stage"] = "policy"
            state["policy_outcome"] = policy_result.outcome.value
            return state

        await self.event_store.append(
            OrchestrationPolicyEscalatedEvent(
                run_id=run_id,
                workflow_name=workflow_name,
                reason=policy_result.reason,
                envelope=state["envelope"],
            )
        )
        state["status"] = PolicyOutcome.ESCALATED.value
        state["reason"] = policy_result.reason
        state["failure_stage"] = "policy"
        state["policy_outcome"] = policy_result.outcome.value
        return state

    async def _interrupt_gate_node(self, state: FlowState) -> FlowState:
        run_id = state["run_id"]
        workflow_name = state["workflow_name"]
        interrupt_payload = {
            "workflow_name": workflow_name,
            "reminder_type": state["reminder_type"],
            "delivery_channel": state["delivery_channel"],
            "reason": state.get("reason") or "manual_approval_required",
            "policy_outcome": state.get("policy_outcome"),
            **(state.get("interrupt_payload") or {}),
        }

        await self.event_store.append(
            OrchestrationNodeEnteredEvent(
                run_id=run_id,
                workflow_name=workflow_name,
                node_id="interrupt_gate",
            )
        )
        await self.event_store.append(
            OrchestrationRunCheckpointEvent(
                run_id=run_id,
                workflow_name=workflow_name,
                checkpoint="interrupt_requested",
                details=interrupt_payload,
            )
        )

        decision = interrupt(interrupt_payload)

        await self.event_store.append(
            OrchestrationRunCheckpointEvent(
                run_id=run_id,
                workflow_name=workflow_name,
                checkpoint="interrupt_resumed",
                details={"approved": self._resume_allows(decision)},
            )
        )
        state["interrupt_decision"] = decision
        await self.event_store.append(
            OrchestrationNodeCompletedEvent(
                run_id=run_id,
                workflow_name=workflow_name,
                node_id="interrupt_gate",
                result={"approved": self._resume_allows(decision)},
            )
        )

        if not self._resume_allows(decision):
            state["status"] = "failed"
            state["reason"] = "interrupt_rejected"
            state["failure_stage"] = "interrupt"
            state["result"] = {"resume_value": decision}
            return state

        state.pop("status", None)
        state.pop("reason", None)
        state.pop("failure_stage", None)
        return state

    async def _delivery_prepare_node(self, state: FlowState) -> FlowState:
        run_id = state["run_id"]
        workflow_name = state["workflow_name"]

        await self.event_store.append(
            OrchestrationNodeEnteredEvent(
                run_id=run_id,
                workflow_name=workflow_name,
                node_id="delivery_prepare",
            )
        )
        prepared_delivery = await self._resolve_callback(
            self._callback_bundle(run_id).prepare_delivery
        )
        state["prepared_delivery"] = prepared_delivery
        await self.event_store.append(
            OrchestrationNodeCompletedEvent(
                run_id=run_id,
                workflow_name=workflow_name,
                node_id="delivery_prepare",
                result=prepared_delivery or {"skipped": True},
            )
        )
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
            execute = self._callback_bundle(run_id).execute
            if execute is None:
                raise RuntimeError("missing_execute_callback")
            result = execute()
            if isawaitable(result):
                result = await result
            state["result"] = result or {}
        except Exception as exc:
            await self.event_store.append(
                OrchestrationNodeFallbackEvent(
                    run_id=run_id,
                    workflow_name=workflow_name,
                    node_id="delivery_execution",
                    fallback_node_id="terminal_failure",
                    reason=str(exc),
                )
            )
            state["status"] = "failed"
            state["reason"] = "delivery_exception"
            state["failure_stage"] = "delivery"
            state["result"] = {"exception": str(exc)}
            return state

        sent = bool((state.get("result") or {}).get("sent"))
        if sent:
            state["status"] = "completed"
            state.pop("failure_stage", None)
            return state

        state["status"] = "failed"
        state["reason"] = str((state.get("result") or {}).get("reason") or "delivery_not_sent")
        state["failure_stage"] = "delivery"
        return state

    async def _terminal_success_node(self, state: FlowState) -> FlowState:
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
        self._clear_callbacks(run_id)
        return state

    async def _terminal_failure_node(self, state: FlowState) -> FlowState:
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
        elif state.get("failure_stage") == "policy":
            details = {"policy_outcome": state.get("policy_outcome")}

        if state.get("failure_stage") == "delivery":
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
        self._clear_callbacks(run_id)
        return state

    @staticmethod
    def _resume_allows(decision: Any) -> bool:
        if isinstance(decision, bool):
            return decision
        if isinstance(decision, str):
            return decision.strip().lower() in {"approve", "approved", "continue", "resume", "yes"}
        if isinstance(decision, dict):
            approved = decision.get("approved")
            if isinstance(approved, bool):
                return approved
        return bool(decision)

    @staticmethod
    def _interrupt_result(run_id: str, final_state: dict[str, Any]) -> dict[str, Any]:
        interrupts = [getattr(item, "value", item) for item in final_state.get("__interrupt__", [])]
        return {
            "run_id": run_id,
            "status": "interrupted",
            "interrupts": interrupts,
            "interrupt": interrupts[0] if interrupts else None,
        }

    @staticmethod
    def _terminal_result(run_id: str, final_state: dict[str, Any]) -> dict[str, Any]:
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

    async def run_flow(
        self,
        workflow_name: str,
        reminder_type: str,
        execute: Callable[[], Any],
        envelope: dict[str, Any],
        trigger: str = "scheduler",
        delivery_channel: str = "telegram",
        fingerprint: str | None = None,
        gather_context: Callable[[], Any] | None = None,
        prepare_delivery: Callable[[], Any] | None = None,
        interrupt_before_delivery: bool = False,
        interrupt_on_policy_escalation: bool = False,
        interrupt_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        run_id = str(uuid4())
        self._register_callbacks(
            run_id,
            gather_context=gather_context,
            prepare_delivery=prepare_delivery,
            execute=execute,
        )

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
                "envelope": envelope,
                "trigger": trigger,
                "delivery_channel": delivery_channel,
                "fingerprint": fingerprint,
                "run_id": run_id,
                "interrupt_before_delivery": interrupt_before_delivery,
                "interrupt_on_policy_escalation": interrupt_on_policy_escalation,
                "interrupt_payload": interrupt_payload or {},
            },
            config=self._graph_config(run_id),
        )

        if "__interrupt__" in final_state:
            return self._interrupt_result(run_id, final_state)

        return self._terminal_result(run_id, final_state)

    async def resume_flow(
        self,
        run_id: str,
        resume_value: Any,
        *,
        execute: Callable[[], Any] | None = None,
        gather_context: Callable[[], Any] | None = None,
        prepare_delivery: Callable[[], Any] | None = None,
    ) -> dict[str, Any]:
        self._register_callbacks(
            run_id,
            gather_context=gather_context,
            prepare_delivery=prepare_delivery,
            execute=execute,
        )

        final_state = await self._graph.ainvoke(
            Command(resume=resume_value),
            config=self._graph_config(run_id),
        )

        if "__interrupt__" in final_state:
            return self._interrupt_result(run_id, final_state)

        return self._terminal_result(run_id, final_state)
