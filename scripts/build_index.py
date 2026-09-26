from __future__ import annotations

import argparse
import json

from rag.index import RagIndex


def main() -> None:
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
