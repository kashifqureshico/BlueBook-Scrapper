# Use Apify Python base image
FROM apify/actor-python:3.11

# Install Chrome & dependencies (no libindicator7)
RUN apt-get update && apt-get install -y \
    wget unzip curl gnupg \
    xvfb libxi6 libgconf-2-4 \
    libnss3 libasound2 libxss1 libappindicator1 \
    fonts-liberation libatk-bridge2.0-0 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy files
COPY . /app
WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run script
CMD ["python", "-m", "main"]
