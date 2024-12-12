# Use an official Node.js runtime as the base image
FROM node:16

# Set the working directory
WORKDIR /app

# Copy package files first
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Expose the port (adjust if needed)
EXPOSE 5000

# Set the entry point to run the frontend app
CMD ["npm", "start"]
