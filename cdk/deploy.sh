#!/bin/bash

# Optimized AWS CDK deployment script for DiViz API
# Focuses on minimal package sizes and faster deployments

set -e

echo "🚀 Starting optimized DiViz API deployment to AWS..."

# Check prerequisites
for cmd in uv cdk aws; do
    if ! command -v $cmd &> /dev/null; then
        echo "❌ $cmd is not installed. Please install it first."
        exit 1
    fi
done

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI is not configured. Please run 'aws configure' first."
    exit 1
fi

# Install CDK dependencies
echo "📦 Installing CDK dependencies..."
uv sync --no-dev

# Create Lambda function package with dependencies bundled (no separate layer)
echo "📦 Creating Lambda function package (code + dependencies)..."
rm -rf lambda_package
mkdir -p lambda_package

# Copy application code
cp -r ../diviz lambda_package/

# Include frontend static export if available; build it if possible
if [ -d "../frontend" ]; then
  echo " Building frontend (Next.js static export)..."
  if command -v npm >/dev/null 2>&1; then
    pushd ../frontend >/dev/null
    if [ -f package-lock.json ]; then
      npm ci || npm install
    else
      npm install
    fi
    npm run build || {
      echo "⚠️  Frontend build failed; proceeding without static UI";
    }
    popd >/dev/null
  else
    echo "⚠️  npm not found; skipping frontend build"
  fi
  if [ -d "../frontend/out" ]; then
    mkdir -p lambda_package/frontend
    cp -R ../frontend/out lambda_package/frontend/
    echo " Included frontend static export at lambda_package/frontend/out"
  else
    echo "⚠️  No frontend/out found; UI will not be served"
  fi
fi

# Build dependencies into the package using Docker with layer caching
if command -v docker &> /dev/null && docker info &> /dev/null; then
    echo "🐳 Building dependency image (cached)..."
    export DOCKER_BUILDKIT=1
    IMAGE_NAME="diviz-lambda-deps:py311"
    DOCKER_PLATFORM="linux/amd64"

    # Build the image using pinned requirements; will be cached if unchanged
    docker build \
        --platform ${DOCKER_PLATFORM} \
        -f ../cdk/Dockerfile.lambda \
        -t ${IMAGE_NAME} \
        ..

    echo "📦 Extracting installed dependencies from image..."
    CID=$(docker create ${IMAGE_NAME})
    # Copy the contents of /opt/python (site-packages) into the package root
    docker cp "${CID}:/opt/python/." lambda_package/
    docker rm "${CID}" >/dev/null
else
    echo "⚠️  Docker not available, building dependencies locally (may not be Lambda-compatible)"
    pip install --target lambda_package --no-cache-dir -r cdk/requirements.lambda.txt
fi

# Include explicit Lambda handler from repository
cp lambda/lambda_handler.py lambda_package/lambda_handler.py

# Clean unnecessary caches
find lambda_package -name "*.pyc" -delete
find lambda_package -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Show package size
echo "📊 Package size: $(du -sh lambda_package | cut -f1)"

# Bootstrap CDK if needed
echo "🔧 Checking CDK bootstrap..."
if ! aws cloudformation describe-stacks --stack-name CDKToolkit &>/dev/null; then
    echo "Bootstrapping CDK..."
    uv run cdk bootstrap
fi

# Deploy with optimizations
echo "🚀 Deploying stack..."
uv run cdk deploy --require-approval never --progress events DivizApiStack

# Clean up
echo "🧹 Cleaning up..."
rm -rf lambda_package 

echo "✅ Optimized deployment completed!"
echo "📋 Check CloudFormation outputs for your API Gateway URL"