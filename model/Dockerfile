# Use Python 3.10 as a base image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files from the current directory
COPY . .

# Set the entry point to run the model (adjust as needed)
CMD ["python", "model.py"]
