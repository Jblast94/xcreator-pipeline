// Character API Routes
const express = require('express');
const { asyncHandler } = require('../../middleware/error-handler');
const logger = require('../../utils/logger');

class CharacterAPI {
  constructor(characterManager, elizaBridge) {
    this.characterManager = characterManager;
    this.elizaBridge = elizaBridge;
    this.router = express.Router();
    logger.info('CharacterAPI initialized');
  }

  setupRoutes() {
    // List all characters
    this.router.get('/characters', asyncHandler(async (req, res) => {
      const filters = {
        status: req.query.status,
        visibility: req.query.visibility
      };

      const characters = await this.characterManager.listCharacters(filters);
      
      res.json({
        success: true,
        count: characters.length,
        data: characters
      });
    }));

    // Get character by ID
    this.router.get('/characters/:id', asyncHandler(async (req, res) => {
      const character = await this.characterManager.getCharacter(req.params.id);
      
      if (!character) {
        return res.status(404).json({
          success: false,
          error: 'Character not found'
        });
      }

      res.json({
        success: true,
        data: character
      });
    }));

    // Create new character
    this.router.post('/characters', asyncHandler(async (req, res) => {
      const characterData = req.body;
      
      // Validate required fields
      if (!characterData.name) {
        return res.status(400).json({
          success: false,
          error: 'Character name is required'
        });
      }

      const character = await this.characterManager.createCharacter(characterData);
      
      res.status(201).json({
        success: true,
        message: 'Character created successfully',
        data: character
      });
    }));

    // Update character
    this.router.put('/characters/:id', asyncHandler(async (req, res) => {
      const updates = req.body;
      const character = await this.characterManager.updateCharacter(req.params.id, updates);
      
      res.json({
        success: true,
        message: 'Character updated successfully',
        data: character
      });
    }));

    // Delete character
    this.router.delete('/characters/:id', asyncHandler(async (req, res) => {
      const result = await this.characterManager.deleteCharacter(req.params.id);
      
      res.json({
        success: true,
        message: result.message
      });
    }));

    // Interact with character
    this.router.post('/characters/:id/interact', asyncHandler(async (req, res) => {
      const { message, context } = req.body;
      
      if (!message) {
        return res.status(400).json({
          success: false,
          error: 'Message is required'
        });
      }

      const result = await this.characterManager.interact(
        req.params.id,
        message,
        context || {}
      );
      
      res.json({
        success: true,
        data: result
      });
    }));

    // Start autonomous operations
    this.router.post('/characters/:id/start', asyncHandler(async (req, res) => {
      const result = await this.characterManager.startAutonomousOperations(req.params.id);
      
      res.json({
        success: result.success,
        message: result.message
      });
    }));

    // Stop autonomous operations
    this.router.post('/characters/:id/stop', asyncHandler(async (req, res) => {
      const result = await this.characterManager.stopAutonomousOperations(req.params.id);
      
      res.json({
        success: result.success,
        message: result.message
      });
    }));

    // Get character analytics
    this.router.get('/characters/:id/analytics', asyncHandler(async (req, res) => {
      const character = await this.characterManager.getCharacter(req.params.id);
      
      if (!character) {
        return res.status(404).json({
          success: false,
          error: 'Character not found'
        });
      }

      // Return character metadata as analytics
      res.json({
        success: true,
        data: {
          characterId: character.id,
          name: character.name,
          status: character.status,
          interactions: character.metadata.interactions || 0,
          engagementRate: character.metadata.engagementRate || 0,
          lastActive: character.metadata.lastActive,
          createdAt: character.createdAt,
          uptime: character.status === 'active' ? 'Running' : 'Stopped'
        }
      });
    }));

    // Generate character using Eliza
    this.router.post('/characters/generate', asyncHandler(async (req, res) => {
      const { prompt, model, apiKey } = req.body;
      
      if (!prompt) {
        return res.status(400).json({
          success: false,
          error: 'Prompt is required'
        });
      }

      if (!this.elizaBridge || !this.elizaBridge.connected) {
        return res.status(503).json({
          success: false,
          error: 'Eliza service not available',
          message: 'Character generation requires Eliza service to be running'
        });
      }

      // Forward to Eliza bridge
      const response = await this.elizaBridge.app.handle({
        method: 'POST',
        url: '/generate-character',
        body: { prompt, model, apiKey }
      });

      res.json({
        success: true,
        data: response
      });
    }));

    // Refine character using Eliza
    this.router.post('/characters/:id/refine', asyncHandler(async (req, res) => {
      const { prompt, model, apiKey } = req.body;
      
      if (!prompt) {
        return res.status(400).json({
          success: false,
          error: 'Refinement prompt is required'
        });
      }

      const character = await this.characterManager.getCharacter(req.params.id);
      
      if (!character) {
        return res.status(404).json({
          success: false,
          error: 'Character not found'
        });
      }

      if (!this.elizaBridge || !this.elizaBridge.connected) {
        return res.status(503).json({
          success: false,
          error: 'Eliza service not available'
        });
      }

      // Convert character to Eliza format
      const elizaCharacter = await this.elizaBridge.syncCharacter(character);

      // Forward to Eliza bridge
      const response = await this.elizaBridge.app.handle({
        method: 'POST',
        url: '/refine-character',
        body: { prompt, model, currentCharacter: elizaCharacter, apiKey }
      });

      res.json({
        success: true,
        data: response
      });
    }));

    // Model status endpoint
    this.router.get('/models', asyncHandler(async (req, res) => {
      const models = this.characterManager.modelRouter 
        ? this.characterManager.modelRouter.getAvailableModels()
        : [];

      res.json({
        success: true,
        count: models.length,
        data: models
      });
    }));

    // Usage statistics
    this.router.get('/usage', asyncHandler(async (req, res) => {
      // Mock usage statistics for Phase 1
      res.json({
        success: true,
        data: {
          totalCharacters: this.characterManager.characters.size,
          activeCharacters: Array.from(this.characterManager.characters.values())
            .filter(c => c.status === 'active').length,
          totalInteractions: 0,
          apiCalls: 0,
          period: '24h'
        }
      });
    }));

    // Revenue analytics (mock for Phase 1)
    this.router.get('/revenue', asyncHandler(async (req, res) => {
      res.json({
        success: true,
        data: {
          total: 0,
          subscriptions: 0,
          affiliates: 0,
          api: 0,
          period: '30d'
        }
      });
    }));

    return this.router;
  }
}

module.exports = CharacterAPI;
