import unittest

from clients.retrieval.base import RetrievedChunk
from clients.retrieval.local_keyword_client import LocalKeywordRetrievalClient
from clients.retrieval.upstash_vector_client import UpstashVectorRetrievalClient


class FakeQueryResult:
    def __init__(self, score, data, metadata=None):
        self.score = score
        self.data = data
        self.metadata = metadata or {}


class FakeIndex:
    def __init__(self, query_results=None):
        self.query_results = query_results or []
        self.calls = []

    def query(self, **kwargs):
        self.calls.append({"method": "query", "kwargs": kwargs})
        return self.query_results

    def upsert(self, vectors, namespace=""):
        self.calls.append({"method": "upsert", "vectors": vectors, "namespace": namespace})
        return "Success"


class RetrievalClientTests(unittest.TestCase):
    def test_local_keyword_retrieval_finds_sample_project_content(self):
        client = LocalKeywordRetrievalClient(data_dir="data")

        chunks = client.retrieve("agentic portfolio project", top_k=3)

        self.assertGreaterEqual(len(chunks), 1)
        self.assertIn("agentic portfolio", chunks[0].text.lower())

    def test_build_context_orders_by_score(self):
        context = LocalKeywordRetrievalClient.build_kb_context(
            [
                RetrievedChunk(text="second", score=0.2),
                RetrievedChunk(text="first", score=0.9),
            ]
        )

        self.assertTrue(context.startswith("first"))

    def test_upstash_query_payload_and_response_parsing(self):
        client = UpstashVectorRetrievalClient(
            rest_url="https://example-vector.upstash.io",
            rest_token="token",
        )
        fake_index = FakeIndex(
            [
                FakeQueryResult(
                    score=0.91,
                    data="Relevant portfolio text",
                    metadata={"source": "portfolio.md"},
                ),
                FakeQueryResult(score=0.1, data="Low score text"),
            ]
        )
        client.index = fake_index

        chunks = client.retrieve("portfolio", min_score=0.35)

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].text, "Relevant portfolio text")
        self.assertEqual(fake_index.calls[0]["kwargs"]["data"], "portfolio")
        self.assertTrue(fake_index.calls[0]["kwargs"]["include_data"])

    def test_upstash_upsert_payload(self):
        client = UpstashVectorRetrievalClient(
            rest_url="https://example-vector.upstash.io",
            rest_token="token",
        )
        fake_index = FakeIndex()
        client.index = fake_index

        client.upsert_texts(
            [
                {
                    "id": "chunk-1",
                    "text": "Portfolio text",
                    "metadata": {"source": "portfolio.md"},
                }
            ]
        )

        payload = fake_index.calls[0]["vectors"]
        self.assertEqual(payload[0].id, "chunk-1")
        self.assertEqual(payload[0].data, "Portfolio text")
        self.assertEqual(payload[0].metadata["text"], "Portfolio text")


if __name__ == "__main__":
    unittest.main()
