# Use Apify Python + Selenium base image
FROM apify/actor-python-selenium:3.11

# Use non-root user (myuser) recommended by Apify
USER myuser

# Copy files into the actor's directory
COPY --chown=myuser:myuser . /home/myuser/actor
WORKDIR /home/myuser/actor

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the actor
CMD ["python", "-m", "src"]
