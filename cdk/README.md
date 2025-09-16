# Infrastructure as Code (CDK)

This directory contains AWS CDK infrastructure definitions for deploying Ctrl-Alt-Heal to AWS.

## Structure

- **`stacks/`** - CDK stack definitions for different AWS services
- **`app.py`** - Main CDK application entry point
- **`app_fargate_only.py`** - Fargate-only deployment configuration
- **`deploy.sh`** - Deployment script
- **`cdk.json`** - CDK configuration file

## CDK Stacks

### Core Infrastructure
- **`database_stack.py`** - DynamoDB tables for user data, conversations, and prescriptions
- **`secrets_stack.py`** - AWS Secrets Manager for secure credential storage
- **`fargate_stack.py`** - ECS Fargate service for the application
- **`api_gateway_stack.py`** - API Gateway for external access

### Additional Stacks
- **`test_stack.py`** - Test infrastructure for development

## Key Features

### Scalable Architecture
- **Fargate Service**: Containerized application with auto-scaling
- **Application Load Balancer**: High availability and load distribution
- **API Gateway**: Secure external API access
- **DynamoDB**: NoSQL database with auto-scaling

### Security
- **VPC**: Isolated network environment
- **IAM Roles**: Least privilege access control
- **Secrets Manager**: Secure credential management
- **Encryption**: Data encryption at rest and in transit

### Monitoring
- **CloudWatch**: Application and infrastructure monitoring
- **Health Checks**: Automated health monitoring
- **Logging**: Centralized logging and debugging

## Deployment

```bash
# Deploy all stacks
cd cdk
./deploy.sh

# Deploy specific environment
export ENVIRONMENT=production
./deploy.sh
```

## Configuration

The deployment supports multiple environments:
- **Development**: `dev` environment for testing
- **Production**: `production` environment for live deployment

All configurations are environment-specific with no hardcoded values.
