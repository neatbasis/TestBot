from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from langchain_core.documents import Document


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "item"


def load_markdown_documents(directory: str | Path, *, namespace: str) -> list[Document]:
    """Load markdown files as grounding documents.

    All `*.md` files under the directory are indexed recursively.
    """

    root = Path(directory).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Markdown directory does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Markdown directory is not a folder: {root}")

    docs: list[Document] = []
    for path in sorted(root.rglob("*.md")):
        rel = str(path.relative_to(root))
        text = path.read_text(encoding="utf-8")
        docs.append(
            Document(
                id=f"md:{namespace}:{_slug(rel)}",
                page_content=text,
                metadata={
                    "source": "markdown",
                    "namespace": namespace,
                    "path": rel,
                },
            )
        )
    return docs


def fetch_wikipedia_summary(*, title: str, namespace: str, language: str = "en") -> Document:
    encoded = urllib.parse.quote(title.replace(" ", "_"))
    url = f"https://{language}.wikipedia.org/api/rest_v1/page/summary/{encoded}"
    with urllib.request.urlopen(url, timeout=15) as response:  # nosec B310
        payload = json.loads(response.read().decode("utf-8"))

    extract = str(payload.get("extract") or "").strip()
    canonical_title = str(payload.get("title") or title)
    page = payload.get("content_urls", {}).get("desktop", {}).get("page", "")
    return Document(
        id=f"wikipedia:{namespace}:{_slug(canonical_title)}",
        page_content=extract,
        metadata={
            "source": "wikipedia",
            "namespace": namespace,
            "title": canonical_title,
            "url": page,
            "language": language,
        },
    )


def fetch_arxiv_documents(*, query: str, namespace: str, max_results: int = 5) -> list[Document]:
    params = urllib.parse.urlencode(
        {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
    )
    url = f"https://export.arxiv.org/api/query?{params}"
    with urllib.request.urlopen(url, timeout=20) as response:  # nosec B310
        xml_text = response.read().decode("utf-8")

    root = ET.fromstring(xml_text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    docs: list[Document] = []
    for entry in root.findall("atom:entry", ns):
        entry_id = (entry.findtext("atom:id", default="", namespaces=ns) or "").strip()
        title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
        summary = (entry.findtext("atom:summary", default="", namespaces=ns) or "").strip()
        published = (entry.findtext("atom:published", default="", namespaces=ns) or "").strip()
        docs.append(
            Document(
                id=f"arxiv:{namespace}:{_slug(entry_id or title)}",
                page_content=f"{title}\n\n{summary}".strip(),
                metadata={
                    "source": "arxiv",
                    "namespace": namespace,
                    "title": title,
                    "url": entry_id,
                    "published": published,
                },
            )
        )
    return docs
