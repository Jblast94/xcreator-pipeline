FROM node:18-alpine

WORKDIR /app

# Install SQLite3 dependencies
RUN apk add --no-cache \
    python3 \
    make \
    g++ \
    sqlite \
    sqlite-dev

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nodejs -u 1001

# Create data directory and set permissions
RUN mkdir -p /app/data && chown -R nodejs:nodejs /app

USER nodejs

EXPOSE 3001

CMD ["node", "bridge-service.js"]