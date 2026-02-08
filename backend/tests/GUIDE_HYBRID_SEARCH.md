# 🚀 GUIDE D'INSTALLATION : HYBRID SEARCH

**My Juridic Assistant - Phase 2**

Ce guide explique comment activer le **Hybrid Search** (recherche vectorielle + full-text) pour améliorer drastiquement le retrieval.

---

## 📊 Résumé du gain attendu

| Métrique | Avant (vector seul) | Après (hybrid) | Gain |
|----------|---------------------|----------------|------|
| Couverture mots-clés moyenne | 30.3% | **65-75%** | +35-45 pts |
| Questions simples | 38.3% | **75-85%** | +37-47 pts |
| Questions moyennes | 30.0% | **60-70%** | +30-40 pts |
| Questions complexes | 0.0% | **50-60%** | +50-60 pts |

---

## ✅ Prérequis

- [x] Base Supabase configurée avec `setup_supabase_768.sql`
- [x] 178 chunks indexés avec embeddings 768d
- [x] Code backend à jour (retrieval.py modifié)

---

## 📋 Étapes d'installation

### ÉTAPE 1 : Appliquer le script SQL

**Option A : Via Supabase SQL Editor (RECOMMANDÉ)**

1. Ouvrez Supabase Dashboard : https://supabase.com/dashboard
2. Naviguez vers : **SQL Editor** (icône `</>` dans le menu gauche)
3. Cliquez sur **New Query**
4. Copiez tout le contenu de :
   ```
   pipeline/setup_hybrid_search.sql
   ```
5. Collez dans l'éditeur
6. Cliquez sur **Run** (ou `Ctrl+Enter`)
7. Vérifiez que vous voyez le message de confirmation :
   ```
   NOTICE:  ✓ Tous les chunks ont un search_vector
   NOTICE:  SETUP TERMINÉ - Hybrid search prêt à l'emploi !
   ```

**Option B : Via psycopg2 (automatique)**

```bash
cd pipeline
python apply_hybrid_search.py
# Suivre les instructions (fournir la connection string PostgreSQL)
```

**Option C : Via Supabase CLI**

```bash
# Si vous avez Supabase CLI installé
supabase db push
```

---

### ÉTAPE 2 : Vérifier l'installation

Vérifiez que la fonction `hybrid_search_rrf` a été créée :

```sql
-- Dans Supabase SQL Editor
SELECT proname
FROM pg_proc
WHERE proname = 'hybrid_search_rrf';
```

Résultat attendu : Une ligne avec `hybrid_search_rrf`

---

### ÉTAPE 3 : Tester le hybrid search

Redémarrez le backend FastAPI :

```bash
cd backend
python -m api.main
```

Vérifiez les logs de démarrage :
```
[OK] RetrievalService initialized with HYBRID SEARCH (vector + full-text)
```

✅ Si vous voyez ce message : hybrid search est actif !

---

### ÉTAPE 4 : Exécuter les tests comparatifs

Comparez les performances avant/après :

```bash
cd backend
python -m tests.test_hybrid_search
```

Ce script va :
1. Tester les 10 questions avec recherche vectorielle
2. Tester les 10 questions avec hybrid search
3. Calculer le gain de couverture
4. Générer un rapport : `hybrid_search_comparison.json`

---

## 🔍 Que fait le script SQL ?

Le fichier `setup_hybrid_search.sql` effectue les opérations suivantes :

### 1. Ajoute une colonne `search_vector` (tsvector)
```sql
ALTER TABLE legal_chunks ADD COLUMN IF NOT EXISTS search_vector tsvector;
```

### 2. Crée un index GIN pour recherche full-text rapide
```sql
CREATE INDEX idx_search_vector ON legal_chunks USING GIN(search_vector);
```

### 3. Génère les tsvectors pour tous les chunks existants
- Configuration : français (stemming + stop words)
- Peuple automatiquement la colonne `search_vector`

### 4. Crée un trigger de mise à jour automatique
- À chaque insert/update, le `search_vector` est régénéré

### 5. Crée la fonction `hybrid_search_rrf()`
- Combine recherche vectorielle + full-text
- Utilise **Reciprocal Rank Fusion** pour fusionner les résultats
- Retourne les top-k résultats avec scores combinés

### 6. Crée une fonction helper `fulltext_search_chunks()`
- Recherche full-text seule (pour tests)

---

## 🧪 Comment ça marche ?

### Recherche vectorielle pure (AVANT)

```
Query: "charges récupérables article 23"
   ↓
OpenAI embedding (768d)
   ↓
Calcul cosine similarity avec tous les chunks
   ↓
Top-5 chunks les plus similaires
```

**Problème** : Rate souvent les termes juridiques précis ("article 23", "loi 1989")

---

### Hybrid Search avec RRF (APRÈS)

