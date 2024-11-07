# Use an official Node.js runtime as the base image
FROM node:16

# Set the working directory for the frontend
WORKDIR /app/frontend

# Copy the package.json and package-lock.json (if available)
COPY frontend/package*.json ./  
# Install frontend dependencies
RUN npm install

# Copy the rest of the frontend application code
COPY frontend/ ./  

# Expose port 5000
EXPOSE 5000

# Set the entry point to run the frontend app
CMD ["npm", "start"]
