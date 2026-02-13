/**
 * System Service - Handles health checks, settings, and model management
 */

import { apiClient } from '@/lib/api-client';
import { API_CONFIG } from '@/config/api.config';
import type {
    HealthStatus,
    Settings,
    AvailableModels,
    ModelSelectRequest,
    ModelSelectResponse
} from '@/types/api.types';

export const systemService = {
    /**
     * Check backend health
     */
    async getHealth() {
        return apiClient.get<HealthStatus>(API_CONFIG.ENDPOINTS.HEALTH);
    },

    /**
     * Get system settings (now includes multi-provider info)
     */
    async getSettings() {
        return apiClient.get<Settings>(API_CONFIG.ENDPOINTS.SETTINGS);
    },

    /**
     * Get all available models by provider
     */
    async getAvailableModels() {
        return apiClient.get<AvailableModels>(API_CONFIG.ENDPOINTS.MODELS_AVAILABLE);
    },

    /**
     * Select optimal model for a task type
     */
    async selectModel(request: ModelSelectRequest) {
        return apiClient.post<ModelSelectResponse>(API_CONFIG.ENDPOINTS.MODELS_SELECT, request);
    },

    /**
     * Ping the server
     */
    async ping() {
        return apiClient.get(API_CONFIG.ENDPOINTS.ROOT);
    },
};
