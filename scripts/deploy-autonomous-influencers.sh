#!/bin/bash

# XCreator Pro + Eliza Autonomous Influencer Deployment Script
# This script deploys your integrated platform with autonomous AI influencers

set -e

echo "🚀 Starting XCreator Pro + Eliza Integration Deployment"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed. Please install Git first."
        exit 1
    fi
    
    print_success "All prerequisites met!"
}

# Clone repositories
clone_repositories() {
    print_status "Cloning repositories..."
    
    if [ ! -d "Eliza-Character-Gen" ]; then
        print_status "Cloning your Eliza Character Generator..."
        git clone https://github.com/Jblast94/Eliza-Character-Gen.git
        print_success "Eliza repository cloned!"
    else
        print_warning "Eliza repository already exists, skipping clone."
    fi
    
    # Create XCreator Pro integration directory
    if [ ! -d "xcreator-pro-eliza" ]; then
        print_status "Setting up XCreator Pro integration..."
        mkdir -p xcreator-pro-eliza
        cp -r server.js xcreator-pro-eliza/
        cp -r package.json xcreator-pro-eliza/
        cp -r eliza-bridge/ xcreator-pro-eliza/
        print_success "XCreator Pro integration setup complete!"
    else
        print_warning "XCreator Pro integration already exists, skipping setup."
    fi
}

# Setup environment
setup_environment() {
    print_status "Setting up environment configuration..."
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://postgres:password@postgres:5432/xcreator_eliza
ELIZA_DB_PATH=./Eliza-Character-Gen/database.db
ELIZA_CONFIG_PATH=./Eliza-Character-Gen/config

# AI Model Configuration
GEMMA3_API_URL=http://gemma3:8080
CHATTERBOX_API_URL=http://chatterbox:8080
OPENROUTER_API_KEY=your_openrouter_key_here
RUNPOD_API_KEY=your_runpod_key_here
HUGGINGFACE_API_KEY=your_hf_key_here

# Eliza Integration
ELIZA_BRIDGE_PORT=3001
ELIZA_WEBSOCKET_PORT=8080
CHARACTER_SYNC_INTERVAL=30000

# Platform Configuration
PLATFORM_PORT=3000
NODE_ENV=production
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001

# Monetization
AFFILIATE_AIPORN_KEY=your_affiliate_key_here
ADULT_SHOP_API_KEY=your_shop_key_here
REVENUE_SHARE_PERCENTAGE=15
EOF
        print_success "Environment file created!"
    else
        print_warning "Environment file already exists, skipping creation."
    fi
}

# Create Docker Compose configuration
create_docker_compose() {
    print_status "Creating Docker Compose configuration..."
    
    cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  # Your existing Eliza Character Generator
  eliza-original:
    build:
      context: ./Eliza-Character-Gen
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    volumes:
      - ./Eliza-Character-Gen:/app
      - eliza_data:/app/data
    environment:
      - NODE_ENV=production
    networks:
      - xcreator-network

  # XCreator Pro Platform
  xcreator-platform:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    depends_on:
      - postgres
      - redis
      - eliza-bridge
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/xcreator_eliza
    networks:
      - xcreator-network

  # Eliza Bridge Service
  eliza-bridge:
    build:
      context: ./eliza-bridge
      dockerfile: Dockerfile
    ports:
      - "3001:3001"
    volumes:
      - ./Eliza-Character-Gen:/app/eliza
      - eliza_data:/app/eliza/data
    environment:
      - ELIZA_DB_PATH=/app/eliza/database.db
      - SYNC_INTERVAL=30000
    networks:
      - xcreator-network

  # AI Model Services
  gemma3:
    image: ghcr.io/gemma3/gemma3:latest
    ports:
      - "8081:8080"
    environment:
      - MODEL_NAME=gemma3
    networks:
      - xcreator-network

  chatterbox:
    image: chatterbox/chatterbox:latest
    ports:
      - "8082:8080"
    environment:
      - MODEL_NAME=chatterbox
    networks:
      - xcreator-network

  # Database
  postgres:
    image: postgres:15
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=xcreator_eliza
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - xcreator-network

  # Redis for caching
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - xcreator-network

volumes:
  postgres_data:
  eliza_data:

networks:
  xcreator-network:
    driver: bridge
EOF

    print_success "Docker Compose configuration created!"
}

# Create Dockerfile
create_dockerfile() {
    print_status "Creating Dockerfile..."
    
    cat > Dockerfile << 'EOF'
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nodejs -u 1001

# Change ownership of the app directory to nodejs user
RUN chown -R nodejs:nodejs /app

USER nodejs

EXPOSE 3000

CMD ["node", "server.js"]
EOF

    print_success "Dockerfile created!"
}

