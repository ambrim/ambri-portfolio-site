from collections import Counter
import math
import re
from pathlib import Path

from clients.retrieval.base import RetrievedChunk, RetrievalClient


class LocalKeywordRetrievalClient(RetrievalClient):
    """
    Small local retriever for development and fallback deployments.

    This is not a vector store. It gives the app the same retrieval interface
    while using committed markdown/text files as the corpus.
    """

    def __init__(self, data_dir: str = "data", chunk_size: int = 1600, chunk_overlap: int = 150):
        self.data_dir = Path(data_dir)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._chunks = self._load_chunks()

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.05,
    ) -> list[RetrievedChunk]:
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scored_chunks = []
        for chunk in self._chunks:
            score = self._score(query_tokens, self._tokenize(chunk.text))
            if score >= min_score:
                scored_chunks.append(
                    RetrievedChunk(
                        text=chunk.text,
                        score=score,
                        metadata=chunk.metadata,
                    )
                )

        return sorted(scored_chunks, key=lambda item: item.score, reverse=True)[:top_k]

    def _load_chunks(self) -> list[RetrievedChunk]:
        if not self.data_dir.exists():
            return []

        chunks = []
        for path in sorted(self.data_dir.glob("**/*")):
            if path.suffix.lower() not in {".md", ".markdown", ".txt"}:
                continue

            text = path.read_text(encoding="utf-8").strip()
            for idx, chunk_text in enumerate(self._split_text(text)):
                chunks.append(
                    RetrievedChunk(
                        text=chunk_text,
                        score=0.0,
                        metadata={"source": str(path), "chunk_index": idx},
                    )
                )
        return chunks

    def _split_text(self, text: str) -> list[str]:
        if len(text) <= self.chunk_size:
            return [text] if text else []

        if re.search(r"(?m)^#{1,3}\s+", text):
            return self._split_markdown_by_headings(text)

        return self._split_long_text(text)

    def _split_markdown_by_headings(self, text: str) -> list[str]:
        sections = []
        current_heading = None
        current_lines = []

        for line in text.splitlines():
            if re.match(r"^#{1,3}\s+", line):
                if current_lines:
                    sections.append((current_heading, "\n".join(current_lines).strip()))
                current_heading = line.strip()
                current_lines = [line]
            else:
                current_lines.append(line)

        if current_lines:
            sections.append((current_heading, "\n".join(current_lines).strip()))

        chunks = []
        for heading, section in sections:
            if not section:
                continue
            content_lines = [line for line in section.splitlines() if line.strip()]
            if content_lines and all(re.match(r"^#{1,6}\s+", line) for line in content_lines):
                continue
            if len(section) <= self.chunk_size:
                chunks.append(section)
                continue

            section_body = section
            prefix = f"{heading}\n\n" if heading and not section.startswith(heading) else ""
            for chunk in self._split_long_text(section_body):
                chunk_text = f"{prefix}{chunk}".strip()
                if chunk_text:
                    chunks.append(chunk_text)

        return chunks

    def _split_long_text(self, text: str) -> list[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            split_at = text.rfind("\n\n", start, end)
            split_on_paragraph = split_at > start
            if split_at <= start:
                split_at = end

            chunk = text[start:split_at].strip()
            if chunk:
                chunks.append(chunk)

            if split_at >= len(text):
                break
            if split_on_paragraph:
                start = split_at
            else:
                start = max(split_at - self.chunk_overlap, start + 1)

        return chunks

    def _score(self, query_tokens: list[str], chunk_tokens: list[str]) -> float:
        query_counts = Counter(query_tokens)
        chunk_counts = Counter(chunk_tokens)
        overlap = set(query_counts) & set(chunk_counts)
        if not overlap:
            return 0.0

        numerator = sum(query_counts[token] * chunk_counts[token] for token in overlap)
        query_norm = math.sqrt(sum(value * value for value in query_counts.values()))
        chunk_norm = math.sqrt(sum(value * value for value in chunk_counts.values()))
        if query_norm == 0 or chunk_norm == 0:
            return 0.0

        return numerator / (query_norm * chunk_norm)

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"[a-z0-9]+", text.lower())
