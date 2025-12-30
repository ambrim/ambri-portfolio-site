import boto3
from typing import List, Dict, Any


class KnowledgeBaseClient:
    def __init__(
        self,
        knowledge_base_id: str,
        boto_session: boto3.Session,
        region_name: str = "us-east-1",
    ):
        self.knowledge_base_id = knowledge_base_id
        self.client = boto_session.client(
            "bedrock-agent-runtime",
            region_name=region_name,
        )

        print(
            f"[KB] Initialized KnowledgeBaseClient | "
            f"kb_id={knowledge_base_id} | region={region_name}"
        )

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.35,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant text chunks from the knowledge base.
        Returns a list of dicts with 'text' and 'score' keys.
        
        Args:
            query: Search query string
            top_k: Maximum number of results to retrieve (default: 20)
            min_score: Minimum relevance score threshold (0.0-1.0, default: 0.5)
        """

        print(f"[KB] Retrieving chunks | query='{query}' | top_k={top_k} | min_score={min_score}")

        response = self.client.retrieve(
            knowledgeBaseId=self.knowledge_base_id,
            retrievalQuery={
                "text": query
            },
            retrievalConfiguration={
                "vectorSearchConfiguration": {
                    "numberOfResults": top_k
                }
            }
        )

        retrieval_results = response.get("retrievalResults", [])
        print(f"[KB] Raw retrieval results count: {len(retrieval_results)}")

        results = []

        for idx, item in enumerate(retrieval_results):
            content = item.get("content", {})
            text = content.get("text")
            score = item.get("score", 0.0)

            if not text:
                print(f"[KB] ✗ Chunk {idx + 1} missing text field")
                continue

            if score < min_score:
                print(f"[KB] ✗ Chunk {idx + 1} rejected (score={score:.3f} < {min_score})")
                continue

            results.append({
                "text": text,
                "score": score
            })
            print(f"[KB] ✓ Chunk {idx + 1} accepted (score={score:.3f}, {len(text)} chars)")

        print(f"[KB] Final extracted chunks: {len(results)}")

        return results

    @staticmethod
    def build_kb_context(
        chunks: List[Dict[str, Any]],
    ) -> str:
        """
        Concatenate KB chunks into a context block, ordered by relevance score.
        No character limit - includes all chunks that passed the score threshold.
        
        Args:
            chunks: List of dicts with 'text' and 'score' keys
        """
        print(f"[KB] Building KB context | chunks={len(chunks)}")

        if not chunks:
            print("[KB] No chunks to build context from")
            return ""

        sorted_chunks = sorted(chunks, key=lambda x: x.get("score", 0.0), reverse=True)

        context_parts = []
        total_chars = 0

        for idx, chunk in enumerate(sorted_chunks):
            text = chunk.get("text", "")
            score = chunk.get("score", 0.0)
            
            context_parts.append(text)
            total_chars += len(text)

            print(
                f"[KB] Added chunk {idx + 1} | "
                f"score={score:.3f} | chunk_chars={len(text)} | total_chars={total_chars}"
            )

        print(f"[KB] Final KB context size: {total_chars} chars from {len(context_parts)} chunks")

        return "\n\n---\n\n".join(context_parts)
