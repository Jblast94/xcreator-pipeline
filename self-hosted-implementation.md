# Self-Hosted Model Implementation Guide

## Overview

This guide provides detailed technical implementation for setting up and managing self-hosted AI models including Gemma3, Chatterbox, OpenRouter integration, Hugging Face models, and RunPod proxy services.

## Infrastructure Setup

### Server Requirements
```bash
# Minimum server specifications
CPU: 16+ cores (Intel Xeon or AMD EPYC)
RAM: 64GB+ (128GB recommended for multiple models)
GPU: NVIDIA A100 40GB+ or V100 32GB+
Storage: 2TB+ NVMe SSD
Network: 10Gbps+ dedicated bandwidth
OS: Ubuntu 20.04 LTS or CentOS 8
```

### Docker Environment Setup
```bash
# Install Docker and Docker Compose
sudo apt update
sudo apt install docker.io docker-compose-plugin

# Install NVIDIA Docker support
sudo apt install nvidia-docker2
sudo systemctl restart docker

# Verify GPU access
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

## Model Deployment

### 1. Gemma3 Deployment
```yaml
# docker-compose.gemma3.yml
version: '3.8'
services:
  gemma3:
    image: vllm/vllm:latest
    container_name: gemma3-server
    ports:
      - "8001:8000"
    environment:
      - CUDA_VISIBLE_DEVICES=0
      - MODEL=google/gemma-2b-it
      - DTYPE=float16
      - MAX_MODEL_LEN=4096
      - GPU_MEMORY_UTILIZATION=0.8
      - QUANTIZATION=null
    volumes:
      - ./models/gemma3:/models
      - ./cache:/root/.cache
      - ./logs:/app/logs
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
```

### 2. Chatterbox Deployment
```yaml
# docker-compose.chatterbox.yml
version: '3.8'
services:
  chatterbox:
    image: vllm/vllm:latest
    container_name: chatterbox-server
    ports:
      - "8002:8000"
    environment:
      - CUDA_VISIBLE_DEVICES=1
      - MODEL=chatterbox-ai/chatterbox-7b
      - DTYPE=float16
      - MAX_MODEL_LEN=8192
      - GPU_MEMORY_UTILIZATION=0.9
    volumes:
      - ./models/chatterbox:/models
      - ./cache:/root/.cache
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 3. Hugging Face Model Hub
```yaml
# docker-compose.hf-hub.yml
version: '3.8'
services:
  hf-hub:
    image: huggingface/text-generation-inference:latest
    container_name: hf-hub-server
    ports:
      - "8004:80"
    environment:
      - MODEL_ID=mistralai/Mistral-7B-Instruct-v0.1
      - QUANTIZE=gptq
      - MAX_INPUT_LENGTH=4096
      - MAX_TOTAL_TOKENS=8192
      - MAX_BATCH_PREFILL_TOKENS=4096
      - CUDA_VISIBLE_DEVICES=2
    volumes:
      - ./hf-models:/data
      - ./cache:/root/.cache
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80/health"]
      interval: 60s
      timeout: 30s
      retries: 3
```

## Model Router Implementation

