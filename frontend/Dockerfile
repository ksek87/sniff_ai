# Use an official Node.js runtime as the base image
FROM node:16

# Set the working directory for the frontend
WORKDIR /app

# Copy the package.json and package-lock.json (if available) and install the dependencies
COPY package*.json ./  
# Install frontend dependencies
RUN npm install

# Copy the rest of the frontend application code
COPY . ./  

# Expose the correct port (3000 for React by default)
EXPOSE 3000

# Set the entry point to run the frontend app
CMD ["npm", "start"]
