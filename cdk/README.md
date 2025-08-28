# DiViz API - AWS CDK Deployment

This directory contains AWS CDK deployment descriptors for the DiViz API service.

## Architecture

- **AWS Lambda**: Runs the FastAPI application using Mangum adapter
- **API Gateway**: Provides HTTP endpoints and forwards all requests to Lambda
- **IAM Roles**: Configured for Lambda execution and external API access
- **Secrets Manager**: For storing API keys (Google Calendar, OpenAI)

## Prerequisites

1. **AWS CLI**: Configured with appropriate credentials
   ```bash
   aws configure
   ```

2. **AWS CDK CLI**: Install globally
   ```bash
   npm install -g aws-cdk
   ```

3. **Python 3.11+**: For CDK and Lambda runtime
4. **uv**: Fast Python package manager
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

## Required AWS IAM Permissions

Your AWS user/role needs the following permissions for deployment:

### For CDK Bootstrap (one-time setup):
- `s3:CreateBucket`, `s3:GetBucketLocation`, `s3:ListBucket`, `s3:GetBucketPolicy`, `s3:PutBucketPolicy`
- `iam:CreateRole`, `iam:AttachRolePolicy`, `iam:PassRole`, `iam:GetRole`
- `ssm:PutParameter`, `ssm:GetParameter`
- `cloudformation:CreateStack`, `cloudformation:UpdateStack`, `cloudformation:DescribeStacks`
- `ecr:CreateRepository` (if using container images)

### For Lambda Deployment:
- `lambda:CreateFunction`, `lambda:UpdateFunctionCode`, `lambda:UpdateFunctionConfiguration`, `lambda:GetFunction`
- `apigateway:CreateRestApi`, `apigateway:CreateResource`, `apigateway:CreateMethod`, `apigateway:CreateDeployment`
- `iam:CreateRole`, `iam:AttachRolePolicy`, `iam:PassRole`, `iam:GetRole`
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`
- `cloudformation:CreateStack`, `cloudformation:UpdateStack`, `cloudformation:DescribeStacks`

**Tip**: For initial setup, consider using `AdministratorAccess` policy, then create a more restrictive policy for production.

## Deployment

### Quick Deploy
```bash
cd cdk
./deploy.sh
```


### Manual Deployment

1. **Install CDK dependencies**:
   ```bash
   uv sync
   ```

2. **Bootstrap CDK** (first time only):
   ```bash
   cdk bootstrap
   ```

3. **Prepare Lambda package**:
   ```bash
   # Create lambda_package directory with your app code and dependencies
   mkdir -p lambda_package_temp
   cp -r ../diviz lambda_package_temp/
   cp lambda_package/lambda_handler.py lambda_package_temp/
   cp lambda_package/pyproject.toml lambda_package_temp/
   cd lambda_package_temp
   uv sync --no-dev
   uv export --no-hashes --format requirements-txt | uv pip install -r /dev/stdin --target .
   cd ..
   mv lambda_package_temp lambda_package
   ```

4. **Deploy the stack**:
   ```bash
   cdk deploy
   ```

## Configuration

### Environment Variables
Set these in your Lambda function or use AWS Secrets Manager:

- `GOOGLE_CALENDAR_API_KEY`: Google Calendar API credentials
- `OPENAI_API_KEY`: OpenAI API key
- `STAGE`: Environment stage (prod, dev, etc.)

### Secrets Manager
The Lambda function has permissions to read from AWS Secrets Manager. Store sensitive API keys there:

```bash
# Store Google Calendar credentials
aws secretsmanager create-secret \
  --name "diviz/google-calendar-credentials" \
  --secret-string '{"api_key":"your-google-api-key"}'

# Store OpenAI API key
aws secretsmanager create-secret \
  --name "diviz/openai-api-key" \
  --secret-string '{"api_key":"your-openai-api-key"}'
```

## API Endpoints

Once deployed, your API will be available at the API Gateway URL with these endpoints:

- `GET /`: Root endpoint with service information
- `POST /users`: Create user
- `GET /review/gmeet/{google_meet}`: Get meeting review

## Monitoring

- **CloudWatch Logs**: Lambda function logs
- **API Gateway Logs**: Request/response logs
- **X-Ray Tracing**: Distributed tracing (if enabled)

## Cost Optimization

- Lambda is configured with 512MB memory and 30s timeout
- API Gateway uses regional endpoints
- No VPC configuration to avoid NAT Gateway costs

## Cleanup

To remove all AWS resources:

```bash
cdk destroy
```