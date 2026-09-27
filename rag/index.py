from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sqlite3
import tempfile
import time
from collections import Counter
from functools import lru_cache
from pathlib import Path
from threading import Lock
from typing import Any

import httpx
import numpy as np

from rag.ingest import chunk_sections, load_policy_sections

ROOT = Path(__file__).resolve().parents[1]
POLICY_DIR = ROOT / "policies"
DEFAULT_INDEX_PATH = Path(tempfile.gettempdir()) / "msaie-rag" / "rag_index.sqlite3"
TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]{1,}")
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have", "how", "i",
    "in", "is", "it", "of", "on", "or", "that", "the", "this", "to", "was", "what", "when", "with", "you",
}
HASH_MODEL = "msaie-hashing-tfidf-v1"
DEFAULT_LOCAL_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_REMOTE_MODEL = DEFAULT_LOCAL_MODEL
HF_EMBEDDING_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
HF_ONNX_MODEL_FILE = "onnx/model_quint8_avx2.onnx"
HF_EMBEDDING_BACKEND = "onnxruntime-quint8-avx2"
HF_EMBEDDING_MAX_LENGTH = 256
_LOCK = Lock()


def index_path() -> Path:
    return Path(os.getenv("MSAIE_INDEX_PATH", str(DEFAULT_INDEX_PATH)))


def tokenize(text: str) -> list[str]:
    return [token for token in TOKEN_PATTERN.findall(text.lower()) if token not in STOP_WORDS]


def _bucket(token: str, dimensions: int) -> str:
    digest = hashlib.sha256(token.encode("utf-8")).digest()
    return str(int.from_bytes(digest[:4], "big") % dimensions)


def _sparse_vector(tokens: list[str], idf: dict[str, float], dimensions: int) -> dict[str, float]:
    counts = Counter(tokens)
    values: dict[str, float] = {}
    for token, count in counts.items():
        bucket = _bucket(token, dimensions)
        values[bucket] = values.get(bucket, 0.0) + (1.0 + math.log(count)) * idf.get(token, 1.0)
    norm = math.sqrt(sum(value * value for value in values.values())) or 1.0
    return {key: value / norm for key, value in values.items()}