### Router Service
```javascript
// model-router/index.js
const express = require('express');
const axios = require('axios');
const Redis = require('ioredis');
const { RateLimiterRedis } = require('rate-limiter-flexible');

class ModelRouter {
  constructor() {
    this.app = express();
    this.redis = new Redis({
      host: process.env.REDIS_HOST || 'localhost',
      port: process.env.REDIS_PORT || 6379
    });

    this.rateLimiter = new RateLimiterRedis({
      storeClient: this.redis,
      keyPrefix: 'model_rate_limit',
      points: 100, // Number of requests
      duration: 60, // Per 60 seconds
    });

    this.models = this.initializeModels();
    this.setupMiddleware();
    this.setupRoutes();
  }

  initializeModels() {
    return {
      gemma3: {
        name: 'Google Gemma 3',
        endpoint: 'http://gemma3:8000/v1/completions',
        healthEndpoint: 'http://gemma3:8000/health',
        config: {
          model: 'google/gemma-2b-it',
          max_tokens: 2048,
          temperature: 0.7,
          top_p: 0.9
        },
        capabilities: ['text-generation', 'code-generation', 'analysis'],
        loadBalancer: new RoundRobinLoadBalancer(['http://gemma3:8000']),
        isHealthy: true,
        lastHealthCheck: Date.now()
      },

      chatterbox: {
        name: 'Chatterbox AI',
        endpoint: 'http://chatterbox:8000/v1/completions',
        healthEndpoint: 'http://chatterbox:8000/health',
        config: {
          model: 'chatterbox-ai/chatterbox-7b',
          max_tokens: 4096,
          temperature: 0.8,
          top_p: 0.95
        },
        capabilities: ['conversation', 'roleplay', 'character-interaction'],
        loadBalancer: new RoundRobinLoadBalancer(['http://chatterbox:8000']),
        isHealthy: true,
        lastHealthCheck: Date.now()
      },

      hfHub: {
        name: 'Hugging Face Hub',
        endpoint: 'http://hf-hub:80/generate',
        healthEndpoint: 'http://hf-hub:80/health',
        config: {
          temperature: 0.7,
          max_new_tokens: 2048,
          do_sample: true
        },
        capabilities: ['text-generation', 'specialized-tasks'],
        loadBalancer: new RoundRobinLoadBalancer(['http://hf-hub:80']),
        isHealthy: true,
        lastHealthCheck: Date.now()
      }
    };
  }

  setupMiddleware() {
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true }));
    
    // CORS middleware
    this.app.use((req, res, next) => {
      res.header('Access-Control-Allow-Origin', '*');
      res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');
      res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
      next();
    });

    // Rate limiting middleware
    this.app.use(async (req, res, next) => {
      try {
        await this.rateLimiter.consume(req.ip);
        next();
      } catch (rejRes) {
        res.status(429).json({
          error: 'Too Many Requests',
          message: 'Rate limit exceeded. Please try again later.'
        });
      }
    });

    // Logging middleware
    this.app.use((req, res, next) => {
      console.log(`[${new Date().toISOString()}] ${req.method} ${req.path}`);
      next();
    });
  }

  setupRoutes() {
    // Health check endpoint
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        models: Object.keys(this.models).reduce((acc, key) => {
          acc[key] = {
            name: this.models[key].name,
            healthy: this.models[key].isHealthy,
            lastCheck: new Date(this.models[key].lastHealthCheck).toISOString()
          };
          return acc;
        }, {})
      });
    });

    // Model list endpoint
    this.app.get('/models', (req, res) => {
      const modelList = Object.keys(this.models).map(key => ({
        id: key,
        name: this.models[key].name,
        capabilities: this.models[key].capabilities,
        healthy: this.models[key].isHealthy
      }));
      
      res.json({ models: modelList });
    });

    // Main generation endpoint
    this.app.post('/generate', async (req, res) => {
      try {
        const { prompt, model = 'auto', type = 'general', options = {} } = req.body;
        
        if (!prompt) {
          return res.status(400).json({ error: 'Prompt is required' });
        }

        const result = await this.generateContent(prompt, { model, type, ...options });
        res.json(result);
        
      } catch (error) {
        console.error('Generation error:', error);
        res.status(500).json({
          error: 'Generation failed',
          message: error.message
        });
      }
    });

    // Character interaction endpoint
    this.app.post('/character/interact', async (req, res) => {
      try {
        const { character, message, context = {} } = req.body;
        
        if (!character || !message) {
          return res.status(400).json({ error: 'Character and message are required' });
        }

        const result = await this.generateCharacterResponse(character, message, context);
        res.json(result);
        
      } catch (error) {
        console.error('Character interaction error:', error);
        res.status(500).json({
          error: 'Character interaction failed',
          message: error.message
        });
      }
    });

    // Batch generation endpoint
    this.app.post('/batch/generate', async (req, res) => {
      try {
        const { prompts, model = 'auto', type = 'general', options = {} } = req.body;
        
        if (!Array.isArray(prompts) || prompts.length === 0) {
          return res.status(400).json({ error: 'Prompts array is required' });
        }

        if (prompts.length > 10) {
          return res.status(400).json({ error: 'Maximum 10 prompts per batch' });
        }

        const results = await Promise.all(
          prompts.map(prompt => 
            this.generateContent(prompt, { model, type, ...options })
          )
        );

        res.json({ results });
        
      } catch (error) {
        console.error('Batch generation error:', error);
        res.status(500).json({
          error: 'Batch generation failed',
          message: error.message
        });
      }
    });
  }

  async generateContent(prompt, options = {}) {
    const { model = 'auto', type = 'general', temperature, maxTokens, stream = false } = options;

    // Auto-select optimal model
    const selectedModel = model === 'auto' 
      ? this.selectOptimalModel(type, prompt)
      : this.models[model];

    if (!selectedModel) {
      throw new Error(`Model ${model} not found`);
    }

    // Check model health
    if (!selectedModel.isHealthy) {
      const fallbackModel = this.findFallbackModel(selectedModel);
      if (fallbackModel) {
        return this.generateContent(prompt, { ...options, model: Object.keys(this.models).find(key => this.models[key] === fallbackModel) });
      }
      throw new Error('No healthy models available');
    }

    // Prepare request based on model type
    const requestData = this.prepareRequestData(selectedModel, prompt, options);
    const endpoint = selectedModel.loadBalancer.getNextEndpoint();

    try {
      const response = await axios.post(endpoint + '/v1/completions', requestData, {
        timeout: 60000,
        headers: {
          'Content-Type': 'application/json'
        }
      });

      return this.processResponse(selectedModel, response.data);

    } catch (error) {
      console.error(`Model ${selectedModel.name} request failed:`, error.message);
      
      // Mark model as unhealthy and try fallback
      selectedModel.isHealthy = false;
      const fallbackModel = this.findFallbackModel(selectedModel);
      
      if (fallbackModel) {
        return this.generateContent(prompt, { ...options, model: Object.keys(this.models).find(key => this.models[key] === fallbackModel) });
      }
      
      throw new Error('All models unavailable');
    }
  }

  selectOptimalModel(type, prompt) {
    let bestModel = null;
    let bestScore = 0;

    for (const [name, model] of Object.entries(this.models)) {
      if (!model.isHealthy) continue;

      let score = 0;

      // Capability matching
      if (model.capabilities.includes(type)) score += 20;
      
      // Specialized model bonuses
      if (name === 'chatterbox' && type === 'conversation') score += 15;
      if (name === 'gemma3' && type === 'analysis') score += 10;
      if (name === 'hfHub' && type === 'specialized') score += 10;

      // Prompt length consideration
      const promptLength = prompt.length;
      if (promptLength > 1000 && model.config.max_tokens > 2048) score += 5;
      if (promptLength < 500 && model.config.max_tokens <= 1024) score += 3;

      // Model health and performance
      score += 5; // Base score for healthy models

      if (score > bestScore) {
        bestScore = score;
        bestModel = model;
      }
    }

    return bestModel || this.models.gemma3; // Default fallback
  }

  prepareRequestData(model, prompt, options) {
    const baseRequest = {
      model: model.config.model,
      prompt: prompt,
      max_tokens: options.maxTokens || model.config.max_tokens,
      temperature: options.temperature || model.config.temperature,
      top_p: options.top_p || model.config.top_p,
      stream: options.stream || false
    };

    // Model-specific request preparation
    switch (model.name) {
      case 'Hugging Face Hub':
        return {
          inputs: prompt,
          parameters: {
            max_new_tokens: baseRequest.max_tokens,
            temperature: baseRequest.temperature,
            do_sample: true,
            top_p: baseRequest.top_p
          }
        };
      
      default:
        return baseRequest;
    }
  }

  processResponse(model, response) {
    // Model-specific response processing
    switch (model.name) {
      case 'Hugging Face Hub':
        return {
          content: response[0]?.generated_text || '',
          model: model.name,
          usage: {
            prompt_tokens: 0, // HF doesn't provide token count
            completion_tokens: 0,
            total_tokens: 0
          }
        };
      
      default:
        return {
          content: response.choices[0]?.text || response.choices[0]?.message?.content || '',
          model: model.name,
          usage: response.usage || {}
        };
    }
  }

  async startHealthChecks() {
    // Run health checks every 30 seconds
    setInterval(async () => {
      await this.checkModelHealth();
    }, 30000);

    // Initial health check
    await this.checkModelHealth();
  }

  async checkModelHealth() {
    for (const [name, model] of Object.entries(this.models)) {
      try {
        const healthResponse = await axios.get(model.healthEndpoint, {
          timeout: 5000
        });
        
        model.isHealthy = healthResponse.status === 200;
        model.lastHealthCheck = Date.now();
        
        if (!model.isHealthy) {
          console.warn(`Model ${name} health check failed`);
        }
        
      } catch (error) {
        model.isHealthy = false;
        model.lastHealthCheck = Date.now();
        console.error(`Model ${name} health check error:`, error.message);
      }
    }
  }

  start(port = 8080) {
    this.app.listen(port, () => {
      console.log(`Model Router listening on port ${port}`);
      this.startHealthChecks();
    });
  }
}

// Load Balancer Implementation
class RoundRobinLoadBalancer {
  constructor(endpoints) {
    this.endpoints = endpoints;
    this.currentIndex = 0;
  }

  getNextEndpoint() {
    const endpoint = this.endpoints[this.currentIndex];
    this.currentIndex = (this.currentIndex + 1) % this.endpoints.length;
    return endpoint;
  }
}

// Start the service
if (require.main === module) {
  const router = new ModelRouter();
  router.start(process.env.PORT || 8080);
}

module.exports = { ModelRouter, RoundRobinLoadBalancer };
```

