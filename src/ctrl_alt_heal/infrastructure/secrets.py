import json

import boto3
from botocore.exceptions import ClientError


def get_secret(secret_name: str, region_name: str = "ap-southeast-1") -> dict:
    """Retrieve a secret from AWS Secrets Manager."""
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        # For a list of exceptions, see:
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response["SecretString"]

    # Try to parse as JSON, if it fails, assume it's a plain string
    # and return it in a dict.
    try:
        return json.loads(secret)
    except json.JSONDecodeError:
        return {"value": secret}
