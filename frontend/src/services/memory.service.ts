/**
 * Memory Service - Handles core memory and learning operations
 */

import { apiClient } from '@/lib/api-client';
import { API_CONFIG } from '@/config/api.config';
import type {
    BaseMetadata,
    CoreMemory,
    MemorySearchRequest,
    MemorySearchResult,
} from '@/types/api.types';

// Core Memory Fact type
export interface CoreFact {
    id?: string;
    fact: string;
    category?: string;
    importance?: string;
    source?: string;
    timestamp?: string;
    confidence?: number;
}

export interface CoreFactsResponse {
    facts: CoreFact[];
    count: number;
}

export const memoryService = {
    /**
     * Get core memory
     */
    async getCoreMemory() {
        return apiClient.get<CoreMemory>(API_CONFIG.ENDPOINTS.MEMORY_CORE);
    },

    /**
     * Update user preference
     */
    async updatePreference(key: string, value: unknown) {
        return apiClient.post(API_CONFIG.ENDPOINTS.MEMORY_PREFERENCE, {
            key,
            value,
        });
    },

    /**
     * Store a fact in memory
     */
    async storeFact(content: string, metadata?: BaseMetadata) {
        return apiClient.post(API_CONFIG.ENDPOINTS.MEMORY_FACT, {
            content,
            metadata: metadata || {},
        });
    },

    /**
     * Search memory
     */
    async searchMemory(request: MemorySearchRequest) {
        return apiClient.get<MemorySearchResult>(
            API_CONFIG.ENDPOINTS.MEMORY_SEARCH,
            request
        );
    },

    // ============================================
    // Core Memory CRUD Operations
    // ============================================

    /**
     * Get all core memory facts
     */
    async getCoreFacts() {
        return apiClient.get<CoreFactsResponse>(API_CONFIG.ENDPOINTS.MEMORY_FACTS);
    },

    /**
     * Add a new core memory fact
     */
    async addCoreFact(fact: string, category: string = 'learned', importance: string = 'normal') {
        return apiClient.post<{ status: string; fact?: CoreFact }>(
            API_CONFIG.ENDPOINTS.MEMORY_FACTS,
            { fact, category, importance }
        );
    },

    /**
     * Update an existing core memory fact
     */
    async updateCoreFact(factId: string, newFact: string) {
        return apiClient.put<{ status: string; fact_id: string }>(
            API_CONFIG.ENDPOINTS.MEMORY_FACTS,
            { fact_id: factId, new_fact: newFact }
        );
    },

    /**
     * Delete a core memory fact
     */
    async deleteCoreFact(factId: string) {
        return apiClient.delete<{ status: string; fact_id: string }>(
            API_CONFIG.ENDPOINTS.MEMORY_FACT_DELETE(factId)
        );
    },

    /**
     * Clear all core memory facts
     */
    async clearCoreFacts(keepIdentity: boolean = true) {
        return apiClient.post<{ status: string; keep_identity: boolean }>(
            API_CONFIG.ENDPOINTS.MEMORY_FACTS_CLEAR,
            { keep_identity: keepIdentity }
        );
    },
};
