from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from testbot.grounding_ingest import fetch_arxiv_documents
from testbot.grounding_ingest import fetch_wikipedia_summary
from testbot.grounding_ingest import load_markdown_documents


class _FakeResponse:
    def __init__(self, body: str) -> None:
        self._body = body.encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_load_markdown_documents_reads_recursive_directory(tmp_path: Path) -> None:
    root = tmp_path / "grounding"
    root.mkdir()
    (root / "one.md").write_text("# One", encoding="utf-8")
    sub = root / "notes"
    sub.mkdir()
    (sub / "two.md").write_text("# Two", encoding="utf-8")

    docs = load_markdown_documents(root, namespace="testbot")

    assert len(docs) == 2
    assert docs[0].metadata["source"] == "markdown"
    assert {doc.metadata["path"] for doc in docs} == {"one.md", "notes/two.md"}


def test_fetch_wikipedia_summary_maps_payload_to_document() -> None:
    payload = """{
      "title": "Leonardo da Vinci",
      "extract": "Italian polymath of the Renaissance.",
      "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Leonardo_da_Vinci"}}
    }"""

    with patch("urllib.request.urlopen", return_value=_FakeResponse(payload)):
        doc = fetch_wikipedia_summary(title="Leonardo da Vinci", namespace="testbot")

    assert doc.metadata["source"] == "wikipedia"
    assert doc.metadata["title"] == "Leonardo da Vinci"
    assert "Renaissance" in doc.page_content


def test_fetch_arxiv_documents_parses_atom_feed() -> None:
    atom = """<?xml version='1.0' encoding='UTF-8'?>
    <feed xmlns='http://www.w3.org/2005/Atom'>
      <entry>
        <id>http://arxiv.org/abs/1234.5678v1</id>
        <title>Example Paper</title>
        <summary>Summary text.</summary>
        <published>2024-01-01T00:00:00Z</published>
      </entry>
    </feed>
    """

    with patch("urllib.request.urlopen", return_value=_FakeResponse(atom)):
        docs = fetch_arxiv_documents(query="llm safety", namespace="testbot", max_results=1)

    assert len(docs) == 1
    assert docs[0].metadata["source"] == "arxiv"
    assert docs[0].metadata["title"] == "Example Paper"
    assert "Summary text" in docs[0].page_content
