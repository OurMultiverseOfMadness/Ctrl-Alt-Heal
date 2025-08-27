import pytest
import boto3
from moto import mock_aws
import os


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture(scope="function")
def dynamodb(aws_credentials):
    with mock_aws():
        yield boto3.resource("dynamodb", region_name="us-east-1")


@pytest.fixture(scope="function")
def history_table(dynamodb):
    table = dynamodb.create_table(
        TableName="ctrl-alt-heal-history",
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
        ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
    )
    yield table


@pytest.fixture(scope="function")
def users_table(dynamodb):
    table = dynamodb.create_table(
        TableName="ctrl-alt-heal-users",
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
        ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
    )
    yield table


@pytest.fixture(scope="function")
def identities_table(dynamodb):
    table = dynamodb.create_table(
        TableName="ctrl-alt-heal-identities",
        KeySchema=[{"AttributeName": "identity_key", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "identity_key", "AttributeType": "S"}],
        ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
    )
    yield table
