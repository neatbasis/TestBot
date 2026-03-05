#!/usr/bin/env python
from __future__ import annotations

import argparse

from langchain_ollama import OllamaEmbeddings

from testbot.grounding_ingest import fetch_arxiv_documents
from testbot.grounding_ingest import fetch_wikipedia_summary
from testbot.grounding_ingest import load_markdown_documents
from testbot.vector_store import build_memory_store


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest grounding sources into TestBot memory store")
    parser.add_argument("--namespace", required=True)
    parser.add_argument("--markdown-dir")
    parser.add_argument("--wikipedia-title", action="append", default=[])
    parser.add_argument("--arxiv-query", action="append", default=[])
    parser.add_argument("--arxiv-max-results", type=int, default=5)
    parser.add_argument("--memory-store-mode", default="elasticsearch")
    parser.add_argument("--elasticsearch-url", default="http://localhost:9200")
    parser.add_argument("--elasticsearch-index", default="testbot_memory_cards")
    parser.add_argument("--embeddings-model", default="nomic-embed-text")
    parser.add_argument("--embeddings-base-url", default="http://localhost:11434")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    documents = []

    if args.markdown_dir:
        documents.extend(load_markdown_documents(args.markdown_dir, namespace=args.namespace))

    for title in args.wikipedia_title:
        documents.append(fetch_wikipedia_summary(title=title, namespace=args.namespace))

    for query in args.arxiv_query:
        documents.extend(
            fetch_arxiv_documents(
                query=query,
                namespace=args.namespace,
                max_results=args.arxiv_max_results,
            )
        )

    print(f"Prepared {len(documents)} grounding documents")
    if args.dry_run:
        return 0

    embeddings = OllamaEmbeddings(model=args.embeddings_model, base_url=args.embeddings_base_url)
    store = build_memory_store(
        embeddings=embeddings,
        mode=args.memory_store_mode,
        elasticsearch_url=args.elasticsearch_url,
        elasticsearch_index=args.elasticsearch_index,
    )
    store.add_documents(documents)
    print(
        "Ingested documents into memory store "
        f"mode={args.memory_store_mode} index={args.elasticsearch_index}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
