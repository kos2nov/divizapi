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

# Build dependencies into the package using Docker for Lambda compatibility
if command -v docker &> /dev/null && docker info &> /dev/null; then
    echo "🐳 Using Docker for Lambda-compatible build..."
    cat > requirements.txt << EOF
fastapi==0.115.6
mangum==0.19.0
pydantic==2.11.7
google-auth==2.40.3
google-auth-oauthlib==1.2.2
google-auth-httplib2==0.2.0
google-api-python-client==2.179.0
openai==1.102.0
httpx==0.28.1
python-jose==3.3.0
uvicorn==0.35.0
EOF
    docker run --rm \
        -v $(pwd):/workspace \
        -w /workspace \
        --platform linux/x86_64 \
        --entrypoint="" \
        public.ecr.aws/lambda/python:3.11 \
        /bin/bash -c "
            pip install --target lambda_package -r requirements.txt --no-cache-dir && \
            rm requirements.txt && \
            find lambda_package -name '*.pyc' -delete && \
            find lambda_package -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
        "
else
    echo "⚠️  Docker not available, building dependencies locally (may not be Lambda-compatible)"
    pip install --target lambda_package --no-cache-dir \
        "fastapi==0.115.6" \
        "mangum==0.19.0" \
        "pydantic==2.11.7" \
        "google-auth==2.40.3" \
        "google-auth-oauthlib==1.2.2" \
        "google-auth-httplib2==0.2.0" \
        "google-api-python-client==2.179.0" \
        "openai==1.102.0" \
        "httpx==0.28.1" \
        "python-jose==3.3.0" \
        "uvicorn==0.35.0"
fi

# Write the explicit Lambda handler
cat > lambda_package/lambda_handler.py << 'EOF'
from mangum import Mangum
from diviz.main import app
handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    return handler(event, context)
EOF

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
uv run cdk deploy --require-approval never --progress events

# Clean up
echo "🧹 Cleaning up..."
rm -rf lambda_package layer_package

echo "✅ Optimized deployment completed!"
echo "📋 Check CloudFormation outputs for your API Gateway URL"