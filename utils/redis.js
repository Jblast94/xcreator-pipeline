// Redis utility for caching and session management
const Redis = require('ioredis');
const logger = require('./logger');

let redisClient = null;

// Redis configuration from environment
const redisConfig = {
  host: process.env.REDIS_HOST || 'localhost',
  port: process.env.REDIS_PORT || 6379,
  password: process.env.REDIS_PASSWORD || undefined,
  db: process.env.REDIS_DB || 0,
  retryStrategy: (times) => {
    const delay = Math.min(times * 50, 2000);
    return delay;
  },
  maxRetriesPerRequest: 3
};

// Parse REDIS_URL if provided
if (process.env.REDIS_URL) {
  const url = new URL(process.env.REDIS_URL);
  redisConfig.host = url.hostname;
  redisConfig.port = parseInt(url.port) || 6379;
  if (url.password) {
    redisConfig.password = url.password;
  }
}

// Initialize Redis connection
async function setupRedis() {
  try {
    if (redisClient) {
      logger.info('Redis client already initialized');
      return redisClient;
    }

    redisClient = new Redis(redisConfig);

    // Connection event handlers
    redisClient.on('connect', () => {
      logger.info('Redis connection established', {
        host: redisConfig.host,
        port: redisConfig.port
      });
    });

    redisClient.on('ready', () => {
      logger.info('Redis client ready');
    });

    redisClient.on('error', (err) => {
      logger.error('Redis client error', { error: err.message });
    });

    redisClient.on('close', () => {
      logger.warn('Redis connection closed');
    });

    redisClient.on('reconnecting', () => {
      logger.info('Redis client reconnecting');
    });

    // Test connection
    await redisClient.ping();
    logger.info('Redis ping successful');

    return redisClient;
  } catch (error) {
    logger.error('Failed to connect to Redis', {
      error: error.message,
      stack: error.stack
    });
    throw error;
  }
}

// Get Redis client
function getRedis() {
  if (!redisClient) {
    throw new Error('Redis client not initialized. Call setupRedis() first.');
  }
  return redisClient;
}

// Cache helper functions
async function setCache(key, value, ttl = 3600) {
  try {
    const serialized = JSON.stringify(value);
    if (ttl) {
      await redisClient.setex(key, ttl, serialized);
    } else {
      await redisClient.set(key, serialized);
    }
    logger.debug('Cache set', { key, ttl });
  } catch (error) {
    logger.error('Failed to set cache', { key, error: error.message });
    throw error;
  }
}

async function getCache(key) {
  try {
    const value = await redisClient.get(key);
    if (!value) return null;
    return JSON.parse(value);
  } catch (error) {
    logger.error('Failed to get cache', { key, error: error.message });
    return null;
  }
}

async function deleteCache(key) {
  try {
    await redisClient.del(key);
    logger.debug('Cache deleted', { key });
  } catch (error) {
    logger.error('Failed to delete cache', { key, error: error.message });
  }
}

async function clearCacheByPattern(pattern) {
  try {
    const keys = await redisClient.keys(pattern);
    if (keys.length > 0) {
      await redisClient.del(...keys);
      logger.debug('Cache cleared by pattern', { pattern, count: keys.length });
    }
  } catch (error) {
    logger.error('Failed to clear cache by pattern', { pattern, error: error.message });
  }
}

// Close Redis connection
async function closeRedis() {
  if (redisClient) {
    await redisClient.quit();
    redisClient = null;
    logger.info('Redis connection closed');
  }
}

module.exports = {
  setupRedis,
  getRedis,
  setCache,
  getCache,
  deleteCache,
  clearCacheByPattern,
  closeRedis
};
