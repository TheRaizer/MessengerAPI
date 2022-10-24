import os
from dotenv import load_dotenv

load_dotenv()

# normally we want to point to RDS proxy endpoint, however that can only be accessed through within the VPC
# thus the docker container needs to be running in ECS inside the VPC.
RDS_ENDPOINT = os.getenv('RDS_ENDPOINT')
USER = os.getenv('USER')
PASSWORD = os.getenv('PASSWORD')
PORT = os.getenv('PORT')
NAME = os.getenv('NAME')