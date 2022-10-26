Docker Desktop needs to be running.

To run in dev execute (docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build)

We have a github action that is executed with the config called deploy-to-ECR.yml which will deploy a built image of this api to ECR.
It will then fetch this image and deploy it to ECS.

We also have a task definition which is pulled by this github action.

This task definition defines a running task in ECS.
It allows you to define the environment of the Docker container as well as other options.
Here we fetch secrets from AWS parameter store or AWS secrets manager.
We also declare that we will run ECS with Fargate.
