from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class RetrievedChunk:
    text: str
    score: float
    metadata: dict[str, Any] | None = None


class RetrievalClient(ABC):
    @abstractmethod
    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.35,
    ) -> list[RetrievedChunk]:
        raise NotImplementedError

    @staticmethod
    def build_kb_context(chunks: list[RetrievedChunk]) -> str:
        sorted_chunks = sorted(chunks, key=lambda item: item.score, reverse=True)
        return "\n\n---\n\n".join(chunk.text for chunk in sorted_chunks if chunk.text)
