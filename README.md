# Ambri's Portfolio Website
Chat-based multi-agent portfolio website template using Strands to dynamically render UI

## Heroku without AWS

Use Gemini for generation and Upstash Vector for portfolio retrieval:

```bash
heroku config:set AI_PROVIDER=gemini
heroku config:set MODEL_ID=gemini-flash-latest
heroku config:set MODEL_TEMPERATURE=0.3
heroku config:set GEMINI_API_KEY=...

heroku config:set RETRIEVAL_PROVIDER=upstash
heroku config:set UPSTASH_VECTOR_REST_URL=...
heroku config:set UPSTASH_VECTOR_REST_TOKEN=...
```

Create an Upstash Vector index with hosted embeddings enabled. The app sends
plain text to Upstash for both indexing and querying, so no separate embedding
API is needed.

Portfolio source data lives in `data/*.md`. After editing those files, index
them with:

```bash
RETRIEVAL_PROVIDER=upstash \
UPSTASH_VECTOR_REST_URL=... \
UPSTASH_VECTOR_REST_TOKEN=... \
python scripts/index_portfolio.py
```

For local retrieval testing without Upstash:

```bash
RETRIEVAL_PROVIDER=local python -m unittest tests/test_retrieval_clients.py
python scripts/index_portfolio.py --dry-run
```

The provider interfaces are:

- `clients.llm.base.LLMProvider` for generation model providers
- `clients.retrieval.base.RetrievalClient` for RAG/vector retrieval providers
