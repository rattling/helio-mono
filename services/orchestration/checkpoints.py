"""Persistent LangGraph checkpoint helpers for orchestration flows."""

from __future__ import annotations

import pickle
from collections import defaultdict
from pathlib import Path
from typing import Any, Sequence

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import ChannelVersions, Checkpoint, CheckpointMetadata
from langgraph.checkpoint.memory import InMemorySaver


class PersistentInMemorySaver(InMemorySaver):
    """File-backed wrapper around LangGraph's in-memory saver."""

    def __init__(self, path: str):
        super().__init__()
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            self._load()

    def _load(self) -> None:
        with self.path.open("rb") as handle:
            payload = pickle.load(handle)

        storage_payload = payload.get("storage", {})
        self.storage = defaultdict(lambda: defaultdict(dict))
        for thread_id, namespaces in storage_payload.items():
            self.storage[thread_id] = defaultdict(
                dict,
                {
                    checkpoint_ns: dict(checkpoints)
                    for checkpoint_ns, checkpoints in namespaces.items()
                },
            )

        self.writes = defaultdict(
            dict,
            {key: dict(value) for key, value in payload.get("writes", {}).items()},
        )
        self.blobs = defaultdict(None, dict(payload.get("blobs", {})))

    def _persist(self) -> None:
        serialized = {
            "storage": {
                thread_id: {
                    checkpoint_ns: dict(checkpoints)
                    for checkpoint_ns, checkpoints in namespaces.items()
                }
                for thread_id, namespaces in self.storage.items()
            },
            "writes": {key: dict(value) for key, value in self.writes.items()},
            "blobs": dict(self.blobs),
        }

        temp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        with temp_path.open("wb") as handle:
            pickle.dump(serialized, handle)
        temp_path.replace(self.path)

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        result = super().put(config, checkpoint, metadata, new_versions)
        self._persist()
        return result

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        return self.put(config, checkpoint, metadata, new_versions)

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        super().put_writes(config, writes, task_id, task_path)
        self._persist()

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        self.put_writes(config, writes, task_id, task_path)
