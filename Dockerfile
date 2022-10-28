FROM python:3.9

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Install submodule packages
COPY _submodules/messenger_utils /app/_submodules/messenger_utils
RUN pip install _submodules/messenger_utils --upgrade

COPY . .

CMD ["uvicorn", "messenger.fastApi:app", "--host", "0.0.0.0", "--port", "8000"]

# If running behind a proxy like Nginx or Traefik add --proxy-headers
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]