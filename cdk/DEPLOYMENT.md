# Ctrl-Alt-Heal AWS Deployment Guide

This guide provides step-by-step instructions for deploying Ctrl-Alt-Heal to a new AWS account.

## 🚀 **Quick Deployment**

### **Prerequisites**

1. **AWS CLI** configured with appropriate permissions
2. **Node.js** 18+ installed
3. **Python** 3.11+ installed
4. **Docker** (for building Lambda layers)
5. **Amazon Bedrock access** in ap-southeast-1 region

### **One-Command Deployment**

```bash
# Deploy to Fargate (from project root)
./deploy-fargate.sh --profile your-aws-profile
```

The deployment script will:
- ✅ Check AWS CLI configuration
- ✅ Install dependencies
- ✅ Bootstrap CDK (if needed)
- ✅ Deploy all stacks (Database, Secrets, Fargate, API Gateway)
- ✅ Build and push Docker image to ECR
- ✅ Deploy Fargate service
- ✅ Provide API Gateway URLs

## 🔧 **Manual Deployment**

### **1. Environment Setup**

```bash
# Set environment variables
export ENVIRONMENT="dev"           # or "staging", "prod"
export PROJECT_NAME="CtrlAltHeal"  # or your project name
export AWS_REGION="ap-southeast-1" # or your preferred region

# Navigate to CDK directory
cd cdk
```

### **2. Install Dependencies**

```bash
# Install Node.js dependencies
npm install

# Install Python dependencies (if needed)
pip install -r requirements-dev.txt
```

### **3. Bootstrap CDK**

```bash
# Bootstrap CDK (only needed once per account/region)
cdk bootstrap
```

### **4. Deploy Stacks**

```bash
# Deploy all stacks
cdk deploy --all

# Or deploy specific stacks
cdk deploy Cara-AgentsDatabaseStack
cdk deploy Cara-AgentsSecretsStack
cdk deploy Cara-AgentsFargateStack
cdk deploy Cara-AgentsApiGatewayStack
```

## 📋 **Post-Deployment Setup**

### **1. Update Secrets**

After deployment, update the secrets in AWS Secrets Manager:

#### **Serper API Key**
```bash
# Get your Serper API key from https://serper.dev
aws secretsmanager update-secret \
  --secret-id "ctrl-alt-heal/${ENVIRONMENT}/serper/api-key" \
  --secret-string '{"api_key": "your_serper_api_key_here"}'
```

#### **Telegram Bot Token**
```bash
# Get your Telegram bot token from @BotFather
aws secretsmanager update-secret \
  --secret-id "ctrl-alt-heal/${ENVIRONMENT}/telegram/bot-token" \
  --secret-string '{"value": "your_telegram_bot_token_here"}'
```

### **2. Set Telegram Webhook**

```bash
# Get the API Gateway URL from CDK output
cdk output

# Set the webhook (replace with your actual URL)
export WEBHOOK_URL="https://your-api-id.execute-api.${AWS_REGION}.amazonaws.com/webhook"
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_WEBHOOK_SECRET="your_webhook_secret"

# Run webhook setup script
cd ..
python scripts/set_telegram_webhook.py
```

### **3. Test Deployment**

1. **Send a message** to your Telegram bot
2. **Check CloudWatch logs** for any errors
3. **Verify Lambda function** is working correctly
4. **Test Bedrock integration** with Nova Lite model

### **4. Bedrock Model Configuration**

The application is configured to use **Amazon Nova Lite** in the APAC region:

```bash
# Default Bedrock model (already configured)
BEDROCK_MODEL_ID=apac.amazon.nova-lite-v1:0
BEDROCK_MULTIMODAL_MODEL_ID=apac.amazon.nova-lite-v1:0
```

**Features:**
- ✅ **APAC Region**: Optimized for Asia-Pacific users
- ✅ **Nova Lite**: Cost-effective and fast model
- ✅ **Multimodal**: Supports text and image processing
- ✅ **Healthcare Optimized**: Trained for medical conversations

## 🏗️ **Infrastructure Overview**

### **Stacks Deployed**

| Stack | Purpose | Resources |
|-------|---------|-----------|
| **DatabaseStack** | Data storage | DynamoDB tables, S3 buckets |
| **SecretsStack** | Secret management | AWS Secrets Manager |
| **SqsStack** | Message queuing | SQS queue |
| **LambdaStack** | Compute | Lambda functions, IAM roles |
| **ApiGatewayStack** | API management | API Gateway, CloudWatch logs |

### **Resources Created**

