"""
Milestone 4 — Embedding + retrieval for The Unofficial Guide.

Loads chunks.jsonl, embeds each chunk with all-MiniLM-L6-v2 (local, no API key),
and stores the vectors + metadata in a persistent ChromaDB collection. Provides a
retrieve(query, k) function that embeds a query with the SAME model and returns the
top-k chunks with their source metadata and cosine distance.

The collection uses cosine space, so distance is 1 - cosine_similarity:
0.0 = identical direction, ~1.0 = unrelated, higher = opposed. Lower is better.

Setup:  source .venv/bin/activate && pip install -r requirements.txt
Run:    python embed.py                 # build index (if needed) + run eval queries
        python embed.py --rebuild        # force re-embed from chunks.jsonl
        python embed.py --query "..."    # ad-hoc query
        python embed.py --k 10           # change top-k
"""

from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
CHUNKS_FILE = "chunks.jsonl"
DB_PATH = "chroma_db"
COLLECTION = "unofficial_guide"
DEFAULT_K = 5

# The 5 evaluation queries from planning.md.
EVAL_QUERIES = [
    "Is UT Austin's online master's in CS the same degree as the on-campus one, or a lesser version?",
    "Which online Data Science courses are considered easy vs. hard?",
    "How much will I actually interact with professors and classmates online?",
    "What is UT admissions actually looking for and is there an admissions cap?",
    "Is Reinforcement Learning a good course to take online?",
]

_model: SentenceTransformer | None = None


def model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def load_chunks(path: str = CHUNKS_FILE) -> list[dict]:
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"{path} not found — run `python ingest.py` first.")
    return [json.loads(line) for line in p.open(encoding="utf-8")]


def _metadata(c: dict) -> dict:
    """Scalar-only metadata for Chroma (no None values allowed)."""
    md = {
        "source": c["source"],          # source document name (for attribution)
        "chunk_index": c["chunk_index"],  # position within that document
        "kind": c["kind"],
        "section": c["section"],
        "title": c["title"],
        "url": c["url"],
    }
    if c.get("score") is not None:
        md["score"] = c["score"]
    return md


def build_index(rebuild: bool = False) -> chromadb.Collection:
    chunks = load_chunks()
    client = chromadb.PersistentClient(path=DB_PATH)

    existing = {c.name for c in client.list_collections()}
    if rebuild and COLLECTION in existing:
        client.delete_collection(COLLECTION)
        existing.discard(COLLECTION)

    if COLLECTION in existing:
        col = client.get_collection(COLLECTION)
        if col.count() == len(chunks):
            return col                  # up to date — reuse
        client.delete_collection(COLLECTION)  # stale — rebuild from scratch

    col = client.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
    texts = [c["text"] for c in chunks]
    print(f"Embedding {len(texts)} chunks with {MODEL_NAME} ...")
    embeddings = model().encode(
        texts, normalize_embeddings=True, show_progress_bar=True
    ).tolist()
    col.add(
        ids=[c["id"] for c in chunks],
        embeddings=embeddings,
        documents=texts,
        metadatas=[_metadata(c) for c in chunks],
    )
    return col


def retrieve(query: str, k: int = DEFAULT_K, col: chromadb.Collection | None = None) -> list[dict]:
    """Return the top-k chunks for `query` with metadata and cosine distance."""
    if col is None:
        col = chromadb.PersistentClient(path=DB_PATH).get_collection(COLLECTION)
    q_emb = model().encode([query], normalize_embeddings=True).tolist()
    res = col.query(query_embeddings=q_emb, n_results=k)
    hits = []
    for doc, md, dist, _id in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0], res["ids"][0]
    ):
        hits.append({"id": _id, "text": doc, "distance": dist, **md})
    return hits


def _print_hits(query: str, hits: list[dict]) -> None:
    print("=" * 92)
    print(f"Q: {query}   (top-{len(hits)})")
    for r in hits:
        score = f", score {r['score']}" if "score" in r else ""
        print(f"\n  [dist {r['distance']:.3f}] {r['source']}#{r['chunk_index']} "
              f"[{r['kind']}{score}]  §{r['section'] or '—'}")
        print(textwrap.fill(r["text"], width=88,
                            initial_indent="    ", subsequent_indent="    "))
    print()


def main() -> None:
    ap = argparse.ArgumentParser(description="Embed chunks + retrieve (Milestone 4).")
    ap.add_argument("--rebuild", action="store_true", help="force re-embed from chunks.jsonl")
    ap.add_argument("--k", type=int, default=DEFAULT_K, help="top-k chunks to retrieve")
    ap.add_argument("--query", default=None, help="run a single ad-hoc query")
    args = ap.parse_args()

    col = build_index(rebuild=args.rebuild)
    print(f"\nIndex: {col.count()} vectors in '{COLLECTION}'  ({DB_PATH}/, cosine)\n")

    queries = [args.query] if args.query else EVAL_QUERIES
    for q in queries:
        _print_hits(q, retrieve(q, k=args.k, col=col))


if __name__ == "__main__":
    main()