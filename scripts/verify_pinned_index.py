"""Fail unless the built SQLite index matches the production retrieval baseline."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag.index import RagIndex


EXPECTED = {
    "status": "ready",
    "semantic_embeddings": True,
    "embedding_provider": "huggingface",
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "embedding_backend": "onnxruntime-quint8-avx2",
    "embedding_revision": "1110a243fdf4706b3f48f1d95db1a4f5529b4d41",
    "embedding_max_length": 256,
    "dimensions": 384,
    "chunk_words": 120,
    "overlap_words": 20,
}


def main() -> None:
    stats = RagIndex().stats()
    mismatches = {
        key: {"expected": expected, "actual": stats.get(key)}
        for key, expected in EXPECTED.items()
        if stats.get(key) != expected
    }
    if mismatches:
        raise SystemExit(f"SQLite index does not match the pinned production baseline: {mismatches}")
    print("Pinned MiniLM INT8 ONNX 384d 120/20 SQLite policy index is ready")


if __name__ == "__main__":
    main()
