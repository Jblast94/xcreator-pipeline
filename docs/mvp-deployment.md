# XCreator Pro MVP Deployment Guide

## Overview

This guide covers deploying the Minimum Viable Product (MVP) of XCreator Pro + Eliza Integration for testing and continued development.

## Architecture

### Phase 1 MVP Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Main App      │───▶│  Eliza Bridge   │───▶│ Eliza CharGen   │
│   (Port 3000)   │    │   (Port 3004)   │    │   (Port 4001)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                      │
         ▼                      ▼
┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │     Redis       │
│   (Port 5432)   │    │   (Port 6379)   │
└─────────────────┘    └─────────────────┘
```

### Services

1. **Main Application** (`app`) - XCreator Pro Express server
2. **Eliza Character Generator** (`eliza`) - Character generation service
3. **Eliza Bridge** (`eliza-bridge`) - API proxy between app and Eliza
4. **PostgreSQL** - Database for characters, conversations, analytics
5. **Redis** - Caching and session management

## Prerequisites

### Required Software

- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Git** for repository management
- **Node.js 18+** (for local development)

### System Requirements

**Minimum (Phase 1 MVP)**:
- CPU: 2 cores
- RAM: 4GB
- Storage: 20GB
- Network: 100Mbps

**Recommended**:
- CPU: 4 cores
- RAM: 8GB
- Storage: 50GB
- Network: 1Gbps

### Required Environment Variables

Create a `.env` file (already created) with:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@postgres:5432/xcreator_eliza

# Redis
REDIS_URL=redis://redis:6379

# Application
NODE_ENV=development
PORT=3000
JWT_SECRET=your-super-secret-jwt-key

# n8n Integration
N8N_API_TOKEN=your-n8n-token

# Eliza
ELIZA_BASE_URL=http://eliza:4001
```

## Quick Start

### 1. Install Dependencies

```bash
cd /workspaces/XCreator-Pro-Eliza
npm install
```

### 2. Start MVP Services

```bash
# Start all Phase 1 services
docker-compose -f docker-compose.mvp.yml up -d

# Check service status
docker-compose -f docker-compose.mvp.yml ps

# View logs
docker-compose -f docker-compose.mvp.yml logs -f
```

### 3. Verify Deployment

```bash
# Health check - Main app
curl http://localhost:3000/health

# Health check - Eliza service
curl http://localhost:4001

# Health check - Eliza Bridge
curl http://localhost:3004/health

# List available models
curl http://localhost:3000/api/models
```

### 4. Create Test Character

```bash
curl -X POST http://localhost:3000/api/characters \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Character",
    "displayName": "Test - MVP Character",
    "personality": {
      "traits": ["friendly", "helpful", "knowledgeable"],
      "background": "AI assistant for testing MVP functionality"
    },
    "settings": {
      "visibility": "public",
      "autoResponse": false
    }
  }'
```

### 5. Test Character Interaction

```bash
# Replace {CHARACTER_ID} with the ID from step 4
curl -X POST http://localhost:3000/api/characters/{CHARACTER_ID}/interact \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello! How are you today?",
    "context": {
      "platform": "web",
      "username": "tester"
    }
  }'
```

## API Endpoints

### Character Management

- `GET /api/characters` - List all characters
- `POST /api/characters` - Create new character
- `GET /api/characters/:id` - Get character details
- `PUT /api/characters/:id` - Update character
- `DELETE /api/characters/:id` - Delete character

### Character Interaction

- `POST /api/characters/:id/interact` - Interact with character
- `POST /api/characters/:id/start` - Start autonomous operations
- `POST /api/characters/:id/stop` - Stop autonomous operations

### Analytics

- `GET /api/characters/:id/analytics` - Get character analytics
- `GET /api/usage` - Platform usage statistics
- `GET /api/revenue` - Revenue analytics (mock in Phase 1)

### Models

- `GET /api/models` - List available AI models

## Phase 1 Features

### ✅ Implemented

