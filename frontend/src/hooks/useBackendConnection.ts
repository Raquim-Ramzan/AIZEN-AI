/**
 * Custom React Hook for Backend Connection Status
 * Monitors backend health and connection state
 */

import { useState, useEffect, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { systemService } from '@/services/system.service';
import type { ConnectionState } from '@/types/api.types';

export const useBackendConnection = () => {
    const [connectionState, setConnectionState] = useState<ConnectionState>('connecting');
    const [lastConnected, setLastConnected] = useState<Date | null>(null);

    // Poll health endpoint
    const {
        data: healthData,
        isError,
        isLoading,
    } = useQuery({
        queryKey: ['health'],
        queryFn: async () => {
            const response = await systemService.getHealth();
            return response.data;
        },
        refetchInterval: 10000, // Poll every 10 seconds
        retry: 1, // Only retry once if backend is offline
        refetchOnWindowFocus: false, // Don't refetch on window focus
    });

    // Update connection state based on health check
    useEffect(() => {
        if (isLoading) {
            setConnectionState('connecting');
        } else if (isError) {
            setConnectionState('error');
        } else if (healthData) {
            setConnectionState('connected');
            setLastConnected(new Date());
        } else {
            setConnectionState('disconnected');
        }
    }, [healthData, isError, isLoading]);

    // Manual health check
    const checkHealth = useCallback(async () => {
        try {
            const response = await systemService.getHealth();
            if (response.data) {
                setConnectionState('connected');
                setLastConnected(new Date());
                return true;
            }
            return false;
        } catch (error) {
            setConnectionState('error');
            return false;
        }
    }, []);

    return {
        connectionState,
        lastConnected,
        healthData,
        checkHealth,
        isConnected: connectionState === 'connected',
    };
};
