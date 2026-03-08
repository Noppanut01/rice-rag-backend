from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_LLM_MODEL: str = "gemma3:4b"
    OLLAMA_EMBEDDING_MODEL: str = "bge-m3"

    # RAG config (เปลี่ยนเพื่อทำ experiment)
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    RETRIEVAL_STRATEGY: str = "mmr"  # "similarity" หรือ "mmr"
    RETRIEVAL_K: int = 3
    LLM_TEMPERATURE: float = 0.3

    # ChromaDB
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"

    # Upload
    UPLOAD_DIR: str = "./uploads"

    # Auth
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440


settings = Settings()