#### **DynamoDB Tables**
- `ctrl_alt_heal_{env}_user_profiles` - User profiles and preferences
- `ctrl_alt_heal_{env}_external_identities` - External identity mappings (Telegram, etc.)
- `ctrl_alt_heal_{env}_conversation_history` - Conversation history and session management
- `ctrl_alt_heal_{env}_medical_prescriptions` - Medical prescriptions and medication information
- `ctrl_alt_heal_{env}_fhir_resources` - FHIR-compliant healthcare data resources

#### **S3 Buckets**
- `ctrl_alt_heal_{env}_user_uploads` - User file uploads
- `ctrl_alt_heal_{env}_system_assets` - System assets and prompts

#### **Secrets**
- `ctrl-alt-heal/{env}/serper/api-key` - Serper API key
- `ctrl-alt-heal/{env}/telegram/bot-token` - Telegram bot token

#### **Lambda Functions**
- `Worker` - Main application logic
- `LambdaLayer` - Python dependencies

## 🔒 **Security Considerations**

### **IAM Permissions**
- Lambda functions have minimal required permissions
- Secrets are accessed via IAM roles
- S3 buckets have proper access controls

### **Network Security**
- API Gateway is public (required for Telegram webhooks)
- Lambda functions run in VPC (if configured)
- S3 buckets block public access

### **Data Protection**
- All data is encrypted at rest
- Secrets are encrypted with AWS KMS
- DynamoDB tables use AWS-managed encryption

## 🧹 **Cleanup**

### **Destroy All Resources**

```bash
# Destroy all stacks
cdk destroy --all

# Or destroy specific stacks
cdk destroy CtrlAltHealApiGatewayStack
cdk destroy CtrlAltHealLambdaStack
cdk destroy CtrlAltHealSqsStack
cdk destroy CtrlAltHealSecretsStack
cdk destroy CtrlAltHealDatabaseStack
```

### **Manual Cleanup**

If CDK destroy fails, manually delete:
1. **S3 buckets** (must be empty)
2. **DynamoDB tables**
3. **Secrets** in Secrets Manager
4. **Lambda functions**
5. **API Gateway**
6. **CloudWatch log groups**

## 🔧 **Troubleshooting**

### **Common Issues**

#### **CDK Bootstrap Required**
```bash
Error: This stack uses assets, so the toolkit stack must be deployed to the environment
```
**Solution**: Run `cdk bootstrap`

#### **Permission Denied**
```bash
Error: User: arn:aws:sts::123456789012:assumed-role/... is not authorized to perform: ...
```
**Solution**: Ensure your AWS user/role has sufficient permissions

#### **Lambda Layer Build Failed**
```bash
Error: Failed to build Lambda layer
```
**Solution**: Ensure Docker is running and try again

#### **Secrets Not Found**
```bash
Error: Secret not found
```
**Solution**: Update secrets in AWS Secrets Manager with correct values

### **Useful Commands**

```bash
# List all stacks
cdk list

# View stack details
cdk diff

# View stack outputs
cdk output

# View stack events
cdk watch

# Validate CDK app
cdk synth
```

## 📊 **Cost Optimization**

### **Estimated Monthly Costs** (ap-southeast-1)

| Service | Cost (Dev) | Cost (Prod) |
|---------|------------|-------------|
| **Lambda** | ~$5-10 | ~$20-50 |
| **DynamoDB** | ~$2-5 | ~$10-30 |
| **API Gateway** | ~$1-3 | ~$5-15 |
| **S3** | ~$1-2 | ~$5-10 |
| **Secrets Manager** | ~$1-2 | ~$1-2 |
| **CloudWatch** | ~$1-3 | ~$5-15 |
| **Total** | ~$11-25 | ~$46-122 |

### **Cost Optimization Tips**

1. **Use DynamoDB on-demand** for development
2. **Set appropriate TTL** for DynamoDB items
3. **Configure Lambda timeout** appropriately
4. **Use S3 lifecycle policies** for old files
5. **Monitor CloudWatch usage** and set alarms

## 🚀 **Production Deployment**

### **Environment-Specific Configuration**

```bash
# Production deployment
export ENVIRONMENT="prod"
export PROJECT_NAME="CtrlAltHeal"
export AWS_REGION="ap-southeast-1"

# Deploy with production settings
cdk deploy --all --context environment=prod
```

### **Production Considerations**

1. **Enable CloudTrail** for audit logging
2. **Set up monitoring** and alerting
3. **Configure backup** strategies
4. **Implement CI/CD** pipeline
5. **Set up disaster recovery** plan
6. **Configure rate limiting** on API Gateway
7. **Enable WAF** for additional security

---

## 📞 **Support**

For deployment issues:
1. Check CloudWatch logs
2. Review CDK documentation
3. Check AWS service status
4. Contact the development team

**Happy Deploying! 🎉**
