-- AIZEN Cloud Agent - Supabase Migration Schema
-- Run this in your Supabase SQL Editor (Idempotent Version)

-- Enable the pgvector extension to work with embedding vectors
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;

-- Disable RLS for all tables (Personal Local-First Setup)
ALTER TABLE IF EXISTS public.profiles DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.conversations DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.messages DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.memories DISABLE ROW LEVEL SECURITY;

-- 1. Profiles Table (Replaces core_memory.json)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON public.profiles(user_id);

-- 2. Conversations Table (Replaces SQLite conversations table)
CREATE TABLE IF NOT EXISTS public.conversations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON public.conversations(user_id);

-- 3. Messages Table (Replaces SQLite messages table)
CREATE TABLE IF NOT EXISTS public.messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON public.messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON public.messages(created_at);

-- 4. Memories Table (Replaces ChromaDB)
-- Using 384 dimensions for FastEmbed / BAAI/bge-small-en-v1.5
CREATE TABLE IF NOT EXISTS public.memories (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding public.vector(384),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create an index for faster vector search
CREATE INDEX IF NOT EXISTS idx_memories_embedding ON public.memories USING hnsw (embedding public.vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_memories_user_id ON public.memories(user_id);

-- 5. RPC Function for Vector Similarity Search (Hardened & Idempotent)
CREATE OR REPLACE FUNCTION public.match_memories(
    query_embedding public.vector(384),
    match_threshold FLOAT,
    match_count INT,
    p_user_id TEXT
)
RETURNS TABLE (
    id TEXT,
    user_id TEXT,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.id,
        m.user_id,
        m.content,
        m.metadata,
        1 - (m.embedding OPERATOR(public.<=>) query_embedding) AS similarity
    FROM public.memories m
    WHERE m.user_id = p_user_id
        AND 1 - (m.embedding OPERATOR(public.<=>) query_embedding) > match_threshold
    ORDER BY m.embedding OPERATOR(public.<=>) query_embedding
    LIMIT match_count;
END;
$$;
