# Use Python 3.10-slim as a base image
FROM python:3.10-slim

# Set the working directory for the entire application
WORKDIR /app

# Install system dependencies (for Node.js and Python)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Install Node.js and frontend dependencies
RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash - \
    && apt-get install -y nodejs \
    && npm install --prefix /app/frontend

# Copy the backend, model, and frontend code
COPY backend/ /app/backend/
COPY model/ /app/model/
COPY frontend/ /app/frontend/

# Expose the backend and frontend ports
EXPOSE 8000 3000

# Set entrypoint to run both backend (AI) and frontend (Node.js) services
CMD ["bash", "-c", "python /app/backend/model.py & npm start --prefix /app/frontend"]
