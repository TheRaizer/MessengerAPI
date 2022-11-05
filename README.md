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
"git submodule add https://github.com/TheRaizer/Messenger-Utils \_submodules/messenger_utils"

_update sub module by running the following commands:_

"git pull --recurse-submodules"
"git submodule update --remote --recursive"

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

We use a local MySQL database during testing.

This database must be setup before hand using the following instructions.

**Windows:**
Install the MySQL Community Server from the following link (no need for the debug binaries and test suite version)

https://dev.mysql.com/downloads/

This installation also installs the MySQL command line client.

When all is done and configured, you can setup a test database through the MySQL command line client.

You should be able to access the mysql command line client by searching for it in the start menu.

**MAC:**
"brew install mysql-client"

_add the mysql-client binary directory to your PATH:_
"echo 'export PATH="/usr/local/opt/mysql-client/bin:$PATH"' >> ~/.bash_profile"

_reload bash profile:_
"source ~/.bash_profile"

**Linux:**
"sudo apt install mysql-client"

**After each specific setup**
In linux and mac options you will need to create a user.
You can do this in the sql client with standard user creation queries.
Then once you run the create database command below, make sure to give the user you created, admin privilages for that database.

_Within the sql client command line run:_
"mysql create database test"

**test env**
add a file called .test.env with the following variables:
RDS_ENDPOINT="localhost"
RDS_PASSWORD=The password you assigned to your user that can access the local database
RDS_USER=The name of the user that can access the local database
RDS_PORT="3306"
RDS_DB_NAME="test"
