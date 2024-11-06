# Use Python 3.10-slim as a base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (optional if needed for libraries like requests, lxml, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements.txt file into the container and install Python dependencies
COPY data_collection/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy all the data collection code (data_scraper.py, main.py, etc.) into the container
COPY data_collection/ /app/

# Expose the port if your scraping service listens to a specific port (not mandatory for scraping)
# EXPOSE 8000

# Set the entrypoint to run your main scraping script
CMD ["python", "main.py"]
