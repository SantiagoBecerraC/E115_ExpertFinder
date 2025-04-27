FROM node:20.12.0-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application
COPY . .

# Build the application
RUN npm run build

# Expose port
EXPOSE 3000

# Set environment variables
ENV NODE_ENV=production
ENV NEXT_PUBLIC_API_URL=http://localhost:8000
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

# Start the application directly with node
CMD ["node", "node_modules/.bin/next", "start"]
