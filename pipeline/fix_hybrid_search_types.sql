-- Fix pour les types de données dans hybrid_search_rrf

-- Recréer la fonction avec les bons types (REAL au lieu de FLOAT)
CREATE OR REPLACE FUNCTION hybrid_search_rrf(
    query_text TEXT,
    query_embedding vector(768),
    match_count INT DEFAULT 10,
    filter_domaine VARCHAR DEFAULT NULL,
    filter_type VARCHAR DEFAULT NULL,
    filter_layer VARCHAR DEFAULT NULL,
    similarity_threshold REAL DEFAULT 0.3,
    rrf_k INT DEFAULT 60
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
    vector_similarity REAL,
    fulltext_rank REAL,
    combined_score DOUBLE PRECISION
)
LANGUAGE plpgsql
AS $$
DECLARE
    tsquery_text TEXT;
BEGIN
    tsquery_text := regexp_replace(query_text, '\s+', ' & ', 'g');

    RETURN QUERY
    WITH
    vector_search AS (
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
            (1 - (lc.embedding <=> query_embedding))::REAL AS similarity,
            ROW_NUMBER() OVER (ORDER BY lc.embedding <=> query_embedding) AS rank
        FROM legal_chunks lc
        WHERE
            (filter_domaine IS NULL OR lc.domaine = filter_domaine)
            AND (filter_type IS NULL OR lc.type = filter_type)
            AND (filter_layer IS NULL OR lc.layer = filter_layer)
            AND (1 - (lc.embedding <=> query_embedding)) >= similarity_threshold
        ORDER BY lc.embedding <=> query_embedding
        LIMIT 50
    ),
    fulltext_search AS (
        SELECT
            lc.id,
            lc.chunk_id,
            ts_rank(lc.search_vector, to_tsquery('french', tsquery_text))::REAL AS rank_score,
            ROW_NUMBER() OVER (ORDER BY ts_rank(lc.search_vector, to_tsquery('french', tsquery_text)) DESC) AS rank
        FROM legal_chunks lc
        WHERE
            lc.search_vector @@ to_tsquery('french', tsquery_text)
            AND (filter_domaine IS NULL OR lc.domaine = filter_domaine)
            AND (filter_type IS NULL OR lc.type = filter_type)
            AND (filter_layer IS NULL OR lc.layer = filter_layer)
        ORDER BY rank_score DESC
        LIMIT 50
    ),
    rrf_fusion AS (
        SELECT
            COALESCE(vs.id, fs.id) AS id,
            COALESCE(1.0 / (rrf_k + vs.rank), 0.0) AS vector_score,
            COALESCE(1.0 / (rrf_k + fs.rank), 0.0) AS fulltext_score,
            (COALESCE(1.0 / (rrf_k + vs.rank), 0.0) + COALESCE(1.0 / (rrf_k + fs.rank), 0.0))::DOUBLE PRECISION AS combined_score
        FROM vector_search vs
        FULL OUTER JOIN fulltext_search fs ON vs.id = fs.id
    )
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
        vs.similarity AS vector_similarity,
        fs.rank_score AS fulltext_rank,
        rrf.combined_score
    FROM rrf_fusion rrf
    JOIN legal_chunks lc ON lc.id = rrf.id
    LEFT JOIN vector_search vs ON vs.id = rrf.id
    LEFT JOIN fulltext_search fs ON fs.id = rrf.id
    ORDER BY rrf.combined_score DESC
    LIMIT match_count;
END;
$$;

-- Test rapide
SELECT 'Fonction hybrid_search_rrf mise à jour avec succès' AS status;
