import os
from functools import cache


@cache
def read_secret(secret_id):
    import boto3

    value = boto3.client("secretsmanager").get_secret_value(SecretId=secret_id)["SecretString"].strip()
    if not value:
        raise ValueError("Configured Secrets Manager secret is empty")
    return value


def github_token():
    secret_id = os.environ.get("GITHUB_TOKEN_SECRET_ARN")
    return read_secret(secret_id) if secret_id else os.environ.get("GITHUB_TOKEN", "")
