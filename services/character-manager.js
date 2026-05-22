// Character Manager Service
const { v4: uuidv4 } = require('uuid');
const logger = require('../utils/logger');
const { query } = require('../utils/database');
const { setCache, getCache, deleteCache } = require('../utils/redis');

class CharacterManager {
  constructor(elizaBridge = null, modelRouter = null) {
    this.elizaBridge = elizaBridge;
    this.modelRouter = modelRouter;
    this.characters = new Map(); // In-memory cache for Phase 1
    logger.info('CharacterManager initialized');
  }

  // Create a new character
  async createCharacter(characterData) {
    try {
      const characterId = uuidv4();
      const timestamp = new Date().toISOString();

      const character = {
        id: characterId,
        name: characterData.name,
        displayName: characterData.displayName || characterData.name,
        eliza: characterData.eliza || {},
        personality: characterData.personality || {},
        voice: characterData.voice || {},
        visual: characterData.visual || {},
        settings: characterData.settings || {
          visibility: 'private',
          autoResponse: false,
          proactiveEngagement: false,
          contentGeneration: false
        },
        status: 'inactive',
        createdAt: timestamp,
        updatedAt: timestamp,
        metadata: {
          interactions: 0,
          engagementRate: 0,
          lastActive: null
        }
      };

      // Store in database
      const result = await query(
        `INSERT INTO characters (id, name, display_name, eliza_config, personality, voice_config, visual_config, settings, status, created_at, updated_at)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
         RETURNING *`,
        [
          character.id,
          character.name,
          character.displayName,
          JSON.stringify(character.eliza),
          JSON.stringify(character.personality),
          JSON.stringify(character.voice),
          JSON.stringify(character.visual),
          JSON.stringify(character.settings),
          character.status,
          character.createdAt,
          character.updatedAt
        ]
      );

      // Cache character
      this.characters.set(characterId, character);
      await setCache(`character:${characterId}`, character, 3600);

      // Sync with Eliza if bridge is available
      if (this.elizaBridge) {
        try {
          await this.elizaBridge.syncCharacter(character);
          logger.info(`Character synced with Eliza: ${character.name}`);
        } catch (error) {
          logger.warn(`Failed to sync character with Eliza: ${error.message}`);
        }
      }

      logger.info(`Character created: ${character.name} (${characterId})`);
      return character;

    } catch (error) {
      logger.error('Failed to create character', { error: error.message });
      throw error;
    }
  }

  // Get character by ID
  async getCharacter(characterId) {
    try {
      // Check cache first
      let character = this.characters.get(characterId);
      if (character) {
        return character;
      }

      // Check Redis cache
      character = await getCache(`character:${characterId}`);
      if (character) {
        this.characters.set(characterId, character);
        return character;
      }

      // Query database
      const result = await query(
        'SELECT * FROM characters WHERE id = $1',
        [characterId]
      );

      if (result.rows.length === 0) {
        return null;
      }

      const row = result.rows[0];
      character = {
        id: row.id,
        name: row.name,
        displayName: row.display_name,
        eliza: row.eliza_config,
        personality: row.personality,
        voice: row.voice_config,
        visual: row.visual_config,
        settings: row.settings,
        status: row.status,
        createdAt: row.created_at,
        updatedAt: row.updated_at,
        metadata: row.metadata || {}
      };

      // Update caches
      this.characters.set(characterId, character);
      await setCache(`character:${characterId}`, character, 3600);

      return character;

    } catch (error) {
      logger.error('Failed to get character', { characterId, error: error.message });
      throw error;
    }
  }

  // List all characters
  async listCharacters(filters = {}) {
    try {
      let whereClause = 'WHERE 1=1';
      const params = [];

      if (filters.status) {
        params.push(filters.status);
        whereClause += ` AND status = $${params.length}`;
      }

      if (filters.visibility) {
        params.push(filters.visibility);
        whereClause += ` AND settings->>'visibility' = $${params.length}`;
      }

      const result = await query(
        `SELECT * FROM characters ${whereClause} ORDER BY created_at DESC LIMIT 100`,
        params
      );

      const characters = result.rows.map(row => ({
        id: row.id,
        name: row.name,
        displayName: row.display_name,
        eliza: row.eliza_config,
        personality: row.personality,
        voice: row.voice_config,
        visual: row.visual_config,
        settings: row.settings,
        status: row.status,
        createdAt: row.created_at,
        updatedAt: row.updated_at,
        metadata: row.metadata || {}
      }));

      return characters;

    } catch (error) {
      logger.error('Failed to list characters', { error: error.message });
      throw error;
    }
  }

