-- Fix embedding dimension from 1536 to 768
-- Run this in Supabase SQL Editor

-- Step 1: Drop the existing embedding column
ALTER TABLE legal_chunks DROP COLUMN IF EXISTS embedding CASCADE;

-- Step 2: Add new embedding column with 768 dimensions
ALTER TABLE legal_chunks ADD COLUMN embedding vector(768);

-- Step 3: Recreate the vector index
DROP INDEX IF EXISTS idx_embedding;
CREATE INDEX idx_embedding ON legal_chunks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
