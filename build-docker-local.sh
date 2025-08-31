#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PROJECT_NAME=${PROJECT_NAME:-"cara-agents"}
ENVIRONMENT=${ENVIRONMENT:-"production"}
AWS_REGION=${AWS_REGION:-"ap-southeast-1"}

echo -e "${BLUE}🐳 Building Docker image for local testing${NC}"
echo -e "${BLUE}Project Name: ${YELLOW}${PROJECT_NAME}${NC}"
echo -e "${BLUE}Environment: ${YELLOW}${ENVIRONMENT}${NC}"
echo -e "${BLUE}Region: ${YELLOW}${AWS_REGION}${NC}"
echo ""

# Build the Docker image
echo -e "${BLUE}🔨 Building Docker image...${NC}"
docker build -f Dockerfile.fargate -t ${PROJECT_NAME}-local:latest .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image built successfully!${NC}"
    echo ""
    echo -e "${BLUE}📋 Next steps:${NC}"
    echo -e "1. Test the image locally:"
    echo -e "   ${YELLOW}docker run -p 8000:8000 ${PROJECT_NAME}-local:latest${NC}"
    echo ""
    echo -e "2. Test the health endpoint:"
    echo -e "   ${YELLOW}curl http://localhost:8000/health${NC}"
    echo ""
    echo -e "3. Test the chat endpoint:"
    echo -e "   ${YELLOW}curl -X POST http://localhost:8000/chat \\"
    echo -e "     -H \"Content-Type: application/json\" \\"
    echo -e "     -d '{\"prompt\": \"Hello, how are you?\"}'${NC}"
    echo ""
    echo -e "4. When ready, build and push to ECR:"
    echo -e "   ${YELLOW}./build-and-push-ecr.sh${NC}"
else
    echo -e "${RED}❌ Docker build failed!${NC}"
    exit 1
fi
