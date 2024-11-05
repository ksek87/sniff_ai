# Use Python 3.10 as a base image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY model/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the model files into the container
COPY model/ /app/

# Set the entry point to run the model (adjust as needed)
CMD ["python", "model.py"]
