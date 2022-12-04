"""Defines the SecretsManager class"""

import logging
from typing import Optional
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class SecretsManager:
    """Encapsulates Secrets Manager functions."""

    def __init__(self):
        session = boto3.Session()
        client = session.client(
            service_name="secretsmanager",
            region_name="us-east-2",
        )
        self.secretsmanager_client = client

    def get_value(self, secret_id: str, stage: Optional[str] = None) -> str:
        """Gets the value of a secret.

        Args:
            secret_id (str): the identifier/name of the secret whose value we will retrieve.
            stage (str, optional): The stage of the secret to retrieve. If this is None, the
                current stage is retrieved. Defaults to None.

        Returns:
            str: The value of the secret. When the secret is a string, the value is
                contained in the `SecretString` field. When the secret is bytes,
                it is contained in the `SecretBinary` field.
        """

        try:
            kwargs = {"SecretId": secret_id}
            if stage is not None:
                kwargs["VersionStage"] = stage
            response = self.secretsmanager_client.get_secret_value(**kwargs)
            logger.info("got value for secret %s.", secret_id)
        except ClientError:
            logger.exception("couldn't get value for secret %s.", secret_id)
            raise
        else:
            return response
