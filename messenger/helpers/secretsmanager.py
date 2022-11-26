import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


class SecretsManager:
    """Encapsulates Secrets Manager functions."""

    def __init__(self):
        """
        :param secretsmanager_client: A Boto3 Secrets Manager client.
        """
        session = boto3.Session()
        client = session.client(
            service_name="secretsmanager",
            region_name="us-east-2",
        )
        self.secretsmanager_client = client

    def get_value(self, secretId: str, stage=None):
        """
        Gets the value of a secret.

        :param stage: The stage of the secret to retrieve. If this is None, the
                      current stage is retrieved.
        :return: The value of the secret. When the secret is a string, the value is
                 contained in the `SecretString` field. When the secret is bytes,
                 it is contained in the `SecretBinary` field.
        """
        try:
            kwargs = {"SecretId": secretId}
            if stage is not None:
                kwargs["VersionStage"] = stage
            response = self.secretsmanager_client.get_secret_value(**kwargs)
            logger.info("Got value for secret %s.", secretId)
        except ClientError:
            logger.exception("Couldn't get value for secret %s.", secretId)
            raise
        else:
            return response
