# AWS Deployment Script for Conversational Document Assistant (PowerShell)
# This script automates the deployment process to AWS ECS

$ErrorActionPreference = "Stop"

# Configuration
$AWS_REGION = if ($env:AWS_REGION) { $env:AWS_REGION } else { "us-east-1" }
$AWS_ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text).Trim()
$ECR_BACKEND_REPO = "rag-backend"
$ECR_FRONTEND_REPO = "rag-frontend"
$CLUSTER_NAME = "rag-cluster"
$SERVICE_NAME = "rag-backend-service"

Write-Host "🚀 Starting AWS Deployment" -ForegroundColor Green
Write-Host "Region: $AWS_REGION"
Write-Host "Account ID: $AWS_ACCOUNT_ID"
Write-Host ""

# Step 1: Create ECR Repositories
Write-Host "Step 1: Creating ECR repositories..." -ForegroundColor Yellow
try {
    aws ecr describe-repositories --repository-names $ECR_BACKEND_REPO --region $AWS_REGION 2>$null
} catch {
    aws ecr create-repository --repository-name $ECR_BACKEND_REPO --region $AWS_REGION
}

try {
    aws ecr describe-repositories --repository-names $ECR_FRONTEND_REPO --region $AWS_REGION 2>$null
} catch {
    aws ecr create-repository --repository-name $ECR_FRONTEND_REPO --region $AWS_REGION
}

Write-Host "✅ ECR repositories ready" -ForegroundColor Green

# Step 2: Login to ECR
Write-Host "Step 2: Logging into ECR..." -ForegroundColor Yellow
$loginCommand = aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
Write-Host "✅ Logged into ECR" -ForegroundColor Green

# Step 3: Build and Push Backend
Write-Host "Step 3: Building and pushing backend image..." -ForegroundColor Yellow
Set-Location backend
docker build -t "$ECR_BACKEND_REPO`:latest" .
docker tag "$ECR_BACKEND_REPO`:latest" "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_BACKEND_REPO`:latest"
docker push "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_BACKEND_REPO`:latest"
Set-Location ..
Write-Host "✅ Backend image pushed" -ForegroundColor Green

# Step 4: Build and Push Frontend
Write-Host "Step 4: Building and pushing frontend image..." -ForegroundColor Yellow
Set-Location frontend
$API_URL = if ($env:VITE_API_BASE) { $env:VITE_API_BASE } else { "http://localhost:8000" }
docker build --build-arg VITE_API_BASE=$API_URL -t "$ECR_FRONTEND_REPO`:latest" .
docker tag "$ECR_FRONTEND_REPO`:latest" "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_FRONTEND_REPO`:latest"
docker push "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_FRONTEND_REPO`:latest"
Set-Location ..
Write-Host "✅ Frontend image pushed" -ForegroundColor Green

# Step 5: Create ECS Cluster (if not exists)
Write-Host "Step 5: Creating ECS cluster..." -ForegroundColor Yellow
try {
    aws ecs describe-clusters --clusters $CLUSTER_NAME --region $AWS_REGION 2>$null
} catch {
    aws ecs create-cluster --cluster-name $CLUSTER_NAME --region $AWS_REGION
}
Write-Host "✅ ECS cluster ready" -ForegroundColor Green

Write-Host "✅ Deployment preparation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Create task definition using the ECR image: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_BACKEND_REPO`:latest"
Write-Host "2. Create ECS service with the task definition"
Write-Host "3. Set up Application Load Balancer"
Write-Host "4. Configure security groups"
Write-Host ""
Write-Host "See AWS_DEPLOYMENT.md for detailed instructions."


