from __future__ import annotations

from testbot.pipeline_state import PipelineState
from testbot.ports import MemorySearchQuery, PortDocument, ScoredPortDocument
from testbot.sat_chatbot_memory_v2 import stage_retrieve


class _SearchOnlyPortStore:
    def __init__(self) -> None:
        self.last_query: MemorySearchQuery | None = None

    def search_memory_records(self, query: MemorySearchQuery) -> list[ScoredPortDocument]:
        self.last_query = query
        return [
            ScoredPortDocument(
                document=PortDocument(
                    doc_id="mem-1",
                    content="type: user_utterance\ntext: hello",
                    metadata={"doc_id": "mem-1", "record_kind": "utterance_memory"},
                ),
                score=0.9,
            )
        ]


def test_stage_retrieve_wrapper_preserves_port_query_and_dto_boundary() -> None:
    store = _SearchOnlyPortStore()
    state = PipelineState(user_input="hello", rewritten_query="hello")

    _, docs_and_scores = stage_retrieve(store, state)

    assert store.last_query == MemorySearchQuery(query="hello", k=18)
    assert docs_and_scores[0][0].id == "mem-1"
