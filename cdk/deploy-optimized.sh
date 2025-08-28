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

# Create optimized Lambda layer (dependencies only)
echo "📦 Creating optimized Lambda layer..."
rm -rf layer_package
mkdir -p layer_package/python

# Use Docker for Lambda-compatible builds if available
if command -v docker &> /dev/null && docker info &> /dev/null; then
    echo "🐳 Using Docker for Lambda-compatible layer build..."
    
    cat > layer_requirements.txt << EOF
fastapi==0.115.6
mangum==0.19.0
pydantic==2.11.7
google-auth==2.40.3
google-auth-oauthlib==1.2.2
google-auth-httplib2==0.2.0
google-api-python-client==2.179.0
openai==1.102.0
EOF
    
    docker run --rm \
        -v $(pwd):/workspace \
        -w /workspace \
        --platform linux/x86_64 \
        --entrypoint="" \
        public.ecr.aws/lambda/python:3.11 \
        /bin/bash -c "
            pip install --target layer_package/python -r layer_requirements.txt --no-cache-dir && \
            find layer_package/python -name '*.pyc' -delete && \
            find layer_package/python -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true && \
            find layer_package/python -name '*.dist-info' -exec rm -rf {} + 2>/dev/null || true
        "
    
    rm layer_requirements.txt
else
    echo "⚠️  Docker not available, using local pip..."
    pip install --target layer_package/python --no-cache-dir \
        "fastapi==0.115.6" \
        "mangum==0.19.0" \
        "pydantic==2.11.7" \
        "google-auth==2.40.3" \
        "google-auth-oauthlib==1.2.2" \
        "google-auth-httplib2==0.2.0" \
        "google-api-python-client==2.179.0" \
        "openai==1.102.0"
fi

# Create minimal Lambda function package (app code only)
echo "📦 Creating minimal Lambda function package..."
rm -rf lambda_package
mkdir -p lambda_package

# Copy only essential application files
cp -r ../diviz lambda_package/
cat > lambda_package/lambda_handler.py << 'EOF'
import json
import os
from mangum import Mangum
from diviz.main import app

# Create Mangum adapter for AWS Lambda
handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    """AWS Lambda entry point"""
    return handler(event, context)
EOF

# Remove unnecessary files to reduce package size
find lambda_package -name "*.pyc" -delete
find lambda_package -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find lambda_package -name "*.pytest_cache" -exec rm -rf {} + 2>/dev/null || true

# Show package sizes
echo "📊 Package sizes:"
echo "  Layer: $(du -sh layer_package | cut -f1)"
echo "  Function: $(du -sh lambda_package | cut -f1)"

# Bootstrap CDK if needed
echo "🔧 Checking CDK bootstrap..."
if ! aws cloudformation describe-stacks --stack-name CDKToolkit &>/dev/null; then
    echo "Bootstrapping CDK..."
    uv run cdk bootstrap
fi

# Deploy with optimizations
echo "🚀 Deploying stack..."
uv run cdk deploy --require-approval never --progress events

# Clean up
echo "🧹 Cleaning up..."
rm -rf lambda_package layer_package

echo "✅ Optimized deployment completed!"
echo "📋 Check CloudFormation outputs for your API Gateway URL"