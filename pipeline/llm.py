import logging
import os
from openai import OpenAI

log = logging.getLogger(__name__)

# Silence noisy HTTP debug logs from the openai/httpx/httpcore stack
for _lib in ("httpcore", "httpx", "openai"):
    logging.getLogger(_lib).setLevel(logging.WARNING)

LM_STUDIO_URL = os.environ.get("LM_STUDIO_URL", "http://127.0.0.1:1234/v1")
DEFAULT_MODEL = os.environ.get("LM_MODEL", "qwen/qwen3-vl-8b")
DEFAULT_EMBED_MODEL = os.environ.get("LM_EMBED_MODEL", "text-embedding-nomic-ai-nomic-embed-text-v2-moe")

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        # connect_timeout=10s, read timeout=5min (LLM generation can be slow)
        _client = OpenAI(
            base_url=LM_STUDIO_URL,
            api_key="lm-studio",
            timeout=300.0,
        )
    return _client


def embed(text: str, model: str = None) -> list[float]:
    model = model or DEFAULT_EMBED_MODEL
    log.debug("Embedding %d chars with model=%s", len(text), model)
    response = _get_client().embeddings.create(model=model, input=text)
    return response.data[0].embedding


def format_as_markdown(title: str, text: str, model: str = None) -> str:
    model = model or DEFAULT_MODEL
    prompt = (
        f"Convert the following article text into well-structured Markdown.\n"
        f"Use headings, bullet points, bold, and other Markdown formatting where appropriate.\n"
        f"Do not add new content or change the meaning. Return only the Markdown, nothing else.\n\n"
        f"Title: {title}\n\n"
        f"{text}"
    )
    log.debug("Formatting as markdown with model=%s", model or "local-model")
    response = _get_client().chat.completions.create(
        model=model or "local-model",
        messages=[{"role": "user", "content": prompt}],
    )
    result = response.choices[0].message.content.strip()
    log.debug("Formatted markdown (%d chars)", len(result))
    return result


def generate_summary(title: str, text: str, model: str = None) -> str:
    model = model or DEFAULT_MODEL
    prompt = (
        f"Write a summary of this article in a concise way, no fluff.\n"
        f"Title: {title}\n"
        f"Content (excerpt): {text[:3000]}\n"
        f"Return only the summary, nothing else."
    )
    log.debug("Generating summary with model=%s", model or "local-model")
    response = _get_client().chat.completions.create(
        model=model or "local-model",
        messages=[{"role": "user", "content": prompt}],
    )
    summary = response.choices[0].message.content.strip()
    log.debug("Generated summary (%d chars)", len(summary))
    return summary


def generate_tags(title: str, text: str, model: str = None) -> list[str]:
    model = model or DEFAULT_MODEL
    prompt = (
        f"Extract 5-10 concise topic tags for this article.\n"
        f"Title: {title}\n"
        f"Content (excerpt): {text[:2000]}\n"
        f"Return only a comma-separated list of tags, nothing else."
    )
    log.debug("Generating tags with model=%s", model or "local-model")
    response = _get_client().chat.completions.create(
        model=model or "local-model",
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.choices[0].message.content
    tags = [t.strip().lower() for t in raw.split(",") if t.strip()]
    log.debug("Generated tags: %s", tags)
    return tags
