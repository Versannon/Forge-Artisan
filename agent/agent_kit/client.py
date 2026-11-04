"""The Meta Model API client: official OpenAI Python SDK pointing to api.meta.ai."""

from __future__ import annotations

import os
from openai import OpenAI
from agent_kit import settings

DEFAULT_BASE_URL = settings.DEFAULT_BASE_URL
MAX_RETRIES = 3
TIMEOUT_SECONDS = 120


class MissingKeyError(RuntimeError):
    pass


def make_client() -> OpenAI:
    """Creates an OpenAI client for Meta Model API, from MODEL_API_KEY."""
    key = os.environ.get("MODEL_API_KEY", "").strip()
    if not key:
        # Fallback to local or demo key for offline verification
        key = os.environ.get("OPENAI_API_KEY", "meta-api-dummy-key")

    base_url = os.environ.get("MODEL_API_BASE_URL") or DEFAULT_BASE_URL
    return OpenAI(
        api_key=key,
        base_url=base_url,
        max_retries=MAX_RETRIES,
        timeout=TIMEOUT_SECONDS,
    )
