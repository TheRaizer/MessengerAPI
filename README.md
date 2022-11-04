Docker Desktop needs to be running.

To run in dev execute (docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build)

We have a github action that is executed with the config called deploy-to-ECR.yml which will deploy a built image of this api to ECR.
It will then fetch this image and deploy it to ECS.

We also have a task definition which is pulled by this github action.

This task definition defines a running task in ECS.
It allows you to define the environment of the Docker container as well as other options.
Here we fetch secrets from AWS parameter store or AWS secrets manager.
We also declare that we will run ECS with Fargate.

install utils submodule from private git repos: git submodule add https://github.com/TheRaizer/Messenger-Utils \_submodules/messenger_utils
update sub module by running the following commands:
git pull --recurse-submodules
git submodule update --remote --recursive

Run locally using the command:
sh run_locally.sh

There are two deployment cases I will cover.

1. ECR and ECS
   This deployment generates an image using a docker file and github actions.
   It uses a single uvicorn process per a container, and we allow ECS and the application load balancer handle scaling.
   We ensure that the RDS instances are running privately, and are only accessible from microservices running in the same VPC.
   Then make sure that the ECS' launched EC2's are also running in the same VPC as the RDS to allow the api access to the database.
   or we can use nginx instead of application load balancer.

2. VM
   This deployment uses a docker image.
   We then use GUnicorn as a process manager to manage multiple uvicorn processees on one docker container.
   This docker container will then run in a VM.
   We can use the AWS RDS, or setup a MySQL server on the VM.
   We can then configure the VM to only allow HTTP requests from certain domains and etc.
   We could then setup nginx as a TLS Termination Proxy
