from typing import Any
from upstash_vector import Index, Vector

from clients.retrieval.base import RetrievedChunk, RetrievalClient


class UpstashVectorRetrievalClient(RetrievalClient):
    """
    Retrieval client for an Upstash Vector index configured with hosted embeddings.

    The app sends raw query text and portfolio chunk text. Upstash handles the
    embedding step when the index is created with an embedding model.
    """

    def __init__(
        self,
        rest_url: str,
        rest_token: str,
        namespace: str | None = None,
        timeout: int = 10,
    ):
        if not rest_url:
            raise ValueError("UPSTASH_VECTOR_REST_URL is required")
        if not rest_token:
            raise ValueError("UPSTASH_VECTOR_REST_TOKEN is required")

        self.rest_url = rest_url.rstrip("/")
        self.rest_token = rest_token
        self.namespace = namespace
        self.timeout = timeout
        self.index = Index(url=self.rest_url, token=self.rest_token)

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.35,
    ) -> list[RetrievedChunk]:
        matches = self.index.query(
            data=query,
            top_k=top_k,
            include_vectors=False,
            include_metadata=True,
            include_data=True,
            namespace=self.namespace or "",
        )

        chunks = []
        for item in matches:
            score = float(getattr(item, "score", 0.0))
            if score < min_score:
                continue

            metadata = getattr(item, "metadata", None) or {}
            text = getattr(item, "data", None) or metadata.get("text")
            if not text:
                continue

            chunks.append(
                RetrievedChunk(
                    text=text,
                    score=score,
                    metadata=metadata,
                )
            )

        return sorted(chunks, key=lambda item: item.score, reverse=True)

    def upsert_texts(self, chunks: list[dict[str, Any]]) -> Any:
        """
        Upsert text chunks into an Upstash index with hosted embeddings.

        Expected chunk shape:
        {
            "id": "stable-id",
            "text": "chunk text",
            "metadata": {"source": "..."}
        }
        """
        vectors = []
        for chunk in chunks:
            text = chunk["text"]
            metadata = dict(chunk.get("metadata") or {})
            metadata.setdefault("text", text)
            vectors.append(Vector(id=chunk["id"], data=text, metadata=metadata))

        return self.index.upsert(vectors=vectors, namespace=self.namespace or "")
