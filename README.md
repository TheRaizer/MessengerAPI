## Intro

This is a simple messenger API, with authentication, friendships, and private messages.
It uses a AWS RDS MySQL database to store message, friendship, and user data.
It utilizes alembic migrations.

## Running Locally

Before running locally ensure that you have a SSH deploy key for the repos that are used.
You will need the SSH key on your local machine to install the repositories.
Once you have a SSH key on your local machine, change the key path
in run_locally.sh to your SSH key path.

Run locally using the command:
sh run_locally.sh

## Deployment

Deployment is done using github actions which does the following steps.

1. Checkout AWS credentials
2. Login to ECR
3. Prepare SSH agent
4. Build image which uses the SSH agent to pull the utils repos using a deploy key
5. tag and push the built image to ECR
6. Create a task definition which references the previously built image in ECR
7. Deploy the task definition to ECS
8. de-register the previously used task definition

It uses a single uvicorn process per a container, and we allow ECS and the application load balancer to handle scaling.
We ensure that the RDS instances are running privately, and are only accessible from microservices running in the same VPC.
Then make sure that the ECS' launched EC2's are also running in the same VPC as the RDS to allow the api access to the database.
or we can use nginx instead of application load balancer.

Although it is not implemented here, you would want to use something like redis adapter to manage
socket events across multiple socketio servers/EC2 instances.

### The Components:

    1. Secrets Manager
    2. ECS
    3. ECR
    4. EC2
    5. VPC
    6. Lambda
    7. CloudWatch
    8. IAM
    9. RDS

**Secrets Manager**
This service stores important and private environment variables that are used in the API. Many of the secrets have auto rotation on using the AWS Lambda service.

**Lambda**
The lambda service is utilized to rotate secrets.

**ECS**
ECS is a service that is used to scale and manage docker containers. There are multiple deployment options including Fargate and EC2. However for this API we use the EC2 deployment option. When setting up ECS we first create a cluster. This cluster will manage spinning up and down EC2 containers, it will use an auto scaling group to do so. When configuring the cluster we make sure that it is created within the same VPC as the RDS instance. After a cluster is created, we must setup a service. A service uses an ecs-agent on each EC2 instance, in order to manage and monitor docker containers that are deployed onto them through ECS. A service will handle deploying and maintaining a certain number of tasks per EC2 instance. After configuring a service we generate tasks. A task is in charge of specifying container environments and settings in a task definition file. The task definition file acts as instructions to the service on how to deploy the container into the EC2 instance. In our case we use github actions to deploy a docker image of the API into AWS ECR, before generating a task definition with that docker image which is then deployed and executed on ECS.

In the service for development API we set minimumHealth to 0% and maximumHealth to 200%, this allows us to remove the only running task thus bringing service to a health of 0%. This is done so that we can create a new task for a new task definition revision that is deployed from a github action. The maximum health of 200% along with the fact that we have configured a total of 1 desired number of tasks, allows us to at max have 2 tasks running at the same time so that one could be closing while the other opens.

**ECR**
In the task definitions of ECS we reference a docker image to run. This docker image is stored in a private AWS Elastic container repository (ECR).

**EC2**
ECS relies on EC2 instances to actually run our docker containers on. These EC2 instances are deployed from an auto scaling group that is automatically setup when creating a cluster in ECS. The instances can be SSH'ed into and debugged through the ecs-agent.log file. They must also run in the same VPC as the RDS.

**VPC**
The Virtual private cloud (VPC) is integral in maintaining security and isolation of microservices. It allows us to create private and public subnets (with or without access to the internet). And security groups which give us fine grain control on inbound and outbound access that microservices have. For example the RDS has an inbound rule that allows SSH access from an Admin PC IP.

**IAM**
The Identity and Access Management (IAM) is important for maintaining security. It restricts user and service access. For example the github action that deploys the development API to AWS is given a task exection role that allows it to read and write to only very specific actions in certain AWS microservices. There are also many different roles for both real users, and services like this API that interact with the AWS microservices.

### ECS:

ECS is used to deploy the api to EC2 instances. These EC2 instances are managed through an auto scaling group that contains a custom launch template.

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