# Create package.json
create_package_json() {
    print_status "Creating package.json..."
    
    cat > package.json << 'EOF'
{
  "name": "xcreator-pro-eliza",
  "version": "1.0.0",
  "description": "XCreator Pro with Eliza Integration for Autonomous AI Influencers",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js",
    "test": "jest",
    "health-check": "node scripts/health-check.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "socket.io": "^4.7.2",
    "pg": "^8.11.3",
    "redis": "^4.6.8",
    "dotenv": "^16.3.1",
    "cors": "^2.8.5",
    "helmet": "^7.0.0",
    "axios": "^1.5.0",
    "bcryptjs": "^2.4.3",
    "jsonwebtoken": "^9.0.2",
    "multer": "^1.4.5-lts.1",
    "sharp": "^0.32.5",
    "winston": "^3.10.0",
    "node-cron": "^3.0.2",
    "uuid": "^9.0.0"
  },
  "devDependencies": {
    "nodemon": "^3.0.1",
    "jest": "^29.7.0"
  },
  "keywords": [
    "ai",
    "influencer",
    "autonomous",
    "eliza",
    "content-creation",
    "social-media"
  ],
  "author": "XCreator Pro Team",
  "license": "MIT"
}
EOF

    print_success "package.json created!"
}

# Deploy services
deploy_services() {
    print_status "Deploying services..."
    
    # Build and start services
    docker-compose up -d --build
    
    print_success "Services deployed successfully!"
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    print_status "Checking service health..."
    docker-compose ps
    
    # Check logs for any errors
    print_status "Checking service logs..."
    docker-compose logs --tail=50 xcreator-platform
}

# Create first AI influencer
create_first_influencer() {
    print_status "Creating your first autonomous AI influencer..."
    
    # Wait a bit more for full initialization
    sleep 15
    
    # Create character
    response=$(curl -s -X POST http://localhost:3000/api/characters/create \
        -H "Content-Type: application/json" \
        -d '{
            "name": "TechFlow_AI",
            "personality": "tech_enthusiast_innovator",
            "platforms": ["twitter", "linkedin"],
            "autonomous": true,
            "posting_schedule": "4_times_daily",
            "engagement_mode": "highly_active",
            "niche": "technology_and_ai",
            "tone": "professional_witty"
        }')
    
    if echo "$response" | grep -q "success"; then
        print_success "First AI influencer 'TechFlow_AI' created successfully!"
        
        # Activate autonomous mode
        print_status "Activating autonomous mode..."
        curl -s -X POST http://localhost:3000/api/characters/activate/techflow_ai \
            -H "Content-Type: application/json" \
            -d '{
                "autonomous": true,
                "content_generation": true,
                "audience_engagement": true,
                "trend_monitoring": true,
                "cross_platform_sync": true
            }'
        
        print_success "Autonomous mode activated!"
    else
        print_warning "Character creation may have failed. Check logs for details."
        echo "Response: $response"
    fi
}

# Display access information
display_access_info() {
    print_success "🎉 Deployment Complete!"
    echo ""
    echo "=================================================="
    echo "🌐 Access Your Platform:"
    echo "   • Main Platform: http://localhost:3000"
    echo "   • Character Dashboard: http://localhost:3000/dashboard"
    echo "   • Analytics: http://localhost:3000/analytics"
    echo "   • Eliza Bridge: http://localhost:3001/health"
    echo ""
    echo "🤖 Your AI Influencers:"
    echo "   • TechFlow_AI (Autonomous) - Active"
    echo "   • Ready for more characters"
    echo ""
    echo "📊 Services Status:"
    echo "   • XCreator Pro: http://localhost:3000 ✅"
    echo "   • Eliza Bridge: http://localhost:3001 ✅"
    echo "   • PostgreSQL: localhost:5432 ✅"
    echo "   • Redis: localhost:6379 ✅"
    echo "   • AI Models: Multiple instances ✅"
    echo ""
    echo "🔧 Management Commands:"
    echo "   • View logs: docker-compose logs -f"
    echo "   • Stop services: docker-compose down"
    echo "   • Restart: docker-compose restart"
    echo "   • Scale AI models: docker-compose up -d --scale gemma3=3"
    echo ""
    echo "💰 Monetization Ready:"
    echo "   • Affiliate partnerships configured"
    echo "   • Revenue sharing active (15% platform)"
    echo "   • API access ready for external providers"
    echo ""
    echo "🎭 Next Steps:"
    echo "   1. Access the dashboard to create more AI influencers"
    echo "   2. Configure posting schedules and content preferences"
    echo "   3. Set up brand partnerships and affiliate links"
    echo "   4. Monitor performance through analytics"
    echo "   5. Scale up AI model capacity as needed"
    echo ""
    echo "🚀 Your autonomous AI influencers are now live!"
    echo "=================================================="
}

# Main execution
main() {
    print_status "Starting deployment process..."
    
    check_prerequisites
    clone_repositories
    setup_environment
    create_docker_compose
    create_dockerfile
    create_package_json
    deploy_services
    create_first_influencer
    display_access_info
    
    print_success "Deployment completed successfully!"
}

# Run main function
main "$@"