```
Query: "charges récupérables article 23"
   ↓
   ├─── Recherche vectorielle ────► Top-50 chunks (score sémantique)
   │
   └─── Recherche full-text ──────► Top-50 chunks (score mots-clés)
         (PostgreSQL tsvector)

   ↓
Reciprocal Rank Fusion (RRF)
   ↓
Top-5 chunks avec scores combinés
```

**Avantage** : Capture à la fois le sens général ET les termes juridiques exacts

---

## 📐 Formule RRF (Reciprocal Rank Fusion)

Pour chaque chunk :

```
score_rrf = (1 / (k + rank_vector)) + (1 / (k + rank_fulltext))
```

Où :
- `k` = constante RRF (60 par défaut)
- `rank_vector` = position dans les résultats vectoriels
- `rank_fulltext` = position dans les résultats full-text

**Exemple** :
- Chunk A : 1er en vector (rank=1), 3e en full-text (rank=3)
  - score = 1/(60+1) + 1/(60+3) = 0.0164 + 0.0159 = **0.0323**

- Chunk B : 5e en vector (rank=5), 1er en full-text (rank=1)
  - score = 1/(60+5) + 1/(60+1) = 0.0154 + 0.0164 = **0.0318**

Chunk A sera classé avant Chunk B (meilleur score combiné)

---

## 🛠 Configuration avancée

### Ajuster le seuil de similarité vectorielle

Par défaut : `similarity_threshold = 0.3`

Pour être plus strict :
```python
chunks = retrieval_service.hybrid_search_rrf(
    query="...",
    similarity_threshold=0.4  # Plus strict
)
```

Pour être plus permissif :
```python
chunks = retrieval_service.hybrid_search_rrf(
    query="...",
    similarity_threshold=0.2  # Plus permissif
)
```

### Ajuster la constante RRF

Par défaut : `rrf_k = 60`

Valeurs typiques : 20-100
- `rrf_k` faible (20) : Privilégie les premiers résultats
- `rrf_k` élevé (100) : Distribue mieux les scores

```python
chunks = retrieval_service.hybrid_search_rrf(
    query="...",
    rrf_k=40  # Ajustement
)
```

---

## 🐛 Dépannage

### ❌ "Hybrid search non disponible"

**Cause** : La fonction SQL n'est pas créée

**Solution** :
1. Vérifiez que `setup_hybrid_search.sql` a été exécuté
2. Vérifiez dans Supabase SQL Editor :
   ```sql
   SELECT proname FROM pg_proc WHERE proname = 'hybrid_search_rrf';
   ```
3. Si vide, réexécutez le script SQL

---

### ❌ "function hybrid_search_rrf does not exist"

**Cause** : Erreur lors de l'exécution du script SQL

**Solution** :
1. Lisez les logs d'erreur dans Supabase SQL Editor
2. Vérifiez que `pgvector` est activé :
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'vector';
   ```
3. Vérifiez que la colonne `embedding` est de type `vector(768)`

---

### ❌ "column search_vector does not exist"

**Cause** : Le script SQL n'a pas créé la colonne

**Solution** :
1. Exécutez manuellement :
   ```sql
   ALTER TABLE legal_chunks ADD COLUMN search_vector tsvector;
   UPDATE legal_chunks
   SET search_vector = to_tsvector('french', text);
   ```

---

### ⚠️ Performances dégradées

**Symptôme** : Requêtes plus lentes qu'avant

**Causes possibles** :
1. Index GIN non créé
   ```sql
   CREATE INDEX idx_search_vector ON legal_chunks USING GIN(search_vector);
   ```

2. Index HNSW sur embeddings manquant
   ```sql
   CREATE INDEX idx_embedding ON legal_chunks
   USING hnsw (embedding vector_cosine_ops);
   ```

---

## 📊 Métriques de succès

Après installation, les métriques cibles sont :

| Métrique | Cible | Comment mesurer |
|----------|-------|-----------------|
| Couverture mots-clés moyenne | **≥ 70%** | `test_hybrid_search.py` |
| Questions simples | **≥ 80%** | Diagnostic par difficulté |
| Questions moyennes | **≥ 65%** | Diagnostic par difficulté |
| Questions complexes | **≥ 50%** | Diagnostic par difficulté |
| Latence P95 | **< 10s** | Logs API |

---

## 🎯 Prochaines étapes (Phase 3)

Une fois le hybrid search installé et testé :

1. **TÂCHE 3** : Améliorer le prompt de génération
2. **TÂCHE 4** : Étendre le golden dataset à 20 questions
3. **TÂCHE 5** : Rapport comparatif final avant/après

---

## 📞 Support

En cas de problème :

1. Vérifiez les logs backend : `python -m api.main`
2. Exécutez le diagnostic : `python -m tests.diagnostic_phase1`
3. Testez hybrid search : `python -m tests.test_hybrid_search`
4. Consultez les fichiers de résultats :
   - `diagnostic_results.json`
   - `hybrid_search_comparison.json`

---

**Dernière mise à jour** : 2026-02-08
**Version** : Phase 2 - Hybrid Search
