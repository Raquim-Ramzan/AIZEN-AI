/**
 * Custom React Hook for Session/Conversation Management
 * Manages conversation list and active session
 */

import { useState, useCallback, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { chatService } from '@/services/chat.service';
import type { Conversation } from '@/types/api.types';

interface Session {
    id: string;
    title: string;
    timestamp: string;
}

export const useSessions = () => {
    const queryClient = useQueryClient();
    const [activeSessionId, setActiveSessionId] = useState<string | null>(null);

    // Fetch all conversations
    const {
        data: conversations,
        isLoading,
        error,
        refetch,
    } = useQuery({
        queryKey: ['conversations'],
        queryFn: async () => {
            const response = await chatService.getConversations();
            return response.data || [];
        },
        staleTime: 1000 * 60 * 5, // 5 minutes
        retry: false, // Don't retry if backend is offline
        refetchOnWindowFocus: false, // Don't refetch on window focus
        initialData: [], // Start with empty array if backend is offline
    });

    // Convert conversations to UI sessions
    const sessions: Session[] = (conversations || []).map((conv) => ({
        id: conv.id,
        title: conv.title,
        timestamp: new Date(conv.created_at).toLocaleTimeString(),
    }));

    // Create new session
    const createSessionMutation = useMutation({
        mutationFn: async (title?: string) => {
            const response = await chatService.createConversation(title);
            return response.data;
        },
        onSuccess: (newConversation) => {
            // Invalidate and refetch conversations
            queryClient.invalidateQueries({ queryKey: ['conversations'] });

            if (newConversation) {
                setActiveSessionId(newConversation.id);
            }
        },
    });

    // Delete session
    const deleteSessionMutation = useMutation({
        mutationFn: async (id: string) => {
            await chatService.deleteConversation(id);
            return id;
        },
        onSuccess: (deletedId) => {
            // Invalidate and refetch conversations
            queryClient.invalidateQueries({ queryKey: ['conversations'] });

            // If deleted session was active, clear active session
            if (activeSessionId === deletedId) {
                setActiveSessionId(null);
            }
        },
    });

    // Rename session
    const renameSessionMutation = useMutation({
        mutationFn: async ({ id, title }: { id: string; title: string }) => {
            await chatService.renameConversation(id, title);
            return { id, title };
        },
        onSuccess: () => {
            // Invalidate and refetch conversations to get updated title
            queryClient.invalidateQueries({ queryKey: ['conversations'] });
        },
    });

    // Create new session
    const createSession = useCallback(
        async (title?: string) => {
            await createSessionMutation.mutateAsync(title);
        },
        [createSessionMutation]
    );

    // Delete session
    const deleteSession = useCallback(
        async (id: string) => {
            await deleteSessionMutation.mutateAsync(id);
        },
        [deleteSessionMutation]
    );

    // Rename session
    const renameSession = useCallback(
        async (id: string, title: string) => {
            await renameSessionMutation.mutateAsync({ id, title });
        },
        [renameSessionMutation]
    );

    // Select session
    const selectSession = useCallback((id: string) => {
        setActiveSessionId(id);
    }, []);

    // Set active session ID (called when backend creates a new conversation)
    const setActiveSession = useCallback((id: string | null) => {
        setActiveSessionId(id);
        // Refetch conversations to include the new one
        if (id) {
            queryClient.invalidateQueries({ queryKey: ['conversations'] });
        }
    }, [queryClient]);

    // Clear active session (for "New Chat" functionality)
    const clearActiveSession = useCallback(() => {
        setActiveSessionId(null);
    }, []);

    // Auto-select first session if none selected and sessions available
    // This shows recent conversation history on fresh load
    useEffect(() => {
        if (!activeSessionId && sessions.length > 0) {
            setActiveSessionId(sessions[0].id);
        }
    }, [sessions, activeSessionId]);

    return {
        sessions,
        activeSessionId,
        isLoading,
        error: error as Error | null,
        createSession,
        deleteSession,
        renameSession,
        selectSession,
        setActiveSession,
        clearActiveSession,
        refetch,
    };
};
