"""Contract tests for Data Explorer shared models (Milestone 10)."""

from shared.contracts import (
    ExplorerDeepLinkContext,
    ExplorerEntityType,
    ExplorerLookupResponse,
    ExplorerViewMode,
)


def test_explorer_lookup_contract_shape():
    payload = ExplorerLookupResponse(
        entity_type=ExplorerEntityType.TASK,
        entity_id="abc",
        canonical={"task_id": "abc"},
    )
    assert payload.entity_type == ExplorerEntityType.TASK
    assert payload.canonical["task_id"] == "abc"


def test_deep_link_context_defaults():
    context = ExplorerDeepLinkContext(entity_type=ExplorerEntityType.TASK, entity_id="abc")
    assert context.view == ExplorerViewMode.LOOKUP
