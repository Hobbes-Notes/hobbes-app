FROM node:16-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# No need to copy source code as we'll use volumes
# COPY . .

EXPOSE 3000

# Run development server with hot reloading
ENV WATCHPACK_POLLING=true
CMD ["npm", "start"] 