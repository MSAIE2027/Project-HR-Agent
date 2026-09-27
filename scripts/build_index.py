from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag.index import RagIndex


INDEX_ENV_KEYS = {
    "MSAIE_INDEX_PATH",
    "MSAIE_EMBEDDING_PROVIDER",
    "MSAIE_EMBEDDING_MODEL",
    "MSAIE_EMBEDDING_BASE_URL",
    "MSAIE_EMBEDDING_API_KEY",
    "MSAIE_EMBEDDING_BATCH_SIZE",
    "MSAIE_EMBEDDING_TIMEOUT_SECONDS",
    "MSAIE_EMBEDDING_MAX_RETRIES",
}


def load_local_index_environment() -> None:
    """Load only index-related settings from .env without printing credentials."""
    env_path = PROJECT_ROOT / ".env"
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, separator, value = line.partition("=")
        key = key.strip()
        if not separator or key not in INDEX_ENV_KEYS or key in os.environ:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ[key] = value


def main() -> None:
    load_local_index_environment()
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--chunk-words", type=int, default=120)
    parser.add_argument("--overlap-words", type=int, default=20)
    args = parser.parse_args()
    stats = RagIndex().build(
        chunk_words=args.chunk_words,
        overlap_words=args.overlap_words,
        force=args.force,
    )
    print(json.dumps(stats, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
