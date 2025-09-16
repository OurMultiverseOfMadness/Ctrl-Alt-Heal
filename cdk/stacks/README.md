# CDK Stacks

This directory contains AWS CDK stack definitions for different infrastructure components.

## Stack Definitions

### Core Infrastructure Stacks
- **`database_stack.py`** - DynamoDB tables for user data, conversations, and prescriptions
- **`secrets_stack.py`** - AWS Secrets Manager for secure credential storage
- **`fargate_stack.py`** - ECS Fargate service with auto-scaling and load balancing
- **`api_gateway_stack.py`** - API Gateway for external HTTPS access

### Additional Stacks
- **`test_stack.py`** - Test infrastructure for development and CI/CD

## Stack Architecture

### Database Stack
- **Users Table**: User profiles and authentication data
- **Conversations Table**: Chat history and session management
- **Identities Table**: External identity linking (Telegram)
- **Prescriptions Table**: Medical prescription data
- **FHIR Data Table**: FHIR-compliant healthcare records

### Secrets Stack
- **Telegram Bot Token**: Secure bot authentication
- **Serper API Key**: Search API credentials
- **Database Credentials**: Database connection strings
- **Encryption Keys**: Data encryption and decryption keys

### Fargate Stack
- **ECS Cluster**: Container orchestration
- **Fargate Service**: Application containers with auto-scaling
- **Application Load Balancer**: Traffic distribution and health checks
- **VPC Configuration**: Network isolation and security
- **IAM Roles**: Service permissions and access control

### API Gateway Stack
- **REST API**: External API endpoints
- **Webhook Integration**: Telegram webhook handling
- **CORS Configuration**: Cross-origin request handling
- **Rate Limiting**: API abuse prevention
- **SSL/TLS**: Secure HTTPS communication

## Deployment

Each stack can be deployed independently or as part of the complete infrastructure:

```bash
# Deploy all stacks
cd cdk
./deploy.sh

# Deploy specific stack
cdk deploy Cara-AgentsDatabaseStack
```

## Environment Support

All stacks support multiple environments:
- **Development**: `dev` environment for testing
- **Production**: `production` environment for live deployment

Environment-specific configurations are managed through CDK context and environment variables.
