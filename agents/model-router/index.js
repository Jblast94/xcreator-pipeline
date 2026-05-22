// Model Router Service - Phase 1 Mock Implementation
const logger = require('../utils/logger');

class ModelRouter {
  constructor() {
    this.models = new Map();
    this.healthCheckInterval = null;
    this.initializeModels();
    logger.info('ModelRouter initialized (Phase 1 - Mock Mode)');
  }

  initializeModels() {
    // Mock model configurations for Phase 1
    this.models.set('gemma3', {
      name: 'gemma3',
      endpoint: 'http://gemma3:8000/v1/completions',
      status: 'mock',
      capabilities: ['text-generation', 'analysis', 'code'],
      priority: 1,
      responseTime: 0
    });

    this.models.set('chatterbox', {
      name: 'chatterbox',
      endpoint: 'http://chatterbox:8000/v1/completions',
      status: 'mock',
      capabilities: ['conversation', 'roleplay', 'character-interaction'],
      priority: 2,
      responseTime: 0
    });

    this.models.set('openrouter', {
      name: 'openrouter',
      endpoint: 'https://openrouter.ai/api/v1/chat/completions',
      status: 'mock',
      capabilities: ['all'],
      priority: 3,
      fallback: true,
      responseTime: 0
    });

    this.models.set('runpod', {
      name: 'runpod',
      endpoint: 'http://runpod-proxy:3000',
      status: 'mock',
      capabilities: ['all'],
      priority: 4,
      fallback: true,
      responseTime: 0
    });

    logger.info('Mock models initialized', {
      models: Array.from(this.models.keys())
    });
  }

  // Start health checks for models (no-op in Phase 1)
  async startHealthChecks() {
    logger.info('Health checks started (mock mode)');
    // In Phase 1, we just log that health checks would run
    // In Phase 2/3, this will actually ping the model endpoints
    return true;
  }

  // Get available models
  getAvailableModels() {
    return Array.from(this.models.values()).map(model => ({
      name: model.name,
      status: model.status,
      capabilities: model.capabilities,
      priority: model.priority,
      responseTime: model.responseTime
    }));
  }

  // Route a request to the best available model
  async route(request, capability = 'text-generation') {
    try {
      logger.debug('Routing request', { capability });

      // For Phase 1, return mock response
      const mockResponse = {
        model: 'mock-model',
        text: this.generateMockResponse(request),
        confidence: 0.85,
        responseTime: Math.random() * 100 + 50, // 50-150ms mock time
        source: 'mock',
        metadata: {
          phase: 'mvp-phase-1',
          note: 'This is a mock response. Real AI models will be available in Phase 2/3.'
        }
      };

      logger.info('Generated mock response', {
        length: mockResponse.text.length,
        responseTime: `${mockResponse.responseTime}ms`
      });

      return mockResponse;

    } catch (error) {
      logger.error('Failed to route request', { error: error.message });
      throw error;
    }
  }

  // Generate a mock response based on request
  generateMockResponse(request) {
    const { prompt, type = 'general', context = {} } = request;

    // Different mock responses based on type
    switch (type) {
      case 'character-interaction':
        return `Thank you for your message! I'm currently in MVP testing mode. Your input was: "${prompt}". In the full version, I'll provide personalized AI-generated responses based on my character personality.`;

      case 'content-generation':
        return `Here's a mock content piece based on your prompt: "${prompt}". This would be an AI-generated post, tweet, or article tailored to your character's style and audience.`;

      case 'analysis':
        return `Analysis of "${prompt}": This appears to be a request for content analysis. In the production version, I'll provide detailed insights, sentiment analysis, and recommendations.`;

      case 'code':
        return `// Mock code generation\n// Prompt: ${prompt}\n\nfunction mockFunction() {\n  console.log('This is mock code generation');\n  return 'In production, real code will be generated';\n}`;

      default:
        return `Mock response to: "${prompt}". This is a placeholder response for Phase 1 MVP testing. Real AI model responses will be available once the full infrastructure is deployed.`;
    }
  }

  // Generate text using specified model
  async generateText(prompt, options = {}) {
    try {
      const {
        model = 'auto',
        maxTokens = 500,
        temperature = 0.7,
        capability = 'text-generation'
      } = options;

      logger.debug('Generating text', { prompt: prompt.substring(0, 50), model });

      return await this.route({
        prompt,
        type: capability,
        maxTokens,
        temperature
      }, capability);

    } catch (error) {
      logger.error('Failed to generate text', { error: error.message });
      throw error;
    }
  }

  // Chat completion (mock)
  async chatCompletion(messages, options = {}) {
    try {
      const prompt = messages.map(m => `${m.role}: ${m.content}`).join('\n');
      
      logger.debug('Chat completion', { messageCount: messages.length });

      return await this.generateText(prompt, {
        ...options,
        capability: 'conversation'
      });

    } catch (error) {
      logger.error('Failed to complete chat', { error: error.message });
      throw error;
    }
  }

  // Get model status
  getModelStatus(modelName) {
    const model = this.models.get(modelName);
    if (!model) {
      return { status: 'not-found', message: 'Model not found' };
    }

    return {
      name: model.name,
      status: model.status,
      endpoint: model.endpoint,
      capabilities: model.capabilities,
      priority: model.priority,
      responseTime: model.responseTime,
      lastCheck: new Date().toISOString()
    };
  }

  // Get all model statuses
  getAllModelStatuses() {
    const statuses = {};
    for (const [name, model] of this.models) {
      statuses[name] = {
        status: model.status,
        capabilities: model.capabilities,
        priority: model.priority,
        responseTime: model.responseTime
      };
    }
    return statuses;
  }

  // Stop health checks
  stopHealthChecks() {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
      this.healthCheckInterval = null;
      logger.info('Health checks stopped');
    }
  }
}

module.exports = ModelRouter;
