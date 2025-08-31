# Ctrl-Alt-Heal Fargate Deployment

## Overview

This document describes the Fargate deployment of Ctrl-Alt-Heal, which replaces the Lambda-based architecture to eliminate telemetry compatibility issues and enable the use of the latest strands-agents version.

## Architecture Changes

### From Lambda to Fargate

**Previous (Lambda):**
- ❌ Lambda functions with Python 3.11 runtime
- ❌ Lambda layers with dependency packaging
- ❌ SQS message queuing
- ❌ API Gateway routing
- ❌ Telemetry compatibility issues
- ❌ Limited to strands-agents 1.4.0

**New (Fargate):**
- ✅ FastAPI application running on Fargate
- ✅ Python 3.12 with latest dependencies
- ✅ Direct HTTP webhook handling
- ✅ Application Load Balancer
- ✅ No telemetry restrictions
- ✅ Latest strands-agents (>=1.6.0)
- ✅ Auto-scaling based on CPU/Memory

## Architecture Components

### 1. FastAPI Application (`src/ctrl_alt_heal/fargate_app.py`)
- **Webhook Endpoint**: `/webhook` - Handles Telegram messages
- **Health Check**: `/health` - For Fargate health monitoring
- **Async Processing**: Non-blocking message handling
- **Direct Tool Execution**: No dual registration system

### 2. Fargate Service
- **Container**: Python 3.12 with all dependencies
- **Memory**: 2GB (configurable)
- **CPU**: 1 vCPU (configurable)
- **Auto-scaling**: 1-3 instances based on utilization
- **Health Checks**: HTTP health endpoint monitoring

### 3. Application Load Balancer
- **Public Access**: Internet-facing ALB
- **Health Checks**: Monitors container health
- **SSL Termination**: HTTPS support (can be added)
- **Target Groups**: Routes traffic to Fargate tasks

### 4. Infrastructure (Unchanged)
- **DynamoDB Tables**: User data, conversations, prescriptions
- **S3 Buckets**: File storage, assets
- **Secrets Manager**: API keys, bot tokens
- **VPC**: Network isolation

## Benefits

### 1. **No Telemetry Issues**
- Full Python environment without Lambda restrictions
- Latest OpenTelemetry libraries work without issues
- No runtime compatibility problems

### 2. **Latest Dependencies**
- strands-agents >=1.6.0 (latest features)
- Python 3.12 (latest runtime)
- All dependencies at latest versions

### 3. **Better Performance**
- Persistent container environment
- No cold starts
- Better memory management
- Faster tool execution

### 4. **Simplified Architecture**
- Single application instead of multiple Lambda functions
- Direct HTTP handling instead of SQS queuing
- No API Gateway complexity
- Easier debugging and monitoring

## Deployment

### Prerequisites

1. **AWS CLI configured** with appropriate permissions
2. **Docker** installed (for local testing)
3. **Node.js** and **npm** (for CDK)
4. **Python 3.12** and virtual environment

### Quick Deployment

```bash
# Deploy to Fargate
./deploy-fargate.sh --profile mom

# Or with custom environment
./deploy-fargate.sh --profile mom --environment production
```

### Testing After Deployment

Once deployed, you can test your agent using the API Gateway URL:

**Current Deployment URLs:**
- **Base URL**: `https://x2ungeyw8c.execute-api.ap-southeast-1.amazonaws.com/production/`
- **Webhook URL**: `https://x2ungeyw8c.execute-api.ap-southeast-1.amazonaws.com/production/webhook`
- **Health Check**: `https://x2ungeyw8c.execute-api.ap-southeast-1.amazonaws.com/production/health`

```bash
# Get the service URL from the CDK output
SERVICE_URL=$(aws cloudformation describe-stacks \
  --stack-name "CtrlAltHealFargateStack" \
  --query "Stacks[0].Outputs[?OutputKey=='WebhookURL'].OutputValue" \
  --output text \
  --profile mom)

# Test the chat endpoint
curl -X POST \
  http://$SERVICE_URL/chat \
  -H 'Content-Type: application/json' \
  -d '{"prompt": "Hello, how can you help me with my medications?"}'

# Test the streaming endpoint
curl -X POST \
  http://$SERVICE_URL/chat-streaming \
  -H 'Content-Type: application/json' \
  -d '{"prompt": "What medications do I have?"}'
```

### Manual Deployment Steps

1. **Install Dependencies**
   ```bash
   pip install -r requirements-fargate.txt
   cd cdk && npm install
   ```

2. **Deploy Infrastructure**
   ```bash
   cd cdk
   npx cdk deploy --all --profile mom
   ```

3. **Set Telegram Webhook**
   ```bash
   # Get webhook URL from CloudFormation outputs
   WEBHOOK_URL=$(aws cloudformation describe-stacks \
     --stack-name "CtrlAltHealFargateStack" \
     --query 'Stacks[0].Outputs[?OutputKey==`WebhookURL`].OutputValue' \
     --output text \
     --profile mom)

   # Set webhook
   curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d "{\"url\": \"$WEBHOOK_URL\"}"
   ```

## Configuration

### Environment Variables

The Fargate service uses these environment variables:

