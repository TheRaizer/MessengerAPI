#!/bin/bash

sqlCreds=$(aws secretsmanager get-secret-value --secret-id "prod/Messenger/MySQL-Creds" --query "SecretString")
jwtSecret=$(aws secretsmanager get-secret-value --secret-id "prod/MessengerApi/JWT_Secret" --query "SecretString")


sqlCredsUsername=$(python3 -c "import sys, json; print((json.loads(${sqlCreds}))['username'])")
sqlCredsPassword=$(python3 -c "import sys, json; print((json.loads(${sqlCreds}))['password'])")
jwtSecretValue=$(python3 -c "import sys, json; print((json.loads(${jwtSecret}))['secret'])")

export DOCKER_BUILDKIT=1

# TODO: We could generalize this for use with multiple private repos and multiple deploy keys
# TODO...: check https://gist.github.com/vhermecz/4e2ae9468f2ff7532bf3f8155ac95c74

# keys are stored in ssh-agent and are forwarded into docker.

# pass the decoded key to docker buildkit which will use ssh forwarding
# the path stated below should be modified to point towards the ssh deploy key for api-utils repos.
docker build -t messenger_api --no-cache --ssh github_ssh_key=c:/Users/Admin/.ssh/id_rsa .

docker run -d -p 8000:8000 --env-file=.dev.env -it \
    -e RDS_PASSWORD=${sqlCredsPassword} \
    -e RDS_USER=${sqlCredsUsername} \
    -e JWT_SECRET=${jwtSecretValue} \
    messenger_api
