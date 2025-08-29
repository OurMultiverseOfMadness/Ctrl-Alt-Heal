#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT=${ENVIRONMENT:-"dev"}
PROJECT_NAME=${PROJECT_NAME:-"CtrlAltHeal"}
AWS_REGION=${AWS_REGION:-"ap-southeast-1"}

echo -e "${BLUE}🚀 Deploying Ctrl-Alt-Heal to AWS${NC}"
echo -e "${BLUE}Environment: ${YELLOW}${ENVIRONMENT}${NC}"
echo -e "${BLUE}Project Name: ${YELLOW}${PROJECT_NAME}${NC}"
echo -e "${BLUE}AWS Region: ${YELLOW}${AWS_REGION}${NC}"
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo -e "${RED}❌ AWS CLI not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${BLUE}AWS Account ID: ${YELLOW}${AWS_ACCOUNT_ID}${NC}"
echo ""

# Set environment variables for CDK
export CDK_DEFAULT_ACCOUNT=$AWS_ACCOUNT_ID
export CDK_DEFAULT_REGION=$AWS_REGION
export ENVIRONMENT=$ENVIRONMENT
export PROJECT_NAME=$PROJECT_NAME

# Check if CDK is installed
if ! command -v cdk &> /dev/null; then
    echo -e "${RED}❌ CDK CLI not found. Installing...${NC}"
    npm install -g aws-cdk
fi

# Install dependencies
echo -e "${BLUE}📦 Installing dependencies...${NC}"
npm install

# Bootstrap CDK (only needed once per account/region)
echo -e "${BLUE}🔧 Bootstrapping CDK...${NC}"
cdk bootstrap

# Deploy all stacks
echo -e "${BLUE}🚀 Deploying stacks...${NC}"
cdk deploy --all --require-approval never

echo ""
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo -e "1. Update secrets in AWS Secrets Manager:"
echo -e "   - ${YELLOW}ctrl-alt-heal/${ENVIRONMENT}/serper/api-key${NC}"
echo -e "   - ${YELLOW}ctrl-alt-heal/${ENVIRONMENT}/telegram/bot-token${NC}"
echo ""
echo -e "2. Set Telegram webhook:"
echo -e "   - Get the API Gateway URL from the CDK output"
echo -e "   - Run: ${YELLOW}python scripts/set_telegram_webhook.py${NC}"
echo ""
echo -e "3. Test the deployment:"
echo -e "   - Send a message to your Telegram bot"
echo -e "   - Check CloudWatch logs for any errors"
