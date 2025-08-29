# Secrets Setup Guide

This guide explains how to set up the required secrets for the Ctrl-Alt-Heal application.

## Required Secrets

### 1. Serper API Key

The Serper API key is used for web search functionality in the search tool.

#### Getting a Serper API Key

1. Go to [serper.dev](https://serper.dev)
2. Sign up for an account
3. Get your API key from the dashboard
4. They offer a free tier with generous limits

#### Setting Up the Secret

After deploying the CDK stack, update the Serper API key:

```bash
# Deploy the CDK stack first
cd cdk
cdk deploy --all

# Then update the Serper API key
python scripts/update_serper_secret.py <your_serper_api_key>
```

#### Manual Setup (Alternative)

If you prefer to set up the secret manually:

1. Go to AWS Secrets Manager console
2. Create a new secret
3. Name: `ctrl-alt-heal/serper/api-key`
4. Secret value: `{"api_key": "your_serper_api_key_here"}`

### 2. Telegram Bot Token

The Telegram bot token is now managed by the CDK stack as `ctrl-alt-heal/telegram/bot-token`.

#### Getting a Telegram Bot Token

1. Message @BotFather on Telegram
2. Use `/newbot` command to create a new bot
3. Get your bot token from the response

#### Setting Up the Secret

After deploying the CDK stack, update the Telegram bot token:

```bash
# Deploy the CDK stack first
cd cdk
cdk deploy --all

# Then update the Telegram bot token
python scripts/update_telegram_secret.py <your_telegram_bot_token>
```

#### Manual Setup (Alternative)

If you prefer to set up the secret manually:

1. Go to AWS Secrets Manager console
2. Create a new secret
3. Name: `ctrl-alt-heal/telegram/bot-token`
4. Secret value: `{"value": "your_telegram_bot_token_here"}`

### 3. Webhook Secret (Environment Variable)

The webhook secret is used for local development and testing. It's not managed by CDK but should be set as an environment variable:

```bash
export TELEGRAM_WEBHOOK_SECRET=your_webhook_secret_here
```

### 4. Bedrock Credentials

Bedrock credentials are handled automatically through AWS IAM roles. No API keys are needed - the Lambda function has the necessary permissions to invoke Bedrock models.

## CDK Infrastructure

The secrets are managed through CDK infrastructure:

- **SecretsStack**: Creates the Serper secret in AWS Secrets Manager
- **LambdaStack**: Grants Lambda functions permission to access the secrets
- **Environment Variables**: Lambda functions are configured to use the secrets

## Security Notes

- Secrets are stored in AWS Secrets Manager (encrypted at rest)
- Lambda functions have minimal required permissions to access secrets
- API keys are never stored in code or environment variables
- Secrets are automatically rotated by AWS Secrets Manager

## Troubleshooting

### Secret Not Found Error

If you get a "Secret not found" error:

1. Make sure you've deployed the CDK stack: `cdk deploy --all`
2. Check that the secret exists in AWS Secrets Manager console
3. Verify the secret name matches: `ctrl-alt-heal/serper/api-key`

### Permission Denied Error

If you get a permission error:

1. Make sure your AWS credentials are configured
2. Verify you have permission to access Secrets Manager
3. Check that the Lambda function has the correct IAM permissions

### Search Tool Not Working

If the search tool returns "SERPER_API_KEY not found":

1. Verify the secret exists and contains the correct format
2. Check that the API key is valid and active
3. Ensure the Lambda function can access the secret
