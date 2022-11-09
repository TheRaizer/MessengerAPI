## Intro

This is a simple messenger API, with authentication, friendships, group chats, and private messages.

It uses a AWS RDS MySQL database to store message, friendship, and user data.

And has alembic migrations.

It also utilizes docker.

## CI/CD

We have a github action that is executed with the config called deploy-to-ECR.yml which will deploy a built image of this api to ECR.

It will then fetch this image and deploy it to ECS.
We also have a task definition which is pulled by this github action.

This task definition defines a running task in ECS. It allows you to define the environment of the Docker container as well as other options.

In the task definition we fetch secrets from AWS parameter store or AWS secrets manager. We also declare that we will run ECS with Fargate.

## Setting up submodules

_install utils submodule from private git repos:_
git submodule add https://github.com/TheRaizer/Messenger-Utils \_submodules/messenger_utils

_update sub module by running the following commands:_

git pull --recurse-submodules
git submodule update --remote --recursive

## Running in Locally

Run locally using the command:
sh run_locally.sh

There are two deployment cases I will cover.

1. ECR and ECS

This deployment generates an image using a docker file and github actions.

It uses a single uvicorn process per a container, and we allow ECS and the application load balancer handle scaling.

We ensure that the RDS instances are running privately, and are only accessible from microservices running in the same VPC.

Then make sure that the ECS' launched EC2's are also running in the same VPC as the RDS to allow the api access to the database.

or we can use nginx instead of application load balancer.

2. VM (EC2 ubuntu AMI for our case)

This deployment uses a docker image.

We then use GUnicorn as a process manager to manage multiple uvicorn processees on one docker container.

This docker container will then run in an ubuntu EC2 instance.

The EC2 instance will be setup in the same availability zone and VPC as the RDS as to allow the RDS to run privately.

We can then configure the VM to only allow HTTP requests from certain domains and etc.

We could then setup nginx as a TLS Termination Proxy

## Testing

Tests will be run using a test database running in a docker container. It will utilize pytest.

The test database is launched inside a docker container using the start_test_db.sh script.
The docker container will open port 3307 and link it to port 3306 in the docker container.
Port 3306 in the docker container matches the port of the MySQL server.

There will also be a test database hosted on an EC2 instance using a docker image.
This will be used for testing during CI/CD.

No actual tables have to be created on the database as during testing, no actual records are added.
This is done through transaction nesting and save pointing.
The concept of tables, and their relationships are handled within SQLAlchemy transactions. Thus the tests still hold.

https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites

SQLAlchemy Schema that are initialized then used across all tests must be recreated for each tests. Thus we place their initialization in fixtures.

**Running tests**
_Run bash script:_
start_test_db.sh

_Run pytests:_
python -m pytest -s
