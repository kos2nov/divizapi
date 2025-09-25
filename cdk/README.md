

# DiViz API - AWS CDK Deployment

This directory contains AWS CDK deployment descriptors for the DiViz API service.

## Architecture

- **AWS Lambda**: Runs the FastAPI application using Mangum adapter
- **API Gateway**: Provides HTTP endpoints and forwards all requests to Lambda
- **IAM Roles**: Configured for Lambda execution and external API access
- **Secrets Manager**: For storing API keys (Google Calendar, OpenAI)
- **Cognito User Pool**: For user authentication and authorization. Only Google OAuth is supported.

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
4. **uv**: Fast Python package manager (used for every Python command in this repo)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

5. **Docker** *(recommended)*: Used to produce Lambda-compatible dependencies quickly
6. **npm** *(optional)*: Enables building the `frontend/` static export during deploy

7. **Domain Name**: Top level domain name for your API Gateway and Cognito. 
8. **TLS Certificate**: ACM certificate for the custom domain (must be in the same region as API Gateway regional endpoint). Another certificate is required for Cognito domain (must be in us-east-1). You can use the same cert for the API and Cognito if it is a wildcard cert, i.e. (*.diviz.example.com)

## Required AWS IAM Permissions
**Tip**: For initial setup, consider using `AdministratorAccess` policy, then create a more restrictive policy for production.

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

### For Cognito User Pool:
- `cognito:*` (fine grained permissions are TBD)

### For API Gateway: 
- `apigateway:*` (fine grained permissions are TBD)


## Deployment

### First Time Deployment
1. Copy `.env.example` to `.env` and set the required values. Optionally, store secrets in AWS Secrets Manager.
2. Create Cognito stack. From the repository root:
```bash
cd cdk
uv run cdk deploy CognitoStack
```

3. Get the App Client ID and App Client Secret from the Cognito pool App clients screen and set them in the `.env` file.


### Quick Deploy
From the repository root:
```bash
cd cdk
./deploy.sh
```

The script performs the following:

- **Dependency install**: `uv sync --no-dev`
- **Application bundle**: Copies `diviz/`, `lambda/lambda_handler.py`, and (if present) `frontend/out`
- **Frontend export**: Runs `npm install` / `npm run build` when `frontend/` exists and `npm` is available
- **Dependency layer**: Builds `diviz-lambda-deps:py311` via Docker (or falls back to local `pip install`)
- **Bootstrap & deploy**: Runs `uv run cdk bootstrap` when necessary, then `uv run cdk deploy --require-approval never --progress events DivizApiStack`
- **Cleanup**: Removes the temporary `lambda_package/` directory

## Dependency caching (faster deploys)

The deployment pipeline now caches Python dependencies using a small Docker image:

- Dockerfile: `cdk/Dockerfile.lambda`
- Pinned requirements: `cdk/requirements.lambda.txt`

During `./deploy.sh`, we:

1. Build a Docker image based on `public.ecr.aws/lambda/python:3.11` that installs the pinned requirements into `/opt/python`.
2. Thanks to Docker layer caching, this step is instant unless `requirements.lambda.txt` changes.
3. We then extract `/opt/python` from the built image into `lambda_package/` alongside your app code.

If Docker is unavailable, the script falls back to a local `pip install -r cdk/requirements.lambda.txt --target lambda_package` (slower, and may not produce Lambda-compatible wheels on macOS/Windows). In that scenario the script continues the deployment using the locally-built wheel set.

### Updating dependencies

- To add or upgrade a runtime dependency, edit `cdk/requirements.lambda.txt` and run `./deploy.sh`.
- The cache will be invalidated only if the requirements file changes; otherwise, the last built layer is reused.
- Keep `pyproject.toml` in sync with `requirements.lambda.txt` as needed.

### Manual Deployment

1. **Install CDK dependencies** (still inside `cdk/`):
   ```bash
   uv sync --no-dev
   ```

2. **Bundle the Lambda code**:
   ```bash
   rm -rf lambda_package
   mkdir -p lambda_package
   cp -r ../diviz lambda_package/
   cp lambda/lambda_handler.py lambda_package/
   ```

   Optionally build the frontend static export:
   ```bash
   pushd ../frontend
   npm install
   npm run build
   popd
   cp -R ../frontend/out lambda_package/frontend/
   ```

3. **Install Python dependencies for Lambda**:
   - **Preferred (Docker)**
     ```bash
     docker build --platform linux/amd64 -f Dockerfile.lambda -t diviz-lambda-deps:py311 ..
     CID=$(docker create diviz-lambda-deps:py311)
     docker cp "${CID}:/opt/python/." lambda_package/
     docker rm "${CID}"
     ```
   - **Fallback (no Docker)**
     ```bash
     pip install --target lambda_package --no-cache-dir -r requirements.lambda.txt
     ```

4. **Bootstrap CDK** *(first time only)*:
   ```bash
   uv run cdk bootstrap
   ```

5. **Deploy the stack**:
   ```bash
   uv run cdk deploy --require-approval never --progress events DivizApiStack
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