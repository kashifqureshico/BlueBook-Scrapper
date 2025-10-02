# Use Apify Python image
FROM apify/actor-python:3.11

# Install Chrome & dependencies (needed for Selenium)
RUN apt-get update && apt-get install -y wget unzip curl gnupg \
    && apt-get install -y xvfb libxi6 libgconf-2-4 \
    && apt-get install -y libnss3 libasound2 libxss1 libappindicator1 libindicator7 \
    && apt-get install -y fonts-liberation libatk-bridge2.0-0 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy everything
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Start the actor
CMD ["python", "-m", "src.main"]
