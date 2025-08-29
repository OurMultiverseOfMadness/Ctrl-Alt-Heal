from aws_cdk import aws_secretsmanager as secretsmanager, Stack
from constructs import Construct


class SecretsStack(Stack):
    """Stack for managing AWS Secrets Manager resources."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Serper API Secret
        self.serper_secret = secretsmanager.Secret(
            self,
            "CtrlAltHealSerperSecretV2",
            secret_name="ctrl-alt-heal/serper/api-key",
            description="Serper API key for web search functionality",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"api_key": "PLACEHOLDER"}',
                generate_string_key="api_key",
                exclude_characters="\"'\\",
            ),
        )

        # Import existing Telegram Bot Token Secret
        self.telegram_secret = secretsmanager.Secret.from_secret_complete_arn(
            self,
            "CtrlAltHealTelegramSecret",
            secret_complete_arn="arn:aws:secretsmanager:ap-southeast-1:532003627730:secret:ctrl-alt-heal/telegram/bot-token-iVVQbW",
        )

        # Note: The actual API keys should be updated manually after deployment
        # or through a separate process for security reasons
