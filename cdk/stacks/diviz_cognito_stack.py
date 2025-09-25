import aws_cdk as cdk
from aws_cdk import aws_cognito as cognito
from aws_cdk import aws_certificatemanager as certificatemanager
from constructs import Construct

from pathlib import Path
from dotenv import dotenv_values

# Load .env from the parent directory (project root)
dotenv_path = Path(__file__).parent.parent.parent / ".env"
conf = dotenv_values(dotenv_path=dotenv_path)


class CognitoUserPoolStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create the User Pool
        user_pool = cognito.UserPool(
            self,
            "DivizUserPool",
            user_pool_name=conf.get("COGNITO_USER_POOL_NAME"),
            # Sign-in configuration
            sign_in_aliases=cognito.SignInAliases(
                email=True,
                username=True,
            ),
            # Auto-verified attributes
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            # Standard attributes
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=False),
                fullname=cognito.StandardAttribute(required=True, mutable=True),
            ),
            # Custom user attributes
            # custom_attributes={
            #     "google_access": cognito.StringAttribute(mutable=True),
            #     "google_refresh": cognito.StringAttribute(mutable=True),
            #     "google_exp": cognito.StringAttribute(mutable=True),
            # },

            # Password policy
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
            ),
            # Account recovery
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            # MFA configuration
            mfa=cognito.Mfa.OFF,
            # Device tracking
            device_tracking=cognito.DeviceTracking(
                challenge_required_on_new_device=True,
                device_only_remembered_on_user_prompt=False,
            ),
            # Email configuration
            email=cognito.UserPoolEmail.with_cognito(),
            # Deletion protection
            deletion_protection=True,
        )

        # Create Google Identity Provider
        # Prefer Secrets Manager for client secret; fall back to deprecated plain string if not set
        _google_idp_kwargs = {
            "user_pool": user_pool,
            "client_id": conf.get("GOOGLE_CLIENT_ID"),
            "scopes": [
                "email",
                "profile",
                "openid",
                "https://www.googleapis.com/auth/meetings.space.created",
                "https://www.googleapis.com/auth/calendar.readonly",
            ],
            "attribute_mapping": cognito.AttributeMapping(
                email=cognito.ProviderAttribute.other("email"),
                fullname=cognito.ProviderAttribute.other("name"),
                preferred_username=cognito.ProviderAttribute.other("sub"),
                # custom = {
                #     "google_access": cognito.ProviderAttribute.other("access_token"),
                #     "google_refresh": cognito.ProviderAttribute.other("refresh_token"),
                #     "google_exp": cognito.ProviderAttribute.other("expires_in"),
                # }
            ),
        }

        _google_secret_id = (
            conf.get("GOOGLE_CLIENT_SECRET_SECRET_ID")
            or conf.get("GOOGLE_CLIENT_SECRET_SECRET_ARN")
        )
        if _google_secret_id:
            _google_idp_kwargs["client_secret_value"] = cdk.SecretValue.secrets_manager(
                _google_secret_id
            )
        elif conf.get("GOOGLE_CLIENT_SECRET"):
            # Deprecated fallback, keeps backward compatibility
            _google_idp_kwargs["client_secret"] = conf.get("GOOGLE_CLIENT_SECRET")

        google_provider = cognito.UserPoolIdentityProviderGoogle(
            self,
            "Google",
            **_google_idp_kwargs,
        )

        # Create User Pool Client
        user_pool_client = cognito.UserPoolClient(
            self,
            "DivizUserPoolClient",
            user_pool=user_pool,
            user_pool_client_name="DivizUserPoolClient",
            # Authentication flows
            auth_flows=cognito.AuthFlow(
                admin_user_password=True, custom=True, user_password=True, user_srp=True
            ),
            # OAuth settings
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True, implicit_code_grant=False
                ),
                scopes=[
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.PROFILE,
                ],
                callback_urls=[conf.get("BASE_URL") + "/auth/callback"],
                logout_urls=[conf.get("BASE_URL") + "/auth/logout"],
            ),
            # Token validity
            access_token_validity=cdk.Duration.hours(1),
            id_token_validity=cdk.Duration.hours(1),
            refresh_token_validity=cdk.Duration.days(30),
            # Security settings
            generate_secret=True,  
            prevent_user_existence_errors=True,
            # Supported identity providers
            supported_identity_providers=[
                cognito.UserPoolClientIdentityProvider.COGNITO,
                cognito.UserPoolClientIdentityProvider.GOOGLE,
            ],
        )

        # Ensure the client is created after the IdP to avoid "provider does not exist" during deployment
        user_pool_client.node.add_dependency(google_provider)

        domain_prefix = conf.get("COGNITO_DOMAIN_PREFIX")
        user_pool.add_domain("CognitoDomain",
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix=domain_prefix
            )
        )
        certificate_arn = conf.get("AUTH_DOMAIN_CERTIFICATE_ARN")
        domain_cert = certificatemanager.Certificate.from_certificate_arn(self, "domainCert", certificate_arn)

        domain =user_pool.add_domain("CustomDomain",
            custom_domain=cognito.CustomDomainOptions(
                domain_name=domain_prefix + "." + conf.get("API_DOMAIN_NAME"),
                certificate=domain_cert,
            ),
        )

        domain.sign_in_url(user_pool_client,
            redirect_uri=conf.get("BASE_URL") + "/auth/callback",
            sign_in_path="/static/index.html",
        )

        # Outputs
        cdk.CfnOutput(
            self,
            "DivizUserPoolId",
            value=user_pool.user_pool_id,
            description="Cognito User Pool ID",
        )

        cdk.CfnOutput(
            self,
            "DivizUserPoolClientId",
            value=user_pool_client.user_pool_client_id,
            description="Cognito User Pool Client ID",
        )

        cdk.CfnOutput(
            self,
            "DivizUserPoolArn",
            value=user_pool.user_pool_arn,
            description="Cognito User Pool ARN",
        )
