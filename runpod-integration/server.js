// RunPod Integration Service - GPU Proxy
const express = require('express');
const axios = require('axios');
const cors = require('cors');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3005;
const RUNPOD_API_KEY = process.env.RUNPOD_API_KEY;

// Middleware
app.use(cors());
app.use(express.json({ limit: '50mb' }));

// Logging middleware
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
  next();
});

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'runpod-proxy',
    runpodConfigured: !!RUNPOD_API_KEY,
    timestamp: new Date().toISOString()
  });
});

// List available RunPod endpoints
app.get('/endpoints', async (req, res) => {
  try {
    if (!RUNPOD_API_KEY) {
      return res.status(503).json({
        error: 'RunPod API key not configured'
      });
    }

    const response = await axios.get('https://api.runpod.io/v2/endpoints', {
      headers: {
        'Authorization': `Bearer ${RUNPOD_API_KEY}`,
        'Content-Type': 'application/json'
      }
    });

    res.json({
      success: true,
      endpoints: response.data
    });

  } catch (error) {
    console.error('Failed to list endpoints:', error.message);
    res.status(error.response?.status || 500).json({
      error: error.message,
      details: error.response?.data
    });
  }
});

// Text generation endpoint
app.post('/generate', async (req, res) => {
  try {
    if (!RUNPOD_API_KEY) {
      return res.status(503).json({
        error: 'RunPod API key not configured',
        message: 'Please set RUNPOD_API_KEY in environment variables'
      });
    }

    const {
      prompt,
      endpointId,
      maxTokens = 500,
      temperature = 0.7,
      model = 'default'
    } = req.body;

    if (!prompt) {
      return res.status(400).json({
        error: 'Prompt is required'
      });
    }

    if (!endpointId) {
      return res.status(400).json({
        error: 'RunPod endpoint ID is required',
        message: 'Specify which RunPod endpoint to use for generation'
      });
    }

    console.log('Generating text via RunPod:', {
      endpointId,
      promptLength: prompt.length,
      model
    });

    // Call RunPod serverless endpoint
    const response = await axios.post(
      `https://api.runpod.ai/v2/${endpointId}/runsync`,
      {
        input: {
          prompt,
          max_tokens: maxTokens,
          temperature,
          model
        }
      },
      {
        headers: {
          'Authorization': `Bearer ${RUNPOD_API_KEY}`,
          'Content-Type': 'application/json'
        },
        timeout: 60000 // 60 second timeout
      }
    );

    res.json({
      success: true,
      data: response.data,
      metadata: {
        endpointId,
        model,
        timestamp: new Date().toISOString()
      }
    });

  } catch (error) {
    console.error('RunPod generation error:', error.message);
    res.status(error.response?.status || 500).json({
      error: error.message,
      details: error.response?.data
    });
  }
});

// Chat completion endpoint
app.post('/chat', async (req, res) => {
  try {
    if (!RUNPOD_API_KEY) {
      return res.status(503).json({
        error: 'RunPod API key not configured'
      });
    }

    const {
      messages,
      endpointId,
      maxTokens = 500,
      temperature = 0.7,
      model = 'default'
    } = req.body;

    if (!messages || !Array.isArray(messages)) {
      return res.status(400).json({
        error: 'Messages array is required'
      });
    }

    if (!endpointId) {
      return res.status(400).json({
        error: 'RunPod endpoint ID is required'
      });
    }

    // Convert messages to prompt format
    const prompt = messages.map(m => `${m.role}: ${m.content}`).join('\n');

    console.log('Chat completion via RunPod:', {
      endpointId,
      messageCount: messages.length,
      model
    });

    const response = await axios.post(
      `https://api.runpod.ai/v2/${endpointId}/runsync`,
      {
        input: {
          prompt,
          max_tokens: maxTokens,
          temperature,
          model
        }
      },
      {
        headers: {
          'Authorization': `Bearer ${RUNPOD_API_KEY}`,
          'Content-Type': 'application/json'
        },
        timeout: 60000
      }
    );

    res.json({
      success: true,
      data: response.data,
      metadata: {
        endpointId,
        model,
        messageCount: messages.length,
        timestamp: new Date().toISOString()
      }
    });

  } catch (error) {
    console.error('RunPod chat error:', error.message);
    res.status(error.response?.status || 500).json({
      error: error.message,
      details: error.response?.data
    });
  }
});

// Image generation endpoint
app.post('/image', async (req, res) => {
  try {
    if (!RUNPOD_API_KEY) {
      return res.status(503).json({
        error: 'RunPod API key not configured'
      });
    }

    const {
      prompt,
      endpointId,
      width = 512,
      height = 512,
      steps = 20
    } = req.body;

    if (!prompt) {
      return res.status(400).json({
        error: 'Prompt is required'
      });
    }

    if (!endpointId) {
      return res.status(400).json({
        error: 'RunPod endpoint ID is required'
      });
    }

    console.log('Generating image via RunPod:', {
      endpointId,
      promptLength: prompt.length,
      dimensions: `${width}x${height}`
    });

    const response = await axios.post(
      `https://api.runpod.ai/v2/${endpointId}/runsync`,
      {
        input: {
          prompt,
          width,
          height,
          num_inference_steps: steps
        }
      },
      {
        headers: {
          'Authorization': `Bearer ${RUNPOD_API_KEY}`,
          'Content-Type': 'application/json'
        },
        timeout: 120000 // 2 minute timeout for image generation
      }
    );

    res.json({
      success: true,
      data: response.data,
      metadata: {
        endpointId,
        dimensions: `${width}x${height}`,
        timestamp: new Date().toISOString()
      }
    });

  } catch (error) {
    console.error('RunPod image generation error:', error.message);
    res.status(error.response?.status || 500).json({
      error: error.message,
      details: error.response?.data
    });
  }
});

// Check job status
app.get('/status/:jobId', async (req, res) => {
  try {
    if (!RUNPOD_API_KEY) {
      return res.status(503).json({
        error: 'RunPod API key not configured'
      });
    }

    const { jobId } = req.params;
    const { endpointId } = req.query;

    if (!endpointId) {
      return res.status(400).json({
        error: 'Endpoint ID is required as query parameter'
      });
    }

    const response = await axios.get(
      `https://api.runpod.ai/v2/${endpointId}/status/${jobId}`,
      {
        headers: {
          'Authorization': `Bearer ${RUNPOD_API_KEY}`
        }
      }
    );

    res.json({
      success: true,
      data: response.data
    });

  } catch (error) {
    console.error('Failed to check job status:', error.message);
    res.status(error.response?.status || 500).json({
      error: error.message,
      details: error.response?.data
    });
  }
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);
  res.status(500).json({
    error: 'Internal server error',
    message: err.message
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 RunPod Proxy Service started on port ${PORT}`);
  console.log(`📡 RunPod API configured: ${!!RUNPOD_API_KEY}`);
  console.log(`🏥 Health check: http://localhost:${PORT}/health`);
});

module.exports = app;
