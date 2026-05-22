# Main Application Dockerfile for XCreator Pro + Eliza Integration
FROM node:18-alpine

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    make \
    g++ \
    git \
    curl \
    ffmpeg \
    imagemagick

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads logs data

# Set permissions
RUN chown -R node:node /app

# Switch to non-root user
USER node

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Start application
CMD ["npm", "start"]