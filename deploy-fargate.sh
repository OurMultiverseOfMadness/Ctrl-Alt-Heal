#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT=${ENVIRONMENT:-"production"}
PROJECT_NAME=${PROJECT_NAME:-"Cara-Agents"}
AWS_REGION=${AWS_REGION:-"ap-southeast-1"}
AWS_PROFILE=${AWS_PROFILE:-""}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --profile)
            AWS_PROFILE="$2"
            shift 2
            ;;
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --region)
            AWS_REGION="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --profile PROFILE     AWS profile to use"
            echo "  --environment ENV     Environment (default: production)"
            echo "  --region REGION       AWS region (default: ap-southeast-1)"
            echo "  --help               Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Activate virtual environment if it exists
if [[ -f "venv/bin/activate" ]]; then
    echo -e "${BLUE}🐍 Activating virtual environment...${NC}"
    source venv/bin/activate
elif [[ -f ".venv/bin/activate" ]]; then
    echo -e "${BLUE}🐍 Activating virtual environment...${NC}"
    source .venv/bin/activate
else
    echo -e "${YELLOW}⚠️  No virtual environment found. Using system Python.${NC}"
fi

echo -e "${BLUE}🚀 Deploying Cara-Agents to AWS Fargate${NC}"
echo -e "${BLUE}Environment: ${YELLOW}${ENVIRONMENT}${NC}"
echo -e "${BLUE}Project Name: ${YELLOW}${PROJECT_NAME}${NC}"
echo -e "${BLUE}AWS Region: ${YELLOW}${AWS_REGION}${NC}"
if [[ -n "$AWS_PROFILE" ]]; then
    echo -e "${BLUE}AWS Profile: ${YELLOW}${AWS_PROFILE}${NC}"
fi
echo ""

# Build AWS CLI profile argument
AWS_PROFILE_ARG=""
if [[ -n "$AWS_PROFILE" ]]; then
    AWS_PROFILE_ARG="--profile $AWS_PROFILE"
fi

# Check if AWS CLI is configured
if ! aws sts get-caller-identity $AWS_PROFILE_ARG > /dev/null 2>&1; then
    echo -e "${RED}❌ AWS CLI not configured for profile '${AWS_PROFILE:-default}'.${NC}"

    if [[ -n "$AWS_PROFILE" ]]; then
        echo -e "${YELLOW}For AWS SSO profiles, please ensure:${NC}"
        echo -e "1. Your SSO profile is configured in ~/.aws/config"
        echo -e "2. You have an active SSO session: ${YELLOW}aws sso login --profile $AWS_PROFILE${NC}"
        echo -e "3. Or run: ${YELLOW}aws configure sso --profile $AWS_PROFILE${NC}"
    else
        echo -e "${YELLOW}Please run one of:${NC}"
        echo -e "  - ${YELLOW}aws configure${NC} (for access keys)"
        echo -e "  - ${YELLOW}aws configure sso${NC} (for SSO)"
    fi
    exit 1
fi

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity $AWS_PROFILE_ARG --query Account --output text)
if [[ $? -ne 0 ]]; then
    echo -e "${RED}❌ Failed to get AWS account ID.${NC}"
    if [[ -n "$AWS_PROFILE" ]]; then
        echo -e "${YELLOW}Your SSO session may have expired. Try:${NC}"
        echo -e "  ${YELLOW}aws sso login --profile $AWS_PROFILE${NC}"
    fi
    exit 1
fi

echo -e "${GREEN}✅ AWS Account ID: ${YELLOW}${AWS_ACCOUNT_ID}${NC}"

# Set environment variables for CDK
export CDK_DEFAULT_ACCOUNT=$AWS_ACCOUNT_ID
export CDK_DEFAULT_REGION=$AWS_REGION
export AWS_PROFILE=$AWS_PROFILE
export ENVIRONMENT=$ENVIRONMENT
export PROJECT_NAME=$PROJECT_NAME

