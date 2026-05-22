// Global error handling middleware
const logger = require('../utils/logger');

// Custom error class
class AppError extends Error {
  constructor(message, statusCode = 500, isOperational = true) {
    super(message);
    this.statusCode = statusCode;
    this.isOperational = isOperational;
    this.timestamp = new Date().toISOString();
    Error.captureStackTrace(this, this.constructor);
  }
}

// Error handler middleware
function errorHandler(err, req, res, next) {
  let error = { ...err };
  error.message = err.message;
  error.stack = err.stack;

  // Log error
  logger.error('Error occurred', {
    message: err.message,
    statusCode: err.statusCode || 500,
    path: req.path,
    method: req.method,
    ip: req.ip,
    stack: err.stack,
    isOperational: err.isOperational
  });

  // Mongoose bad ObjectId
  if (err.name === 'CastError') {
    const message = 'Resource not found';
    error = new AppError(message, 404);
  }

  // Mongoose duplicate key
  if (err.code === 11000) {
    const message = 'Duplicate field value entered';
    error = new AppError(message, 400);
  }

  // Mongoose validation error
  if (err.name === 'ValidationError') {
    const message = Object.values(err.errors).map(val => val.message).join(', ');
    error = new AppError(message, 400);
  }

  // JWT errors
  if (err.name === 'JsonWebTokenError') {
    const message = 'Invalid token';
    error = new AppError(message, 401);
  }

  if (err.name === 'TokenExpiredError') {
    const message = 'Token expired';
    error = new AppError(message, 401);
  }

  // PostgreSQL errors
  if (err.code === '23505') { // Unique violation
    const message = 'Duplicate entry';
    error = new AppError(message, 400);
  }

  if (err.code === '23503') { // Foreign key violation
    const message = 'Referenced resource not found';
    error = new AppError(message, 400);
  }

  // Prepare response
  const statusCode = error.statusCode || 500;
  const response = {
    success: false,
    error: error.message || 'Internal Server Error',
    timestamp: new Date().toISOString()
  };

  // Include stack trace in development
  if (process.env.NODE_ENV === 'development') {
    response.stack = error.stack;
    response.details = err;
  }

  // Send response
  res.status(statusCode).json(response);
}

// Async error wrapper
function asyncHandler(fn) {
  return (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}

// Not found handler
function notFound(req, res, next) {
  const error = new AppError(`Route not found: ${req.originalUrl}`, 404);
  next(error);
}

module.exports = {
  AppError,
  errorHandler,
  asyncHandler,
  notFound
};
