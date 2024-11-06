# Step 1: Use an official Python runtime as a base image
FROM python:3.10-slim

# Step 2: Set the working directory in the container
WORKDIR /app

# Step 3: Install system dependencies (if needed, like libpq-dev for PostgreSQL)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Step 4: Copy the local code to the container
COPY ./backend /app

# Step 5: Install Python dependencies from requirements.txt
COPY ./backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Step 6: Expose the port the app runs on (example: Flask uses 5000 by default)
EXPOSE 5000

# Step 7: Define the command to run your app
CMD ["python", "main.py"]
