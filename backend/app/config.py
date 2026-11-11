from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    LLM_PROVIDER: Literal["vertex", "bedrock"] = "bedrock"
    GOOGLE_CLOUD_PROJECT: str = ""
    GOOGLE_CLOUD_LOCATION: str = "global"
    GEMINI_MODEL: str = ""

    AWS_REGION: str = "us-east-1"
    BEDROCK_MODEL_ID: str = "us.amazon.nova-lite-v1:0"
    
    HISTORY_DATABASE_URL: str = ""
    HISTORY_DB_PATH: str = "data/query_history.sqlite3"
    QDRANT_URL: str = ""
    QDRANT_API_KEY: str = ""
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = "github_repos"
    
    GITHUB_TOKEN: str = ""
    
    EVAL_SCORE_THRESHOLD: float = 0.7
    MAX_RETRIEVAL_RETRIES: int = 3
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
