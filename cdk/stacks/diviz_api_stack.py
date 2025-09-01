import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_iam as iam,
    aws_cognito as cognito,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_route53_targets as targets,
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



        # Create Lambda function with layer
        diviz_lambda = lambda_.Function(
            self, "DivizApiFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="lambda_handler.lambda_handler",
            code=lambda_.Code.from_asset("lambda_package"),
            role=lambda_role,

            timeout=Duration.seconds(60),
            memory_size=1024,
            environment={
                "PYTHONPATH": "/var/task:/opt/python",
                "STAGE": "prod",
                "LOG_LEVEL": "INFO"
            }
        )

        # Reference existing Cognito User Pool
        user_pool = cognito.UserPool.from_user_pool_id(
            self, "DivizUserPool",
            user_pool_id="us-east-2_GSNdrKDXE"
        )

        # Create Cognito authorizer
        cognito_authorizer = apigateway.CognitoUserPoolsAuthorizer(
            self, "DivizCognitoAuthorizer",
            cognito_user_pools=[user_pool]
        )

        # Reference existing certificate for diviz.knovoselov.com
        certificate = acm.Certificate.from_certificate_arn(
            self, "DivizCertificate",
            certificate_arn="arn:aws:acm:us-east-2:110007951910:certificate/d1e6d4ca-7ccc-4dfa-ba07-d1018291da65"
        )

        # Create API Gateway with custom domain
        api = apigateway.RestApi(
            self, "DivizApi",
            rest_api_name="DiViz API Service",
            description="API Gateway for DiViz meeting efficiency review service",
            endpoint_configuration=apigateway.EndpointConfiguration(
                types=[apigateway.EndpointType.REGIONAL]
            ),
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

        # Import existing custom domain
        domain = apigateway.DomainName.from_domain_name_attributes(
            self, "DivizApiDomain",
            domain_name="diviz.knovoselov.com",
            domain_name_alias_target="d-60kuz6b2f7.execute-api.us-east-2.amazonaws.com",
            domain_name_alias_hosted_zone_id="ZOJJZC49E0EPZ"
        )

        # Note: Base path mapping already exists for this domain

        # Reference existing hosted zone for knovoselov.com
        hosted_zone = route53.HostedZone.from_lookup(
            self, "KnovoselovZone",
            domain_name="knovoselov.com"
        )

        # Create A record for diviz.knovoselov.com
        route53.ARecord(
            self, "DivizARecord",
            zone=hosted_zone,
            record_name="diviz",
            target=route53.RecordTarget.from_alias(
                targets.ApiGatewayDomain(domain)
            )
        )

        # Create Lambda integration
        lambda_integration = apigateway.LambdaIntegration(
            diviz_lambda,
            request_templates={"application/json": '{ "statusCode": "200" }'}
        )

        # Add proxy resource to catch all requests with Cognito auth
        proxy_resource = api.root.add_resource("{proxy+}")
        proxy_resource.add_method(
            "ANY", 
            lambda_integration,
            authorizer=cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # Handle root path requests without auth
        api.root.add_method("ANY", lambda_integration)

        # Output the API Gateway URLs
        cdk.CfnOutput(
            self, "ApiGatewayUrl",
            value=api.url,
            description="API Gateway endpoint URL for DiViz API"
        )

        cdk.CfnOutput(
            self, "CustomDomainUrl",
            value=f"https://{domain.domain_name}",
            description="Custom domain URL for DiViz API"
        )

        cdk.CfnOutput(
            self, "DomainAlias",
            value=domain.domain_name_alias_domain_name,
            description="CloudFront alias for Route53 CNAME record"
        )

        # Output Lambda function ARN
        cdk.CfnOutput(
            self, "LambdaFunctionArn",
            value=diviz_lambda.function_arn,
            description="Lambda function ARN for DiViz API"
        )

        # Output Cognito Auth URLs
        cdk.CfnOutput(
            self, "CognitoLoginUrl",
            value="https://us-east-2gsndrkdxe.auth.us-east-2.amazoncognito.com/login",
            description="Cognito Hosted UI login URL (add client_id and redirect_uri params)"
        )

        cdk.CfnOutput(
            self, "CognitoLogoutUrl",
            value="https://us-east-2gsndrkdxe.auth.us-east-2.amazoncognito.com/logout",
            description="Cognito Hosted UI logout URL (add client_id and logout_uri params)"
        )