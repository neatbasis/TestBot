from __future__ import annotations

import json
from urllib.error import HTTPError, URLError

from testbot.ports import PortDocument
from testbot.source_connectors import (
    ArxivSourceConnector,
    FixtureSourceConnector,
    LocalMarkdownSourceConnector,
    SourceItem,
    WikipediaSummarySourceConnector,
)
from testbot.source_ingest import SourceIngestor


class _FakeStore:
    def __init__(self) -> None:
        self.docs = []

    def add_memory_records(self, records):
        self.docs.extend(records)

    def search_memory_records(self, query):  # pragma: no cover
        del query
        return []


def test_fixture_connector_fetch_normalize_and_cursor_lifecycle() -> None:
    connector = FixtureSourceConnector(
        source_type="calendar",
        fixtures=(
            SourceItem(
                item_id="evt-1",
                content="Morning sync at 09:30.",
                source_uri="calendar://team/evt-1",
                retrieved_at="2026-03-11T09:00:00Z",
                trust_tier="verified",
                metadata={"ts": "2026-03-11T09:30:00Z"},
            ),
            SourceItem(
                item_id="evt-2",
                content="Retrospective at 15:00.",
                source_uri="calendar://team/evt-2",
                retrieved_at="2026-03-11T09:00:00Z",
                trust_tier="verified",
                metadata={"ts": "2026-03-11T15:00:00Z"},
            ),
        ),
    )

    first_batch = connector.fetch(cursor=None, limit=1)
    assert [item.item_id for item in first_batch] == ["evt-1"]

    normalized = connector.normalize(first_batch[0])
    assert normalized.doc_id == "evt-1"
    assert normalized.metadata["doc_id"] == "evt-1"
    assert normalized.metadata["source_uri"] == "calendar://team/evt-1"

    cursor = connector.update_cursor(previous_cursor=None, fetched_items=first_batch)
    assert cursor == "1"

    second_batch = connector.fetch(cursor=cursor, limit=2)
    assert [item.item_id for item in second_batch] == ["evt-2"]

    end_cursor = connector.update_cursor(previous_cursor=cursor, fetched_items=second_batch)
    assert end_cursor == "2"
    assert connector.fetch(cursor=end_cursor, limit=5) == []


def test_local_markdown_connector_ingests_file_and_directory(tmp_path) -> None:
    single = tmp_path / "note.md"
    single.write_text("# Note\n\nA single markdown file.", encoding="utf-8")
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "a.md").write_text("A", encoding="utf-8")
    (docs_dir / "b.md").write_text("B", encoding="utf-8")
    (docs_dir / "skip.txt").write_text("ignore", encoding="utf-8")

    file_connector = LocalMarkdownSourceConnector(markdown_path=str(single))
    directory_connector = LocalMarkdownSourceConnector(markdown_path=str(docs_dir))

    file_items = file_connector.fetch(cursor=None, limit=5)
    assert len(file_items) == 1
    assert file_items[0].metadata["filename"] == "note.md"
    assert file_connector.normalize(file_items[0]).metadata["source_type"] == "local_markdown"

    dir_items = directory_connector.fetch(cursor=None, limit=1)
    assert len(dir_items) == 1
    next_cursor = directory_connector.update_cursor(previous_cursor=None, fetched_items=dir_items)
    assert next_cursor == "1"
    assert len(directory_connector.fetch(cursor=next_cursor, limit=5)) == 1


def test_wikipedia_connector_fetches_summary(monkeypatch) -> None:
    payload = {
        "title": "OpenAI",
        "extract": "OpenAI is an AI research lab.",
        "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/OpenAI"}},
    }

    observed_request = None

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            del exc_type, exc, tb
            return False

        def read(self) -> bytes:
            return json.dumps(payload).encode("utf-8")

    def _fake_open(request, timeout):
        del timeout
        nonlocal observed_request
        observed_request = request
        return _Response()

    connector = WikipediaSummarySourceConnector(topic="OpenAI", opener=_fake_open)
    items = connector.fetch(cursor=None, limit=1)

    assert len(items) == 1
    assert items[0].item_id == "wiki::OpenAI"
    assert items[0].source_uri == "https://en.wikipedia.org/wiki/OpenAI"
    assert observed_request is not None
    assert observed_request.headers["User-agent"].startswith("TestBot/")
    assert connector.fetch(cursor="done", limit=1) == []


def test_wikipedia_connector_returns_empty_list_on_http_403() -> None:
    def _raise_http_error(request, timeout):
        del request, timeout
        raise HTTPError(
            url="https://en.wikipedia.org/wiki/OpenAI",
            code=403,
            msg="Forbidden",
            hdrs=None,
            fp=None,
        )

    connector = WikipediaSummarySourceConnector(topic="OpenAI", opener=_raise_http_error)

    assert connector.fetch(cursor=None, limit=1) == []




def test_arxiv_connector_returns_empty_list_on_http_or_network_failure(monkeypatch) -> None:
    def _raise_network_error(*args, **kwargs):
        del args, kwargs
        raise URLError("network down")

    monkeypatch.setattr("testbot.source_connectors.urlopen", _raise_network_error)

    connector = ArxivSourceConnector(query="cat:cs.AI")

    assert connector.fetch(cursor=None, limit=2) == []


