"""Shared OpenAI client — singleton with connection pooling for OpenRouter."""

from __future__ import annotations

import threading
from typing import Optional

import openai

from app.config import settings

_client: Optional[openai.AsyncOpenAI] = None
_lock = threading.Lock()


def get_client() -> openai.AsyncOpenAI:
    """Return a shared AsyncOpenAI client (lazy-initialized, thread-safe).

    Using a single client across all tools avoids creating redundant TCP
    connections and benefits from httpx's built-in connection pooling.
    """
    global _client
    if _client is None:
        with _lock:
            if _client is None:  # double-checked locking
                _client = openai.AsyncOpenAI(
                    base_url=settings.OPENROUTER_BASE_URL,
                    api_key=settings.OPENROUTER_API_KEY,
                    default_headers={
                        "HTTP-Referer": "https://github.com/mysticalseeker24/notebrew",
                        "X-Title": "NoteBrew",
                    },
                )
    return _client