  // Update character
  async updateCharacter(characterId, updates) {
    try {
      const character = await this.getCharacter(characterId);
      if (!character) {
        throw new Error('Character not found');
      }

      const updatedCharacter = {
        ...character,
        ...updates,
        updatedAt: new Date().toISOString()
      };

      await query(
        `UPDATE characters SET 
         name = $2, display_name = $3, eliza_config = $4, personality = $5,
         voice_config = $6, visual_config = $7, settings = $8, status = $9, updated_at = $10
         WHERE id = $1`,
        [
          characterId,
          updatedCharacter.name,
          updatedCharacter.displayName,
          JSON.stringify(updatedCharacter.eliza),
          JSON.stringify(updatedCharacter.personality),
          JSON.stringify(updatedCharacter.voice),
          JSON.stringify(updatedCharacter.visual),
          JSON.stringify(updatedCharacter.settings),
          updatedCharacter.status,
          updatedCharacter.updatedAt
        ]
      );

      // Update caches
      this.characters.set(characterId, updatedCharacter);
      await setCache(`character:${characterId}`, updatedCharacter, 3600);

      // Sync with Eliza
      if (this.elizaBridge) {
        try {
          await this.elizaBridge.syncCharacter(updatedCharacter);
        } catch (error) {
          logger.warn(`Failed to sync updated character with Eliza: ${error.message}`);
        }
      }

      logger.info(`Character updated: ${updatedCharacter.name} (${characterId})`);
      return updatedCharacter;

    } catch (error) {
      logger.error('Failed to update character', { characterId, error: error.message });
      throw error;
    }
  }

  // Delete character
  async deleteCharacter(characterId) {
    try {
      const character = await this.getCharacter(characterId);
      if (!character) {
        throw new Error('Character not found');
      }

      await query('DELETE FROM characters WHERE id = $1', [characterId]);

      // Clear caches
      this.characters.delete(characterId);
      await deleteCache(`character:${characterId}`);

      logger.info(`Character deleted: ${character.name} (${characterId})`);
      return { success: true, message: 'Character deleted' };

    } catch (error) {
      logger.error('Failed to delete character', { characterId, error: error.message });
      throw error;
    }
  }

  // Interact with character
  async interact(characterId, message, context = {}) {
    try {
      const character = await this.getCharacter(characterId);
      if (!character) {
        throw new Error('Character not found');
      }

      const startTime = Date.now();

      let response;
      if (this.elizaBridge) {
        // Use Eliza for interaction
        response = await this.elizaBridge.interact(character.eliza.agentId, message, context);
      } else {
        // Fallback mock response
        response = {
          text: `Hello! I'm ${character.name}. I received your message: "${message}". This is a mock response for testing.`,
          confidence: 0.8,
          source: 'mock'
        };
      }

      const responseTime = Date.now() - startTime;

      // Store conversation
      await query(
        `INSERT INTO conversations (id, character_id, user_message, character_response, context, response_time, created_at)
         VALUES ($1, $2, $3, $4, $5, $6, $7)`,
        [
          uuidv4(),
          characterId,
          message,
          response.text,
          JSON.stringify(context),
          responseTime,
          new Date().toISOString()
        ]
      );

      // Update character metadata
      character.metadata.interactions = (character.metadata.interactions || 0) + 1;
      character.metadata.lastActive = new Date().toISOString();
      await this.updateCharacter(characterId, { metadata: character.metadata });

      logger.info(`Character interaction: ${character.name}`, { responseTime: `${responseTime}ms` });

      return {
        response: response.text,
        confidence: response.confidence,
        responseTime,
        timestamp: new Date().toISOString()
      };

    } catch (error) {
      logger.error('Failed to interact with character', { characterId, error: error.message });
      throw error;
    }
  }

  // Start autonomous operations for a character
  async startAutonomousOperations(characterId) {
    try {
      const character = await this.getCharacter(characterId);
      if (!character) {
        throw new Error('Character not found');
      }

      if (character.status === 'active') {
        logger.warn(`Character already active: ${character.name}`);
        return { success: false, message: 'Character already active' };
      }

      await this.updateCharacter(characterId, { status: 'active' });

      logger.info(`Started autonomous operations for: ${character.name}`);
      return { success: true, message: 'Autonomous operations started' };

    } catch (error) {
      logger.error('Failed to start autonomous operations', { characterId, error: error.message });
      throw error;
    }
  }

  // Stop autonomous operations for a character
  async stopAutonomousOperations(characterId) {
    try {
      const character = await this.getCharacter(characterId);
      if (!character) {
        throw new Error('Character not found');
      }

      await this.updateCharacter(characterId, { status: 'inactive' });

      logger.info(`Stopped autonomous operations for: ${character.name}`);
      return { success: true, message: 'Autonomous operations stopped' };

    } catch (error) {
      logger.error('Failed to stop autonomous operations', { characterId, error: error.message });
      throw error;
    }
  }
}

module.exports = CharacterManager;