## OpenRouter Integration

### OpenRouter Proxy Service
```javascript
// openrouter-integration/index.js
const express = require('express');
const axios = require('axios');

class OpenRouterProxy {
  constructor() {
    this.app = express();
    this.apiKey = process.env.OPENROUTER_API_KEY;
    this.baseURL = 'https://openrouter.ai/api/v1';
    this.setupMiddleware();
    this.setupRoutes();
  }

  setupMiddleware() {
    this.app.use(express.json());
    this.app.use((req, res, next) => {
      res.header('Access-Control-Allow-Origin', '*');
      res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');
      next();
    });
  }

  setupRoutes() {
    // Chat completions endpoint
    this.app.post('/chat/completions', async (req, res) => {
      try {
        const { messages, model = 'openai/gpt-3.5-turbo', ...options } = req.body;
        
        const response = await axios.post(`${this.baseURL}/chat/completions`, {
          model,
          messages,
          ...options
        }, {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            'HTTP-Referer': process.env.APP_URL || 'http://localhost:3000',
            'X-Title': 'XCreator Pro'
          }
        });

        res.json(response.data);
        
      } catch (error) {
        console.error('OpenRouter API error:', error.response?.data || error.message);
        res.status(error.response?.status || 500).json({
          error: 'OpenRouter API error',
          message: error.response?.data?.error?.message || error.message
        });
      }
    });

    // Models endpoint
    this.app.get('/models', async (req, res) => {
      try {
        const response = await axios.get(`${this.baseURL}/models`, {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`
          }
        });

        res.json(response.data);
        
      } catch (error) {
        console.error('OpenRouter models error:', error.response?.data || error.message);
        res.status(error.response?.status || 500).json({
          error: 'Failed to fetch models',
          message: error.message
        });
      }
    });

    // Route-specific endpoints
    this.app.post('/route/:provider', async (req, res) => {
      try {
        const { provider } = req.params;
        const { prompt, ...options } = req.body;
        
        let model;
        switch (provider) {
          case 'openai':
            model = 'openai/gpt-4';
            break;
          case 'anthropic':
            model = 'anthropic/claude-3-sonnet';
            break;
          case 'google':
            model = 'google/gemini-pro';
            break;
          default:
            return res.status(400).json({ error: 'Invalid provider' });
        }

        const response = await axios.post(`${this.baseURL}/chat/completions`, {
          model,
          messages: [{ role: 'user', content: prompt }],
          ...options
        }, {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            'HTTP-Referer': process.env.APP_URL || 'http://localhost:3000',
            'X-Title': 'XCreator Pro'
          }
        });

        res.json({
          provider,
          model,
          response: response.data.choices[0].message.content,
          usage: response.data.usage
        });
        
      } catch (error) {
        console.error(`OpenRouter ${req.params.provider} error:`, error.response?.data || error.message);
        res.status(error.response?.status || 500).json({
          error: `${req.params.provider} API error`,
          message: error.response?.data?.error?.message || error.message
        });
      }
    });
  }

  start(port = 3000) {
    this.app.listen(port, () => {
      console.log(`OpenRouter Proxy listening on port ${port}`);
    });
  }
}

