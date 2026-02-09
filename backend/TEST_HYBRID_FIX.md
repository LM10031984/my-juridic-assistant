# Test du Correctif Hybrid Search - Affichage des Scores

## Résumé des Changements

### 1. `backend/api/services/retrieval.py` (lignes 236-246)
**Problème** : Le score RRF (0.02-0.04) écrasait `similarity` et était affiché comme "2-4%"
**Solution** :
- Stocke `rrf_score` séparément
- Conserve `vector_similarity` comme score principal
- Ajoute `vector_rank` pour diagnostic

```python
# AVANT
chunk['similarity'] = chunk.get('combined_score', 0.0)  # ❌ Écrase similarity

# APRÈS
chunk['rrf_score'] = chunk.get('combined_score', 0.0)  # ✅ Score RRF séparé
chunk['similarity'] = chunk.get('vector_similarity', 0.0)  # ✅ Garde vector_similarity
```

### 2. `backend/api/routes/ask.py` (lignes 179-220)
**Problème** : Affichage trompeur "Pertinence: 2%" en mode hybrid
**Solution** :
- Affiche `vector_similarity` en % lisible (ex: "86% (vector)")
- Affiche `rrf_score` en brut pour debug (optionnel)
- Corrige duplication "Article Article X"

```python
# AVANT
sources.append(f"{source_ref} - Pertinence: {chunk['similarity']:.0%}")
# Affichait "2%" avec RRF score

# APRÈS
if method_used == "hybrid":
    vector_sim = chunk.get('vector_similarity', chunk.get('similarity', 0.0))
    pertinence_str = f"Pertinence: {vector_sim:.0%} (vector)"
    if chunk.get('rrf_score'):
        pertinence_str += f" | RRF: {chunk['rrf_score']:.4f}"
else:
    pertinence_str = f"Pertinence: {chunk['similarity']:.0%}"
# Affiche "86% (vector) | RRF: 0.0321"
```

### 3. Logs de Diagnostic (lignes 83-98)
**Ajout** : Logs détaillés des top 3 chunks après retrieval
- Affiche `source_file`, `domaine`, `type`
- Affiche tous les scores selon la méthode (hybrid/vector)
- Affiche les ranks pour diagnostic

### 4. Endpoint `/ask/debug` (lignes 249-319)
**Ajout** : Endpoint de diagnostic complet sans génération de réponse
- Retourne tous les détails des chunks trouvés
- Permet de comparer hybrid vs vector
- Utile pour diagnostiquer les problèmes de pertinence

---

## Tests de Validation

### Prerequisites
```bash
# 1. S'assurer que l'API tourne
cd backend
python -m api.main

# 2. Vérifier que hybrid search est activé
# Devrait afficher "HYBRID SEARCH (vector + full-text)"
```

### Test 1: Endpoint de diagnostic `/ask/debug`

**Test A - Question sur transaction**
```bash
curl -X POST http://localhost:8000/api/ask/debug \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quelles sont les obligations du vendeur concernant les diagnostics immobiliers ?",
    "domaine": "transaction"
  }'
```

**Résultat attendu** :
```json
{
  "query": "Quelles sont les obligations du vendeur...",
  "domaine_filter": "transaction",
  "method_used": "hybrid",
  "hybrid_available": true,
  "embedding_dimension": 768,
  "chunks_found": 5,
  "chunks": [
    {
      "rank": 1,
      "source_file": "...",
      "domaine": "transaction",
      "type": "loi",
      "scores": {
        "vector_similarity": 0.86,     // ✅ Score lisible 86%
        "rrf_score": 0.0321,           // ✅ Score RRF brut
        "vector_rank": 1,
        "fulltext_rank": 2
      },
      "text_preview": "..."
    }
  ]
}
```

**Test B - Question sur location**
```bash
curl -X POST http://localhost:8000/api/ask/debug \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quelles charges peut récupérer le bailleur sur le locataire ?",
    "domaine": "location"
  }'
```

**Test C - Sans filtre de domaine**
```bash
curl -X POST http://localhost:8000/api/ask/debug \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quelles sont les règles sur les charges en copropriété ?"
  }'
```

### Test 2: Endpoint normal `/ask` (avec génération de réponse)

**Test D - Réponse complète avec sources corrigées**
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Le bailleur peut-il récupérer les frais de syndic sur le locataire ?",
    "domaine": "location",
    "enable_prequestioning": false
  }'
```

**Résultat attendu dans `sources`** :
```json
{
  "sources": [
    "Loi (Article 23) - Pertinence: 86% (vector) | RRF: 0.0321",
    "Décret (Article 2, Article 3) - Pertinence: 78% (vector) | RRF: 0.0298",
    "Fiche technique - Pertinence: 72% (vector) | RRF: 0.0276"
  ]
}
```

**❌ AVANT le fix** :
```json
"sources": [
  "Loi (Article 23) - Pertinence: 2%",  // ❌ Trompeur !
  "Décret (Article 2, Article 3) - Pertinence: 2%"
]
```

**✅ APRÈS le fix** :
```json
"sources": [
  "Loi (Article 23) - Pertinence: 86% (vector) | RRF: 0.0321",  // ✅ Clair !
  "Décret (Article 2, Article 3) - Pertinence: 78% (vector) | RRF: 0.0298"
]
```

### Test 3: Vérifier les logs de diagnostic

**Dans la console du serveur**, après `/ask` ou `/ask/debug`, vérifier :

```
[ASK] Retrieved 5 chunks using hybrid search

