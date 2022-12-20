# syntax = docker/dockerfile:1.0-experimental
FROM python:3.9-alpine

USER root

WORKDIR /app

RUN apk add --no-cache openssh-client git

COPY ./requirements.txt /app/requirements.txt

# download public key for github.com
RUN mkdir -p -m 0600 ~/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts
RUN --mount=type=ssh,id=github_ssh_key pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY . .

CMD ["uvicorn", "messenger.fastapi:app", "--host", "0.0.0.0", "--port", "8000"]

# If running behind a proxy like Nginx or Traefik add --proxy-headers
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]