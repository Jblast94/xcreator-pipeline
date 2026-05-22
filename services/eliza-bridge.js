// Eliza Bridge Service - Wraps Eliza Character Generator
const express = require('express');
const axios = require('axios');
const cors = require('cors');
const logger = require('../utils/logger');

class ElizaBridge {
  constructor(elizaBaseUrl = null) {
    this.elizaBaseUrl = elizaBaseUrl || process.env.ELIZA_BASE_URL || 'http://localhost:4001';
    this.connected = false;
    this.app = express();
    this.setupMiddleware();
    this.setupRoutes();
    logger.info('ElizaBridge initialized', { elizaBaseUrl: this.elizaBaseUrl });
  }

  setupMiddleware() {
    this.app.use(cors());
    this.app.use(express.json({ limit: '10mb' }));
  }

  setupRoutes() {
    // Health check
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        elizaConnected: this.connected,
        elizaBaseUrl: this.elizaBaseUrl,
        timestamp: new Date().toISOString()
      });
    });

    // Proxy to Eliza's generate character endpoint
    this.app.post('/generate-character', async (req, res) => {
      try {
        const { prompt, model, apiKey } = req.body;
        
        logger.info('Generating character via Eliza', { promptLength: prompt?.length });

        const response = await axios.post(
          `${this.elizaBaseUrl}/api/generate-character`,
          { prompt, model },
          {
            headers: {
              'Content-Type': 'application/json',
              'X-API-Key': apiKey
            },
            timeout: 60000 // 60 second timeout
          }
        );

        res.json(response.data);
      } catch (error) {
        logger.error('Failed to generate character', { error: error.message });
        res.status(error.response?.status || 500).json({
          error: error.message,
          details: error.response?.data
        });
      }
    });

    // Proxy to Eliza's refine character endpoint
    this.app.post('/refine-character', async (req, res) => {
      try {
        const { prompt, model, currentCharacter, apiKey } = req.body;
        
        logger.info('Refining character via Eliza', { characterName: currentCharacter?.name });

        const response = await axios.post(
          `${this.elizaBaseUrl}/api/refine-character`,
          { prompt, model, currentCharacter },
          {
            headers: {
              'Content-Type': 'application/json',
              'X-API-Key': apiKey
            },
            timeout: 60000
          }
        );

        res.json(response.data);
      } catch (error) {
        logger.error('Failed to refine character', { error: error.message });
        res.status(error.response?.status || 500).json({
          error: error.message,
          details: error.response?.data
        });
      }
    });

    // Proxy to Eliza's process files endpoint
    this.app.post('/process-files', async (req, res) => {
      try {
        const formData = req.body;
        
        logger.info('Processing files via Eliza');

        const response = await axios.post(
          `${this.elizaBaseUrl}/api/process-files`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data'
            },
            timeout: 120000 // 2 minute timeout for file processing
          }
        );

        res.json(response.data);
      } catch (error) {
        logger.error('Failed to process files', { error: error.message });
        res.status(error.response?.status || 500).json({
          error: error.message,
          details: error.response?.data
        });
      }
    });
  }

  // Connect to Eliza service
  async connectToEliza() {
    try {
      logger.info('Attempting to connect to Eliza service', { url: this.elizaBaseUrl });
      
      const response = await axios.get(`${this.elizaBaseUrl}/`, {
        timeout: 5000
      });

      this.connected = true;
      logger.info('Successfully connected to Eliza service');
      return true;

    } catch (error) {
      this.connected = false;
      logger.warn('Failed to connect to Eliza service', {
        error: error.message,
        note: 'Eliza service may not be running yet. Bridge will operate in fallback mode.'
      });
      return false;
    }
  }

  // Sync character to Eliza format
  async syncCharacter(character) {
    try {
      // Convert XCreator character format to Eliza JSON format
      const elizaCharacter = {
        name: character.name,
        clients: character.eliza?.clients || [],
        modelProvider: character.eliza?.modelProvider || 'openrouter',
        settings: {
          secrets: {},
          voice: {
            model: character.voice?.model || ''
          }
        },
        plugins: character.eliza?.plugins || [],
        bio: character.personality?.bio || [],
        lore: character.personality?.lore || [],
        knowledge: character.personality?.knowledge || [],
        messageExamples: character.personality?.messageExamples || [],
        postExamples: character.personality?.postExamples || [],
        topics: character.personality?.topics || [],
        style: {
          all: character.personality?.style?.all || [],
          chat: character.personality?.style?.chat || [],
          post: character.personality?.style?.post || []
        },
        adjectives: character.personality?.adjectives || [],
        people: character.personality?.people || []
      };

      logger.debug('Character synced to Eliza format', { name: character.name });
      return elizaCharacter;

    } catch (error) {
      logger.error('Failed to sync character', { error: error.message });
      throw error;
    }
  }

  // Interact with Eliza agent (for future Phase 2)
  async interact(agentId, message, context = {}) {
    try {
      // This is a placeholder for Phase 2 when Eliza agents are fully integrated
      logger.debug('Character interaction (mock)', { agentId, message: message.substring(0, 50) });

      return {
        text: `Response from Eliza agent ${agentId}: Received "${message}". (Phase 1 mock response)`,
        confidence: 0.8,
        source: 'eliza-mock'
      };

    } catch (error) {
      logger.error('Failed to interact with Eliza agent', { error: error.message });
      throw error;
    }
  }

  // Get agent status (for future Phase 2)
  async getAgentStatus(agentId) {
    try {
      logger.debug('Getting agent status (mock)', { agentId });

      return {
        agentId,
        healthy: true,
        status: 'running',
        lastActive: new Date().toISOString()
      };

    } catch (error) {
      logger.error('Failed to get agent status', { error: error.message });
      return null;
    }
  }

  // Start the bridge service
  start(port = 3004) {
    return new Promise((resolve) => {
      this.server = this.app.listen(port, () => {
        logger.info(`🌉 Eliza Bridge started on port ${port}`);
        resolve();
      });
    });
  }

  // Stop the bridge service
  stop() {
    if (this.server) {
      this.server.close();
      logger.info('Eliza Bridge stopped');
    }
  }
}

// Export both class and instance
module.exports = ElizaBridge;

// If run directly, start the bridge service
if (require.main === module) {
  const bridge = new ElizaBridge();
  const port = process.env.PORT || 3004;
  
  bridge.connectToEliza().then(() => {
    bridge.start(port);
  });
}
