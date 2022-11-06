#!/bin/bash

sqlCreds=$(aws secretsmanager get-secret-value --secret-id "prod/Messenger/MySQL-Creds" --query "SecretString")
jwtSecret=$(aws secretsmanager get-secret-value --secret-id "prod/MessengerApi/JWT_Secret" --query "SecretString")


sqlCredsUsername=$(python3 -c "import sys, json; print((json.loads(${sqlCreds}))['username'])")
sqlCredsPassword=$(python3 -c "import sys, json; print((json.loads(${sqlCreds}))['password'])")
jwtSecretValue=$(python3 -c "import sys, json; print((json.loads(${jwtSecret}))['secret'])")

export RDS_USER="${sqlCredsUsername}"
export RDS_PASSWORD="${sqlCredsPassword}"
export JWT_SECRET="${jwtSecretValue}"

docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build