-- Setup script for Supabase with 768-dimension embeddings (local model)
-- Run this AFTER running setup_supabase.sql

-- Drop existing vector column and recreate with correct dimension
ALTER TABLE legal_chunks DROP COLUMN IF EXISTS embedding CASCADE;
ALTER TABLE legal_chunks ADD COLUMN embedding vector(768);

-- Recreate vector index with new dimension
DROP INDEX IF EXISTS idx_embedding;
CREATE INDEX idx_embedding ON legal_chunks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
