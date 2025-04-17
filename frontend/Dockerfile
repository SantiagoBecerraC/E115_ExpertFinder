# Use Node.js LTS version
FROM node:20.12.0

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy project files
COPY . .

# Expose port
EXPOSE 3000

# Start the development server
ENV NODE_ENV=development
ENV NEXT_PUBLIC_API_URL=http://localhost:8000
CMD ["npx", "next", "dev", "-H", "0.0.0.0"]
