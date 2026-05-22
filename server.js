// Main Server File for XCreator Pro + Eliza Integration
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const { createServer } = require('http');
const { Server } = require('socket.io');
require('dotenv').config();

// Import services
const ElizaBridge = require('./services/eliza-bridge');
const CharacterManager = require('./services/character-manager');
const ModelRouter = require('./model-router');
const CharacterAPI = require('./api/routes/characters');

// Import utilities
const logger = require('./utils/logger');
const { setupDatabase } = require('./utils/database');
const { setupRedis } = require('./utils/redis');
const { errorHandler } = require('./middleware/error-handler');

class XCreatorServer {
  constructor() {
    // Core objects
    this.app = express();
    this.server = createServer(this.app);
    this.io = new Server(this.server, {
      cors: {
        origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
        methods: ['GET', 'POST']
      }
    });

    // Service placeholders
    this.elizaBridge = null;
    this.characterManager = null;
    this.modelRouter = null;
    this.characterAPI = null;
    this.initialized = false;

    // Non-async middleware first; async service setup deferred to start()
    this.setupMiddleware();
  }

  setupMiddleware() {
    // Security middleware
    this.app.use(helmet({
      contentSecurityPolicy: false,
      crossOriginEmbedderPolicy: false
    }));

    // CORS middleware
    this.app.use(cors({
      origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
      credentials: true
    }));

    // Rate limiting
    const limiter = rateLimit({
      windowMs: 15 * 60 * 1000, // 15 minutes
      max: 1000, // Limit each IP to 1000 requests per windowMs
      message: {
        error: 'Too many requests',
        message: 'Rate limit exceeded. Please try again later.'
      },
      standardHeaders: true,
      legacyHeaders: false
    });
    this.app.use('/api/', limiter);

    // Body parsing middleware
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true, limit: '10mb' }));

    // Logging middleware
    this.app.use((req, res, next) => {
      logger.info(`${req.method} ${req.path}`, {
        ip: req.ip,
        userAgent: req.get('User-Agent'),
        timestamp: new Date().toISOString()
      });
      next();
    });
  }

  async setupServices() {
    try {
      logger.info('🚀 Setting up services...');

      // Initialize database
      await setupDatabase();
      logger.info('✅ Database connected');

      // Initialize Redis
      await setupRedis();
      logger.info('✅ Redis connected');

      // Initialize Model Router
      this.modelRouter = new ModelRouter();
      await this.modelRouter.startHealthChecks();
      logger.info('✅ Model Router initialized');

      // Initialize Eliza Bridge
      this.elizaBridge = new ElizaBridge();
      const elizaConnected = await this.elizaBridge.connectToEliza();
      if (elizaConnected) {
        logger.info('✅ Eliza Bridge connected');
      } else {
        logger.warn('⚠️ Eliza Bridge not connected (Eliza service may not be running)');
      }

      // Initialize Character Manager
      this.characterManager = new CharacterManager(this.elizaBridge, this.modelRouter);
      logger.info('✅ Character Manager initialized');

      // Initialize Character API and attach routes AFTER services ready
      this.characterAPI = new CharacterAPI(this.characterManager, this.elizaBridge);
      logger.info('✅ Character API initialized');

      // Now that services exist, finish remaining setup steps
      this.setupRoutes();
      this.setupSocketIO();
      this.setupErrorHandling();

      this.initialized = true;
      logger.info('✅ All services initialized successfully');

    } catch (error) {
      logger.error('❌ Failed to initialize services:', error);
      process.exit(1);
    }
  }

  setupRoutes() {
    // Prevent crashes if called before CharacterAPI initialization (e.g. stale build)
    if (!this.characterAPI) {
      logger.warn('⚠️ CharacterAPI not initialized when setupRoutes() called; skipping for now');
      return;
    }
    // Health check endpoint
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        services: {
          database: true,
          redis: true,
          eliza: this.elizaBridge ? true : false,
          modelRouter: this.modelRouter ? true : false
        }
      });
    });

    // API routes
    this.app.use('/api', this.characterAPI.setupRoutes());

    // Static files
    this.app.use('/uploads', express.static('uploads'));
    this.app.use('/static', express.static('static'));

    // Root endpoint
    this.app.get('/', (req, res) => {
      res.json({
        name: 'XCreator Pro + Eliza Integration',
        version: '1.0.0',
        description: 'Autonomous AI Influencer Platform',
        status: 'running',
        timestamp: new Date().toISOString()
      });
    });
  }

  setupSocketIO() {
    this.io.on('connection', (socket) => {
      logger.info(`🔌 Client connected: ${socket.id}`);

      // Join character room
      socket.on('join-character', (characterId) => {
        socket.join(`character-${characterId}`);
        logger.info(`👤 Client ${socket.id} joined character room: ${characterId}`);
      });

      // Character interaction
      socket.on('character-interaction', async (data) => {
        try {
          const { characterId, message, context } = data;
          
          const result = await this.characterManager.interact(characterId, message, context);
          
          // Emit response to all clients in the room
          this.io.to(`character-${characterId}`).emit('character-response', {
            characterId,
            response: result.response,
            responseTime: result.responseTime,
            timestamp: result.timestamp
          });

        } catch (error) {
          logger.error('❌ Socket.IO character interaction error:', error);
          socket.emit('error', { message: 'Character interaction failed' });
        }
      });

      // Real-time analytics
      socket.on('subscribe-analytics', (characterId) => {
        socket.join(`analytics-${characterId}`);
        logger.info(`📊 Client ${socket.id} subscribed to analytics: ${characterId}`);
      });

      // Disconnect handler
      socket.on('disconnect', () => {
        logger.info(`🔌 Client disconnected: ${socket.id}`);
      });
    });
  }

  setupErrorHandling() {
    // 404 handler
    this.app.use((req, res) => {
      res.status(404).json({
        error: 'Not Found',
        message: 'The requested resource was not found',
        path: req.path
      });
    });

    // Global error handler
    this.app.use(errorHandler);
  }

  async startAutonomousCharacters() {
    try {
      // Start any existing characters
      const characters = Array.from(this.characterManager.characters.values());
      
      for (const character of characters) {
        if (character.status === 'active') {
          await this.characterManager.startAutonomousOperations(character.id);
          logger.info(`🚀 Started autonomous operations for: ${character.name}`);
        }
      }

      // Schedule periodic character health checks
      setInterval(async () => {
        await this.checkCharacterHealth();
      }, 60000); // Check every minute

    } catch (error) {
      logger.error('❌ Failed to start autonomous characters:', error);
    }
  }

  async checkCharacterHealth() {
    try {
      for (const [characterId, character] of this.characterManager.characters) {
        // Check Eliza agent health
        if (this.elizaBridge) {
          const status = await this.elizaBridge.getAgentStatus(character.elizaAgentId);
          if (status && status.healthy) {
            logger.debug(`✅ Character ${character.name} is healthy`);
          } else {
            logger.warn(`⚠️ Character ${character.name} may be unhealthy`);
          }
        }

        // Emit health status via Socket.IO
        this.io.to(`character-${characterId}`).emit('character-health', {
          characterId,
          status: character.status,
          timestamp: new Date().toISOString()
        });
      }
    } catch (error) {
      logger.error('❌ Character health check failed:', error);
    }
  }

  async start(port = process.env.PORT || 3000) {
    try {
      if (!this.initialized) {
        await this.setupServices();
      } else {
        logger.warn('Server start called but services already initialized');
      }

      this.server.listen(port, () => {
        logger.info(`🚀 XCreator Pro + Eliza server started on port ${port}`);
        logger.info(`📱 Socket.IO server running on port ${port}`);
        logger.info(`🌐 Health check: http://localhost:${port}/health`);
      });

      // Start autonomous characters after short delay
      setTimeout(async () => {
        await this.startAutonomousCharacters();
      }, 5000);

      // Graceful shutdown handlers
      const shutdown = (signal) => {
        logger.info(`🛑 Received ${signal}, shutting down gracefully`);
        this.server.close(() => {
          logger.info('✅ Server closed');
          process.exit(0);
        });
      };
      process.on('SIGTERM', () => shutdown('SIGTERM'));
      process.on('SIGINT', () => shutdown('SIGINT'));

    } catch (error) {
      logger.error('❌ Failed to start server:', error);
      process.exit(1);
    }
  }
}

// Start the server
if (require.main === module) {
  const server = new XCreatorServer();
  server.start();
}

module.exports = XCreatorServer;