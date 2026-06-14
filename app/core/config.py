from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str

    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"

    # RAG config (เปลี่ยนเพื่อทำ experiment)
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    RETRIEVAL_K: int = 5
    LLM_TEMPERATURE: float = 0.3

    # ChromaDB
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"

    # Upload
    UPLOAD_DIR: str = "./uploads"

    # Auth
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440


settings = Settings()
