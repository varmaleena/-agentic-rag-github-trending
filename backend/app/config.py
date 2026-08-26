import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    AWS_REGION: str = "us-east-1"
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-haiku-20240307-v1:0"
    
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
