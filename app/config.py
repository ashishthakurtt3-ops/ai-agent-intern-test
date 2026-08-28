from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    model: str = "gpt-5.6-luna"
    data_dir: str = "data"
    knowledge_dir: str = "knowledge-base"
    retrieval_top_k: int = 6


def get_settings() -> Settings:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set. Copy .env.example to .env and add your key.")
    return Settings(
        openai_api_key=key,
        model=os.getenv("OPENAI_MODEL", "gpt-5.6-luna"),
    )