def _sparse_cosine(left: dict[str, float], right: dict[str, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(key, 0.0) for key, value in left.items())


def _dense_cosine(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    left_norm = math.sqrt(sum(value * value for value in left)) or 1.0
    right_norm = math.sqrt(sum(value * value for value in right)) or 1.0
    return sum(a * b for a, b in zip(left, right, strict=True)) / (left_norm * right_norm)


def _embedding_config() -> dict[str, str] | None:
    provider = os.getenv("MSAIE_EMBEDDING_PROVIDER", "huggingface").lower()
    if provider not in {"openrouter", "remote"}:
        return None
    base_url = os.getenv("MSAIE_EMBEDDING_BASE_URL")
    api_key = os.getenv("MSAIE_EMBEDDING_API_KEY")
    if not base_url or not api_key:
        return None
    return {
        "base_url": base_url.rstrip("/"),
        "api_key": api_key,
        "model": os.getenv("MSAIE_EMBEDDING_MODEL", DEFAULT_REMOTE_MODEL),
    }


def _requested_embedding_model() -> str:
    config = _embedding_config()
    return config["model"] if config else os.getenv("MSAIE_EMBEDDING_MODEL", DEFAULT_LOCAL_MODEL)


def _embedding_config_signature() -> str:
    config = _embedding_config()
    signature = {
        "provider": "openrouter" if config else "huggingface",
        "model": config["model"] if config else _requested_embedding_model(),
        "base_url": config["base_url"] if config else None,
    }
    if not config:
        signature.update(
            {
                "backend": HF_EMBEDDING_BACKEND,
                "revision": _local_embedding_revision(_requested_embedding_model()),
                "onnx_model_file": HF_ONNX_MODEL_FILE,
            }
        )
    return hashlib.sha256(json.dumps(signature, sort_keys=True).encode("utf-8")).hexdigest()


def _policy_source_fingerprint() -> str:
    digest = hashlib.sha256()
    for path in sorted(POLICY_DIR.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".markdown", ".html", ".htm"}:
            continue
        digest.update(path.relative_to(POLICY_DIR).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _local_embedding_revision(model_name: str) -> str:
    if model_name == DEFAULT_LOCAL_MODEL:
        return HF_EMBEDDING_REVISION
    return os.getenv("MSAIE_EMBEDDING_REVISION", "main")


class HuggingFaceOnnxEmbedder:
    """Run the pinned MiniLM checkpoint with the Hugging Face INT8 ONNX export."""

    def __init__(self, model_name: str, revision: str) -> None:
        if model_name != DEFAULT_LOCAL_MODEL:
            raise ValueError(
                f"Local Hugging Face embeddings supports only {DEFAULT_LOCAL_MODEL}"
            )

        from huggingface_hub import hf_hub_download
        from tokenizers import Tokenizer
        import onnxruntime as ort

        model_path = hf_hub_download(
            repo_id=model_name,
            filename=HF_ONNX_MODEL_FILE,
            revision=revision,
        )
        tokenizer_path = hf_hub_download(
            repo_id=model_name,
            filename="tokenizer.json",
            revision=revision,
        )
        self.tokenizer = Tokenizer.from_file(tokenizer_path)
        self.tokenizer.enable_truncation(max_length=HF_EMBEDDING_MAX_LENGTH)
        self.tokenizer.enable_padding()

        options = ort.SessionOptions()
        options.intra_op_num_threads = max(1, int(os.getenv("MSAIE_EMBEDDING_THREADS", "1")))
        options.inter_op_num_threads = 1
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        self.session = ort.InferenceSession(
            model_path,
            sess_options=options,
            providers=["CPUExecutionProvider"],
        )
        self.input_names = {item.name for item in self.session.get_inputs()}
        self.output_name = self.session.get_outputs()[0].name

    def encode(
        self,
        texts: list[str],
        *,
        normalize_embeddings: bool = True,
        batch_size: int = 32,
    ) -> np.ndarray:
        if not texts:
            return np.empty((0, 384), dtype=np.float32)

        vectors: list[np.ndarray] = []
        for offset in range(0, len(texts), max(1, batch_size)):
            batch = texts[offset : offset + max(1, batch_size)]
            encodings = self.tokenizer.encode_batch(batch)
            values = {
                "input_ids": np.asarray([item.ids for item in encodings], dtype=np.int64),
                "attention_mask": np.asarray(
                    [item.attention_mask for item in encodings], dtype=np.int64
                ),
                "token_type_ids": np.asarray([item.type_ids for item in encodings], dtype=np.int64),
            }
            inputs = {name: values[name] for name in self.input_names}
            hidden = self.session.run([self.output_name], inputs)[0].astype(np.float32)
            mask = values["attention_mask"][..., None].astype(np.float32)
            pooled = (hidden * mask).sum(axis=1) / np.maximum(mask.sum(axis=1), 1.0)
            if normalize_embeddings:
                pooled /= np.maximum(np.linalg.norm(pooled, axis=1, keepdims=True), 1e-12)
            vectors.append(pooled)
        return np.concatenate(vectors, axis=0)


@lru_cache(maxsize=2)
def _local_embedding_model(model_name: str, revision: str) -> HuggingFaceOnnxEmbedder:
    return HuggingFaceOnnxEmbedder(model_name, revision)


def _local_embeddings(texts: list[str], model_name: str) -> list[list[float]]:
    revision = _local_embedding_revision(model_name)
    model = _local_embedding_model(model_name, revision)
    vectors = model.encode(texts, normalize_embeddings=True, batch_size=32).tolist()
    return [[float(value) for value in vector] for vector in vectors]


def _remote_embeddings(texts: list[str], config: dict[str, str]) -> list[list[float]]:
    """Generate learned embeddings in bounded batches using an OpenAI-compatible endpoint."""
    if not texts:
        return []
    batch_size = max(1, min(int(os.getenv("MSAIE_EMBEDDING_BATCH_SIZE", "32")), 64))
    timeout = float(os.getenv("MSAIE_EMBEDDING_TIMEOUT_SECONDS", "120"))
    retries = max(0, int(os.getenv("MSAIE_EMBEDDING_MAX_RETRIES", "3")))
    vectors: list[list[float]] = []
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
        "X-Title": "MSAIE HR Agent",
    }
    public_url = os.getenv("MSAIE_PUBLIC_URL")
    if public_url:
        headers["HTTP-Referer"] = public_url

    for offset in range(0, len(texts), batch_size):
        batch = texts[offset : offset + batch_size]
        last_error: Exception | None = None
        for attempt in range(retries + 1):
            try:
                with httpx.Client(timeout=timeout) as client:
                    response = client.post(
                        f"{config['base_url']}/embeddings",
                        headers=headers,
                        json={"model": config["model"], "input": batch, "encoding_format": "float"},
                    )
                if response.status_code == 429 or response.status_code >= 500:
                    response.raise_for_status()
                if response.status_code >= 400:
                    raise RuntimeError(f"Embedding provider returned HTTP {response.status_code}: {response.text[:300]}")
                payload = response.json()
                items = sorted(payload.get("data", []), key=lambda item: int(item.get("index", 0)))
                current = [item.get("embedding") for item in items]
                if len(current) != len(batch) or any(not isinstance(vector, list) or not vector for vector in current):
                    raise RuntimeError("Embedding provider returned malformed vectors")
                vectors.extend([[float(value) for value in vector] for vector in current])
                last_error = None
                break
            except (httpx.HTTPError, RuntimeError, ValueError, TypeError, KeyError) as exc:
                last_error = exc
                if attempt >= retries:
                    break
                time.sleep(min(2**attempt, 8))
        if last_error is not None:
            raise RuntimeError(f"Embedding request failed after retries: {last_error}")
    return vectors


class RagIndex:
    def __init__(self, path: Path | None = None, *, dimensions: int = 384) -> None:
        self.path = path or index_path()
        self.dimensions = dimensions

    def build(self, *, chunk_words: int = 120, overlap_words: int = 20, force: bool = False) -> dict[str, Any]:
        with _LOCK:
            source_fingerprint = _policy_source_fingerprint()
            if self.path.exists() and not force:
                try:
                    with sqlite3.connect(self.path) as connection:
                        metadata = self._metadata(connection)
                    if (
                        metadata.get("source_fingerprint") == source_fingerprint
                        and metadata.get("chunk_words") == str(chunk_words)
                        and metadata.get("overlap_words") == str(overlap_words)
                        and metadata.get("requested_embedding_model") == _requested_embedding_model()
                        and metadata.get("embedding_config_signature") == _embedding_config_signature()
                    ):
                        return self.stats()
                except sqlite3.Error:
                    pass
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self.path.exists():
                self.path.unlink()

            sections = load_policy_sections(POLICY_DIR)
            chunks = chunk_sections(sections, chunk_words=chunk_words, overlap_words=overlap_words)
            tokenized = [tokenize(str(chunk["content"])) for chunk in chunks]
            requested_model = _requested_embedding_model()
            embedding_config = _embedding_config()
            actual_model = HASH_MODEL
            provider = "local-hashing-fallback"
            embedding_backend = "sparse-hash"
            embedding_revision = ""
            vector_format = "sparse"
            embedding_error = ""
            idf: dict[str, float] = {}
            vectors: list[list[float] | dict[str, float]] = []
            dimensions = self.dimensions

            if embedding_config:
                try:
                    embedding_inputs = [
                        f"{chunk['title']}\n{chunk['section']}\n{chunk['content']}" for chunk in chunks
                    ]
                    dense_vectors = _remote_embeddings(embedding_inputs, embedding_config)
                    dimensions = len(dense_vectors[0]) if dense_vectors else 0
                    if dimensions <= 0 or any(len(vector) != dimensions for vector in dense_vectors):
                        raise RuntimeError("Embedding vectors have inconsistent dimensions")
                    vectors = dense_vectors
                    actual_model = embedding_config["model"]
                    provider = "openrouter"
                    embedding_backend = "remote-api"
                    vector_format = "dense"
                except Exception as exc:
                    embedding_error = str(exc)[:500]
            else:
                try:
                    embedding_inputs = [
                        f"{chunk['title']}\n{chunk['section']}\n{chunk['content']}" for chunk in chunks
                    ]
                    dense_vectors = _local_embeddings(embedding_inputs, requested_model)
                    dimensions = len(dense_vectors[0]) if dense_vectors else 0
                    if dimensions <= 0 or any(len(vector) != dimensions for vector in dense_vectors):
                        raise RuntimeError("Local embedding vectors have inconsistent dimensions")
                    vectors = dense_vectors
                    actual_model = requested_model
                    provider = "huggingface"
                    embedding_backend = HF_EMBEDDING_BACKEND
                    embedding_revision = _local_embedding_revision(requested_model)
                    vector_format = "dense"
                except Exception as exc:
                    embedding_error = str(exc)[:500]

            if vector_format == "sparse":
                document_frequency: Counter[str] = Counter()
                for tokens in tokenized:
                    document_frequency.update(set(tokens))
                total = max(len(chunks), 1)
                idf = {
                    token: math.log((total + 1) / (frequency + 1)) + 1.0
                    for token, frequency in document_frequency.items()
                }
                vectors = [_sparse_vector(tokens, idf, self.dimensions) for tokens in tokenized]
                dimensions = self.dimensions

            with sqlite3.connect(self.path) as connection:
                connection.executescript(
                    """
                    PRAGMA journal_mode=WAL;
                    CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                    CREATE TABLE chunks (
                        chunk_id TEXT PRIMARY KEY,
                        document_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        section TEXT NOT NULL,
                        source_path TEXT NOT NULL,
                        content TEXT NOT NULL,
                        vector_json TEXT NOT NULL,
                        word_count INTEGER NOT NULL,
                        estimated_pages REAL NOT NULL
                    );
                    CREATE INDEX idx_chunks_document_id ON chunks(document_id);
                    """
                )
                connection.executemany(
                    "INSERT INTO metadata(key, value) VALUES (?, ?)",
                    [
                        ("embedding_model", actual_model),
                        ("requested_embedding_model", requested_model),
                        ("embedding_config_signature", _embedding_config_signature()),
                        ("source_fingerprint", source_fingerprint),
                        ("embedding_provider", provider),
                        ("embedding_backend", embedding_backend),
                        ("embedding_revision", embedding_revision),
                        ("embedding_error", embedding_error),
                        ("vector_format", vector_format),
                        ("dimensions", str(dimensions)),
                        ("idf", json.dumps(idf, sort_keys=True)),
                        ("chunk_words", str(chunk_words)),
                        ("overlap_words", str(overlap_words)),
                    ],
                )
                rows = []
                for chunk, vector in zip(chunks, vectors, strict=True):
                    rows.append(
                        (
                            chunk["chunk_id"],
                            chunk["document_id"],
                            chunk["title"],
                            chunk["section"],
                            chunk["source_path"],
                            chunk["content"],
                            json.dumps(vector, sort_keys=isinstance(vector, dict)),
                            chunk["word_count"],
                            chunk["estimated_pages"],
                        )
                    )
                connection.executemany(
                    """INSERT INTO chunks(
                        chunk_id, document_id, title, section, source_path, content,
                        vector_json, word_count, estimated_pages
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    rows,
                )
                connection.commit()
            return self.stats()

    def ensure(self) -> dict[str, Any]:
        return self.build()

    def _metadata(self, connection: sqlite3.Connection) -> dict[str, str]:
        return {row[0]: row[1] for row in connection.execute("SELECT key, value FROM metadata")}

    def search(
        self, query: str, *, limit: int = 4, document_prefix: str | None = None
    ) -> list[dict[str, Any]]:
        self.ensure()
        with sqlite3.connect(self.path) as connection:
            connection.row_factory = sqlite3.Row
            metadata = self._metadata(connection)
            vector_format = metadata.get("vector_format", "sparse")
            query_tokens = tokenize(query)
            query_vector: list[float] | dict[str, float] | None
            if vector_format == "dense":
                config = _embedding_config()
                try:
                    if config:
                        query_vector = _remote_embeddings([query], config)[0]
                    else:
                        query_vector = _local_embeddings(
                            [query], metadata.get("requested_embedding_model", DEFAULT_LOCAL_MODEL)
                        )[0]
                except Exception:
                    query_vector = None
            else:
                idf = json.loads(metadata.get("idf", "{}"))
                dimensions = int(metadata.get("dimensions", str(self.dimensions)))
                query_vector = _sparse_vector(query_tokens, idf, dimensions)

            if vector_format == "dense":
                retrieval_method = (
                    f'{metadata.get("embedding_provider", "unknown")}_dense_cosine'
                    if isinstance(query_vector, list)
                    else "lexical_only_after_embedding_error"
                )
            else:
                retrieval_method = "hashing_tfidf_sparse_cosine"

            sql = "SELECT * FROM chunks"
            params: tuple[Any, ...] = ()
            if document_prefix:
                sql += " WHERE document_id LIKE ?"
                params = (f"{document_prefix}%",)
            candidates = []
            query_lower = query.lower()
            for row in connection.execute(sql, params):
                lexical_tokens = set(tokenize(f"{row['title']} {row['section']} {row['content']}"))
                lexical_overlap = set(query_tokens) & lexical_tokens
                if vector_format == "sparse" and not lexical_overlap:
                    continue
                stored_vector = json.loads(row["vector_json"])
                if vector_format == "dense" and isinstance(query_vector, list) and isinstance(stored_vector, list):
                    score = _dense_cosine(query_vector, [float(value) for value in stored_vector])
                elif vector_format == "sparse" and isinstance(query_vector, dict) and isinstance(stored_vector, dict):
                    score = _sparse_cosine(query_vector, stored_vector)
                else:
                    score = 0.0

                title_section = f"{row['title']} {row['section']}".lower()
                lexical_hits = sum(1 for token in lexical_overlap if token in title_section)
                lexical_ratio = len(lexical_overlap) / max(len(set(query_tokens)), 1)
                phrase_bonus = 0.08 if query_lower in row["content"].lower() else 0.0
                score += lexical_ratio * 0.08 + lexical_hits * 0.025 + phrase_bonus
                if score <= 0:
                    continue
                content = row["content"]
                candidates.append(
                    {
                        "chunk_id": row["chunk_id"],
                        "document_id": row["document_id"],
                        "title": row["title"],
                        "section": row["section"],
                        "source_path": row["source_path"],
                        "retrieval_method": retrieval_method,
                        "snippet": content,
                        "score": round(score, 4),
                    }
                )
            candidates.sort(key=lambda item: item["score"], reverse=True)
            return candidates[: max(1, min(limit, 10))]

    def rerank_mmr(
        self,
        candidates: list[dict[str, Any]],
        *,
        limit: int = 5,
        lambda_value: float = 0.5,
        seed_chunk_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Rerank a score-ordered candidate pool by relevance and vector diversity."""
        if not 0.0 <= lambda_value <= 1.0:
            raise ValueError("lambda_value must be between 0 and 1")
        if not candidates:
            return []

        unique: list[dict[str, Any]] = []
        seen: set[str] = set()
        for candidate in candidates[:10]:
            chunk_id = str(candidate.get("chunk_id", ""))
            if not chunk_id or chunk_id in seen:
                continue
            seen.add(chunk_id)
            unique.append(candidate)
        if not unique:
            return []

        vectors: dict[str, list[float]] = {}
        if self.path.exists():
            placeholders = ",".join("?" for _ in seen)
            try:
                with sqlite3.connect(f"{self.path.as_uri()}?mode=ro", uri=True) as connection:
                    rows = connection.execute(
                        f"SELECT chunk_id, vector_json FROM chunks WHERE chunk_id IN ({placeholders})",
                        tuple(seen),
                    ).fetchall()
                for chunk_id, vector_json in rows:
                    value = json.loads(vector_json)
                    if isinstance(value, list):
                        vectors[str(chunk_id)] = [float(item) for item in value]
            except (sqlite3.Error, json.JSONDecodeError, TypeError, ValueError):
                vectors = {}

        scores = {str(item["chunk_id"]): float(item.get("score", 0.0)) for item in unique}
        low, high = min(scores.values()), max(scores.values())
        span = high - low
        relevance = {
            chunk_id: ((score - low) / span if span else 1.0)
            for chunk_id, score in scores.items()
        }
        target = max(1, min(int(limit), 10))
        remaining = list(unique)
        chosen: list[dict[str, Any]] = []

        for seed_id in seed_chunk_ids or []:
            seed = next((item for item in remaining if item["chunk_id"] == seed_id), None)
            if seed is not None and len(chosen) < target:
                chosen.append(seed)
                remaining.remove(seed)

        while remaining and len(chosen) < target:
            best = remaining[0]
            best_value = float("-inf")
            for candidate in remaining:
                vector = vectors.get(str(candidate["chunk_id"]), [])
                redundancy = max(
                    (
                        max(0.0, _dense_cosine(vector, vectors.get(str(selected["chunk_id"]), [])))
                        for selected in chosen
                    ),
                    default=0.0,
                )
                value = (
                    lambda_value * relevance[str(candidate["chunk_id"])]
                    - (1.0 - lambda_value) * redundancy
                )
                if value > best_value:
                    best, best_value = candidate, value
            chosen.append(best)
            remaining.remove(best)
        return chosen

    def get_section(self, document_id: str, section: str | None = None) -> list[dict[str, Any]]:
        self.ensure()
        with sqlite3.connect(self.path) as connection:
            connection.row_factory = sqlite3.Row
            if section:
                rows = connection.execute(
                    """SELECT * FROM chunks WHERE document_id = ? AND lower(section) LIKE ?
                       ORDER BY chunk_id""",
                    (document_id.upper(), f"%{section.lower()}%"),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM chunks WHERE document_id = ? ORDER BY chunk_id",
                    (document_id.upper(),),
                ).fetchall()
            return [
                {
                    "chunk_id": row["chunk_id"],
                    "document_id": row["document_id"],
                    "title": row["title"],
                    "section": row["section"],
                    "source_path": row["source_path"],
                    "snippet": row["content"],
                }
                for row in rows
            ]

    def list_documents(self) -> list[dict[str, Any]]:
        """List safe document-level fields stored in the local SQLite index."""
        self.ensure()
        database_uri = f"{self.path.resolve().as_uri()}?mode=ro"
        with sqlite3.connect(database_uri, uri=True) as connection:
            rows = connection.execute(
                """SELECT document_id, title, COUNT(*) AS chunk_count,
                          COUNT(DISTINCT section) AS section_count,
                          MAX(estimated_pages) AS estimated_pages
                   FROM chunks
                   GROUP BY document_id, title
                   ORDER BY document_id"""
            ).fetchall()
        return [
            {
                "document_id": row[0],
                "title": row[1],
                "chunk_count": int(row[2]),
                "section_count": int(row[3]),
                "estimated_pages": round(float(row[4] or 0), 1),
            }
            for row in rows
        ]

    def get_chunks(self, document_id: str, *, limit: int = 20) -> list[dict[str, Any]]:
        """Return full text and citation metadata for a bounded document preview."""
        self.ensure()
        capped_limit = max(1, min(int(limit), 50))
        database_uri = f"{self.path.resolve().as_uri()}?mode=ro"
        with sqlite3.connect(database_uri, uri=True) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """SELECT chunk_id, document_id, title, section, source_path, content
                   FROM chunks
                   WHERE document_id = ?
                   ORDER BY chunk_id
                   LIMIT ?""",
                (document_id.upper(), capped_limit),
            ).fetchall()
        return [
            {
                "chunk_id": row["chunk_id"],
                "document_id": row["document_id"],
                "title": row["title"],
                "section": row["section"],
                "source_path": row["source_path"],
                "snippet": row["content"],
            }
            for row in rows
        ]

    def stats(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"status": "missing", "path": str(self.path)}
        with sqlite3.connect(self.path) as connection:
            chunk_count = connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
            document_count = connection.execute("SELECT COUNT(DISTINCT document_id) FROM chunks").fetchone()[0]
            estimated_pages = connection.execute(
                "SELECT SUM(pages) FROM (SELECT document_id, MAX(estimated_pages) AS pages FROM chunks GROUP BY document_id)"
            ).fetchone()[0]
            metadata = self._metadata(connection)
        return {
            "status": "ready",
            "path": str(self.path),
            "documents": document_count,
            "chunks": chunk_count,
            "estimated_pages": round(float(estimated_pages or 0), 1),
            "embedding_model": metadata.get("embedding_model", "unknown"),
            "requested_embedding_model": metadata.get("requested_embedding_model", "unknown"),
            "embedding_provider": metadata.get("embedding_provider", "unknown"),
            "embedding_backend": metadata.get("embedding_backend", "unknown"),
            "embedding_revision": metadata.get("embedding_revision") or None,
            "semantic_embeddings": metadata.get("vector_format") == "dense",
            "embedding_error": metadata.get("embedding_error") or None,
            "dimensions": int(metadata.get("dimensions", "0")),
            "chunk_words": int(metadata.get("chunk_words", "0")),
            "overlap_words": int(metadata.get("overlap_words", "0")),
        }


_INDEX: RagIndex | None = None


def get_index() -> RagIndex:
    global _INDEX
    if _INDEX is None:
        _INDEX = RagIndex()
    return _INDEX
