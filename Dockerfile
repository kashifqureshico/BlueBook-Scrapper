# Use Apify Python base image
FROM apify/actor-python:3.11

# Install Chrome & dependencies
RUN apt-get update && apt-get install -y \
    wget unzip curl gnupg \
    xvfb libxi6 libgconf-2-4 \
    libnss3 libasound2 libxss1 libappindicator1 \
    fonts-liberation libatk-bridge2.0-0 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy actor metadata and source
COPY .actor /app/.actor
COPY src /app/src
COPY requirements.txt README.md LICENSE Dockerfile /app/

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Debug: confirm files exist
RUN ls -R /app

# Entrypoint handled by actor.json
