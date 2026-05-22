const express = require('express');
const { Server } = require('socket.io');
const { createServer } = require('http');
const sqlite3 = require('sqlite3').verbose();
const fs = require('fs').promises;
const path = require('path');
const axios = require('axios');
const cron = require('node-cron');

class ElizaBridgeService {
    constructor() {
        this.app = express();
        this.server = createServer(this.app);
        this.io = new Server(this.server, {
            cors: {
                origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
                methods: ['GET', 'POST']
            }
        });
        
        this.elizaPath = process.env.ELIZA_DB_PATH || './Eliza-Character-Gen/database.db';
        this.syncInterval = parseInt(process.env.SYNC_INTERVAL) || 30000;
        this.characters = new Map();
        this.autonomousCharacters = new Set();
        
        this.setupMiddleware();
        this.setupRoutes();
        this.setupSocketHandlers();
        this.startSync();
        this.startAutonomousOperations();
    }

    setupMiddleware() {
        this.app.use(express.json());
        this.app.use(express.static('public'));
        
        // Health check
        this.app.get('/health', (req, res) => {
            res.json({ 
                status: 'healthy', 
                characters: this.characters.size,
                autonomous: this.autonomousCharacters.size,
                timestamp: new Date().toISOString()
            });
        });
    }

    setupRoutes() {
        // Get all characters
        this.app.get('/api/characters', async (req, res) => {
            try {
                const characters = await this.getAllCharacters();
                res.json({ success: true, characters });
            } catch (error) {
                console.error('Error getting characters:', error);
                res.status(500).json({ success: false, error: error.message });
            }
        });

        // Get character by ID
        this.app.get('/api/characters/:id', async (req, res) => {
            try {
                const character = await this.getCharacter(req.params.id);
                res.json({ success: true, character });
            } catch (error) {
                console.error('Error getting character:', error);
                res.status(500).json({ success: false, error: error.message });
            }
        });

        // Create new character
        this.app.post('/api/characters', async (req, res) => {
            try {
                const character = await this.createCharacter(req.body);
                res.json({ success: true, character });
            } catch (error) {
                console.error('Error creating character:', error);
                res.status(500).json({ success: false, error: error.message });
            }
        });

        // Update character
        this.app.put('/api/characters/:id', async (req, res) => {
            try {
                const character = await this.updateCharacter(req.params.id, req.body);
                res.json({ success: true, character });
            } catch (error) {
                console.error('Error updating character:', error);
                res.status(500).json({ success: false, error: error.message });
            }
        });

        // Activate autonomous mode
        this.app.post('/api/characters/:id/activate', async (req, res) => {
            try {
                const { autonomous = true } = req.body;
                await this.activateAutonomousMode(req.params.id, autonomous);
                res.json({ success: true, message: 'Autonomous mode updated' });
            } catch (error) {
                console.error('Error activating autonomous mode:', error);
                res.status(500).json({ success: false, error: error.message });
            }
        });

        // Get character analytics
        this.app.get('/api/characters/:id/analytics', async (req, res) => {
            try {
                const analytics = await this.getCharacterAnalytics(req.params.id);
                res.json({ success: true, analytics });
            } catch (error) {
                console.error('Error getting analytics:', error);
                res.status(500).json({ success: false, error: error.message });
            }
        });
    }

    setupSocketHandlers() {
        this.io.on('connection', (socket) => {
            console.log('Client connected:', socket.id);

            // Join character room
            socket.on('join-character', (characterId) => {
                socket.join(`character-${characterId}`);
                console.log(`Socket ${socket.id} joined character ${characterId}`);
            });

            // Leave character room
            socket.on('leave-character', (characterId) => {
                socket.leave(`character-${characterId}`);
                console.log(`Socket ${socket.id} left character ${characterId}`);
            });

            // Real-time character update
            socket.on('character-update', (data) => {
                socket.to(`character-${data.characterId}`).emit('character-updated', data);
            });

            socket.on('disconnect', () => {
                console.log('Client disconnected:', socket.id);
            });
        });
    }

