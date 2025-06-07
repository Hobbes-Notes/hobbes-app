/**
 * Logging utility for the frontend.
 */

/**
 * Log a message with a prefix.
 * 
 * @param {string} prefix - The prefix to add to the message
 * @param {string} message - The message to log
 * @param {any} data - Optional data to log
 */
export const logWithPrefix = (prefix, message, data) => {
  if (process.env.NODE_ENV === 'development') {
    if (data) {
      console.log(`${prefix} - ${message}`, data);
    } else {
      console.log(`${prefix} - ${message}`);
    }
  }
};

/**
 * Log an error with a prefix.
 * 
 * @param {string} prefix - The prefix to add to the message
 * @param {string} message - The message to log
 * @param {Error} error - The error to log
 */
export const logErrorWithPrefix = (prefix, message, error) => {
  if (process.env.NODE_ENV === 'development') {
    console.error(`${prefix} - ${message}`, error);
  }
};

/**
 * Create a logger for a specific component or service.
 * 
 * @param {string} prefix - The prefix to use for all logs
 * @returns {Object} - An object with log and logError methods
 */
export const createLogger = (prefix) => {
  return {
    log: (message, data) => logWithPrefix(prefix, message, data),
    logError: (message, error) => logErrorWithPrefix(prefix, message, error)
  };
};

export default {
  logWithPrefix,
  logErrorWithPrefix,
  createLogger
}; 