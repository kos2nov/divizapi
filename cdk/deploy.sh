#!/bin/bash

# AWS CDK deployment script for DiViz API

set -e

echo "🚀 Starting DiViz API deployment to AWS..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install it first:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check if CDK is installed
if ! command -v cdk &> /dev/null; then
    echo "❌ AWS CDK CLI is not installed. Please install it first:"
    echo "npm install -g aws-cdk"
    exit 1
fi

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI is not configured. Please run 'aws configure' first."
    exit 1
fi

# Install CDK dependencies using uv
echo "📦 Installing CDK dependencies with uv..."
uv sync

# Prepare Lambda layer package (dependencies)
echo "📦 Preparing Lambda layer package (dependencies)..."

# Create temporary directory for layer package
rm -rf layer_package_temp
mkdir -p layer_package_temp/python

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo "Using Docker to build Lambda-compatible packages for layer..."
    
    # Create requirements.txt with current stable dependencies
    cat > layer_package_temp/requirements.txt << EOF
fastapi==0.115.6
mangum==0.19.0
pydantic==2.11.7
google-auth==2.40.3
google-auth-oauthlib==1.2.2
google-auth-httplib2==0.2.0
google-api-python-client==2.179.0
openai==1.102.0
EOF
    
    # Use Amazon Linux 2023 image to exactly match Lambda runtime
    docker run --rm \
        -v $(pwd)/layer_package_temp:/var/task \
        -w /var/task \
        --platform linux/x86_64 \
        --entrypoint="" \
        public.ecr.aws/lambda/python:3.11 \
        /bin/bash -c "
            pip install --target /var/task/python -r /var/task/requirements.txt --no-cache-dir && \
            rm /var/task/requirements.txt && \
            find /var/task/python -name '*.pyc' -delete && \
            find /var/task/python -name '__pycache__' -exec rm -rf {} + || true && \
            find /var/task/python -name '*.dist-info' -exec rm -rf {} + || true
        "
    
    echo "✅ Layer Docker build completed"
else
    echo "⚠️  Docker not available for layer, using pip with current packages..."
    cd layer_package_temp
    python3 -m pip install --target python --no-cache-dir \
        "fastapi==0.115.6" \
        "mangum==0.19.0" \
        "pydantic==2.11.7" \
        "google-auth==2.40.3" \
        "google-auth-oauthlib==1.2.2" \
        "google-auth-httplib2==0.2.0" \
        "google-api-python-client==2.179.0" \
        "openai==1.102.0"
    # Clean up to reduce size
    find python -name '*.pyc' -delete
    find python -name '__pycache__' -exec rm -rf {} + || true
    find python -name '*.dist-info' -exec rm -rf {} + || true
    cd ..
fi

# Replace layer_package with the prepared package
rm -rf layer_package
mv layer_package_temp layer_package

# Prepare Lambda function package (just application code)
echo "📦 Preparing Lambda function package (application code only)..."

# Create temporary directory for Lambda function package
rm -rf lambda_package_temp
mkdir -p lambda_package_temp

# Copy only application code (no dependencies)
cp -r ../diviz lambda_package_temp/
cp lambda_package/lambda_handler.py lambda_package_temp/

# Replace lambda_package with the prepared package
rm -rf lambda_package
mv lambda_package_temp lambda_package

# Bootstrap CDK (only needed once per account/region)
echo "🔧 Bootstrapping CDK (if needed)..."
if ! uv run cdk bootstrap; then
    echo "⚠️  CDK bootstrap failed. This might be due to insufficient permissions."
    echo "You may need the following IAM permissions:"
    echo "  - s3:CreateBucket, s3:GetBucketLocation, s3:ListBucket, s3:GetBucketPolicy, s3:PutBucketPolicy"
    echo "  - iam:CreateRole, iam:AttachRolePolicy, iam:PassRole"
    echo "  - ssm:PutParameter, ssm:GetParameter"
    echo "  - cloudformation:CreateStack, cloudformation:UpdateStack"
    echo ""
    echo "Continuing with deployment attempt..."
fi

# Deploy the stack
echo "🚀 Deploying DiViz API stack..."
if ! uv run cdk deploy --require-approval never; then
    echo "❌ Deployment failed. Common issues:"
    echo "  1. Insufficient AWS permissions"
    echo "  2. CDK bootstrap not completed"
    echo "  3. Invalid AWS credentials"
    echo ""
    echo "Required IAM permissions for Lambda deployment:"
    echo "  - lambda:CreateFunction, lambda:UpdateFunctionCode, lambda:UpdateFunctionConfiguration"
    echo "  - apigateway:CreateRestApi, apigateway:CreateResource, apigateway:CreateMethod"
    echo "  - iam:CreateRole, iam:AttachRolePolicy, iam:PassRole"
    echo "  - logs:CreateLogGroup"
    exit 1
fi

# Clean up
echo "🧹 Cleaning up temporary files..."
rm -rf lambda_package layer_package

echo "✅ Deployment completed successfully!"
echo "📋 Check the CloudFormation outputs for your API Gateway URL"