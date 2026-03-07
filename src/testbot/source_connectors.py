from __future__ import annotations

import json
import logging
import socket
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Callable, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from langchain_core.documents import Document


_LOGGER = logging.getLogger(__name__)


try:
    _TESTBOT_VERSION = version("testbot")
except PackageNotFoundError:
    _TESTBOT_VERSION = "0.0.0"

_DEFAULT_WIKIPEDIA_USER_AGENT = f"TestBot/{_TESTBOT_VERSION} (+contact)"


@dataclass(frozen=True)
class SourceItem:
    """Raw item fetched from an external source connector."""

    item_id: str
    content: str
    source_uri: str
    retrieved_at: str
    trust_tier: str
    metadata: dict[str, str]

    def __post_init__(self) -> None:
        if not self.source_uri.strip():
            raise ValueError("SourceItem.source_uri must be non-empty")
        if not self.retrieved_at.strip():
            raise ValueError("SourceItem.retrieved_at must be non-empty")
        if not self.trust_tier.strip():
            raise ValueError("SourceItem.trust_tier must be non-empty")


class SourceConnector(Protocol):
    """Contract for source acquisition connectors.

    Connectors fetch raw source items, normalize each item into a canonical document,
    and maintain a connector-specific cursor/watermark.
    """

    source_type: str

    def fetch(self, *, cursor: str | None, limit: int = 50) -> list[SourceItem]: ...

    def normalize(self, item: SourceItem) -> Document: ...

    def update_cursor(self, *, previous_cursor: str | None, fetched_items: list[SourceItem]) -> str | None: ...


@dataclass(frozen=True)
class FixtureSourceConnector:
    """Deterministic fixture-backed connector for local source-ingestion tests/runtime.

    Cursor semantics are index-based (`"0"`, `"1"`, ...), making lifecycle behavior
    deterministic and easy to assert.
    """

    source_type: str
    fixtures: tuple[SourceItem, ...]

    @classmethod
    def from_json_file(cls, *, source_type: str, fixture_path: str) -> "FixtureSourceConnector":
        raw = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
        items = tuple(
            SourceItem(
                item_id=str(entry["item_id"]),
                content=str(entry["content"]),
                source_uri=str(entry["source_uri"]),
                retrieved_at=str(entry["retrieved_at"]),
                trust_tier=str(entry["trust_tier"]),
                metadata={str(k): str(v) for k, v in dict(entry.get("metadata", {})).items()},
            )
            for entry in raw
        )
        return cls(source_type=source_type, fixtures=items)

    def _parse_cursor(self, cursor: str | None, *, context: str) -> int:
        if cursor is None:
            return 0
        try:
            parsed = int(cursor)
        except (TypeError, ValueError):
            _LOGGER.warning("Invalid %s cursor=%r; defaulting to 0", context, cursor)
            return 0
        if parsed < 0:
            _LOGGER.warning("Negative %s cursor=%r; defaulting to 0", context, cursor)
            return 0
        return parsed

    def fetch(self, *, cursor: str | None, limit: int = 50) -> list[SourceItem]:
        if limit <= 0:
            return []
        start = self._parse_cursor(cursor, context="fetch")
        if start >= len(self.fixtures):
            return []
        return list(self.fixtures[start : start + limit])

    def normalize(self, item: SourceItem) -> Document:
        metadata = {
            **item.metadata,
            "doc_id": item.item_id,
            "source_type": self.source_type,
            "source_uri": item.source_uri,
            "retrieved_at": item.retrieved_at,
            "trust_tier": item.trust_tier,
        }
        return Document(id=item.item_id, page_content=item.content, metadata=metadata)

    def update_cursor(self, *, previous_cursor: str | None, fetched_items: list[SourceItem]) -> str | None:
        if not fetched_items:
            return previous_cursor
        previous_index = self._parse_cursor(previous_cursor, context="update_cursor")
        return str(previous_index + len(fetched_items))


@dataclass(frozen=True)
class LocalMarkdownSourceConnector:
    """Ingest markdown content from a local file or directory."""

    markdown_path: str
    source_type: str = "local_markdown"
    trust_tier: str = "operator"

    def _parse_cursor(self, cursor: str | None) -> int:
        if cursor is None:
            return 0
        try:
            parsed = int(cursor)
        except (TypeError, ValueError):
            _LOGGER.warning("Invalid local_markdown cursor=%r; defaulting to 0", cursor)
            return 0
        return max(parsed, 0)

    def _discover_markdown_files(self) -> list[Path]:
        root = Path(self.markdown_path).expanduser()
        if root.is_file():
            return [root] if root.suffix.lower() == ".md" else []
        if not root.exists() or not root.is_dir():
            return []
        return sorted(path for path in root.rglob("*.md") if path.is_file())

    def fetch(self, *, cursor: str | None, limit: int = 50) -> list[SourceItem]:
        if limit <= 0:
            return []
        files = self._discover_markdown_files()
        start = self._parse_cursor(cursor)
        if start >= len(files):
            return []
        retrieved_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        items: list[SourceItem] = []
        for path in files[start : start + limit]:
            content = path.read_text(encoding="utf-8")
            item_id = str(path.resolve())
            items.append(
                SourceItem(
                    item_id=item_id,
                    content=content,
                    source_uri=f"file://{path.resolve()}",
                    retrieved_at=retrieved_at,
                    trust_tier=self.trust_tier,
                    metadata={"path": str(path), "filename": path.name},
                )
            )
        return items

    def normalize(self, item: SourceItem) -> Document:
        return _normalize_source_item(item=item, source_type=self.source_type)

    def update_cursor(self, *, previous_cursor: str | None, fetched_items: list[SourceItem]) -> str | None:
        if not fetched_items:
            return previous_cursor
        return str(self._parse_cursor(previous_cursor) + len(fetched_items))


