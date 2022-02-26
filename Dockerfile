# For more information, please refer to https://aka.ms/vscode-docker-python
# FROM python:3.8-slim-buster
FROM osgeo/gdal:ubuntu-small-3.2.0

EXPOSE 5000
ENV VAR1=10

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
RUN apt-get update && apt-get install -y \
    python3-pip
RUN python3 -m pip install -r requirements.txt

WORKDIR /app
COPY ./app /app

ENV STATIC_URL /static
ENV STATIC_PATH ./app/static

# Switching to a non-root user, please refer to https://aka.ms/vscode-docker-python-user-rights
RUN useradd appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
