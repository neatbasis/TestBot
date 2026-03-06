import os
from dataclasses import dataclass
from pathlib import Path

# Try loading .env if available
try:
    from dotenv import load_dotenv

    load_dotenv(Path("~/.testbot/.env").expanduser())
    _DOTENV_LOADED = True
except ImportError:
    _DOTENV_LOADED = False


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _float_from_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        parsed = float(raw)
    except ValueError as exc:
        raise RuntimeError(f"Invalid float for {name}: {raw!r}") from exc
    if parsed < 0:
        raise RuntimeError(f"{name} must be non-negative; got {parsed}")
    return parsed


def _int_from_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        parsed = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"Invalid int for {name}: {raw!r}") from exc
    if parsed < 0:
        raise RuntimeError(f"{name} must be non-negative; got {parsed}")
    return parsed

@dataclass(frozen=True)
class Config:
    OLLAMA_BASE_URL: str
    OLLAMA_MODEL: str
    HA_API_URL: str
    HA_API_SECRET: str
    HA_SATELLITE_ENTITY_ID: str
    MEMORY_NEAR_TIE_DELTA: float
    SOURCE_INGEST_ENABLED: bool
    SOURCE_CONNECTOR_TYPE: str
    SOURCE_FIXTURE_PATH: str
    SOURCE_INGEST_LIMIT: int
    SOURCE_INGEST_CURSOR: str | None
    SOURCE_MARKDOWN_PATH: str
    SOURCE_WIKIPEDIA_TOPIC: str
    SOURCE_WIKIPEDIA_LANGUAGE: str
    SOURCE_ARXIV_QUERY: str

    @classmethod
    def from_env(cls) -> "Config":
        ollama_base_url = os.getenv("OLLAMA_BASE_URL") or os.getenv("OLLAMA_HOST") or "http://localhost:11434"
        return cls(
            OLLAMA_BASE_URL=ollama_base_url,
            OLLAMA_MODEL=os.getenv("OLLAMA_MODEL", "llama3.1:latest"),
            HA_API_URL=os.getenv("HA_API_URL", "http://localhost:8123"),
            HA_API_SECRET=_require("HA_API_SECRET"),
            HA_SATELLITE_ENTITY_ID=_require("HA_SATELLITE_ENTITY_ID"),
            MEMORY_NEAR_TIE_DELTA=_float_from_env("MEMORY_NEAR_TIE_DELTA", 0.02),
            SOURCE_INGEST_ENABLED=(os.getenv("SOURCE_INGEST_ENABLED", "0") == "1"),
            SOURCE_CONNECTOR_TYPE=os.getenv("SOURCE_CONNECTOR_TYPE", "fixture"),
            SOURCE_FIXTURE_PATH=os.getenv("SOURCE_FIXTURE_PATH", ""),
            SOURCE_INGEST_LIMIT=_int_from_env("SOURCE_INGEST_LIMIT", 50),
            SOURCE_INGEST_CURSOR=os.getenv("SOURCE_INGEST_CURSOR") or None,
            SOURCE_MARKDOWN_PATH=os.getenv("SOURCE_MARKDOWN_PATH", ""),
            SOURCE_WIKIPEDIA_TOPIC=os.getenv("SOURCE_WIKIPEDIA_TOPIC", ""),
            SOURCE_WIKIPEDIA_LANGUAGE=os.getenv("SOURCE_WIKIPEDIA_LANGUAGE", "en"),
            SOURCE_ARXIV_QUERY=os.getenv("SOURCE_ARXIV_QUERY", ""),
        )
