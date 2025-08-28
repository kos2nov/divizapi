import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_iam as iam,
    Duration,
)
from constructs import Construct


class DivizApiStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create IAM role for Lambda function
        lambda_role = iam.Role(
            self, "DivizLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )

        # Add permissions for external API calls
        lambda_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret"
            ],
            resources=["*"]
        ))

        # Create Lambda layer for dependencies
        dependencies_layer = lambda_.LayerVersion(
            self, "DivizDependenciesLayer",
            code=lambda_.Code.from_asset("layer_package"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_11],
            description="DiViz API dependencies layer"
        )

        # Create Lambda function with layer
        diviz_lambda = lambda_.Function(
            self, "DivizApiFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="lambda_handler.lambda_handler",
            code=lambda_.Code.from_asset("lambda_package"),
            role=lambda_role,
            layers=[dependencies_layer],
            timeout=Duration.seconds(60),
            memory_size=1024,
            environment={
                "PYTHONPATH": "/var/task:/opt/python",
                "STAGE": "prod",
                "LOG_LEVEL": "INFO"
            }
        )

        # Create API Gateway with throttling and caching
        api = apigateway.RestApi(
            self, "DivizApi",
            rest_api_name="DiViz API Service",
            description="API Gateway for DiViz meeting efficiency review service",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"]
            ),
            deploy_options=apigateway.StageOptions(
                stage_name="prod",
                throttling_rate_limit=10,
                throttling_burst_limit=20
            )
        )

        # Create Lambda integration
        lambda_integration = apigateway.LambdaIntegration(
            diviz_lambda,
            request_templates={"application/json": '{ "statusCode": "200" }'}
        )

        # Add proxy resource to catch all requests
        proxy_resource = api.root.add_resource("{proxy+}")
        proxy_resource.add_method("ANY", lambda_integration)
        
        # Also handle root path requests
        api.root.add_method("ANY", lambda_integration)

        # Output the API Gateway URL
        cdk.CfnOutput(
            self, "ApiGatewayUrl",
            value=api.url,
            description="API Gateway endpoint URL for DiViz API"
        )

        # Output Lambda function ARN
        cdk.CfnOutput(
            self, "LambdaFunctionArn",
            value=diviz_lambda.function_arn,
            description="Lambda function ARN for DiViz API"
        )