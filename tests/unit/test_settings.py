from __future__ import annotations

from src.ctrl_alt_heal.config.settings import Settings


def test_settings_defaults() -> None:
    settings = Settings.load()
    assert settings.aws_region == "us-east-1"
    assert settings.bedrock_model_id.startswith("amazon.nova")
