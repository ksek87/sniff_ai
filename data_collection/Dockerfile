# Use Python 3.10 as a base image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY data_collection/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the data_collection collection scripts into the container
COPY data_collection/ /app/

# Set the entry point to your data_collection collection script
CMD ["python", "scraper.py"]
