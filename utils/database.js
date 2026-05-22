// Database utility for PostgreSQL connection
const { Pool } = require('pg');
const logger = require('./logger');

let pool = null;

// Database configuration from environment
const dbConfig = {
  connectionString: process.env.DATABASE_URL,
  max: 20, // Maximum pool size
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
};

// Initialize database connection pool
async function setupDatabase() {
  try {
    if (pool) {
      logger.info('Database pool already initialized');
      return pool;
    }

    pool = new Pool(dbConfig);

    // Test connection
    const client = await pool.connect();
    const result = await client.query('SELECT NOW()');
    client.release();

    logger.info('Database connection established', {
      timestamp: result.rows[0].now
    });

    // Handle pool errors
    pool.on('error', (err) => {
      logger.error('Unexpected database pool error', { error: err.message });
    });

    return pool;
  } catch (error) {
    logger.error('Failed to connect to database', {
      error: error.message,
      stack: error.stack
    });
    throw error;
  }
}

// Get database pool
function getPool() {
  if (!pool) {
    throw new Error('Database pool not initialized. Call setupDatabase() first.');
  }
  return pool;
}

// Execute a query
async function query(text, params) {
  try {
    const start = Date.now();
    const result = await pool.query(text, params);
    const duration = Date.now() - start;
    
    logger.debug('Executed query', {
      query: text,
      duration: `${duration}ms`,
      rows: result.rowCount
    });
    
    return result;
  } catch (error) {
    logger.error('Database query error', {
      error: error.message,
      query: text,
      params
    });
    throw error;
  }
}

// Get a client from the pool for transactions
async function getClient() {
  return await pool.connect();
}

// Close database connection pool
async function closeDatabase() {
  if (pool) {
    await pool.end();
    pool = null;
    logger.info('Database connection pool closed');
  }
}

module.exports = {
  setupDatabase,
  getPool,
  query,
  getClient,
  closeDatabase
};
