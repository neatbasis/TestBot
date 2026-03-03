import os
from dataclasses import dataclass

# Try loading .env if available
try:
    from dotenv import load_dotenv
    load_dotenv()
    _DOTENV_LOADED = True
except ImportError:
    _DOTENV_LOADED = False


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

@dataclass(frozen=True)
class Config:
    OLLAMA_BASE_URL: str
    OLLAMA_MODEL: str
    HA_API_URL: str
    HA_API_SECRET: str
    HA_SATELLITE_ENTITY_ID: str

    @classmethod
    def from_env(cls) -> "Config":
        ollama_base_url = os.getenv("OLLAMA_BASE_URL") or os.getenv("OLLAMA_HOST") or "http://localhost:11434"
        return cls(
            OLLAMA_BASE_URL=ollama_base_url,
            OLLAMA_MODEL=os.getenv("OLLAMA_MODEL", "llama3.1:latest"),
            HA_API_URL=os.getenv("HA_API_URL", "http://localhost:8123"),
            HA_API_SECRET=_require("HA_API_SECRET"),
            HA_SATELLITE_ENTITY_ID=_require("HA_SATELLITE_ENTITY_ID"),
        )
