-- Mise à jour des search_vectors pour tous les nouveaux chunks
-- À exécuter après l'indexation

-- ÉTAPE 1 : Mise à jour des search_vectors pour les chunks sans search_vector
UPDATE legal_chunks
SET search_vector = to_tsvector('french',
    COALESCE(text, '') || ' ' ||
    COALESCE(domaine, '') || ' ' ||
    COALESCE(array_to_string(sous_themes, ' '), '') || ' ' ||
    COALESCE(array_to_string(keywords, ' '), '') || ' ' ||
    COALESCE(array_to_string(articles, ' '), '')
)
WHERE search_vector IS NULL;

-- ÉTAPE 2 : Vérification
SELECT
    COUNT(*) as total_chunks,
    COUNT(search_vector) as with_search_vector,
    COUNT(*) - COUNT(search_vector) as missing_search_vector
FROM legal_chunks;

-- ÉTAPE 3 : Statistiques par domaine
SELECT
    domaine,
    COUNT(*) as nb_chunks,
    COUNT(search_vector) as with_search_vector,
    ROUND(AVG(word_count), 0) as avg_words
FROM legal_chunks
GROUP BY domaine
ORDER BY domaine;

-- ÉTAPE 4 : Derniers chunks insérés
SELECT
    id,
    chunk_id,
    domaine,
    source_file,
    word_count,
    CASE
        WHEN search_vector IS NOT NULL THEN 'OK'
        ELSE 'MISSING'
    END as search_vector_status
FROM legal_chunks
ORDER BY id DESC
LIMIT 20;
