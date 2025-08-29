from aws_cdk import aws_secretsmanager as secretsmanager, Stack
from constructs import Construct


class SecretsStack(Stack):
    """Stack for managing AWS Secrets Manager resources."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Serper API Secret
        self.serper_secret = secretsmanager.Secret(
            self,
            "CtrlAltHealSerperSecret",
            secret_name="CtrlAltHealSerperSecret",
            description="Serper API key for web search functionality",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"api_key": "PLACEHOLDER"}',
                generate_string_key="api_key",
                exclude_characters="\"'\\",
            ),
        )

        # Create Telegram Bot Token Secret
        self.telegram_secret = secretsmanager.Secret(
            self,
            "CtrlAltHealTelegramSecret",
            secret_name="ctrl-alt-heal/telegram/bot-token",
            description="Telegram bot token for messaging functionality",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"value": "PLACEHOLDER"}',
                generate_string_key="value",
                exclude_characters="\"'\\",
            ),
        )

        # Note: The actual API keys should be updated manually after deployment
        # or through a separate process for security reasons
