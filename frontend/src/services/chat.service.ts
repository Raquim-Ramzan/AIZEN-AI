/**
 * Chat Service - Handles all chat and messaging operations
 */

import { apiClient } from '@/lib/api-client';
import { API_CONFIG } from '@/config/api.config';
import type {
    ChatRequest,
    ChatResponse,
    Message,
    Conversation,
} from '@/types/api.types';

export const chatService = {
    /**
     * Send a non-streaming chat message
     */
    async sendMessage(request: ChatRequest) {
        return apiClient.post<ChatResponse>(API_CONFIG.ENDPOINTS.CHAT, request);
    },

    /**
     * Get all conversations
     */
    async getConversations() {
        return apiClient.get<Conversation[]>(API_CONFIG.ENDPOINTS.CONVERSATIONS);
    },

    /**
     * Create a new conversation
     */
    async createConversation(title?: string) {
        return apiClient.post<Conversation>(API_CONFIG.ENDPOINTS.CONVERSATIONS, {
            title: title || `New Conversation ${new Date().toLocaleDateString()}`,
        });
    },

    /**
     * Get a specific conversation
     */
    async getConversation(id: string) {
        return apiClient.get<Conversation>(API_CONFIG.ENDPOINTS.CONVERSATION_BY_ID(id));
    },

    /**
     * Delete a conversation
     */
    async deleteConversation(id: string) {
        return apiClient.delete(API_CONFIG.ENDPOINTS.CONVERSATION_BY_ID(id));
    },

    /**
     * Get messages for a conversation
     */
    async getMessages(conversationId: string) {
        return apiClient.get<Message[]>(
            API_CONFIG.ENDPOINTS.CONVERSATION_MESSAGES(conversationId)
        );
    },

    /**
     * Rename a conversation
     */
    async renameConversation(id: string, title: string) {
        return apiClient.put<Conversation>(API_CONFIG.ENDPOINTS.CONVERSATION_BY_ID(id), {
            title,
        });
    },
};
