/**
 * HTTP API Client for AIZEN Backend
 * Handles all REST API requests with error handling, retries, and logging
 */

import { API_CONFIG, getApiUrl } from '@/config/api.config';
import type { ApiResponse } from '@/types/api.types';

class ApiClient {
    private baseUrl: string;
    private timeout: number;
    private retryAttempts: number;
    private retryDelay: number;

    constructor() {
        this.baseUrl = API_CONFIG.BASE_URL;
        this.timeout = API_CONFIG.TIMEOUT;
        this.retryAttempts = API_CONFIG.RETRY_ATTEMPTS;
        this.retryDelay = API_CONFIG.RETRY_DELAY;
    }

    /**
     * Generic request method with retry logic
     */
    private async request<T>(
        endpoint: string,
        options: RequestInit = {},
        attempt: number = 1
    ): Promise<ApiResponse<T>> {
        const url = getApiUrl(endpoint);

        // Set default headers
        const headers = new Headers(options.headers);
        if (!headers.has('Content-Type') && options.body) {
            headers.set('Content-Type', 'application/json');
        }

        const config: RequestInit = {
            ...options,
            headers,
            signal: AbortSignal.timeout(this.timeout),
        };

        try {
            if (API_CONFIG.DEBUG) {
                console.log(`[API] ${options.method || 'GET'} ${url}`, options.body);
            }

            const response = await fetch(url, config);
            const data = await response.json().catch(() => null);

            if (!response.ok) {
                throw new Error(data?.detail || data?.message || `HTTP ${response.status}`);
            }

            if (API_CONFIG.DEBUG) {
                console.log(`[API] Response:`, data);
            }

            return {
                data,
                status: response.status,
            };
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';

            // Retry logic for network errors
            if (attempt < this.retryAttempts && this.shouldRetry(error)) {
                if (API_CONFIG.DEBUG) {
                    console.log(`[API] Retrying request (${attempt}/${this.retryAttempts})...`);
                }
                await this.delay(this.retryDelay * attempt);
                return this.request<T>(endpoint, options, attempt + 1);
            }

            if (API_CONFIG.DEBUG) {
                console.error(`[API] Error:`, errorMessage);
            }

            return {
                error: errorMessage,
                status: 0,
            };
        }
    }

    /**
     * Determine if request should be retried
     */
    private shouldRetry(error: unknown): boolean {
        // Retry on network errors or timeouts
        if (error instanceof TypeError) return true;
        if (error && typeof error === 'object' && 'name' in error && error.name === 'AbortError') return true;
        if (error && typeof error === 'object' && 'message' in error && typeof error.message === 'string' && error.message.includes('fetch')) return true;

        return false;
    }

    /**
     * Delay helper for retries
     */
    private delay(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // ============================================
    // HTTP Methods
    // ============================================

    async get<T>(endpoint: string, params?: Record<string, string | number | boolean | null | undefined>): Promise<ApiResponse<T>> {
        let url = endpoint;

        if (params) {
            const searchParams = new URLSearchParams();
            Object.entries(params).forEach(([key, value]) => {
                if (value !== undefined && value !== null) {
                    searchParams.append(key, String(value));
                }
            });
            url = `${endpoint}?${searchParams.toString()}`;
        }

        return this.request<T>(url, { method: 'GET' });
    }

    async post<T>(endpoint: string, body?: unknown): Promise<ApiResponse<T>> {
        return this.request<T>(endpoint, {
            method: 'POST',
            body: body ? JSON.stringify(body) : undefined,
        });
    }

    async put<T>(endpoint: string, body?: unknown): Promise<ApiResponse<T>> {
        return this.request<T>(endpoint, {
            method: 'PUT',
            body: body ? JSON.stringify(body) : undefined,
        });
    }

    async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
        return this.request<T>(endpoint, { method: 'DELETE' });
    }

    async patch<T>(endpoint: string, body?: unknown): Promise<ApiResponse<T>> {
        return this.request<T>(endpoint, {
            method: 'PATCH',
            body: body ? JSON.stringify(body) : undefined,
        });
    }

    /**
     * Upload files (multipart/form-data)
     */
    async upload<T>(endpoint: string, formData: FormData): Promise<ApiResponse<T>> {
        return this.request<T>(endpoint, {
            method: 'POST',
            body: formData,
            // Don't set Content-Type header for FormData - browser will set it with boundary
            headers: {},
        });
    }

    /**
     * Download blob data
     */
    async download(endpoint: string): Promise<Blob | null> {
        try {
            const url = getApiUrl(endpoint);
            const response = await fetch(url, {
                signal: AbortSignal.timeout(this.timeout),
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            return await response.blob();
        } catch (error) {
            console.error('[API] Download error:', error);
            return null;
        }
    }
}

// Export singleton instance
export const apiClient = new ApiClient();