```bash
# Database Tables
USERS_TABLE_NAME=ctrl-alt-heal-dev_user_profiles
IDENTITIES_TABLE_NAME=ctrl-alt-heal-dev_external_identities
CONVERSATIONS_TABLE_NAME=ctrl-alt-heal-dev_conversation_history
PRESCRIPTIONS_TABLE_NAME=ctrl-alt-heal-dev_medical_prescriptions
FHIR_DATA_TABLE_NAME=ctrl-alt-heal-dev_fhir_resources

# S3 Buckets
UPLOADS_BUCKET_NAME=ctrl-alt-heal-dev-user-uploads
ASSETS_BUCKET_NAME=ctrl-alt-heal-dev-system-assets

# Secrets
SERPER_SECRET_NAME=ctrl-alt-heal/dev/serper/api-key
TELEGRAM_SECRET_NAME=ctrl-alt-heal/dev/telegram/bot-token

# Application
ENVIRONMENT=dev
AGENT_VERSION=4.0
```

### Scaling Configuration

```python
# Auto-scaling settings
min_capacity=1
max_capacity=3
target_cpu_utilization=70%
target_memory_utilization=70%
```

## Monitoring

### CloudWatch Logs
- **Log Group**: `/aws/ecs/ctrl-alt-heal`
- **Log Stream**: Container-specific streams
- **Retention**: 7 days

### Metrics
- **CPU Utilization**: Auto-scaling trigger
- **Memory Utilization**: Auto-scaling trigger
- **Request Count**: ALB metrics
- **Response Time**: ALB metrics

### Health Checks
- **Endpoint**: `/health`
- **Interval**: 30 seconds
- **Timeout**: 5 seconds
- **Retries**: 3
- **Start Period**: 60 seconds

## Local Development

### Running Locally

```bash
# Install dependencies
pip install -r requirements-fargate.txt

# Run FastAPI app
python -m uvicorn src.ctrl_alt_heal.fargate_app:app --host 0.0.0.0 --port 8000
```

### Docker Testing

```bash
# Build image
docker build -f Dockerfile.fargate -t ctrl-alt-heal-fargate .

# Run container
docker run -p 8000:8000 \
  -e USERS_TABLE_NAME=your-table \
  -e TELEGRAM_SECRET_NAME=your-secret \
  ctrl-alt-heal-fargate
```

## Troubleshooting

### Common Issues

1. **Container Health Check Failing**
   - Check `/health` endpoint returns 200
   - Verify container can start within 60 seconds
   - Check CloudWatch logs for startup errors

2. **Webhook Not Receiving Messages**
   - Verify webhook URL is correctly set
   - Check ALB security groups allow HTTP traffic
   - Verify Fargate service is running

3. **High CPU/Memory Usage**
   - Monitor CloudWatch metrics
   - Consider increasing task resources
   - Check for memory leaks in application

4. **Secrets Access Issues**
   - Verify task role has Secrets Manager permissions
   - Check secret names match environment variables
   - Ensure secrets exist in correct region

### Logs and Debugging

```bash
# View Fargate logs
aws logs tail /aws/ecs/ctrl-alt-heal --follow --profile mom

# Check service status
aws ecs describe-services \
  --cluster CtrlAltHealCluster \
  --services CtrlAltHealFargateService \
  --profile mom

# View task logs
aws logs describe-log-streams \
  --log-group-name /aws/ecs/ctrl-alt-heal \
  --profile mom
```

## Migration from Lambda

### Data Migration
- **No data migration required** - same DynamoDB tables
- **Same S3 buckets** - files remain accessible
- **Same secrets** - no changes needed

### Webhook Migration
1. Deploy Fargate service
2. Update Telegram webhook URL
3. Test functionality
4. Remove Lambda deployment (optional)

### Rollback Plan
1. Keep Lambda deployment running initially
2. Test Fargate deployment thoroughly
3. Switch webhook URL back to Lambda if needed
4. Remove Fargate deployment if issues arise

## Cost Comparison

### Lambda (Previous)
- Pay per request + execution time
- Cold start overhead
- Limited memory (10GB max)
- SQS costs for queuing

### Fargate (Current)
- Pay for running containers
- No cold starts
- Higher memory limits
- ALB costs for load balancing
- More predictable pricing for high traffic

## Security

### Network Security
- **VPC**: Private subnets for Fargate tasks
- **Security Groups**: Restrict traffic to ALB only
- **NAT Gateway**: Outbound internet access

### IAM Permissions
- **Task Role**: Minimal permissions for AWS services
- **Execution Role**: ECS task execution permissions
- **Principle of Least Privilege**: Only required permissions

### Secrets Management
- **AWS Secrets Manager**: Secure storage of API keys
- **No hardcoded secrets**: All secrets via environment variables
- **Encryption at rest**: All secrets encrypted

## Future Enhancements

### Planned Improvements
1. **HTTPS Support**: SSL termination at ALB
2. **Custom Domain**: Route53 integration
3. **Blue/Green Deployment**: Zero-downtime updates
4. **Enhanced Monitoring**: Custom CloudWatch dashboards
5. **Multi-region**: Global deployment for latency

### Potential Optimizations
1. **Container Optimization**: Multi-stage Docker builds
2. **Caching**: Redis for session storage
3. **CDN**: CloudFront for static assets
4. **Database Optimization**: Connection pooling
5. **Async Processing**: Background task queues
