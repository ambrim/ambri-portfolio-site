import argparse
import hashlib
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from clients.retrieval.local_keyword_client import LocalKeywordRetrievalClient
from clients.retrieval.upstash_vector_client import UpstashVectorRetrievalClient
from utils.retrieval_config import create_retrieval_client


def build_chunks(data_dir: str) -> list[dict]:
    local_client = LocalKeywordRetrievalClient(data_dir=data_dir)
    chunks = []

    for chunk in local_client._chunks:
        source = chunk.metadata.get("source", "unknown") if chunk.metadata else "unknown"
        chunk_index = chunk.metadata.get("chunk_index", 0) if chunk.metadata else 0
        digest = hashlib.sha1(f"{source}:{chunk_index}:{chunk.text}".encode("utf-8")).hexdigest()[:12]
        chunks.append(
            {
                "id": f"{Path(source).stem}-{chunk_index}-{digest}",
                "text": chunk.text,
                "metadata": chunk.metadata or {},
            }
        )

    return chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Index portfolio data into Upstash Vector.")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear the target Upstash namespace before upserting chunks.",
    )
    args = parser.parse_args()

    chunks = build_chunks(args.data_dir)
    print(f"Prepared {len(chunks)} chunks from {args.data_dir}")

    if args.dry_run:
        for chunk in chunks[:3]:
            print(f"- {chunk['id']}: {chunk['text'][:120].replace(chr(10), ' ')}")
        return

    client = create_retrieval_client()
    if not isinstance(client, UpstashVectorRetrievalClient):
        raise RuntimeError("Set RETRIEVAL_PROVIDER=upstash before indexing.")

    if args.reset:
        print("Resetting target Upstash namespace before indexing...")
        print(client.index.reset(namespace=client.namespace or ""))

    result = client.upsert_texts(chunks)
    print(result)


if __name__ == "__main__":
    main()