    async getAllCharacters() {
        try {
            // Read from your Eliza database
            const db = new sqlite3.Database(this.elizaPath);
            
            return new Promise((resolve, reject) => {
                const characters = [];
                
                db.each("SELECT * FROM characters", (err, row) => {
                    if (err) {
                        reject(err);
                        return;
                    }
                    
                    characters.push({
                        id: row.id,
                        name: row.name,
                        personality: row.personality,
                        settings: JSON.parse(row.settings || '{}'),
                        created: row.created_at,
                        lastActive: row.last_active,
                        autonomous: this.autonomousCharacters.has(row.id)
                    });
                }, (err, count) => {
                    db.close();
                    if (err) {
                        reject(err);
                    } else {
                        resolve(characters);
                    }
                });
            });
        } catch (error) {
            console.error('Error reading characters:', error);
            return [];
        }
    }

    async getCharacter(id) {
        if (this.characters.has(id)) {
            return this.characters.get(id);
        }

        // Fetch from database
        const db = new sqlite3.Database(this.elizaPath);
        
        return new Promise((resolve, reject) => {
            db.get("SELECT * FROM characters WHERE id = ?", [id], (err, row) => {
                db.close();
                if (err) {
                    reject(err);
                } else if (row) {
                    const character = {
                        id: row.id,
                        name: row.name,
                        personality: row.personality,
                        settings: JSON.parse(row.settings || '{}'),
                        created: row.created_at,
                        lastActive: row.last_active,
                        autonomous: this.autonomousCharacters.has(row.id)
                    };
                    
                    this.characters.set(id, character);
                    resolve(character);
                } else {
                    reject(new Error('Character not found'));
                }
            });
        });
    }