if (require.main === module) {
  const proxy = new OpenRouterProxy();
  proxy.start(3003);
}

module.exports = OpenRouterProxy;
```

## RunPod Integration

### RunPod Proxy Service
```javascript
// runpod-integration/index.js
const express = require('express');
const axios = require('axios');

class RunPodProxy {
  constructor() {
    this.app = express();
    this.apiKey = process.env.RUNPOD_API_KEY;
    this.baseURL = 'https://api.runpod.io/v2';
    this.setupMiddleware();
    this.setupRoutes();
  }

  setupMiddleware() {
    this.app.use(express.json());
    this.app.use((req, res, next) => {
      res.header('Access-Control-Allow-Origin', '*');
      res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');
      next();
    });
  }

  setupRoutes() {
    // Create endpoint
    this.app.post('/create-endpoint', async (req, res) => {
      try {
        const { templateId, name, gpuType, minMemory, maxMemory } = req.body;
        
        const response = await axios.post(`${this.baseURL}/endpoint`, {
          templateId,
          name,
          gpuType,
          minMemory,
          maxMemory
        }, {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`
          }
        });

        res.json(response.data);
        
      } catch (error) {
        console.error('RunPod create endpoint error:', error.response?.data || error.message);
        res.status(error.response?.status || 500).json({
          error: 'Failed to create endpoint',
          message: error.response?.data?.error || error.message
        });
      }
    });

    // Run inference
    this.app.post('/run', async (req, res) => {
      try {
        const { endpointId, input, timeout = 300 } = req.body;
        
        const response = await axios.post(`${this.baseURL}/endpoint/${endpointId}/run`, {
          input,
          timeout
        }, {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`
          }
        });

        res.json({
          jobId: response.data.id,
          status: response.data.status
        });
        
      } catch (error) {
        console.error('RunPod run error:', error.response?.data || error.message);
        res.status(error.response?.status || 500).json({
          error: 'Failed to run job',
          message: error.response?.data?.error || error.message
        });
      }
    });

