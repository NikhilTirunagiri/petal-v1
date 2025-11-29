-- Petal Backend - pgvector Migration
-- Run this in Supabase SQL Editor AFTER running supabase_setup.sql

-- Step 1: Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Step 2: Add embedding column to session_memories
ALTER TABLE session_memories
ADD COLUMN IF NOT EXISTS embedding vector(1536);

-- Step 3: Create index for vector similarity search
-- Using ivfflat for faster approximate nearest neighbor search
CREATE INDEX IF NOT EXISTS idx_memories_embedding
ON session_memories
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Step 4: Create function for semantic search within a session
CREATE OR REPLACE FUNCTION match_session_memories(
    query_embedding vector(1536),
    p_session_id uuid,
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id uuid,
    processed_text text,
    created_at timestamptz,
    similarity float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        id,
        processed_text,
        created_at,
        1 - (embedding <=> query_embedding) as similarity
    FROM session_memories
    WHERE
        session_id = p_session_id
        AND embedding IS NOT NULL
        AND 1 - (embedding <=> query_embedding) > match_threshold
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
$$;

-- Step 5: Create function for semantic search across all user sessions
CREATE OR REPLACE FUNCTION match_user_memories(
    query_embedding vector(1536),
    p_user_id text,
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 20
)
RETURNS TABLE (
    id uuid,
    session_id uuid,
    session_name text,
    processed_text text,
    created_at timestamptz,
    similarity float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        sm.id,
        sm.session_id,
        s.name as session_name,
        sm.processed_text,
        sm.created_at,
        1 - (sm.embedding <=> query_embedding) as similarity
    FROM session_memories sm
    JOIN sessions s ON sm.session_id = s.id
    WHERE
        sm.user_id = p_user_id
        AND sm.embedding IS NOT NULL
        AND 1 - (sm.embedding <=> query_embedding) > match_threshold
    ORDER BY sm.embedding <=> query_embedding
    LIMIT match_count;
$$;

-- Step 6: Create function to find similar memories (duplicate detection)
CREATE OR REPLACE FUNCTION find_similar_memories(
    check_embedding vector(1536),
    p_session_id uuid,
    similarity_threshold float DEFAULT 0.95,
    max_results int DEFAULT 5
)
RETURNS TABLE (
    id uuid,
    processed_text text,
    similarity float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        id,
        processed_text,
        1 - (embedding <=> check_embedding) as similarity
    FROM session_memories
    WHERE
        session_id = p_session_id
        AND embedding IS NOT NULL
        AND id != id  -- Exclude exact same record
        AND 1 - (embedding <=> check_embedding) > similarity_threshold
    ORDER BY embedding <=> check_embedding
    LIMIT max_results;
$$;

-- Verify setup
SELECT
    'pgvector extension' as component,
    CASE WHEN EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'vector'
    ) THEN 'Installed ✓' ELSE 'Not installed ✗' END as status
UNION ALL
SELECT
    'embedding column',
    CASE WHEN EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'session_memories' AND column_name = 'embedding'
    ) THEN 'Added ✓' ELSE 'Not added ✗' END
UNION ALL
SELECT
    'vector index',
    CASE WHEN EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE indexname = 'idx_memories_embedding'
    ) THEN 'Created ✓' ELSE 'Not created ✗' END;
