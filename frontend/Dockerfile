# Use an official Node.js runtime as the base image
FROM node:16

# Set the working directory for the frontend (where your frontend code will live inside the container)
WORKDIR /app

# Copy the package.json and package-lock.json (if available)
COPY frontend/package*.json ./frontend/

# Install frontend dependencies
RUN npm install --prefix /app/frontend

# Copy the rest of the frontend application code
COPY frontend/ ./frontend/

# Expose the port (adjust if needed)
EXPOSE 5000

# Set the entry point to run the frontend app
CMD ["npm", "start", "--prefix", "/app/frontend"]
