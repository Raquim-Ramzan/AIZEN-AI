/**
 * API Configuration for AIZEN Backend
 * Centralized configuration for all backend API endpoints
 */

// Environment-based configuration
const isDevelopment = import.meta.env.MODE === 'development';

// Backend server configuration
export const API_CONFIG = {
  // Base URLs
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001',
  WS_BASE_URL: import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8001',

  // API Endpoints
  ENDPOINTS: {
    // Health & Status
    HEALTH: '/health',
    ROOT: '/',

    // Conversations
    CONVERSATIONS: '/api/conversations',
    CONVERSATION_BY_ID: (id: string) => `/api/conversations/${id}`,
    CONVERSATION_MESSAGES: (id: string) => `/api/conversations/${id}/messages`,

    // Chat
    CHAT: '/api/chat',
    WEBSOCKET: (clientId: string) => `/api/ws/${clientId}`,

    // Memory
    MEMORY_CORE: '/api/memory/core',
    MEMORY_PREFERENCE: '/api/memory/preference',
    MEMORY_FACT: '/api/memory/fact',
    MEMORY_SEARCH: '/api/memory/search',
    // Core Memory CRUD
    MEMORY_FACTS: '/api/memory/facts',
    MEMORY_FACTS_CLEAR: '/api/memory/facts/clear',
    MEMORY_FACT_DELETE: (factId: string) => `/api/memory/facts/${factId}`,


    // Tools
    TOOLS: '/api/tools',
    TOOLS_EXECUTE: '/api/tools/execute',

    // Speech
    SPEECH_TRANSCRIBE: '/api/speech/transcribe',
    SPEECH_SYNTHESIZE: '/api/speech/synthesize',

    // Settings
    SETTINGS: '/api/settings',

    // Model Management (NEW)
    MODELS_AVAILABLE: '/api/models/available',
    MODELS_SELECT: '/api/models/select',

    // Image Generation (NEW)
    IMAGE_GENERATE: '/api/image/generate',
  },

  // Request configuration
  TIMEOUT: 30000, // 30 seconds
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000, // 1 second

  // WebSocket configuration
  WS_RECONNECT_DELAY: 2000,
  WS_MAX_RECONNECT_ATTEMPTS: 5,
  WS_PING_INTERVAL: 30000, // 30 seconds

  // Debug mode
  DEBUG: isDevelopment,
} as const;

// Generate full URL for API endpoint
export const getApiUrl = (endpoint: string): string => {
  return `${API_CONFIG.BASE_URL}${endpoint}`;
};

// Generate full URL for WebSocket endpoint
export const getWsUrl = (endpoint: string): string => {
  return `${API_CONFIG.WS_BASE_URL}${endpoint}`;
};

// Client ID generator (can be customized)
export const generateClientId = (): string => {
  return `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};
