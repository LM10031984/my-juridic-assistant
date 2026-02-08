-- Setup script for Supabase database
-- Run this in your Supabase SQL Editor

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the legal_chunks table
CREATE TABLE IF NOT EXISTS legal_chunks (
    id SERIAL PRIMARY KEY,
    chunk_id VARCHAR(16) UNIQUE NOT NULL,
    text TEXT NOT NULL,
    embedding vector(1536),  -- Adjust dimension based on your embedding model

    -- Metadata fields
    layer VARCHAR(50),
    type VARCHAR(50),
    domaine VARCHAR(50),
    source_file VARCHAR(255),
    articles TEXT[],  -- Array of article numbers
    sous_themes TEXT[],  -- Array of sub-themes
    keywords TEXT[],  -- Array of keywords
    word_count INTEGER,
    has_context BOOLEAN,
    version_date VARCHAR(50),
    section_title TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for fast filtering
CREATE INDEX IF NOT EXISTS idx_domaine ON legal_chunks(domaine);
CREATE INDEX IF NOT EXISTS idx_type ON legal_chunks(type);
CREATE INDEX IF NOT EXISTS idx_layer ON legal_chunks(layer);
CREATE INDEX IF NOT EXISTS idx_source_file ON legal_chunks(source_file);

-- Create GIN indexes for array columns (faster text search in arrays)
CREATE INDEX IF NOT EXISTS idx_articles ON legal_chunks USING GIN(articles);
CREATE INDEX IF NOT EXISTS idx_sous_themes ON legal_chunks USING GIN(sous_themes);
CREATE INDEX IF NOT EXISTS idx_keywords ON legal_chunks USING GIN(keywords);

-- Create vector index for similarity search (HNSW for better performance)
CREATE INDEX IF NOT EXISTS idx_embedding ON legal_chunks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Create function for similarity search with metadata filters
CREATE OR REPLACE FUNCTION search_legal_chunks(
    query_embedding vector(1536),
    match_count INT DEFAULT 5,
    filter_domaine VARCHAR DEFAULT NULL,
    filter_type VARCHAR DEFAULT NULL,
    filter_layer VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    id INT,
    chunk_id VARCHAR,
    text TEXT,
    layer VARCHAR,
    type VARCHAR,
    domaine VARCHAR,
    source_file VARCHAR,
    articles TEXT[],
    sous_themes TEXT[],
    keywords TEXT[],
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        lc.id,
        lc.chunk_id,
        lc.text,
        lc.layer,
        lc.type,
        lc.domaine,
        lc.source_file,
        lc.articles,
        lc.sous_themes,
        lc.keywords,
        1 - (lc.embedding <=> query_embedding) AS similarity
    FROM legal_chunks lc
    WHERE
        (filter_domaine IS NULL OR lc.domaine = filter_domaine)
        AND (filter_type IS NULL OR lc.type = filter_type)
        AND (filter_layer IS NULL OR lc.layer = filter_layer)
    ORDER BY lc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_legal_chunks_updated_at
    BEFORE UPDATE ON legal_chunks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust based on your RLS policies)
-- For now, allow anon and authenticated users to read
ALTER TABLE legal_chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access" ON legal_chunks
    FOR SELECT
    USING (true);

-- Only allow service role to insert/update/delete
CREATE POLICY "Allow service role all access" ON legal_chunks
    FOR ALL
    USING (auth.role() = 'service_role');
