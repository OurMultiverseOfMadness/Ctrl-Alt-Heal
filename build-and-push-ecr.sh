#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PROJECT_NAME=${PROJECT_NAME_LOWERCASE:-"cara-agents"}
ENVIRONMENT=${ENVIRONMENT:-"production"}
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

echo -e "${BLUE}🐳 Building and pushing Docker image to ECR${NC}"
echo -e "${BLUE}Project Name: ${YELLOW}${PROJECT_NAME}${NC}"
echo -e "${BLUE}Environment: ${YELLOW}${ENVIRONMENT}${NC}"
echo -e "${BLUE}Region: ${YELLOW}${AWS_REGION}${NC}"
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
    exit 1
fi

echo -e "${GREEN}✅ AWS Account ID: ${YELLOW}${AWS_ACCOUNT_ID}${NC}"

# Set ECR repository URI
ECR_REPO_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}"
IMAGE_TAG="latest"

echo -e "${BLUE}🔧 ECR Repository URI: ${YELLOW}${ECR_REPO_URI}${NC}"
echo -e "${BLUE}🔧 Image Tag: ${YELLOW}${IMAGE_TAG}${NC}"
echo ""

# Build the Docker image
echo -e "${BLUE}🔨 Building Docker image...${NC}"
docker build -f Dockerfile.fargate -t ${PROJECT_NAME}:${IMAGE_TAG} .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Docker build failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker image built successfully!${NC}"

# Get ECR login token
echo -e "${BLUE}🔐 Getting ECR login token...${NC}"
aws ecr get-login-password --region ${AWS_REGION} $AWS_PROFILE_ARG | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to authenticate with ECR!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ ECR authentication successful!${NC}"

# Tag the image for ECR
echo -e "${BLUE}🏷️  Tagging image for ECR...${NC}"
docker tag ${PROJECT_NAME}:${IMAGE_TAG} ${ECR_REPO_URI}:${IMAGE_TAG}

# Push the image to ECR
echo -e "${BLUE}📤 Pushing image to ECR...${NC}"
docker push ${ECR_REPO_URI}:${IMAGE_TAG}

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Image pushed to ECR successfully!${NC}"
    echo ""
    echo -e "${BLUE}📋 Image Details:${NC}"
    echo -e "  Repository: ${YELLOW}${ECR_REPO_URI}${NC}"
    echo -e "  Tag: ${YELLOW}${IMAGE_TAG}${NC}"
    echo -e "  Region: ${YELLOW}${AWS_REGION}${NC}"
    echo ""
    echo -e "${BLUE}📋 Next steps:${NC}"
    echo -e "1. Deploy the CDK stack:"
    echo -e "   ${YELLOW}./deploy-fargate.sh --profile ${AWS_PROFILE:-default}${NC}"
    echo ""
    echo -e "2. Or deploy manually:"
    echo -e "   ${YELLOW}cd cdk && npx cdk deploy --all${NC}"
else
    echo -e "${RED}❌ Failed to push image to ECR!${NC}"
    exit 1
fi
