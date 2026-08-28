from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str = "z-ai/glm-5.3"
    base_url: str | None = "https://api.tokenrouter.io/v1"
    data_dir: str = "data"
    knowledge_dir: str = "knowledge-base"
    retrieval_top_k: int = 6


def get_settings() -> Settings:
    key = os.getenv("TOKENROUTER_API_KEY", "").strip() or os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("TOKENROUTER_API_KEY is not set. Copy .env.example to .env and add your TokenRouter key.")
    return Settings(
        api_key=key,
        model=os.getenv("ASTER_MODEL", "z-ai/glm-5.3").strip() or "z-ai/glm-5.3",
        base_url=os.getenv("ASTER_BASE_URL", "https://api.tokenrouter.io/v1").strip() or None,
        data_dir=os.getenv("ASTER_DATA_DIR", "data"),
        knowledge_dir=os.getenv("ASTER_KNOWLEDGE_DIR", "knowledge-base"),
        retrieval_top_k=int(os.getenv("ASTER_RETRIEVAL_TOP_K", "6")),
    )


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]