- Character CRUD operations
- Basic character interactions (mock responses)
- Database persistence (PostgreSQL)
- Caching layer (Redis)
- Health monitoring
- API documentation
- Docker containerization
- Eliza Character Generator integration
- n8n API token configuration

### ⚠️ Mock/Limited

- AI model responses (returns mock text)
- Character interactions (pre-scripted responses)
- Analytics (basic counters)
- Autonomous operations (status tracking only)

### ❌ Not Yet Implemented

- Real AI model integration (GPU services)
- Voice synthesis
- Avatar generation
- Social media integrations
- Advanced monitoring (Prometheus/Grafana)
- Production authentication/authorization

## Upgrading to Phase 2

### Phase 2 Additions

1. **Eliza Agent Integration**
   - Real character agents with Eliza framework
   - Character personality-driven responses
   - Conversation context and memory

2. **OpenRouter API**
   - Access to multiple AI models
   - Fallback model routing
   - Cost optimization

3. **Basic Monitoring**
   - Prometheus metrics collection
   - Grafana dashboards
   - Performance tracking

### Migration Steps

```bash
# Stop Phase 1 services
docker-compose -f docker-compose.mvp.yml down

# Update environment variables
# Add OPENROUTER_API_KEY to .env

# Start Phase 2 services
docker-compose -f docker-compose.phase2.yml up -d
```

## Upgrading to Phase 3 (Full Platform)

### Phase 3 Additions

1. **RunPod GPU Integration**
   - Serverless GPU access
   - On-demand model deployment
   - Cost-effective scaling

2. **Self-Hosted AI Models** (Optional)
   - Gemma3, Chatterbox, Mistral
   - Requires NVIDIA GPU

3. **Advanced Features**
   - Voice synthesis (ElevenLabs)
   - Image generation
   - Social media automation
   - Revenue tracking
   - Advanced analytics

### Migration Steps

```bash
# Add RunPod API key to .env
RUNPOD_API_KEY=your-runpod-key

# Start full platform
docker-compose -f docker-compose.eliza.yml up -d
```

## Troubleshooting

### Services Won't Start

```bash
# Check Docker status
docker ps -a

# View service logs
docker-compose -f docker-compose.mvp.yml logs app
docker-compose -f docker-compose.mvp.yml logs eliza
docker-compose -f docker-compose.mvp.yml logs postgres

# Restart specific service
docker-compose -f docker-compose.mvp.yml restart app
```

### Database Connection Issues

```bash
# Check database status
docker-compose -f docker-compose.mvp.yml exec postgres pg_isready -U postgres

# Access database directly
docker-compose -f docker-compose.mvp.yml exec postgres psql -U postgres -d xcreator_eliza

# View database logs
docker-compose -f docker-compose.mvp.yml logs postgres
```

### Redis Connection Issues

```bash
# Check Redis status
docker-compose -f docker-compose.mvp.yml exec redis redis-cli ping

# View Redis logs
docker-compose -f docker-compose.mvp.yml logs redis
```

### Port Conflicts

If ports are already in use:

```bash
# Check what's using the port
sudo lsof -i :3000
sudo lsof -i :5432

# Kill the process or change ports in docker-compose.mvp.yml
```

### Eliza Service Not Responding

```bash
# Check Eliza logs
docker-compose -f docker-compose.mvp.yml logs eliza

# Restart Eliza service
docker-compose -f docker-compose.mvp.yml restart eliza

# Access Eliza container
docker-compose -f docker-compose.mvp.yml exec eliza sh
```

### Application Errors

```bash
# View application logs
docker-compose -f docker-compose.mvp.yml logs -f app

# Check logs directory
ls -la logs/
tail -f logs/combined.log
tail -f logs/error.log
```

## Development Workflow

### Local Development

```bash
# Install dependencies
npm install

# Start infrastructure (database, redis)
docker-compose -f docker-compose.mvp.yml up -d postgres redis eliza

# Run app locally
npm run dev

# Access app at http://localhost:3000
```

### Making Changes

