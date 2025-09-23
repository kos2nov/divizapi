from mangum import Mangum
from diviz.main import app

handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    return handler(event, context)
