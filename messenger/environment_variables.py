"""Environment variables loaded from a .env file."""

import os

# TODO: since this secret is rotated, dont get it from env variable.
# use AWS SDK to retrieve this secret
# On each request where the secret is used compare it with the last request for the secret.
# If the secrets differ, auto refresh the users token.
JWT_SECRET = os.environ["JWT_SECRET"]
