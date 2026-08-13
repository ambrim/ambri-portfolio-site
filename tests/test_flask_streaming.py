import json
import unittest
from unittest.mock import patch

from agents.orchestrator.orchestrator_agent import PortfolioAgentResult
import app as portfolio_app
from utils.html_cache import HTMLCacheEntry


class FakeChatStore:
    stores = {}
    session_ids = []

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.entries = self.stores.setdefault(session_id, [])
        self.session_ids.append(session_id)

    def add(self, role: str, content: str) -> None:
        self.entries.append({"role": role, "content": content})

    def format_messages(self):
        return [
            {
                "id": idx,
                "role": entry["role"],
                "content": entry["content"],
                "timestamp": "2026-01-01T00:00:00+00:00",
            }
            for idx, entry in enumerate(self.entries)
        ]

    def __len__(self):
        return len(self.entries)


class FakeHTMLCache:
    stores = {}
    session_ids = []

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.entries = self.stores.setdefault(session_id, [])
        self.session_ids.append(session_id)

    def add(self, query: str, html: str) -> None:
        self.entries.insert(
            0,
            HTMLCacheEntry(
                query=query,
                html=html,
                timestamp="2026-01-01T00:00:00+00:00",
            ),
        )

    def latest(self):
        return self.entries[0] if self.entries else None

    def all(self):
        return self.entries

    def get(self, index: int):
        return self.entries[index] if 0 <= index < len(self.entries) else None

    def promote(self, entry):
        self.entries.remove(entry)
        self.entries.insert(0, entry)

    def __len__(self):
        return len(self.entries)


def parse_sse_events(response):
    raw = b"".join(response.response).decode("utf-8")
    events = []
    for block in raw.split("\n\n"):
        if block.startswith("data: "):
            events.append(json.loads(block[6:]))
    return events


class FlaskStreamingTests(unittest.TestCase):
    def setUp(self):
        portfolio_app.app.config.update(TESTING=True, SECRET_KEY="test-secret")
        FakeChatStore.stores = {}
        FakeChatStore.session_ids = []
        FakeHTMLCache.stores = {}
        FakeHTMLCache.session_ids = []

    def test_streaming_endpoint_returns_sse_events_and_history(self):
        def fake_run_portfolio_request(user_action, html_cache=None, progress_callback=None, chat_history=None):
            progress_callback("Synthetic progress")
            return PortfolioAgentResult(
                success=True,
                chat_message=f"Handled {user_action}",
                html="<section><h2>Synthetic HTML</h2></section>",
            )

        with (
            patch.object(portfolio_app, "ChatStore", FakeChatStore),
            patch.object(portfolio_app, "HTMLCache", FakeHTMLCache),
            patch.object(portfolio_app, "run_portfolio_request", fake_run_portfolio_request),
            portfolio_app.app.test_client() as client,
        ):
            response = client.post("/chat/stream", json={"instruction": "Show projects"})
            events = parse_sse_events(response)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/event-stream")
        self.assertEqual(response.headers["Cache-Control"], "no-cache")
        self.assertEqual(response.headers["X-Accel-Buffering"], "no")

        statuses = [event["status"] for event in events]
        self.assertIn("started", statuses)
        self.assertIn("progress", statuses)
        self.assertEqual(events[-1]["status"], "complete")
        self.assertIn("Synthetic HTML", events[-1]["html"])
        self.assertEqual(events[-1]["history"][-1]["content"], "Handled Show projects")

    def test_same_client_reuses_session_for_context_stores(self):
        def fake_run_portfolio_request(user_action, html_cache=None, progress_callback=None, chat_history=None):
            latest = html_cache.latest()
            html = "<section>refined</section>" if latest and latest.query == "Show projects" else "<section>first</section>"
            return PortfolioAgentResult(
                success=True,
                chat_message=f"Handled {user_action}",
                html=html,
            )

        with (
            patch.object(portfolio_app, "ChatStore", FakeChatStore),
            patch.object(portfolio_app, "HTMLCache", FakeHTMLCache),
            patch.object(portfolio_app, "run_portfolio_request", fake_run_portfolio_request),
            portfolio_app.app.test_client() as client,
        ):
            first = client.post("/chat/stream", json={"instruction": "Show projects"})
            first_events = parse_sse_events(first)
            second = client.post("/chat/stream", json={"instruction": "Make it blue"})
            second_events = parse_sse_events(second)

        self.assertEqual(first_events[-1]["html"], "<section>first</section>")
        self.assertEqual(second_events[-1]["html"], "<section>refined</section>")
        self.assertEqual(len(set(FakeChatStore.session_ids)), 1)
        self.assertEqual(len(set(FakeHTMLCache.session_ids)), 1)
