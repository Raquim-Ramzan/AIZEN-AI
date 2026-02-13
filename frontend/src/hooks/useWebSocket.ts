/**
 * Custom React Hook for WebSocket Connection
 * Manages WebSocket lifecycle and provides real-time messaging
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { websocketClient } from '@/lib/websocket-client';
import type { WebSocketMessage, WebSocketMessageType, MessageMetadata } from '@/types/api.types';

interface UseWebSocketOptions {
    autoConnect?: boolean;
    onMessage?: (message: WebSocketMessage) => void;
    onError?: (error: Error) => void;
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
    const { autoConnect = true, onMessage, onError } = options;

    const [isConnected, setIsConnected] = useState(false);
    const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
    const unsubscribersRef = useRef<(() => void)[]>([]);

    // Connect to WebSocket
    const connect = useCallback(() => {
        websocketClient.connect();
    }, []);

    // Disconnect from WebSocket
    const disconnect = useCallback(() => {
        websocketClient.disconnect();
    }, []);

    // Send message
    const sendMessage = useCallback((message: WebSocketMessage) => {
        return websocketClient.send(message);
    }, []);

    // Send chat message (convenience method)
    const sendChatMessage = useCallback(
        (content: string, conversationId?: string | null, metadata?: MessageMetadata) => {
            return websocketClient.sendChatMessage(content, conversationId, metadata);
        },
        []
    );

    // Request new session (convenience method)
    const sendNewSession = useCallback(() => {
        return websocketClient.send({ type: 'new_session' } as WebSocketMessage);
    }, []);

    // Subscribe to specific message types
    const subscribe = useCallback((type: WebSocketMessageType, handler: (msg: WebSocketMessage) => void) => {
        const unsubscribe = websocketClient.on(type, handler);
        unsubscribersRef.current.push(unsubscribe);
        return unsubscribe;
    }, []);

    // Setup event listeners
    useEffect(() => {
        // Connection status handler
        const unsubConnection = websocketClient.onConnection((connected) => {
            setIsConnected(connected);
        });

        // Error handler
        const unsubError = websocketClient.onError((error) => {
            console.error('[useWebSocket] Error:', error);
            onError?.(error);
        });

        // Message handler - listen to all message types
        const unsubMessage = websocketClient.on('status', (message) => {
            setLastMessage(message);
            onMessage?.(message);
        });

        unsubscribersRef.current.push(unsubConnection, unsubError, unsubMessage);

        // Auto-connect if enabled
        if (autoConnect) {
            connect();
        }

        // Cleanup on unmount
        return () => {
            unsubscribersRef.current.forEach(unsub => unsub());
            unsubscribersRef.current = [];

            if (autoConnect) {
                disconnect();
            }
        };
    }, [autoConnect, connect, disconnect, onMessage, onError]);

    return {
        isConnected,
        lastMessage,
        connect,
        disconnect,
        sendMessage,
        sendChatMessage,
        sendNewSession,
        subscribe,
    };
};
