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
    uploads_bucket_name: str
    telegram_secret_name: str

    class Config:
        env_file = ".env"
        # Allow reading from environment variables as a fallback
        env_file_encoding = "utf-8"


settings = Settings()

logger.info("--- Settings Loaded ---")
logger.info(f"Bedrock Model ID: {settings.bedrock_model_id}")
logger.info(f"Bedrock Multimodal Model ID: {settings.bedrock_multimodal_model_id}")
logger.info(f"Database Table Name: {settings.database_table_name}")
logger.info(f"Uploads Bucket Name: {settings.uploads_bucket_name}")
logger.info(f"Telegram Secret Name: {settings.telegram_secret_name}")
logger.info("----------------------")
