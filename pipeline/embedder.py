import logging
import os
from openai import OpenAI

log = logging.getLogger(__name__)

LM_STUDIO_URL = os.environ.get("LM_STUDIO_URL", "http://127.0.0.1:1234/v1")
DEFAULT_EMBED_MODEL = os.environ.get("LM_EMBED_MODEL", "text-embedding-nomic-ai-nomic-embed-text-v2-moe")

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(base_url=LM_STUDIO_URL, api_key="lm-studio")
    return _client


def embed(text: str, model: str = None) -> list[float]:
    model = model or DEFAULT_EMBED_MODEL
    log.debug("Embedding %d chars with model=%s", len(text), model)
    response = _get_client().embeddings.create(model=model, input=text)
    return response.data[0].embedding