    // Get job status
    this.app.get('/status/:jobId', async (req, res) => {
      try {
        const { jobId } = req.params;
        
        const response = await axios.get(`${this.baseURL}/status/${jobId}`, {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`
          }
        });

        res.json(response.data);
        
      } catch (error) {
        console.error('RunPod status error:', error.response?.data || error.message);
        res.status(error.response?.status || 500).json({
          error: 'Failed to get job status',
          message: error.response?.data?.error || error.message
        });
      }
    });

    // Stream job output
    this.app.get('/stream/:jobId', async (req, res) => {
      try {
        const { jobId } = req.params;
        
        const response = await axios.get(`${this.baseURL}/stream/${jobId}`, {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`
          },
          responseType: 'stream'
        });

        response.data.pipe(res);
        
      } catch (error) {
        console.error('RunPod stream error:', error.response?.data || error.message);
        res.status(error.response?.status || 500).json({
          error: 'Failed to stream job output',
          message: error.response?.data?.error || error.message
        });
      }
    });

    // Generate content with RunPod
    this.app.post('/generate', async (req, res) => {
      try {
        const { prompt, model = 'mistral-7b', maxTokens = 2048, temperature = 0.7 } = req.body;
        
        // Use pre-configured endpoint for specific models
        const endpointMap = {
          'mistral-7b': process.env.RUNPOD_MISTRAL_ENDPOINT,
          'llama2-13b': process.env.RUNPOD_LLAMA_ENDPOINT,
          'falcon-40b': process.env.RUNPOD_FALCON_ENDPOINT
        };

        const endpointId = endpointMap[model];
        if (!endpointId) {
          return res.status(400).json({ error: 'Model not available on RunPod' });
        }

        const input = {
          prompt,
          max_new_tokens: maxTokens,
          temperature,
          do_sample: true,
          top_p: 0.95
        };

        // Start job
        const jobResponse = await axios.post(`${this.baseURL}/endpoint/${endpointId}/run`, {
          input
        }, {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`
          }
        });

        const jobId = jobResponse.data.id;
        
        // Poll for completion
        const result = await this.pollForCompletion(jobId);
        
        res.json({
          content: result.output,
          model,
          endpoint: endpointId,
          jobId,
          execution_time: result.executionTime
        });
        
      } catch (error) {
        console.error('RunPod generate error:', error.response?.data || error.message);
        res.status(error.response?.status || 500).json({
          error: 'Failed to generate content',
          message: error.response?.data?.error || error.message
        });
      }
    });
  }

  async pollForCompletion(jobId, maxAttempts = 60, interval = 2000) {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const response = await axios.get(`${this.baseURL}/status/${jobId}`, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`
        }
      });

      if (response.data.status === 'COMPLETED') {
        return response.data;
      }

      if (response.data.status === 'FAILED') {
        throw new Error(`Job failed: ${response.data.error}`);
      }

      await new Promise(resolve => setTimeout(resolve, interval));
    }

    throw new Error('Job timeout');
  }

  start(port = 3000) {
    this.app.listen(port, () => {
      console.log(`RunPod Proxy listening on port ${port}`);
    });
  }
}

