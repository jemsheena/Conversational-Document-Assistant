#!/bin/bash

# AWS Deployment Script for Conversational Document Assistant
# This script automates the deployment process to AWS ECS

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_BACKEND_REPO="rag-backend"
ECR_FRONTEND_REPO="rag-frontend"
CLUSTER_NAME="rag-cluster"
SERVICE_NAME="rag-backend-service"

echo -e "${GREEN}🚀 Starting AWS Deployment${NC}"
echo "Region: $AWS_REGION"
echo "Account ID: $AWS_ACCOUNT_ID"
echo ""

# Step 1: Create ECR Repositories
echo -e "${YELLOW}Step 1: Creating ECR repositories...${NC}"
aws ecr describe-repositories --repository-names $ECR_BACKEND_REPO --region $AWS_REGION 2>/dev/null || \
  aws ecr create-repository --repository-name $ECR_BACKEND_REPO --region $AWS_REGION

aws ecr describe-repositories --repository-names $ECR_FRONTEND_REPO --region $AWS_REGION 2>/dev/null || \
  aws ecr create-repository --repository-name $ECR_FRONTEND_REPO --region $AWS_REGION

echo -e "${GREEN}✅ ECR repositories ready${NC}"

# Step 2: Login to ECR
echo -e "${YELLOW}Step 2: Logging into ECR...${NC}"
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
echo -e "${GREEN}✅ Logged into ECR${NC}"

# Step 3: Build and Push Backend
echo -e "${YELLOW}Step 3: Building and pushing backend image...${NC}"
cd backend
docker build -t $ECR_BACKEND_REPO:latest .
docker tag $ECR_BACKEND_REPO:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_BACKEND_REPO:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_BACKEND_REPO:latest
cd ..
echo -e "${GREEN}✅ Backend image pushed${NC}"

# Step 4: Build and Push Frontend
echo -e "${YELLOW}Step 4: Building and pushing frontend image...${NC}"
cd frontend
# Get API URL from environment or use default
API_URL="${VITE_API_BASE:-http://localhost:8000}"
docker build --build-arg VITE_API_BASE=$API_URL -t $ECR_FRONTEND_REPO:latest .
docker tag $ECR_FRONTEND_REPO:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_FRONTEND_REPO:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_FRONTEND_REPO:latest
cd ..
echo -e "${GREEN}✅ Frontend image pushed${NC}"

# Step 5: Create ECS Cluster (if not exists)
echo -e "${YELLOW}Step 5: Creating ECS cluster...${NC}"
aws ecs describe-clusters --clusters $CLUSTER_NAME --region $AWS_REGION 2>/dev/null || \
  aws ecs create-cluster --cluster-name $CLUSTER_NAME --region $AWS_REGION
echo -e "${GREEN}✅ ECS cluster ready${NC}"

echo -e "${GREEN}✅ Deployment preparation complete!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Create task definition using the ECR image: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_BACKEND_REPO:latest"
echo "2. Create ECS service with the task definition"
echo "3. Set up Application Load Balancer"
echo "4. Configure security groups"
echo ""
echo "See AWS_DEPLOYMENT.md for detailed instructions."


