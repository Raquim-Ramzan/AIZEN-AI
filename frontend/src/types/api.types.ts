/**
 * TypeScript types matching the backend API models
 * These interfaces ensure type safety when communicating with the FastAPI backend
 * 
 * Phase 3: Strict typing for @typescript-eslint/no-explicit-any compliance
 */

// ============================================
// Base Types (Strict)
// ============================================

/** Generic metadata structure for extensibility */
export interface BaseMetadata {
    [key: string]: string | number | boolean | null | undefined | BaseMetadata | BaseMetadata[];
}

/** Strict type for operation parameters (Alias to BaseMetadata for compatibility) */
export type OperationParameters = BaseMetadata;

/** Attached file metadata for vision/multimodal */
export interface AttachedFileMetadata {
    name: string;
    type: string;
    size: number;
    data: string;  // base64
}

/** Message metadata with strict typing */
export interface MessageMetadata {
    model?: string;
    tokens?: number;
    provider?: string;
    temperature?: number;
    tool_calls?: ToolCall[];
    attached_file?: AttachedFileMetadata;
    model_provider?: string;
    model_name?: string;
    pending_operations?: PendingOperation[];
}

/** Pending system operation requiring approval */
export interface PendingOperation {
    operation_id: string;
    tool: string;
    parameters: BaseMetadata;
    message?: string;
    risk_level?: string;
}

// ============================================
// Conversation & Message Types
// ============================================

export interface Conversation {
    id: string;
    title: string;
    created_at: string;
    updated_at?: string;
    metadata?: BaseMetadata;
}

export interface Message {
    id: string;
    conversation_id?: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
    metadata?: MessageMetadata;
}

/**
 * ChatMessage - Strict interface for chat UI components
 * Use this in ChatInterface.tsx and related components
 */
export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: number;  // Unix timestamp for UI sorting
    isStreaming?: boolean;
    error?: string;
    metadata?: {
        provider?: string;
        model?: string;
        tokens?: number;
        processingTime?: number;
    };
}

export interface ToolCall {
    id: string;
    name: string;
    parameters: BaseMetadata;
    result?: string | number | boolean | BaseMetadata;
}

// ============================================
// Chat Request/Response Types
// ============================================

export interface ChatRequest {
    message: string;
    conversation_id?: string | null;
    temperature?: number;
    use_ollama?: boolean;
    stream?: boolean;
    metadata?: MessageMetadata;
    // New multi-provider fields
    model_provider?: 'gemini' | 'groq' | 'perplexity' | 'ollama';
    model_name?: string;
    preferred_provider?: string;
}

export interface ChatResponse {
    response: string;
    conversation_id: string;
    message_id: string;
    content?: string; // NEW: Backend returns 'content' not 'response'
    metadata?: {
        model?: string;
        tokens?: number;
        processing_time?: number;
    };
    // New multi-provider fields
    provider?: string;
    model?: string;
}

// ============================================
// WebSocket Message Types
// ============================================

export type WebSocketMessageType =
    | 'message'
    | 'message_received'
    | 'token'
    | 'complete'
    | 'error'
    | 'ping'
    | 'pong'
    | 'status'
    | 'thinking'
    | 'stream_start'
    | 'tool_execution'
    | 'operation_approval_required'
    | 'session_cleared'
    | 'session_created'
    | 'new_session'
    | 'title_updated';

export interface WebSocketMessage {
    type: WebSocketMessageType;
    conversation_id?: string | null;
    content?: string;
    metadata?: MessageMetadata;
    error?: string;
    full_response?: string;
    message_id?: string;
    // NEW: Multi-provider metadata
    provider?: string;
    model?: string;
    selected_provider?: string;
    selected_model?: string;
    // NEW: System operation fields
    operation_id?: string;
    tool?: string;
    parameters?: OperationParameters;
    message?: string;
    risk_level?: string;
}

// ============================================
// Memory Types
// ============================================

export interface CoreMemory {
    user_profile: {
        name?: string;
        preferences?: BaseMetadata;
        [key: string]: string | number | boolean | null | undefined | BaseMetadata | BaseMetadata[];
    };
    facts: MemoryFact[];
    conversation_summaries: ConversationSummary[];
    unlocked_skills: string[];
}

export interface MemoryFact {
    id: string;
    content: string;
    timestamp: string;
    confidence?: number;
    metadata?: BaseMetadata;
}

export interface ConversationSummary {
    conversation_id: string;
    summary: string;
    timestamp: string;
    key_points?: string[];
}

export interface MemorySearchRequest {
    query: string;
    top_k?: number;
    threshold?: number;
    [key: string]: string | number | boolean | undefined;
}

export interface MemorySearchResult {
    results: Array<{
        content: string;
        score: number;
        metadata?: BaseMetadata;
    }>;
}

// ============================================
// Tool Types
// ============================================

export interface Tool {
    name: string;
    description: string;
    parameters: {
        type: string;
        properties: BaseMetadata;
        required: string[];
    };
}

export interface ToolExecuteRequest {
    tool_name: string;
    parameters: BaseMetadata;
}

export interface ToolExecuteResponse {
    result: unknown;
    success: boolean;
    error?: string;
    metadata?: BaseMetadata;
}

// ============================================
// Speech Types
// ============================================

export interface TranscribeRequest {
    audio: Blob | File;
    language?: string;
}

export interface TranscribeResponse {
    text: string;
    confidence?: number;
    language?: string;
    duration?: number;
}

export interface SynthesizeRequest {
    text: string;
    voice?: string;
    speed?: number;
}

export interface SynthesizeResponse {
    audio: Blob;
    duration?: number;
}

// ============================================
// System Types
// ============================================

export interface HealthStatus {
    status: string;
    perplexity: string;
    ollama: string;
    chromadb: string;
    mongodb: string;
}

export interface Settings {
    providers: {
        gemini: ProviderInfo;
        groq: ProviderInfo;
        perplexity: ProviderInfo;
        ollama: ProviderInfo;
    };
    model_preferences: {
        coding: string;
        chat: string;
        reasoning: string;
        search: string;
        research: string;
        image: string;
        embedding: string;
        stt: string;
        tts: string;
    };
    whisper_model: string;
    piper_model: string;
}

export interface ProviderInfo {
    configured: boolean;
    models: string[];
}

export interface AvailableModels {
    gemini: {
        available: boolean;
        models: ModelInfo[];
    };
    groq: {
        available: boolean;
        models: ModelInfo[];
    };
    perplexity: {
        available: boolean;
        models: ModelInfo[];
    };
    ollama: {
        available: boolean;
        models: ModelInfo[];
    };
}

export interface ModelInfo {
    name: string;
    description: string;
}

export interface ModelSelectRequest {
    task_type: string;
    manual_provider?: string;
    manual_model?: string;
}

export interface ModelSelectResponse {
    task_type: string;
    selected_provider: string;
    selected_model: string;
}

// ============================================
// API Response Wrapper
// ============================================

export interface ApiResponse<T = unknown> {
    data?: T;
    error?: string;
    status: number;
    message?: string;
}

// ============================================
// Connection Status Types
// ============================================

export type ConnectionState = 'connected' | 'disconnected' | 'connecting' | 'error';

export interface ConnectionStatus {
    state: ConnectionState;
    lastConnected?: Date;
    error?: string;
}
