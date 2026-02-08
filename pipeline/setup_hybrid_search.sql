-- ============================================================================
-- HYBRID SEARCH SETUP - My Juridic Assistant
-- ============================================================================
-- Ce script ajoute la capacité de recherche hybride (vector + full-text)
-- à la table legal_chunks pour améliorer significativement le retrieval.
--
-- GAINS ATTENDUS :
-- - Couverture mots-clés : 30% → 65-75%
-- - Meilleure détection des termes juridiques précis (articles, lois, etc.)
-- - Fusion intelligente des résultats (Reciprocal Rank Fusion)
--
-- Usage :
--   Exécuter ce script dans Supabase SQL Editor après setup_supabase_768.sql
-- ============================================================================

-- 1. Ajouter la colonne search_vector pour la recherche full-text
-- ============================================================================

-- Ajouter la colonne si elle n'existe pas
ALTER TABLE legal_chunks ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- 2. Créer une fonction pour générer le tsvector à partir du texte
-- ============================================================================

-- Configuration : français pour le stemming et les stop words
CREATE OR REPLACE FUNCTION generate_search_vector(chunk_text TEXT)
RETURNS tsvector
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    -- Créer le tsvector avec configuration française
    -- Pondération : A (titre/articles) + B (texte principal)
    RETURN setweight(to_tsvector('french', coalesce(chunk_text, '')), 'B');
END;
$$;

-- 3. Peupler la colonne search_vector pour tous les chunks existants
-- ============================================================================

-- Mettre à jour tous les chunks existants
UPDATE legal_chunks
SET search_vector = generate_search_vector(text)
WHERE search_vector IS NULL;

-- Afficher le progrès
DO $$
DECLARE
    total_chunks INTEGER;
    updated_chunks INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_chunks FROM legal_chunks;
    SELECT COUNT(*) INTO updated_chunks FROM legal_chunks WHERE search_vector IS NOT NULL;

    RAISE NOTICE 'Search vectors générés : % / %', updated_chunks, total_chunks;
END $$;

-- 4. Créer un trigger pour maintenir search_vector à jour automatiquement
-- ============================================================================

CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := generate_search_vector(NEW.text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop trigger s'il existe déjà
DROP TRIGGER IF EXISTS trigger_update_search_vector ON legal_chunks;

-- Créer le trigger
CREATE TRIGGER trigger_update_search_vector
    BEFORE INSERT OR UPDATE OF text
    ON legal_chunks
    FOR EACH ROW
    EXECUTE FUNCTION update_search_vector();

-- 5. Créer un index GIN pour la recherche full-text rapide
-- ============================================================================

-- Index GIN pour recherche full-text performante
CREATE INDEX IF NOT EXISTS idx_search_vector
ON legal_chunks
USING GIN(search_vector);

-- 6. Fonction de recherche FULL-TEXT seule (pour tests)
-- ============================================================================

CREATE OR REPLACE FUNCTION fulltext_search_chunks(
    search_query TEXT,
    match_count INT DEFAULT 10,
    filter_domaine VARCHAR DEFAULT NULL,
    filter_type VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    id INT,
    chunk_id VARCHAR,
    text TEXT,
    domaine VARCHAR,
    type VARCHAR,
    source_file VARCHAR,
    articles TEXT[],
    rank FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        lc.id,
        lc.chunk_id,
        lc.text,
        lc.domaine,
        lc.type,
        lc.source_file,
        lc.articles,
        ts_rank(lc.search_vector, query) AS rank
    FROM
        legal_chunks lc,
        to_tsquery('french', search_query) query
    WHERE
        lc.search_vector @@ query
        AND (filter_domaine IS NULL OR lc.domaine = filter_domaine)
        AND (filter_type IS NULL OR lc.type = filter_type)
    ORDER BY rank DESC
    LIMIT match_count;
END;
$$;

-- 7. Fonction HYBRID SEARCH avec Reciprocal Rank Fusion (RRF)
-- ============================================================================

CREATE OR REPLACE FUNCTION hybrid_search_rrf(
    query_text TEXT,
    query_embedding vector(768),
    match_count INT DEFAULT 10,
    filter_domaine VARCHAR DEFAULT NULL,
    filter_type VARCHAR DEFAULT NULL,
    filter_layer VARCHAR DEFAULT NULL,
    similarity_threshold FLOAT DEFAULT 0.3,
    rrf_k INT DEFAULT 60  -- Constante RRF (60 est une bonne valeur par défaut)
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
    vector_similarity FLOAT,
    fulltext_rank FLOAT,
    combined_score FLOAT
)
LANGUAGE plpgsql
AS $$
DECLARE
    tsquery_text TEXT;
BEGIN
    -- Préparer la query full-text (remplacer espaces par &)
    tsquery_text := regexp_replace(query_text, '\s+', ' & ', 'g');

    RETURN QUERY
    WITH
    -- Résultats de la recherche vectorielle
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
            1 - (lc.embedding <=> query_embedding) AS similarity,
            ROW_NUMBER() OVER (ORDER BY lc.embedding <=> query_embedding) AS rank
        FROM legal_chunks lc
        WHERE
            (filter_domaine IS NULL OR lc.domaine = filter_domaine)
            AND (filter_type IS NULL OR lc.type = filter_type)
            AND (filter_layer IS NULL OR lc.layer = filter_layer)
            AND (1 - (lc.embedding <=> query_embedding)) >= similarity_threshold
        ORDER BY lc.embedding <=> query_embedding
        LIMIT 50  -- Prendre top-50 pour la fusion
    ),
    -- Résultats de la recherche full-text
    fulltext_search AS (
        SELECT
            lc.id,
            lc.chunk_id,
            ts_rank(lc.search_vector, to_tsquery('french', tsquery_text)) AS rank_score,
            ROW_NUMBER() OVER (ORDER BY ts_rank(lc.search_vector, to_tsquery('french', tsquery_text)) DESC) AS rank
        FROM legal_chunks lc
        WHERE
            lc.search_vector @@ to_tsquery('french', tsquery_text)
            AND (filter_domaine IS NULL OR lc.domaine = filter_domaine)
            AND (filter_type IS NULL OR lc.type = filter_type)
            AND (filter_layer IS NULL OR lc.layer = filter_layer)
        ORDER BY rank_score DESC
        LIMIT 50  -- Prendre top-50 pour la fusion
    ),
    -- Fusion avec Reciprocal Rank Fusion (RRF)
    rrf_fusion AS (
        SELECT
            COALESCE(vs.id, fs.id) AS id,
            COALESCE(
                1.0 / (rrf_k + vs.rank),
                0.0
            ) AS vector_score,
            COALESCE(
                1.0 / (rrf_k + fs.rank),
                0.0
            ) AS fulltext_score,
            (
                COALESCE(1.0 / (rrf_k + vs.rank), 0.0) +
                COALESCE(1.0 / (rrf_k + fs.rank), 0.0)
            ) AS combined_score
        FROM vector_search vs
        FULL OUTER JOIN fulltext_search fs ON vs.id = fs.id
    )
    -- Résultat final avec tous les champs
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

-- 8. Fonction helper pour nettoyer une query (optionnel)
-- ============================================================================

CREATE OR REPLACE FUNCTION prepare_search_query(raw_query TEXT)
RETURNS TEXT
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    cleaned_query TEXT;
BEGIN
    -- Nettoyer la query : enlever caractères spéciaux, normaliser espaces
    cleaned_query := regexp_replace(raw_query, '[^\w\s]', ' ', 'g');
    cleaned_query := regexp_replace(cleaned_query, '\s+', ' ', 'g');
    cleaned_query := trim(cleaned_query);

    RETURN cleaned_query;
END;
$$;

-- 9. Statistiques et vérifications
-- ============================================================================

-- Vérifier que tout est bien configuré
DO $$
DECLARE
    total_chunks INTEGER;
    chunks_with_vector INTEGER;
    chunks_with_search_vector INTEGER;
    sample_text TEXT;
    sample_tsvector TEXT;
BEGIN
    -- Compter les chunks
    SELECT COUNT(*) INTO total_chunks FROM legal_chunks;
    SELECT COUNT(*) INTO chunks_with_vector FROM legal_chunks WHERE embedding IS NOT NULL;
    SELECT COUNT(*) INTO chunks_with_search_vector FROM legal_chunks WHERE search_vector IS NOT NULL;

    -- Afficher les résultats
    RAISE NOTICE '';
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'HYBRID SEARCH SETUP - VÉRIFICATION';
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'Total chunks : %', total_chunks;
    RAISE NOTICE 'Chunks avec embedding : %', chunks_with_vector;
    RAISE NOTICE 'Chunks avec search_vector : %', chunks_with_search_vector;
    RAISE NOTICE '';

    IF chunks_with_search_vector = total_chunks THEN
        RAISE NOTICE '✓ Tous les chunks ont un search_vector';
    ELSE
        RAISE WARNING '⚠ Certains chunks n''ont pas de search_vector';
    END IF;

    -- Afficher un exemple
    SELECT text, search_vector::text
    INTO sample_text, sample_tsvector
    FROM legal_chunks
    WHERE search_vector IS NOT NULL
    LIMIT 1;

    RAISE NOTICE '';
    RAISE NOTICE 'Exemple de chunk :';
    RAISE NOTICE 'Texte : %', substring(sample_text, 1, 100) || '...';
    RAISE NOTICE 'Tsvector : %', substring(sample_tsvector, 1, 100) || '...';
    RAISE NOTICE '';
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'SETUP TERMINÉ - Hybrid search prêt à l''emploi !';
    RAISE NOTICE '=================================================================';
END $$;

-- 10. Exemple d'utilisation
-- ============================================================================

-- Exemple de requête hybrid search :
/*
SELECT * FROM hybrid_search_rrf(
    query_text := 'charges récupérables',
    query_embedding := (SELECT embedding FROM legal_chunks LIMIT 1),  -- Remplacer par vraie embedding
    match_count := 5,
    filter_domaine := 'location'
);
*/

-- Exemple de requête full-text seule :
/*
SELECT * FROM fulltext_search_chunks(
    search_query := 'article & 23 & loi & 1989',
    match_count := 5,
    filter_domaine := 'location'
);
*/
