# Use an official Node.js runtime as the base image
FROM node:16

# Set the working directory for the frontend
WORKDIR /app

# Copy the package.json and install the dependencies
COPY frontend/package.json /app/package.json
RUN npm install

# Copy the rest of the frontend application code
COPY frontend/ /app/

# Expose port 3000 (or whatever your frontend uses)
EXPOSE 3000

# Set the entry point to run the frontend app (adjust as needed)
CMD ["npm", "start"]