echo -e "${BLUE}🔑 Using AWS SSO profile credentials...${NC}"
if [[ -n "$AWS_PROFILE" ]]; then
    # For SSO profiles, we use the profile directly without getting session tokens
    echo -e "${GREEN}✅ Using SSO profile: $AWS_PROFILE${NC}"
    # Set AWS_PROFILE for CDK to use
    export AWS_PROFILE=$AWS_PROFILE
else
    echo -e "${YELLOW}⚠️  No AWS profile specified, using default credentials${NC}"
fi

echo -e "${BLUE}🔧 CDK Environment Variables:${NC}"
echo -e "  CDK_DEFAULT_ACCOUNT: ${YELLOW}${CDK_DEFAULT_ACCOUNT}${NC}"
echo -e "  CDK_DEFAULT_REGION: ${YELLOW}${CDK_DEFAULT_REGION}${NC}"
echo -e "  AWS_PROFILE: ${YELLOW}${AWS_PROFILE}${NC}"
echo ""

# Install Python dependencies
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
pip install -r requirements-fargate.txt

# Install Node.js dependencies
echo -e "${BLUE}📦 Installing Node.js dependencies...${NC}"
cd cdk
npm install

# Bootstrap CDK if needed
echo -e "${BLUE}🔧 Bootstrapping CDK...${NC}"
npx cdk bootstrap $AWS_PROFILE_ARG

# Deploy stacks first to create ECR repository
echo -e "${BLUE}🚀 Deploying CDK stacks...${NC}"
npx cdk deploy --all $AWS_PROFILE_ARG --require-approval never

echo -e "${GREEN}✅ CDK stacks deployed successfully!${NC}"

# Go back to root directory
cd ..

# Get AWS account ID for unique ECR repository naming
echo -e "${BLUE}🔍 Getting AWS account ID...${NC}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text $AWS_PROFILE_ARG)
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to get AWS account ID!${NC}"
    exit 1
fi
echo -e "${GREEN}📋 Using AWS Account ID: $AWS_ACCOUNT_ID${NC}"

# Build and push Docker image to ECR
echo -e "${BLUE}🐳 Building and pushing Docker image to ECR...${NC}"
PROJECT_NAME_LOWERCASE="cara-agents-${AWS_ACCOUNT_ID}" ./build-and-push-ecr.sh --profile "$AWS_PROFILE" --environment "$ENVIRONMENT" --region "$AWS_REGION"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Docker build and push failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker image pushed to ECR successfully!${NC}"

# Force new ECS deployment to use the latest image
echo -e "${BLUE}🔄 Forcing new ECS deployment to use latest image...${NC}"

# Get the ECS service name from CloudFormation outputs
ECS_SERVICE_NAME=$(aws cloudformation describe-stacks \
    --stack-name "${PROJECT_NAME}FargateStack" \
    --query 'Stacks[0].Outputs[?OutputKey==`ECSServiceName`].OutputValue' \
    --output text \
    $AWS_PROFILE_ARG)

ECS_CLUSTER_NAME=$(aws cloudformation describe-stacks \
    --stack-name "${PROJECT_NAME}FargateStack" \
    --query 'Stacks[0].Outputs[?OutputKey==`ECSClusterName`].OutputValue' \
    --output text \
    $AWS_PROFILE_ARG)

