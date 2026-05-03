FROM node:18-slim

WORKDIR /app

COPY package*.json ./

RUN npm ci --legacy-peer-deps

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