    async createCharacter(characterData) {
        const id = `char_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const character = {
            id,
            ...characterData,
            created: new Date().toISOString(),
            lastActive: new Date().toISOString(),
            autonomous: false
        };

        this.characters.set(id, character);
        
        // Emit real-time update
        this.io.emit('character-created', character);
        
        return character;
    }

    async updateCharacter(id, updates) {
        if (!this.characters.has(id)) {
            throw new Error('Character not found');
        }

        const character = this.characters.get(id);
        const updatedCharacter = {
            ...character,
            ...updates,
            lastActive: new Date().toISOString()
        };

        this.characters.set(id, updatedCharacter);
        
        // Emit real-time update
        this.io.to(`character-${id}`).emit('character-updated', updatedCharacter);
        
        return updatedCharacter;
    }

    async activateAutonomousMode(id, enable = true) {
        if (enable) {
            this.autonomousCharacters.add(id);
            
            // Start autonomous operations for this character
            this.startCharacterAutonomousOps(id);
        } else {
            this.autonomousCharacters.delete(id);
        }

        // Update character status
        if (this.characters.has(id)) {
            const character = this.characters.get(id);
            character.autonomous = enable;
            character.lastActive = new Date().toISOString();
            
            this.io.to(`character-${id}`).emit('autonomous-mode-changed', {
                characterId: id,
                enabled: enable
            });
        }
    }

    startCharacterAutonomousOps(characterId) {
        // Schedule content generation
        cron.schedule('*/15 * * * *', async () => {
            if (this.autonomousCharacters.has(characterId)) {
                await this.generateAutonomousContent(characterId);
            }
        });

        // Schedule engagement activities
        cron.schedule('*/10 * * * *', async () => {
            if (this.autonomousCharacters.has(characterId)) {
                await this.performEngagementActivities(characterId);
            }
        });

        // Schedule trend monitoring
        cron.schedule('0 */2 * * *', async () => {
            if (this.autonomousCharacters.has(characterId)) {
                await this.monitorTrends(characterId);
            }
        });
    }

    async generateAutonomousContent(characterId) {
        try {
            const character = this.characters.get(characterId);
            if (!character) return;

            // Generate content using AI models
            const content = await this.callAIModel('content-generation', {
                character: character,
                type: 'social_post',
                platform: character.platforms?.[0] || 'twitter'
            });

            // Emit new content event
            this.io.to(`character-${characterId}`).emit('content-generated', {
                characterId,
                content,
                timestamp: new Date().toISOString()
            });

            console.log(`Autonomous content generated for ${character.name}`);
        } catch (error) {
            console.error('Error generating autonomous content:', error);
        }
    }

    async performEngagementActivities(characterId) {
        try {
            const character = this.characters.get(characterId);
            if (!character) return;

            // Simulate engagement activities
            const activities = [
                'like_post',
                'reply_to_comment',
                'share_relevant_content',
                'follow_user',
                'comment_on_trend'
            ];

            const activity = activities[Math.floor(Math.random() * activities.length)];

            this.io.to(`character-${characterId}`).emit('engagement-activity', {
                characterId,
                activity,
                timestamp: new Date().toISOString()
            });

            console.log(`Engagement activity ${activity} performed by ${character.name}`);
        } catch (error) {
            console.error('Error performing engagement activities:', error);
        }
    }

    async monitorTrends(characterId) {
        try {
            // Monitor trending topics and hashtags
            const trends = await this.callAIModel('trend-analysis', {
                categories: ['technology', 'ai', 'business']
            });

            this.io.to(`character-${characterId}`).emit('trends-updated', {
                characterId,
                trends,
                timestamp: new Date().toISOString()
            });

            console.log(`Trends monitored for character ${characterId}`);
        } catch (error) {
            console.error('Error monitoring trends:', error);
        }
    }

    async callAIModel(endpoint, data) {
        // This would connect to your self-hosted AI models
        // For now, return mock data
        return {
            content: `Generated content for ${data.character?.name}`,
            engagement_score: Math.random() * 100,
            recommendations: ['trend1', 'trend2', 'trend3']
        };
    }

    async getCharacterAnalytics(characterId) {
        const character = this.characters.get(characterId);
        if (!character) {
            throw new Error('Character not found');
        }

        // Generate analytics data
        return {
            characterId,
            postsGenerated: Math.floor(Math.random() * 100) + 50,
            engagementRate: (Math.random() * 5 + 2).toFixed(2),
            followerGrowth: Math.floor(Math.random() * 1000) + 100,
            contentPerformance: {
                bestTime: '14:00-16:00',
                topHashtags: ['#AI', '#Tech', '#Innovation'],
                engagementByPlatform: {
                    twitter: Math.floor(Math.random() * 500) + 200,
                    linkedin: Math.floor(Math.random() * 300) + 100
                }
            },
            revenueGenerated: (Math.random() * 1000 + 100).toFixed(2),
            lastUpdated: new Date().toISOString()
        };
    }

    startSync() {
        // Sync with your Eliza database periodically
        setInterval(async () => {
            try {
                const characters = await this.getAllCharacters();
                characters.forEach(char => {
                    this.characters.set(char.id, char);
                });
                
                console.log(`Synced ${characters.length} characters from Eliza database`);
            } catch (error) {
                console.error('Error syncing characters:', error);
            }
        }, this.syncInterval);
    }

    startAutonomousOperations() {
        // Start autonomous operations for all characters
        this.autonomousCharacters.forEach(characterId => {
            this.startCharacterAutonomousOps(characterId);
        });
        
        console.log('Autonomous operations started');
    }

    start(port = 3001) {
        this.server.listen(port, () => {
            console.log(`🚀 Eliza Bridge Service running on port ${port}`);
            console.log(`📝 Managing ${this.characters.size} characters`);
            console.log(`🤖 ${this.autonomousCharacters.size} autonomous characters active`);
        });
    }
}

// Start the service
const bridgeService = new ElizaBridgeService();
bridgeService.start(process.env.ELIZA_BRIDGE_PORT || 3001);

module.exports = ElizaBridgeService;