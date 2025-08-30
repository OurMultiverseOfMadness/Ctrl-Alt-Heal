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
            echo "  --environment ENV     Environment (default: dev)"
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
if [[ -f "../venv/bin/activate" ]]; then
    echo -e "${BLUE}🐍 Activating virtual environment...${NC}"
    source ../venv/bin/activate
elif [[ -f "venv/bin/activate" ]]; then
    echo -e "${BLUE}🐍 Activating virtual environment...${NC}"
    source venv/bin/activate
else
    echo -e "${YELLOW}⚠️  No virtual environment found. Using system Python.${NC}"
fi

echo -e "${BLUE}🚀 Deploying Ctrl-Alt-Heal to AWS${NC}"
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
echo -e "${BLUE}AWS Account ID: ${YELLOW}${AWS_ACCOUNT_ID}${NC}"
echo ""

# Set environment variables for CDK
export CDK_DEFAULT_ACCOUNT=$AWS_ACCOUNT_ID
export CDK_DEFAULT_REGION=$AWS_REGION
export ENVIRONMENT=$ENVIRONMENT
export PROJECT_NAME=$PROJECT_NAME

# For AWS SSO profiles, get temporary credentials for CDK
if [[ -n "$AWS_PROFILE" ]]; then
    echo -e "${BLUE}🔑 Getting temporary AWS credentials for SSO profile...${NC}"
    # Get temporary credentials from SSO profile
    TEMP_CREDS=$(aws configure export-credentials --profile $AWS_PROFILE --format env 2>/dev/null)
    if [[ $? -eq 0 ]]; then
        # Export the temporary credentials
        eval "$TEMP_CREDS"
        echo -e "${GREEN}✅ Temporary credentials obtained successfully${NC}"
    else
        echo -e "${YELLOW}⚠️  Could not get temporary credentials, using profile directly${NC}"
        export AWS_PROFILE=$AWS_PROFILE
        export AWS_DEFAULT_PROFILE=$AWS_PROFILE
    fi
else
    export AWS_PROFILE=$AWS_PROFILE
    export AWS_DEFAULT_PROFILE=$AWS_PROFILE
fi

# Debug: Show environment variables
echo -e "${BLUE}🔧 CDK Environment Variables:${NC}"
echo -e "  CDK_DEFAULT_ACCOUNT: ${YELLOW}${CDK_DEFAULT_ACCOUNT}${NC}"
echo -e "  CDK_DEFAULT_REGION: ${YELLOW}${CDK_DEFAULT_REGION}${NC}"
echo -e "  AWS_PROFILE: ${YELLOW}${AWS_PROFILE:-'not set'}${NC}"
if [[ -n "$AWS_ACCESS_KEY_ID" ]]; then
    echo -e "  AWS_ACCESS_KEY_ID: ${YELLOW}${AWS_ACCESS_KEY_ID:0:10}...${NC}"
fi
echo ""

# Check if CDK is installed
if ! command -v cdk &> /dev/null; then
    echo -e "${RED}❌ CDK CLI not found. Installing...${NC}"
    npm install -g aws-cdk
fi

# Install Python dependencies (including AWS CDK)
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
if [[ -f "../requirements.txt" ]]; then
    pip install -r ../requirements.txt
elif [[ -f "requirements-dev.txt" ]]; then
    pip install -r requirements-dev.txt
else
    echo -e "${YELLOW}⚠️  No requirements file found. Installing AWS CDK dependencies manually...${NC}"
    pip install aws-cdk-lib constructs
fi

# Verify AWS CDK is available
if ! python -c "import aws_cdk" 2>/dev/null; then
    echo -e "${RED}❌ AWS CDK not found. Installing...${NC}"
    pip install aws-cdk-lib constructs
fi

# Install Node.js dependencies
echo -e "${BLUE}📦 Installing Node.js dependencies...${NC}"
npm install

# Bootstrap CDK (only needed once per account/region)
echo -e "${BLUE}🔧 Bootstrapping CDK...${NC}"
cdk bootstrap $AWS_PROFILE_ARG

# Deploy all stacks
echo -e "${BLUE}🚀 Deploying stacks...${NC}"
cdk deploy --all --require-approval never $AWS_PROFILE_ARG

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
