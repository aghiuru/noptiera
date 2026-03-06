# noptiera

Personal knowledge pipeline. Ingest articles from URLs, index them with vector embeddings, search semantically. Accessible via CLI, MCP server, or Telegram bot.

## Requirements

- Python 3.11+
- [LM Studio](https://lmstudio.ai) running locally with:
  - A chat model with tool-calling support (e.g. `qwen2.5`, `mistral-nemo`)
  - An embedding model (e.g. `nomic-embed-text-v2-moe`)

## Setup

```bash
poetry install
cp .env.example .env  # fill in values
```

`.env`:
```
TELEGRAM_TOKEN=...
TELEGRAM_USER_ID=...
LM_STUDIO_URL=http://127.0.0.1:1234/v1   # default
LM_MODEL=qwen/qwen3-vl-8b                 # default
LM_EMBED_MODEL=text-embedding-nomic-ai-nomic-embed-text-v2-moe  # default
```

## CLI

```bash
poetry run noptiera ingest https://example.com/article
poetry run noptiera search "machine learning"
poetry run noptiera list
poetry run noptiera fetch https://example.com/article   # preview extraction only
```

## Telegram bot

```bash
poetry run python bot.py
```

Send any message — the LLM agent decides whether to ingest or search based on your intent.

## MCP server

```bash
poetry run python mcp_server.py
```

Exposes two tools over stdio MCP transport:
- `ingest(url, force=False)` — download, parse, tag and index an article
- `search(query, top_k=5)` — semantic search over indexed articles

## How it works

```
User message
    └── bot.py (Telegram)
            └── pipeline/agent.py
                    ├── fastmcp.Client → mcp_server.py (in-process)
                    │       lists tool schemas
                    ├── LM Studio LLM (tool-calling)
                    │       picks ingest or search
                    └── fastmcp.Client.call_tool()
                            ├── pipeline/ingest.py
                            │       parser → llm (format/tag/summarise) → embedder → store
                            └── pipeline/search.py
                                    embedder → store (ChromaDB vector query)
```

Ingested articles are saved as Markdown with YAML frontmatter in `articles/`. The vector index lives in `.index/` (ChromaDB).
