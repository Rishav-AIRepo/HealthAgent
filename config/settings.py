from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    # Azure OpenAI
    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = "2024-02-01"
    azure_openai_deployment_name: str = "gpt-4o"
    azure_openai_embedding_deployment: str = "text-embedding-3-small"

    # Application
    app_env: str = "development"
    app_secret_key: str = "change-me-in-production"
    app_debug: bool = False
    app_log_level: str = "INFO"

    # Database
    database_url: str = "sqlite:///./data/health.db"

    # Storage
    pdf_storage_path: str = "./data/pdfs"
    faiss_index_path: str = "./data/faiss_index"
    drug_knowledge_path: str = "./data/drug_knowledge"

    # Embedding
    embedding_chunk_size: int = 500
    embedding_chunk_overlap: int = 50
    faiss_top_k: int = 5

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Frontend (used in OAuth redirects and Stripe return URLs)
    frontend_url: str = "http://localhost:3000"

    # Google OAuth (F1)
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/callback"

    # Stripe (F2)
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_standard: str = ""
    stripe_price_premium: str = ""

    class Config:
        env_file = "config/.env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
