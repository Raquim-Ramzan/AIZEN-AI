from functools import lru_cache

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    AIZEN backend configuration.

    All fields are populated automatically by pydantic-settings from
    environment variables and the `.env` file.  Do NOT use os.getenv()
    in field defaults — it bypasses .env loading order.
    """

    # --- API Keys -------------------------------------------------------
    perplexity_api_key: str = ""
    perplexity_base_url: str = "https://api.perplexity.ai"
    gemini_api_key: str = ""
    google_api_key: str = ""
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"

    # --- AIZEN Server Auth -----------------------------------------------
    aizen_api_key: str = ""

    # --- Supabase Database & Auth ----------------------------------------
    supabase_url: str = ""
    supabase_key: str = ""

    # --- Ollama Configuration (local fallback) ---------------------------
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b-instruct-q6_K"

    # --- Model Preferences for Different Task Types ----------------------
    model_coding: str = "gemini-3.1-pro-preview"
    model_chat: str = "gemini-3-flash-preview"
    model_reasoning: str = "gemini-3-flash-preview"
    model_search: str = "sonar-pro"
    model_research: str = "sonar-deep-research"
    model_image: str = "gemini-3.1-flash-image-preview"
    model_embedding: str = "BAAI/bge-small-en-v1.5"
    model_fast_streaming: str = "groq-compound"

    # --- Memory Configuration -------------------------------------------
    mongo_url: str = "mongodb://localhost:27017"
    db_name: str = "ai_assistant"
    chroma_persist_dir: str = "./data/vector_store"
    sqlite_db: str = "./data/conversations.db"
    core_memory_file: str = "./data/core_memory.json"

    # --- Server Settings -------------------------------------------------
    host: str = "0.0.0.0"
    port: int = 8001
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # --- Application Settings -------------------------------------------
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    # --- Timeout and retry settings -------------------------------------
    request_timeout: int = 30
    max_retries: int = 3

    # --- RAG Budget (tokens) --------------------------------------------
    rag_context_budget_tokens: int = 8_000

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="allow",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
