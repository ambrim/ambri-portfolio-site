from clients.kb_client import KnowledgeBaseClient
from clients.retrieval.base import RetrievedChunk, RetrievalClient


class AwsKnowledgeBaseRetrievalClient(RetrievalClient):
    def __init__(self, knowledge_base_client: KnowledgeBaseClient):
        self.knowledge_base_client = knowledge_base_client

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.35,
    ) -> list[RetrievedChunk]:
        chunks = self.knowledge_base_client.retrieve(
            query=query,
            top_k=top_k,
            min_score=min_score,
        )
        return [
            RetrievedChunk(
                text=chunk["text"],
                score=chunk["score"],
                metadata=chunk.get("metadata"),
            )
            for chunk in chunks
        ]
