# Phase 1 - Instructions de Déploiement

## ✅ Ce qui est déjà fait

- ✅ Corpus juridique structuré (3 couches : sources, fiches IA-ready, règles de liaison)
- ✅ Nommage des dossiers harmonisé
- ✅ Code civil responsabilité enrichi (16 articles)
- ✅ Script de chunking intelligent (`chunker.py`)
- ✅ Script d'enrichissement métadonnées (`metadata_enricher.py`)
- ✅ Script d'indexation Supabase (`supabase_indexer.py`)
- ✅ Script SQL d'initialisation (`setup_supabase.sql`)

## 🎯 Ce qu'il reste à faire (30 minutes)

### Étape 1: Créer un compte Supabase (5 min)

1. **Aller sur** [https://supabase.com](https://supabase.com)
2. **Créer un compte** (gratuit, pas de carte de crédit requise)
3. **Créer un nouveau projet**
   - Nom : `juridic-assistant` (ou autre)
   - Password : choisir un mot de passe fort
   - Région : Europe West (Frankfurt) recommandé
4. **Attendre** que le projet soit créé (~2 minutes)
5. **Noter vos credentials** :
   - Dans Settings → API
   - `Project URL` : `https://xxxxx.supabase.co`
   - `anon public` key : `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

### Étape 2: Initialiser la base de données (5 min)

1. **Dans Supabase Dashboard**, aller dans **SQL Editor** (menu de gauche)
2. **Cliquer sur** "New query"
3. **Copier-coller** tout le contenu du fichier `pipeline/setup_supabase.sql`
4. **Cliquer sur** "Run" (ou F5)
5. **Vérifier** que :
   - Aucune erreur n'apparaît
   - Dans "Table Editor", la table `legal_chunks` existe

### Étape 3: Obtenir une clé API OpenAI (5 min)

1. **Aller sur** [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. **Créer un compte** si vous n'en avez pas (carte de crédit requise, mais coût ~$0.02)
3. **Créer une nouvelle clé** : "Create new secret key"
   - Nom : `juridic-assistant`
4. **Copier la clé** (elle ne sera affichée qu'une fois) : `sk-proj-xxxxx...`
5. **Ajouter du crédit** si nécessaire (minimum $5, mais seulement ~$0.02 seront utilisés)

### Étape 4: Configurer l'environnement (2 min)

1. **Ouvrir** le dossier `pipeline` dans votre terminal
2. **Créer le fichier .env** :
   ```bash
   cp .env.example .env
   ```
3. **Éditer .env** et remplir vos credentials :
   ```env
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   OPENAI_API_KEY=sk-proj-xxxxx...
   EMBEDDING_MODEL=text-embedding-3-small
   EMBEDDING_DIMENSION=1536
   ```

### Étape 5: Installer les dépendances Python (2 min)

```bash
cd pipeline
pip install -r requirements.txt
```

### Étape 6: Exécuter l'indexation (10 min)

⚠️ **Important** : Les chunks sont déjà générés, il suffit d'indexer !

```bash
python supabase_indexer.py
```

**Ce qui va se passer :**
- Chargement de 175 chunks enrichis ✅
- Génération de 175 embeddings via OpenAI (~2-3 min, ~$0.02)
- Insertion dans Supabase (~30 secondes)
- Test de recherche automatique

**Sortie attendue :**
```
================================================================================
MY JURIDIC ASSISTANT - SUPABASE INDEXER
================================================================================

Loading chunks from: output/chunks_enriched.json
[OK] Loaded 175 chunks
[OK] Connected to Supabase: https://xxxxx.supabase.co
[OK] Using embedding model: text-embedding-3-small

================================================================================
INDEXING 175 CHUNKS TO SUPABASE
================================================================================

[1/2] Generating embeddings...
  Generating embeddings for batch 1 (50 texts)...
  Generating embeddings for batch 2 (50 texts)...
  Generating embeddings for batch 3 (50 texts)...
  Generating embeddings for batch 4 (25 texts)...
[OK] Generated 175 embeddings

[2/2] Inserting chunks into Supabase...
  Inserted batch 1/4 (50/175 chunks)
  Inserted batch 2/4 (100/175 chunks)
  Inserted batch 3/4 (150/175 chunks)
  Inserted batch 4/4 (175/175 chunks)

[OK] Indexing complete!
  - Successfully indexed: 175
  - Errors: 0

================================================================================
DATABASE STATISTICS
================================================================================

Total chunks in database: 175

By domain:
  copropriete: 5
  location: 141
  pro_immo: 5
  transaction: 24

By type:
  code_civil: 15
  code_consommation: 8
  decret: 7
  fiche: 10
  loi: 125
  regle_liaison: 4

================================================================================
TEST SEARCH
================================================================================

Test query: 'charges récupérables location'
Searching in domain 'location'...

[OK] Found 3 results:
...

================================================================================
[OK] INDEXING COMPLETE!
================================================================================
```

### Étape 7: Vérifier dans Supabase (2 min)

1. **Dans Supabase Dashboard**, aller dans **Table Editor**
2. **Cliquer sur** la table `legal_chunks`
3. **Vérifier** que vous voyez 175 lignes
4. **Cliquer sur une ligne** pour voir les métadonnées

## ✅ Phase 1 Terminée !

Vous avez maintenant :
- ✅ 175 chunks juridiques indexés dans Supabase
- ✅ Recherche vectorielle fonctionnelle avec filtres métadonnées
- ✅ Infrastructure prête pour le backend RAG

## 💰 Coût Total Phase 1

- **Supabase** : Gratuit (plan free)
- **OpenAI embeddings** : ~$0.02
- **Total** : ~$0.02

## 🔍 Tester la Recherche

Dans Supabase SQL Editor :

```sql
-- Recherche simple
SELECT
    chunk_id,
    domaine,
    type,
    source_file,
    sous_themes,
    LEFT(text, 100) as preview
FROM legal_chunks
WHERE domaine = 'location'
LIMIT 5;
```

## 🚀 Prochaines Étapes (Phase 2)

1. **Backend API** avec endpoint `/ask`
   - Retrieval top-k avec filtres
   - Appel Claude API avec prompt contraignant
   - Implémentation Layer 4 (pré-questionnement)

2. **Prompts système**
   - Anti-hallucination
   - Citations obligatoires
   - Format de réponse structuré

3. **Tests qualité**
   - 100 questions métier
   - Validation précision/pertinence

## 📞 Support

En cas de problème, vérifier :
- `.env` est bien configuré
- Supabase projet est actif
- OpenAI API key est valide
- `pip install -r requirements.txt` a réussi

## 🎉 Félicitations !

Vous avez terminé la Phase 1 - Pipeline de Traitement du Corpus !
