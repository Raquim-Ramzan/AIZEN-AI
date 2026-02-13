/**
 * WebSocket Client for Real-time AI Streaming
 * Handles WebSocket connection with auto-reconnection and message handling
 */

import { API_CONFIG, getWsUrl, generateClientId } from '@/config/api.config';
import type { WebSocketMessage, WebSocketMessageType, MessageMetadata } from '@/types/api.types';

type MessageHandler = (message: WebSocketMessage) => void;
type ConnectionHandler = (connected: boolean) => void;
type ErrorHandler = (error: Error) => void;

export class WebSocketClient {
    private ws: WebSocket | null = null;
    private clientId: string;
    private reconnectAttempts: number = 0;
    private reconnectTimeout: NodeJS.Timeout | null = null;
    private pingInterval: NodeJS.Timeout | null = null;
    private isManualClose: boolean = false;

    private messageHandlers: Map<WebSocketMessageType, MessageHandler[]> = new Map();
    private connectionHandlers: ConnectionHandler[] = [];
    private errorHandlers: ErrorHandler[] = [];

    constructor(clientId?: string) {
        this.clientId = clientId || generateClientId();
    }

    /**
     * Connect to WebSocket server
     */
    connect(): void {
        if (this.ws?.readyState === WebSocket.OPEN) {
            if (API_CONFIG.DEBUG) {
                console.log('[WS] Already connected');
            }
            return;
        }

        this.isManualClose = false;
        const wsUrl = getWsUrl(API_CONFIG.ENDPOINTS.WEBSOCKET(this.clientId));

        if (API_CONFIG.DEBUG) {
            console.log(`[WS] Connecting to ${wsUrl}...`);
        }

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = this.handleOpen.bind(this);
            this.ws.onmessage = this.handleMessage.bind(this);
            this.ws.onerror = this.handleError.bind(this);
            this.ws.onclose = this.handleClose.bind(this);
        } catch (error) {
            console.error('[WS] Connection error:', error);
            this.scheduleReconnect();
        }
    }

    /**
     * Disconnect from WebSocket server
     */
    disconnect(): void {
        this.isManualClose = true;
        this.clearReconnectTimeout();
        this.clearPingInterval();

        if (this.ws) {
            this.ws.close(1000, 'Client disconnect');
            this.ws = null;
        }

        if (API_CONFIG.DEBUG) {
            console.log('[WS] Disconnected');
        }
    }

    /**
     * Send message through WebSocket
     */
    send(message: WebSocketMessage): boolean {
        if (this.ws?.readyState !== WebSocket.OPEN) {
            console.error('[WS] Cannot send - not connected');
            return false;
        }

        try {
            this.ws.send(JSON.stringify(message));

            if (API_CONFIG.DEBUG) {
                console.log('[WS] Sent:', message);
            }

            return true;
        } catch (error) {
            console.error('[WS] Send error:', error);
            return false;
        }
    }

    /**
     * Send chat message
     */
    sendChatMessage(
        content: string,
        conversationId?: string | null,
        metadata?: MessageMetadata
    ): boolean {
        return this.send({
            type: 'message',
            conversation_id: conversationId,
            content,
            metadata,
        });
    }

    // ============================================
    // Event Handlers
    // ============================================

    private handleOpen(): void {
        if (API_CONFIG.DEBUG) {
            console.log('[WS] Connected successfully');
        }

        this.reconnectAttempts = 0;
        this.startPing();
        this.notifyConnectionHandlers(true);
    }

    private handleMessage(event: MessageEvent): void {
        try {
            const message: WebSocketMessage = JSON.parse(event.data);

            if (API_CONFIG.DEBUG && message.type !== 'pong') {
                console.log('[WS] Received:', message);
            }

            // Handle pong responses
            if (message.type === 'pong') {
                return;
            }

            // Notify specific type handlers
            const handlers = this.messageHandlers.get(message.type) || [];
            handlers.forEach(handler => handler(message));

            // Notify wildcard handlers
            const wildcardHandlers = this.messageHandlers.get('status') || [];
            wildcardHandlers.forEach(handler => handler(message));
        } catch (error) {
            console.error('[WS] Message parse error:', error);
        }
    }

    private handleError(event: Event): void {
        const error = new Error('WebSocket error');
        console.error('[WS] Error:', event);
        this.notifyErrorHandlers(error);
    }

    private handleClose(event: CloseEvent): void {
        if (API_CONFIG.DEBUG) {
            console.log(`[WS] Closed: ${event.code} ${event.reason}`);
        }

        this.clearPingInterval();
        this.notifyConnectionHandlers(false);

        // Auto-reconnect if not manually closed
        if (!this.isManualClose) {
            this.scheduleReconnect();
        }
    }

    // ============================================
    // Reconnection Logic
    // ============================================

    private scheduleReconnect(): void {
        if (this.reconnectAttempts >= API_CONFIG.WS_MAX_RECONNECT_ATTEMPTS) {
            console.error('[WS] Max reconnection attempts reached');
            return;
        }

        this.clearReconnectTimeout();

        const delay = API_CONFIG.WS_RECONNECT_DELAY * Math.pow(2, this.reconnectAttempts);
        this.reconnectAttempts++;

        if (API_CONFIG.DEBUG) {
            console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})...`);
        }

        this.reconnectTimeout = setTimeout(() => {
            this.connect();
        }, delay);
    }

    private clearReconnectTimeout(): void {
        if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout);
            this.reconnectTimeout = null;
        }
    }

    // ============================================
    // Ping/Pong Keep-Alive
    // ============================================

    private startPing(): void {
        this.clearPingInterval();

        this.pingInterval = setInterval(() => {
            if (this.ws?.readyState === WebSocket.OPEN) {
                this.send({ type: 'ping' });
            }
        }, API_CONFIG.WS_PING_INTERVAL);
    }

    private clearPingInterval(): void {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }

    // ============================================
    // Event Subscription
    // ============================================

    on(type: WebSocketMessageType, handler: MessageHandler): () => void {
        if (!this.messageHandlers.has(type)) {
            this.messageHandlers.set(type, []);
        }
        this.messageHandlers.get(type)!.push(handler);

        // Return unsubscribe function
        return () => {
            const handlers = this.messageHandlers.get(type) || [];
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        };
    }

    onConnection(handler: ConnectionHandler): () => void {
        this.connectionHandlers.push(handler);
        return () => {
            const index = this.connectionHandlers.indexOf(handler);
            if (index > -1) {
                this.connectionHandlers.splice(index, 1);
            }
        };
    }

    onError(handler: ErrorHandler): () => void {
        this.errorHandlers.push(handler);
        return () => {
            const index = this.errorHandlers.indexOf(handler);
            if (index > -1) {
                this.errorHandlers.splice(index, 1);
            }
        };
    }

    // ============================================
    // Notification Helpers
    // ============================================

    private notifyConnectionHandlers(connected: boolean): void {
        this.connectionHandlers.forEach(handler => handler(connected));
    }

    private notifyErrorHandlers(error: Error): void {
        this.errorHandlers.forEach(handler => handler(error));
    }

    // ============================================
    // Utility Methods
    // ============================================

    isConnected(): boolean {
        return this.ws?.readyState === WebSocket.OPEN;
    }

    getClientId(): string {
        return this.clientId;
    }
}

// Export singleton instance
export const websocketClient = new WebSocketClient();
