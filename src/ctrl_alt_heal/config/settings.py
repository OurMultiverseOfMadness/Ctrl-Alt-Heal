from pydantic_settings import BaseSettings
import logging

# Set up logging
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    bedrock_model_id: str = "apac.amazon.nova-lite-v1:0"
    bedrock_multimodal_model_id: str = "apac.amazon.nova-lite-v1:0"
    google_client_secrets_file: str = "client_secret.json"
    google_redirect_uri: str = "https://your-redirect-uri.com/oauth2callback"
    database_table_name: str = ""
    uploads_bucket_name: str = "test-uploads-bucket"
    telegram_secret_name: str = "test-telegram-secret"

    class Config:
        env_file = ".env"
        # Allow reading from environment variables as a fallback
        env_file_encoding = "utf-8"


settings = Settings()