[DIAGNOSTIC] Top 3 chunks retrieved:
  [1] Loi_1989_Article_23_charges.md
      Domaine: location | Type: loi
      Method: hybrid
      Vector similarity: 86.21%
      RRF score: 0.0321
      Vector rank: 1
      Fulltext rank: 2

  [2] Decret_1987_charges_recuperables.md
      Domaine: location | Type: decret
      Method: hybrid
      Vector similarity: 78.45%
      RRF score: 0.0298
      Vector rank: 2
      Fulltext rank: 1

  [3] Fiche_IA_READY_charges_locatives.md
      Domaine: location | Type: fiche
      Method: hybrid
      Vector similarity: 72.10%
      RRF score: 0.0276
      Vector rank: 3
      Fulltext rank: 5
```

---

## Validation des Correctifs

### ✅ Checklist de validation

- [ ] **Score lisible** : Les sources affichent "86% (vector)" au lieu de "2%"
- [ ] **Score RRF séparé** : Le score RRF (0.0321) est affiché séparément si présent
- [ ] **Pas de duplication** : Plus de "Article Article X" dans les sources
- [ ] **Logs détaillés** : Les top 3 chunks sont loggés avec tous les scores
- [ ] **Endpoint debug** : `/ask/debug` retourne les détails complets
- [ ] **Compatibilité** : Le mode `vector` pur continue de fonctionner (affiche "Pertinence: 86%")

### Test de non-régression

**Test E - Mode vector pur (si hybrid non disponible)**
```bash
# Temporairement désactiver hybrid en renommant la fonction SQL
# OU tester sur un environnement sans hybrid_search_rrf

curl -X POST http://localhost:8000/api/ask/debug \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Test mode vector pur"
  }'
```

**Résultat attendu** :
```json
{
  "method_used": "vector",  // ✅ Fallback sur vector
  "chunks": [
    {
      "scores": {
        "similarity": 0.85  // ✅ Pas de rrf_score en mode vector
      }
    }
  ]
}
```

---

## Métriques à Surveiller

### Avant le fix
- **Pertinence affichée** : 2-4% (trompeur)
- **Score utilisé** : RRF (0.02-0.04)
- **Duplication** : "Article Article 23"
- **Diagnostic** : Impossible de voir les vrais scores

### Après le fix
- **Pertinence affichée** : 70-95% (vector similarity, lisible)
- **Score RRF** : Affiché séparément (0.0321) pour debug
- **Duplication** : Corrigée ("Article 23")
- **Diagnostic** : Endpoint `/ask/debug` + logs détaillés

---

## Troubleshooting

### Problème : "method_used": "vector" au lieu de "hybrid"
**Cause** : La fonction SQL `hybrid_search_rrf` n'est pas créée
**Solution** :
```bash
cd backend
psql $SUPABASE_URL -f setup_hybrid_search.sql
```

### Problème : Scores toujours affichés en "2%"
**Cause** : Code non redémarré ou erreur dans les modifications
**Solution** :
1. Vérifier que les fichiers modifiés sont bien sauvegardés
2. Redémarrer l'API : `Ctrl+C` puis `python -m api.main`
3. Vérifier les logs pour voir si les modifications sont appliquées

### Problème : "Article Article X" toujours présent
**Cause** : Les articles en base contiennent déjà "Article"
**Solution** : Le code corrige maintenant automatiquement (ligne 196-202)

---

## Prochaines Améliorations (Optionnel)

1. **Toggle RRF score display** : Ajouter un paramètre `show_technical_scores` pour masquer le RRF par défaut
2. **Score normalization** : Normaliser le RRF score (0.02-0.04 → 20-40) si on veut l'afficher comme pertinence principale
3. **Weighted hybrid** : Permettre de pondérer vector vs fulltext (ex: 70% vector + 30% fulltext)
4. **Caching** : Mettre en cache les embeddings des queries fréquentes

---

## Résumé

| Métrique | Avant | Après |
|----------|-------|-------|
| Affichage pertinence | 2% (RRF) | 86% (vector) |
| Score RRF | Écrasait similarity | Séparé (debug) |
| Duplication articles | "Article Article X" | "Article X" |
| Logs diagnostic | Basiques | Détaillés (top 3) |
| Endpoint debug | ❌ Absent | ✅ Présent |
| Compatibilité | ✅ OK | ✅ OK |

**Objectif atteint** : Les sources affichent maintenant un score lisible et cohérent en mode hybrid !
