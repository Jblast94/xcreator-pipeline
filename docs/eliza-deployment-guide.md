# XCreator Pro + Eliza Integration Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying your integrated XCreator Pro platform with Eliza Character Generator, creating autonomous AI influencers with zero downtime.

## Prerequisites
- Docker and Docker Compose installed
- Git repository access
- Your existing Eliza Character Generator setup
- 8GB+ RAM recommended for AI models

## Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   XCreator Pro  │◄──►│  Eliza Bridge    │◄──►│  Your Eliza DB  │
│    Platform     │    │    Service       │    │  (SQLite/JSON)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Self-Hosted   │    │   WebSocket      │    │   Character     │
│   AI Models     │    │   Real-time      │    │   Management    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Step 1: Clone and Setup

```bash
# Clone your Eliza repository
git clone https://github.com/Jblast94/Eliza-Character-Gen.git
cd Eliza-Character-Gen

# Clone XCreator Pro integration
git clone https://github.com/your-org/xcreator-pro-eliza.git
cd xcreator-pro-eliza
```

## Step 2: Environment Configuration

Create `.env` file:
```env
# Database Configuration
DATABASE_URL=postgresql://postgres:password@postgres:5432/xcreator_eliza
ELIZA_DB_PATH=./Eliza-Character-Gen/database.db
ELIZA_CONFIG_PATH=./Eliza-Character-Gen/config

# AI Model Configuration
GEMMA3_API_URL=http://gemma3:8080
CHATTERBOX_API_URL=http://chatterbox:8080
OPENROUTER_API_KEY=your_openrouter_key
RUNPOD_API_KEY=your_runpod_key
HUGGINGFACE_API_KEY=your_hf_key

# Eliza Integration
ELIZA_BRIDGE_PORT=3001
ELIZA_WEBSOCKET_PORT=8080
CHARACTER_SYNC_INTERVAL=30000

# Platform Configuration
PLATFORM_PORT=3000
NODE_ENV=production
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001

# Monetization
AFFILIATE_AIPORN_KEY=your_affiliate_key
ADULT_SHOP_API_KEY=your_shop_key
REVENUE_SHARE_PERCENTAGE=15
```

## Step 3: Docker Deployment

### Main Docker Compose:
```yaml
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
```

## Step 4: Deploy Commands

```bash
# Deploy all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f xcreator-platform
docker-compose logs -f eliza-bridge

# Scale AI model instances
docker-compose up -d --scale gemma3=2 --scale chatterbox=2
```

## Step 5: Character Migration

### Zero-Downtime Migration Script:
```bash
#!/bin/bash
# migrate-characters.sh

echo "Starting character migration..."

# Backup existing Eliza data
docker exec eliza-original cp -r /app/data /app/data.backup

# Run migration service
docker-compose run --rm migration-service

# Verify migration
docker exec xcreator-platform node scripts/verify-migration.js

echo "Migration complete!"
```

## Step 6: Autonomous Influencer Setup

### Create Your First AI Influencer:
```bash
# Access platform
curl -X POST http://localhost:3000/api/characters/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "AI_Influencer_1",
    "personality": "witty_tech_enthusiast",
    "platforms": ["twitter", "instagram"],
    "autonomous": true,
    "posting_schedule": "3_times_daily",
    "engagement_mode": "active"
  }'
```

### Start Autonomous Operations:
```bash
# Activate autonomous mode
curl -X POST http://localhost:3000/api/characters/activate/ai_influencer_1 \
  -H "Content-Type: application/json" \
  -d '{
    "autonomous": true,
    "content_generation": true,
    "audience_engagement": true,
    "trend_monitoring": true
  }'
```

## Step 7: Monitoring and Management

### Access Dashboards:
- **XCreator Pro Platform**: http://localhost:3000
- **Character Management**: http://localhost:3000/dashboard
- **Analytics**: http://localhost:3000/analytics
- **Eliza Bridge**: http://localhost:3001/health

### Monitor AI Influencers:
```bash
# Check active characters
curl http://localhost:3000/api/characters/status

# View performance metrics
curl http://localhost:3000/api/analytics/performance

# Monitor engagement
curl http://localhost:3000/api/analytics/engagement
```

## Step 8: Monetization Setup

### Configure Affiliate Links:
```bash
# Add affiliate partnerships
curl -X POST http://localhost:3000/api/monetization/affiliates \
  -H "Content-Type: application/json" \
  -d '{
    "partner": "aiporn",
    "api_key": "your_affiliate_key",
    "commission_rate": 0.25
  }'

# Setup revenue sharing
curl -X POST http://localhost:3000/api/monetization/revenue \
  -H "Content-Type: application/json" \
  -d '{
    "platform_percentage": 15,
    "creator_percentage": 85,
    "payout_schedule": "monthly"
  }'
```

## Troubleshooting

### Common Issues:
1. **Port Conflicts**: Ensure ports 3000, 3001, 8080, 5432 are available
2. **Database Connection**: Verify PostgreSQL is running and accessible
3. **AI Model Loading**: Models may take 2-3 minutes to initialize
4. **Character Sync**: Check Eliza Bridge logs for sync status

### Debug Commands:
```bash
# Check service health
docker-compose exec xcreator-platform npm run health-check

# Reset character sync
docker-compose exec eliza-bridge npm run reset-sync

# View real-time logs
docker-compose logs -f --tail=100
```

## Scaling Production

### For Production Deployment:
```bash
# Use production compose
docker-compose -f docker-compose.prod.yml up -d

# Add load balancer
docker-compose up -d nginx

# Setup monitoring
docker-compose up -d prometheus grafana
```

## Success Metrics

Your integrated platform should now:
- ✅ Preserve all existing Eliza characters and data
- ✅ Enable autonomous AI influencer operations
- ✅ Provide real-time character management
- ✅ Support multiple monetization streams
- ✅ Offer uncensored content generation
- ✅ Maintain zero downtime during migration

## Next Steps
1. Test character interactions
2. Configure posting schedules
3. Set up brand partnerships
4. Monitor performance metrics
5. Scale AI model capacity as needed

Your autonomous AI influencers are now live and ready to engage!