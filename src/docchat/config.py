import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    nvidia_api_key: str

    # copy exact IDs from build.nvidia.com
    chat_model: str = "meta/llama-3.1-70b-instruct"
    embedding_model: str = "nvidia/nv-embed-v1"

    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 10

    raw_dir: Path = ROOT / "data" / "raw"

    # Qdrant: local on-disk mode by default
    vectorstore_dir: Path = ROOT / "data" / "vectorstore"
    collection_name: str = "docs"
    # optional: set these in .env to use a Qdrant server or Qdrant Cloud instead
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None

    app_title: str = "Chat with your documents"
    snippet_chars: int = 1000


settings = Settings()
os.environ["NVIDIA_API_KEY"] = settings.nvidia_api_key