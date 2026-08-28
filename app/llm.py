from __future__ import annotations

from typing import Any

from openai import OpenAI

from .config import Settings


class LLMClient:
    """Thin OpenAI-compatible client; works with TokenRouter or api.openai.com."""

    def __init__(self, settings: Settings):
        kwargs: dict[str, Any] = {"api_key": settings.api_api_key}
        if settings.base_url:
            kwargs["base_url"] = settings.base_url
        self.client = OpenAI(**kwargs)
        self.model = settings.model

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None):
        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools or None,
            temperature=0.2,
        )
