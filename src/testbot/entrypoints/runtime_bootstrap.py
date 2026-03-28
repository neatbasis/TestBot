"""Canonical runtime bootstrap helpers for CLI startup wiring.

Ownership:
- This module is the canonical owner for runtime environment bootstrap and
  memory-store bootstrap wiring used by entrypoint startup paths.
- Legacy compatibility façades may re-export/delegate to these helpers during
  retirement windows.
"""

from __future__ import annotations

import os

from langchain_core.embeddings import Embeddings

from testbot.adapters.memory_store_factory import build_memory_store, normalize_memory_store_mode
from testbot.config import Config
from testbot.ports import MemoryStorePort


def read_runtime_env() -> dict[str, object]:
    config = Config.from_env()
    memory_store_mode = os.getenv("MEMORY_STORE_MODE", "in_memory")
    debug_verbose = os.getenv("TESTBOT_DEBUG_VERBOSE", "0") == "1"
    return {
        "ha_base_url": config.HA_BASE_URL,
        "ha_api_token": config.HA_API_TOKEN,
        "ha_satellite_entity_id": config.HA_SATELLITE_ENTITY_ID,
        "ollama_base_url": config.OLLAMA_BASE_URL,
        "ollama_model": config.OLLAMA_MODEL,
        "ollama_embedding_model": config.OLLAMA_EMBEDDING_MODEL,
        "x_ollama_key": config.X_OLLAMA_KEY,
        "memory_near_tie_delta": config.MEMORY_NEAR_TIE_DELTA,
        "memory_store_mode": memory_store_mode,
        "memory_store_backend": normalize_memory_store_mode(memory_store_mode),
        "elasticsearch_url": os.getenv("ELASTICSEARCH_URL", "http://localhost:9200"),
        "elasticsearch_index": os.getenv("ELASTICSEARCH_INDEX", "testbot_memory_cards"),
        "source_ingest_enabled": config.SOURCE_INGEST_ENABLED,
        "source_connector_type": config.SOURCE_CONNECTOR_TYPE,
        "source_fixture_path": config.SOURCE_FIXTURE_PATH,
        "source_ingest_limit": config.SOURCE_INGEST_LIMIT,
        "source_ingest_cursor": config.SOURCE_INGEST_CURSOR,
        "source_markdown_path": config.SOURCE_MARKDOWN_PATH,
        "source_wikipedia_topic": config.SOURCE_WIKIPEDIA_TOPIC,
        "source_wikipedia_language": config.SOURCE_WIKIPEDIA_LANGUAGE,
        "source_arxiv_query": config.SOURCE_ARXIV_QUERY,
        "source_ingest_async_continuation": os.getenv("SOURCE_INGEST_ASYNC_CONTINUATION", "0") == "1",
        "source_ingest_background_future": None,
        "source_ingest_background_in_progress": False,
        "source_ingest_background_request_id": "",
        "debug_verbose": debug_verbose,
    }


def build_runtime_memory_store(*, runtime: dict[str, object], embeddings: Embeddings) -> MemoryStorePort:
    return build_memory_store(
        embeddings=embeddings,
        mode=str(runtime["memory_store_mode"]),
        elasticsearch_url=str(runtime["elasticsearch_url"]),
        elasticsearch_index=str(runtime["elasticsearch_index"]),
    )
