/**
 * Custom React Hook for Chat Operations
 * Manages chat state, streaming responses, and message history
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { useWebSocket } from './useWebSocket';
import { chatService } from '@/services/chat.service';
import type { Message, PendingOperation, MessageMetadata } from '@/types/api.types';
import type { Message as UIMessage } from '@/components/ChatInterface';

interface UseChatOptions {
    onConversationCreated?: (conversationId: string) => void;
}

export const useChat = (conversationId?: string | null, options?: UseChatOptions) => {
    const [messages, setMessages] = useState<UIMessage[]>([]);
    const [isStreaming, setIsStreaming] = useState(false);
    const [currentStreamingMessage, setCurrentStreamingMessage] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [pendingOperation, setPendingOperation] = useState<PendingOperation | null>(null);

    // Track the actual conversation ID (might be different if created by backend)
    const [activeConversationId, setActiveConversationId] = useState<string | null>(conversationId || null);

    // Use ref to track current streaming message for closure
    const streamingMessageRef = useRef('');

    // WebSocket connection for streaming
    const { isConnected, sendChatMessage, sendNewSession, subscribe } = useWebSocket({
        autoConnect: true,
    });

    // Sync with external conversationId
    useEffect(() => {
        if (conversationId && conversationId !== activeConversationId) {
            setActiveConversationId(conversationId);
        }
    }, [conversationId]);

    // Load initial messages if conversation ID provided
    useEffect(() => {
        if (activeConversationId) {
            loadMessages(activeConversationId);
        }
    }, [activeConversationId]);

    // Subscribe to streaming messages
    useEffect(() => {
        // Message received - backend acknowledges message and returns conversation ID
        const unsubReceived = subscribe('message_received', (message) => {
            console.log('[useChat] Message received:', message);
            if (message.conversation_id && message.conversation_id !== activeConversationId) {
                setActiveConversationId(message.conversation_id);
                // Notify parent about the new conversation
                options?.onConversationCreated?.(message.conversation_id);
            }
        });

        // Token streaming
        const unsubToken = subscribe('token', (message) => {
            setIsStreaming(true);
            streamingMessageRef.current += (message.content || '');
            setCurrentStreamingMessage(prev => prev + (message.content || ''));
        });

        // Complete message
        const unsubComplete = subscribe('complete', (message) => {
            setIsStreaming(false);

            const completeMessage: UIMessage = {
                id: message.message_id || Date.now().toString(),
                role: 'assistant',
                content: message.full_response || streamingMessageRef.current,
                timestamp: new Date().toLocaleTimeString(),
                metadata: {
                    provider: message.provider,
                    model: message.model,
                },
            };

            setMessages((prev) => [...prev, completeMessage]);
            setCurrentStreamingMessage('');
            streamingMessageRef.current = '';

            // Check for pending operations in message metadata
            if (message.metadata?.pending_operations && message.metadata.pending_operations.length > 0) {
                const pendingOp = message.metadata.pending_operations[0];
                setPendingOperation(pendingOp);
            }
        });

        // Error handling
        const unsubError = subscribe('error', (message) => {
            setIsStreaming(false);
            setError(message.error || 'An error occurred');
            setCurrentStreamingMessage('');
            streamingMessageRef.current = '';
        });

        // Operation approval required
        const unsubApproval = subscribe('operation_approval_required', (message) => {
            console.log('[useChat] Operation approval required:', message);
            setPendingOperation({
                operation_id: message.operation_id,
                tool: message.tool,
                parameters: message.parameters,
                message: message.message,
                risk_level: message.risk_level,
            });
        });

        // New session created (from NEW SESSION button)
        const unsubSessionCreated = subscribe('session_created', (message) => {
            console.log('[useChat] New session created:', message);
            if (message.conversation_id) {
                setActiveConversationId(message.conversation_id);
                setMessages([]);
                setCurrentStreamingMessage('');
                streamingMessageRef.current = '';
                options?.onConversationCreated?.(message.conversation_id);
            }
        });

        return () => {
            unsubReceived();
            unsubToken();
            unsubComplete();
            unsubError();
            unsubApproval();
            unsubSessionCreated();
        };
    }, [subscribe, activeConversationId, options]);

    // Load messages from backend
    const loadMessages = useCallback(async (convId: string) => {
        try {
            const response = await chatService.getMessages(convId);

            if (response.data) {
                const uiMessages: UIMessage[] = response.data.map((msg) => ({
                    id: msg.id,
                    role: msg.role,
                    content: msg.content,
                    timestamp: new Date(msg.timestamp).toLocaleTimeString(),
                    metadata: msg.metadata,
                }));
                setMessages(uiMessages);
            }
        } catch (err) {
            console.error('[useChat] Error loading messages:', err);
            setError('Failed to load messages');
        }
    }, []);

    // Send message (streaming via WebSocket)
    const sendMessage = useCallback(
        async (content: string, metadata?: MessageMetadata) => {
            // Add user message immediately
            const userMessage: UIMessage = {
                id: Date.now().toString(),
                role: 'user',
                content,
                timestamp: new Date().toLocaleTimeString(),
            };

            setMessages((prev) => [...prev, userMessage]);
            setError(null);
            streamingMessageRef.current = '';

            // Send via WebSocket for streaming response
            // Pass the activeConversationId (may be null for first message)
            const success = sendChatMessage(content, activeConversationId, metadata);

            if (!success) {
                setError('Failed to send message - not connected');
            }

            return success;
        },
        [activeConversationId, sendChatMessage]
    );

    // Clear messages
    const clearMessages = useCallback(() => {
        setMessages([]);
        setCurrentStreamingMessage('');
        streamingMessageRef.current = '';
        setError(null);
    }, []);

    // Clear pending operation
    const clearPendingOperation = useCallback(() => {
        setPendingOperation(null);
    }, []);

    // Reset for new conversation
    const resetForNewConversation = useCallback(() => {
        setMessages([]);
        setCurrentStreamingMessage('');
        streamingMessageRef.current = '';
        setError(null);
        setActiveConversationId(null);
    }, []);

    // Create new session via WebSocket
    const createNewSession = useCallback(() => {
        // Clear local state
        setMessages([]);
        setCurrentStreamingMessage('');
        streamingMessageRef.current = '';
        setError(null);
        setActiveConversationId(null);
        // Tell backend to create new session
        return sendNewSession();
    }, [sendNewSession]);

    return {
        messages,
        isStreaming,
        currentStreamingMessage,
        isConnected,
        error,
        pendingOperation,
        activeConversationId,
        sendMessage,
        loadMessages,
        clearMessages,
        clearPendingOperation,
        resetForNewConversation,
        createNewSession,
    };
};