@dataclass(frozen=True)
class WikipediaSummarySourceConnector:
    """Fetches summary content for a single Wikipedia topic."""

    topic: str
    source_type: str = "wikipedia"
    language: str = "en"
    trust_tier: str = "community"
    user_agent: str = _DEFAULT_WIKIPEDIA_USER_AGENT
    request_factory: Callable[..., Request] = Request
    opener: Callable[..., Any] = urlopen

    def fetch(self, *, cursor: str | None, limit: int = 50) -> list[SourceItem]:
        if limit <= 0 or cursor is not None:
            return []
        normalized_topic = self.topic.strip()
        if not normalized_topic:
            return []
        encoded_topic = quote(normalized_topic, safe="")
        url = f"https://{self.language}.wikipedia.org/api/rest_v1/page/summary/{encoded_topic}"
        request = self.request_factory(url, headers={"User-Agent": self.user_agent})
        try:
            with self.opener(request, timeout=5.0) as response:  # noqa: S310
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError) as exc:
            _LOGGER.warning("Wikipedia summary fetch failed for topic=%r: %s", normalized_topic, exc)
            return []
        title = str(payload.get("title") or normalized_topic)
        extract = str(payload.get("extract") or "").strip()
        if not extract:
            return []
        source_uri = str(payload.get("content_urls", {}).get("desktop", {}).get("page") or url)
        retrieved_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        return [
            SourceItem(
                item_id=f"wiki::{title}",
                content=extract,
                source_uri=source_uri,
                retrieved_at=retrieved_at,
                trust_tier=self.trust_tier,
                metadata={"title": title, "topic": normalized_topic, "language": self.language},
            )
        ]

    def normalize(self, item: SourceItem) -> Document:
        return _normalize_source_item(item=item, source_type=self.source_type)

    def update_cursor(self, *, previous_cursor: str | None, fetched_items: list[SourceItem]) -> str | None:
        return "done" if fetched_items else previous_cursor


@dataclass(frozen=True)
class ArxivSourceConnector:
    """Fetches arXiv metadata and abstract content from Atom API."""

    query: str
    source_type: str = "arxiv"
    trust_tier: str = "preprint"

    def _parse_cursor(self, cursor: str | None) -> int:
        if cursor is None:
            return 0
        try:
            parsed = int(cursor)
        except (TypeError, ValueError):
            _LOGGER.warning("Invalid arxiv cursor=%r; defaulting to 0", cursor)
            return 0
        return max(parsed, 0)

    def fetch(self, *, cursor: str | None, limit: int = 50) -> list[SourceItem]:
        if limit <= 0:
            return []
        query = self.query.strip()
        if not query:
            return []
        start = self._parse_cursor(cursor)
        params = urlencode({"search_query": query, "start": start, "max_results": limit})
        url = f"https://export.arxiv.org/api/query?{params}"
        try:
            with urlopen(url, timeout=8.0) as response:  # noqa: S310
                payload = response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError, socket.timeout) as exc:
            _LOGGER.warning("arXiv fetch failed for query=%r: %s", query, exc)
            return []
        try:
            root = ET.fromstring(payload)
        except ET.ParseError as exc:
            _LOGGER.warning("arXiv feed parse failed for query=%r: %s", query, exc)
            return []
        namespace = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", namespace)
        retrieved_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        items: list[SourceItem] = []
        for entry in entries:
            entry_id = (entry.findtext("atom:id", default="", namespaces=namespace) or "").strip()
            title = " ".join((entry.findtext("atom:title", default="", namespaces=namespace) or "").split())
            summary = " ".join((entry.findtext("atom:summary", default="", namespaces=namespace) or "").split())
            if not entry_id or not summary:
                continue
            authors = [
                (author.findtext("atom:name", default="", namespaces=namespace) or "").strip()
                for author in entry.findall("atom:author", namespace)
            ]
            updated = (entry.findtext("atom:updated", default="", namespaces=namespace) or "").strip() or retrieved_at
            content = f"{title}\n\n{summary}" if title else summary
            items.append(
                SourceItem(
                    item_id=entry_id,
                    content=content,
                    source_uri=entry_id,
                    retrieved_at=retrieved_at,
                    trust_tier=self.trust_tier,
                    metadata={
                        "title": title,
                        "updated": updated,
                        "authors": ", ".join(a for a in authors if a),
                        "query": query,
                    },
                )
            )
        return items

    def normalize(self, item: SourceItem) -> Document:
        return _normalize_source_item(item=item, source_type=self.source_type)

    def update_cursor(self, *, previous_cursor: str | None, fetched_items: list[SourceItem]) -> str | None:
        if not fetched_items:
            return previous_cursor
        return str(self._parse_cursor(previous_cursor) + len(fetched_items))


def _normalize_source_item(*, item: SourceItem, source_type: str) -> Document:
    metadata = {
        **item.metadata,
        "doc_id": item.item_id,
        "source_type": source_type,
        "source_uri": item.source_uri,
        "retrieved_at": item.retrieved_at,
        "trust_tier": item.trust_tier,
    }
    return Document(id=item.item_id, page_content=item.content, metadata=metadata)