if (require.main === module) {
  const proxy = new RunPodProxy();
  proxy.start(3005);
}

module.exports = RunPodProxy;
```

## Deployment Configuration

### Production Docker Compose
```yaml
# docker-compose.production.yml
version: '3.8'

services:
  # Reverse Proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - model-router
      - openrouter-proxy
      - runpod-proxy
    restart: unless-stopped

  # Model Router
  model-router:
    build:
      context: ./model-router
      dockerfile: Dockerfile
    environment:
      - NODE_ENV=production
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    depends_on:
      - redis
      - gemma3
      - chatterbox
      - hf-hub
    restart: unless-stopped
    deploy:
      replicas: 2

  # Redis for caching and rate limiting
  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
    restart: unless-stopped

  # PostgreSQL for metadata
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=xcreator_models
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    restart: unless-stopped

  # Monitoring
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana-data:/var/lib/grafana
    restart: unless-stopped

volumes:
  redis-data:
  postgres-data:
  grafana-data:
```

### Nginx Configuration
```nginx
# nginx.conf
upstream model_router {
    server model-router:8080;
}

upstream openrouter_proxy {
    server openrouter-proxy:3003;
}

upstream runpod_proxy {
    server runpod-proxy:3005;
}

server {
    listen 80;
    server_name api.xcreator-pro.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.xcreator-pro.com;
    
    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    # Main API endpoint
    location /api/v1/ {
        proxy_pass http://model_router/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    # OpenRouter proxy
    location /api/openrouter/ {
        proxy_pass http://openrouter_proxy/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
    
    # RunPod proxy
    location /api/runpod/ {
        proxy_pass http://runpod_proxy/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://model_router/health;
        access_log off;
    }
    
    # Static files
    location /static/ {
        alias /var/www/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Monitoring and Alerting

### Prometheus Configuration
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'model-router'
    static_configs:
      - targets: ['model-router:8080']
    metrics_path: /metrics
    scrape_interval: 10s

  - job_name: 'gemma3'
    static_configs:
      - targets: ['gemma3:8000']
    metrics_path: /metrics
    scrape_interval: 30s

  - job_name: 'chatterbox'
    static_configs:
      - targets: ['chatterbox:8000']
    metrics_path: /metrics
    scrape_interval: 30s

  - job_name: 'hf-hub'
    static_configs:
      - targets: ['hf-hub:80']
    metrics_path: /metrics
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
```

### Alert Rules
```yaml
# alert_rules.yml
groups:
  - name: model_health
    rules:
      - alert: ModelDown
        expr: up{job=~"gemma3|chatterbox|hf-hub"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Model {{ $labels.job }} is down"
          description: "Model {{ $labels.job }} has been down for more than 2 minutes"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: HighLatency
        expr: histogram_quantile(0.95, http_request_duration_seconds_bucket) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "95th percentile latency is {{ $value }} seconds"

      - alert: LowGPUUtilization
        expr: nvidia_gpu_utilization_gpu < 20
        for: 10m
        labels:
          severity: info
        annotations:
          summary: "Low GPU utilization"
          description: "GPU utilization is {{ $value }}%"
```

## Security Considerations

### API Security
```javascript
// API authentication middleware
const jwt = require('jsonwebtoken');
const crypto = require('crypto');

class APISecurity {
  constructor() {
    this.jwtSecret = process.env.JWT_SECRET || crypto.randomBytes(64).toString('hex');
  }

  generateAPIKey(userId, tier = 'free') {
    const payload = {
      userId,
      tier,
      iat: Math.floor(Date.now() / 1000),
      exp: Math.floor(Date.now() / 1000) + (365 * 24 * 60 * 60) // 1 year
    };

    return jwt.sign(payload, this.jwtSecret);
  }

  verifyAPIKey(apiKey) {
    try {
      const decoded = jwt.verify(apiKey, this.jwtSecret);
      return {
        valid: true,
        userId: decoded.userId,
        tier: decoded.tier
      };
    } catch (error) {
      return {
        valid: false,
        error: error.message
      };
    }
  }

  generateSecureKey(length = 32) {
    return crypto.randomBytes(length).toString('base64url');
  }

  hashAPIKey(apiKey) {
    return crypto.createHash('sha256').update(apiKey).digest('hex');
  }
}
```

### Content Filtering (Optional)
```javascript
// Optional content filtering for legal compliance
class ContentFilter {
  constructor() {
    this.bannedPatterns = [
      /\b(child|minor|underage)\b/gi,
      /\b(non-consensual|rape|forced)\b/gi,
      /\b(bestiality|animal)\b/gi
    ];
  }

  filterContent(content) {
    let filtered = content;
    let violations = [];

    for (const pattern of this.bannedPatterns) {
      if (pattern.test(content)) {
        violations.push(pattern.source);
        filtered = filtered.replace(pattern, '[FILTERED]');
      }
    }

    return {
      content: filtered,
      violations,
      isClean: violations.length === 0
    };
  }
}
```

## Cost Optimization

### Model Usage Optimization
```javascript
class CostOptimizer {
  constructor() {
    this.modelCosts = {
      'gemma3': { input: 0.0001, output: 0.0002 },
      'chatterbox': { input: 0.00015, output: 0.0003 },
      'openrouter': { input: 0.0005, output: 0.0015 },
      'runpod': { input: 0.0002, output: 0.0004 }
    };
  }

  calculateCost(model, inputTokens, outputTokens) {
    const costs = this.modelCosts[model];
    if (!costs) return 0;

    return (inputTokens * costs.input + outputTokens * costs.output) / 1000;
  }

  selectCostEffectiveModel(prompt, requirements) {
    const models = Object.keys(this.modelCosts);
    let bestModel = null;
    let bestValue = Infinity;

    for (const model of models) {
      const estimatedTokens = this.estimateTokens(prompt);
      const cost = this.calculateCost(model, estimatedTokens, estimatedTokens * 0.7);
      const quality = this.getModelQuality(model, requirements);
      const value = cost / quality;

      if (value < bestValue) {
        bestValue = value;
        bestModel = model;
      }
    }

    return bestModel;
  }

  estimateTokens(text) {
    // Rough estimation: 1 token ≈ 4 characters
    return Math.ceil(text.length / 4);
  }

  getModelQuality(model, requirements) {
    const qualityMap = {
      'gemma3': { general: 0.8, analysis: 0.9, creative: 0.7 },
      'chatterbox': { general: 0.7, conversation: 0.95, creative: 0.8 },
      'openrouter': { general: 0.9, analysis: 0.95, creative: 0.85 },
      'runpod': { general: 0.75, speed: 0.9, batch: 0.95 }
    };

    return qualityMap[model]?.[requirements.type] || 0.5;
  }
}
```

## Deployment Scripts

### Deployment Automation
```bash
#!/bin/bash
# deploy.sh - Production deployment script

set -e

echo "Starting deployment..."

# Check prerequisites
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "Error: $1 is not installed"
        exit 1
    fi
}

check_command docker
check_command docker-compose
check_command git

# Environment setup
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
    exit 1
fi

# Pull latest changes
echo "Pulling latest changes..."
git pull origin main

# Build and start services
echo "Building and starting services..."
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 30

# Health check
echo "Performing health checks..."
for service in gemma3 chatterbox hf-hub; do
    if docker-compose -f docker-compose.production.yml ps $service | grep -q "healthy"; then
        echo "✅ $service is healthy"
    else
        echo "❌ $service is not healthy"
        exit 1
    fi
done

# Setup monitoring
echo "Setting up monitoring..."
docker-compose -f docker-compose.production.yml exec -T postgres psql -U postgres -d xcreator_models < ./setup-monitoring.sql

echo "Deployment completed successfully!"
echo "Services are available at:"
echo "- API: https://api.xcreator-pro.com"
echo "- Monitoring: https://monitor.xcreator-pro.com"
echo "- Grafana: https://grafana.xcreator-pro.com"
```

## Conclusion

This self-hosted implementation provides a robust, scalable, and cost-effective solution for running AI models. The architecture supports multiple models, intelligent routing, load balancing, and comprehensive monitoring while maintaining high performance and reliability.

Key benefits:
- **Cost Control**: No per-token fees from major providers
- **Performance**: Optimized for your specific use case
- **Privacy**: All data stays on your infrastructure
- **Flexibility**: Easy to add new models and features
- **Scalability**: Horizontal scaling design

The implementation includes proper error handling, monitoring, security, and deployment automation to ensure production-ready operation.