"""Thin Anthropic Messages API client. Returns None when no key / any failure,
so every agent can fall back to offline (rule-based) mode."""
import logging
from app.core.config import settings

log = logging.getLogger("jeevanai.llm")


def llm_available() -> bool:
    return bool(settings.anthropic_api_key)


def complete(system: str, user: str, max_tokens: int = 1500):
    if not llm_available():
        return None
    import httpx
    for attempt in range(2):
        try:
            r = httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": settings.anthropic_api_key,
                         "anthropic-version": "2023-06-01",
                         "content-type": "application/json"},
                json={"model": settings.llm_model, "max_tokens": max_tokens, "system": system,
                      "messages": [{"role": "user", "content": user}]},
                timeout=60,
            )
            r.raise_for_status()
            text = "".join(b.get("text", "") for b in r.json().get("content", []) if b.get("type") == "text")
            return text.strip() or None
        except (httpx.HTTPError, ValueError) as e:
            log.warning("LLM call failed (try %s): %s", attempt + 1, e)
    return None
