from pydantic import BaseSettings


class Settings(BaseSettings):
    telegram_bot_token: str
    bedrock_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    google_client_secrets_file: str = "client_secret.json"
    google_redirect_uri: str = "https://your-redirect-uri.com/oauth2callback"

    class Config:
        env_file = ".env"


settings = Settings()
