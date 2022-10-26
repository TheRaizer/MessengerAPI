#!/bin/bash

sqlCreds=$(aws secretsmanager get-secret-value --secret-id "Messenger/MySQLCreds" --query "SecretString")

sqlCredsUsername=$(python3 -c "import sys, json; print((json.loads(${sqlCreds}))['username'])")
sqlCredsPassword=$(python3 -c "import sys, json; print((json.loads(${sqlCreds}))['password'])")

export RDS_USER="${sqlCredsUsername}"
export RDS_PASSWORD="${sqlCredsPassword}"

docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build