if [[ -n "$ECS_SERVICE_NAME" && -n "$ECS_CLUSTER_NAME" ]]; then
    echo -e "${BLUE}📋 ECS Cluster: ${YELLOW}${ECS_CLUSTER_NAME}${NC}"
    echo -e "${BLUE}📋 ECS Service: ${YELLOW}${ECS_SERVICE_NAME}${NC}"

    # Force new deployment
    aws ecs update-service \
        --cluster "$ECS_CLUSTER_NAME" \
        --service "$ECS_SERVICE_NAME" \
        --force-new-deployment \
        $AWS_PROFILE_ARG

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ ECS deployment initiated successfully!${NC}"
        echo -e "${BLUE}⏳ Waiting for deployment to complete...${NC}"

        # Wait for deployment to complete
        aws ecs wait services-stable \
            --cluster "$ECS_CLUSTER_NAME" \
            --services "$ECS_SERVICE_NAME" \
            $AWS_PROFILE_ARG

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ ECS deployment completed successfully!${NC}"
        else
            echo -e "${YELLOW}⚠️  ECS deployment may still be in progress. Check AWS Console for status.${NC}"
        fi
    else
        echo -e "${RED}❌ Failed to initiate ECS deployment!${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  Could not retrieve ECS service information. Manual deployment may be required.${NC}"
fi

echo ""

# Get the webhook URL from CloudFormation outputs
echo -e "${BLUE}🔗 Getting API Gateway webhook URL...${NC}"
WEBHOOK_URL=$(aws cloudformation describe-stacks \
    --stack-name "${PROJECT_NAME}ApiGatewayStack" \
    --query 'Stacks[0].Outputs[?OutputKey==`WebhookURL`].OutputValue' \
    --output text \
    $AWS_PROFILE_ARG)

API_GATEWAY_URL=$(aws cloudformation describe-stacks \
    --stack-name "${PROJECT_NAME}ApiGatewayStack" \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayURL`].OutputValue' \
    --output text \
    $AWS_PROFILE_ARG)

ALB_URL=$(aws cloudformation describe-stacks \
    --stack-name "${PROJECT_NAME}FargateStack" \
    --query 'Stacks[0].Outputs[?OutputKey==`ALBURL`].OutputValue' \
    --output text \
    $AWS_PROFILE_ARG)

if [[ -n "$WEBHOOK_URL" ]]; then
    echo -e "${GREEN}🎯 API Gateway Webhook URL (HTTPS):${NC}"
    echo -e "${YELLOW}${WEBHOOK_URL}${NC}"
    echo ""
    echo -e "${GREEN}🌐 API Gateway Base URL (HTTPS):${NC}"
    echo -e "${YELLOW}${API_GATEWAY_URL}${NC}"
    echo ""
    echo -e "${GREEN}🌐 Application Load Balancer URL (HTTP):${NC}"
    echo -e "${YELLOW}${ALB_URL}${NC}"
    echo ""
    echo -e "${BLUE}📋 Next steps:${NC}"
    echo -e "1. Update secrets in AWS Secrets Manager:"
    echo -e "   - ctrl-alt-heal/${ENVIRONMENT}/serper/api-key"
    echo -e "   - ctrl-alt-heal/${ENVIRONMENT}/telegram/bot-token"
    echo ""
    echo -e "2. Set Telegram webhook using the HTTPS URL above:"
    echo -e "   curl -X POST \"https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook\" \\"
    echo -e "     -H \"Content-Type: application/json\" \\"
    echo -e "     -d '{\"url\": \"${WEBHOOK_URL}\"}'"
    echo ""
    echo -e "3. Test the health endpoint:"
    echo -e "   ${YELLOW}curl ${API_GATEWAY_URL}health${NC}"
    echo ""
    echo -e "4. Test the chat endpoint:"
    echo -e "   ${YELLOW}curl -X POST ${API_GATEWAY_URL}chat \\"
    echo -e "     -H \"Content-Type: application/json\" \\"
    echo -e "     -d '{\"prompt\": \"Hello, how are you?\"}'${NC}"
    echo ""
    echo -e "5. Test the deployment by sending a message to your Telegram bot"
    echo ""
    echo -e "${GREEN}✅ Benefits of this setup:${NC}"
    echo -e "  • HTTPS endpoint (secure for production)"
    echo -e "  • Built-in rate limiting and throttling"
    echo -e "  • Request/response logging"
    echo -e "  • Easy integration with other AWS services"
else
    echo -e "${RED}❌ Could not retrieve webhook URL from CloudFormation outputs${NC}"
fi
