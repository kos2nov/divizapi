#!/usr/bin/env python3
import os
import aws_cdk as cdk
from stacks.diviz_api_stack import DivizApiStack

app = cdk.App()

DivizApiStack(app, "DivizApiStack",
    env=cdk.Environment(
        account='110007951910',
        region='us-east-2'
    )
)

app.synth()