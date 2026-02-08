-- Mise à jour des search_vectors pour les 5 nouveaux chunks
-- (IDs 183-187)

UPDATE legal_chunks
SET search_vector = to_tsvector('french',
    COALESCE(text, '') || ' ' ||
    COALESCE(domaine, '') || ' ' ||
    COALESCE(array_to_string(sous_themes, ' '), '') || ' ' ||
    COALESCE(array_to_string(keywords, ' '), '') || ' ' ||
    COALESCE(array_to_string(articles, ' '), '')
)
WHERE id IN (183, 184, 185, 186, 187);

-- Vérifier les résultats
SELECT
    id,
    chunk_id,
    domaine,
    source_file,
    CASE
        WHEN search_vector IS NOT NULL THEN 'OK'
        ELSE 'MISSING'
    END as search_vector_status
FROM legal_chunks
WHERE id IN (183, 184, 185, 186, 187)
ORDER BY id;