1. Edit source files
2. Rebuild Docker image: `docker-compose -f docker-compose.mvp.yml build app`
3. Restart service: `docker-compose -f docker-compose.mvp.yml up -d app`

### Database Migrations

```bash
# Access database
docker-compose -f docker-compose.mvp.yml exec postgres psql -U postgres -d xcreator_eliza

# Run SQL scripts
docker-compose -f docker-compose.mvp.yml exec postgres psql -U postgres -d xcreator_eliza -f /docker-entrypoint-initdb.d/init.sql
```

## Monitoring

### Check Service Health

```bash
# Main app
curl http://localhost:3000/health

# Eliza
curl http://localhost:4001

# Eliza Bridge
curl http://localhost:3004/health
```

### View Metrics

```bash
# Character count
curl http://localhost:3000/api/characters | jq '.count'

# Usage statistics
curl http://localhost:3000/api/usage | jq

# Model status
curl http://localhost:3000/api/models | jq
```

### Resource Usage

```bash
# View container stats
docker stats

# View logs size
du -sh logs/

# Clean up logs
rm logs/*.log
```

## Security Notes

### Phase 1 (Development)

⚠️ **WARNING**: Phase 1 is for development/testing only!

- Default database password (`password`)
- No authentication/authorization
- No rate limiting on character creation
- Public API endpoints
- No SSL/TLS

### Production Checklist

Before deploying to production:

- [ ] Change all default passwords
- [ ] Implement authentication (JWT)
- [ ] Add API key management
- [ ] Enable rate limiting
- [ ] Configure SSL/TLS (Let's Encrypt)
- [ ] Set secure JWT_SECRET
- [ ] Restrict ALLOWED_ORIGINS
- [ ] Enable database backups
- [ ] Configure firewall rules
- [ ] Set up monitoring alerts
- [ ] Review and update CORS settings

## Performance Tuning

### Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX idx_characters_status ON characters(status);
CREATE INDEX idx_conversations_character ON conversations(character_id);
CREATE INDEX idx_conversations_created ON conversations(created_at);
```

### Redis Optimization

```bash
# Adjust Redis memory
docker-compose -f docker-compose.mvp.yml exec redis redis-cli CONFIG SET maxmemory 256mb
docker-compose -f docker-compose.mvp.yml exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### Application Scaling

```bash
# Scale app instances
docker-compose -f docker-compose.mvp.yml up -d --scale app=3

# Use nginx for load balancing (Phase 3)
```

## Backup and Recovery

### Database Backup

```bash
# Create backup
docker-compose -f docker-compose.mvp.yml exec postgres pg_dump -U postgres xcreator_eliza > backup_$(date +%Y%m%d).sql

# Restore backup
cat backup_20251114.sql | docker-compose -f docker-compose.mvp.yml exec -T postgres psql -U postgres xcreator_eliza
```

### Redis Backup

```bash
# Save Redis snapshot
docker-compose -f docker-compose.mvp.yml exec redis redis-cli BGSAVE

# Copy snapshot
docker cp $(docker-compose -f docker-compose.mvp.yml ps -q redis):/data/dump.rdb ./redis_backup.rdb
```

## Next Steps

1. ✅ **Phase 1 Complete** - Test MVP functionality
2. **Integrate Eliza Agents** - Connect real AI character agents
3. **Add OpenRouter** - Enable external AI model access
4. **Implement RunPod** - Add GPU-powered AI generation
5. **Deploy Monitoring** - Set up Prometheus/Grafana
6. **Production Hardening** - Security, auth, SSL
7. **Scale Infrastructure** - Load balancing, CDN
8. **Launch Platform** - Go live with full features

## Support

### Documentation

- API Documentation: `/api-docs` (when implemented)
- Architecture: `design.md`
- Integration Guide: `eliza-integration-plan.md`

### Issues

Report issues at: https://github.com/bbj4t/XCreator-Pro-Eliza/issues

### Community

- Discord: (to be created)
- Twitter: @xcreator_pro (placeholder)

---

**Built with ❤️ for the future of autonomous AI influencers**