def test_arxiv_connector_returns_empty_list_on_malformed_xml(monkeypatch) -> None:
    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            del exc_type, exc, tb
            return False

        def read(self) -> bytes:
            return b"<feed><entry>not closed"

    monkeypatch.setattr("testbot.source_connectors.urlopen", lambda *args, **kwargs: _Response())

    connector = ArxivSourceConnector(query="cat:cs.AI")

    assert connector.fetch(cursor=None, limit=2) == []

def test_arxiv_connector_parses_feed(monkeypatch) -> None:
    xml_payload = """<?xml version='1.0' encoding='UTF-8'?>
<feed xmlns='http://www.w3.org/2005/Atom'>
  <entry>
    <id>http://arxiv.org/abs/1234.5678v1</id>
    <updated>2026-03-01T12:00:00Z</updated>
    <title>Useful Paper</title>
    <summary>We show deterministic testing.</summary>
    <author><name>Ada Lovelace</name></author>
    <author><name>Grace Hopper</name></author>
  </entry>
</feed>
"""

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            del exc_type, exc, tb
            return False

        def read(self) -> bytes:
            return xml_payload.encode("utf-8")

    monkeypatch.setattr("testbot.source_connectors.urlopen", lambda *args, **kwargs: _Response())

    connector = ArxivSourceConnector(query="cat:cs.AI")
    items = connector.fetch(cursor=None, limit=2)

    assert len(items) == 1
    assert items[0].item_id == "http://arxiv.org/abs/1234.5678v1"
    assert "Useful Paper" in items[0].content
    assert items[0].metadata["authors"] == "Ada Lovelace, Grace Hopper"


def test_source_ingest_canonicalizes_fixture_connector_docs() -> None:
    connector = FixtureSourceConnector(
        source_type="calendar",
        fixtures=(
            SourceItem(
                item_id="evt-3",
                content="Bill due Friday.",
                source_uri="calendar://finance/evt-3",
                retrieved_at="2026-03-12T08:15:00Z",
                trust_tier="high",
                metadata={"ts": "2026-03-13T10:00:00Z"},
            ),
        ),
    )
    store = _FakeStore()

    result = SourceIngestor(connector=connector, memory_store=store).ingest_once(cursor=None)

    assert result.fetched_count == 1
    assert result.stored_count == 2
    memory_doc = result.memory_documents[0]
    evidence_doc = result.evidence_documents[0]
    assert memory_doc.metadata["record_kind"] == "utterance_memory"
    assert evidence_doc.metadata["record_kind"] == "source_evidence"
    assert evidence_doc.metadata["source_type"] == "calendar"
    assert evidence_doc.metadata["trust_tier"] == "high"


def test_fixture_connector_can_load_json_fixture_file(tmp_path) -> None:
    fixture_path = tmp_path / "source_fixture.json"
    fixture_path.write_text(
        json.dumps(
            [
                {
                    "item_id": "src-1",
                    "content": "Task: utility bill due Friday",
                    "source_uri": "ha://tasks/utility-bill",
                    "retrieved_at": "2026-03-10T09:00:00Z",
                    "trust_tier": "verified",
                    "metadata": {"ts": "2026-03-14T00:00:00Z"},
                }
            ]
        ),
        encoding="utf-8",
    )

    connector = FixtureSourceConnector.from_json_file(source_type="home_automation", fixture_path=str(fixture_path))

    items = connector.fetch(cursor=None, limit=10)
    assert len(items) == 1
    assert items[0].item_id == "src-1"
    assert connector.normalize(items[0]).metadata["source_type"] == "home_automation"


def test_fixture_connector_fetch_invalid_cursor_defaults_to_start(caplog) -> None:
    connector = FixtureSourceConnector(
        source_type="calendar",
        fixtures=(
            SourceItem(
                item_id="evt-1",
                content="Morning sync at 09:30.",
                source_uri="calendar://team/evt-1",
                retrieved_at="2026-03-11T09:00:00Z",
                trust_tier="verified",
                metadata={"ts": "2026-03-11T09:30:00Z"},
            ),
        ),
    )

    with caplog.at_level("WARNING"):
        batch = connector.fetch(cursor="oops", limit=1)

    assert [item.item_id for item in batch] == ["evt-1"]
    assert "Invalid fetch cursor" in caplog.text


def test_fixture_connector_update_cursor_invalid_previous_cursor_defaults_to_start(caplog) -> None:
    connector = FixtureSourceConnector(
        source_type="calendar",
        fixtures=(
            SourceItem(
                item_id="evt-1",
                content="Morning sync at 09:30.",
                source_uri="calendar://team/evt-1",
                retrieved_at="2026-03-11T09:00:00Z",
                trust_tier="verified",
                metadata={"ts": "2026-03-11T09:30:00Z"},
            ),
        ),
    )

    with caplog.at_level("WARNING"):
        cursor = connector.update_cursor(previous_cursor="invalid", fetched_items=list(connector.fixtures))

    assert cursor == "1"
    assert "Invalid update_cursor cursor" in caplog.text
