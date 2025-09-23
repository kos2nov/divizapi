#!/usr/bin/env python3
import os
from pathlib import Path
from dotenv import load_dotenv
import aws_cdk as cdk
from stacks.diviz_api_stack import DivizApiStack

# Load .env from project root
load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env', override=False)

app = cdk.App()

account = os.getenv('AWS_ACCOUNT_ID') or os.environ.get('CDK_DEFAULT_ACCOUNT')
region = os.getenv('DEPLOYMENT_AWS_REGION') or os.getenv('AWS_REGION') or os.environ.get('CDK_DEFAULT_REGION')

DivizApiStack(app, "DivizApiStack",
    env=cdk.Environment(
        account=account,
        region=region
    )
)

app.synth()