# My Juridic Assistant - Pipeline de Traitement

Pipeline de traitement du corpus juridique pour My Juridic Assistant.

## 📁 Structure

```
pipeline/
├── chunker.py              # Découpage intelligent en chunks
├── metadata_enricher.py    # Enrichissement des métadonnées
├── supabase_indexer.py     # Indexation dans Supabase avec embeddings
├── setup_supabase.sql      # Script SQL d'initialisation Supabase
├── requirements.txt        # Dépendances Python
├── .env.example            # Template de configuration
└── output/                 # Fichiers générés
    ├── chunks.json
    └── chunks_enriched.json
```

## 🚀 Installation

### 1. Installer les dépendances Python

```bash
cd pipeline
pip install -r requirements.txt
```

### 2. Configurer Supabase

#### a. Créer un projet Supabase

1. Aller sur [https://supabase.com](https://supabase.com)
2. Créer un compte (gratuit)
3. Créer un nouveau projet
4. Noter votre `Project URL` et `anon/public API key`

#### b. Initialiser la base de données

1. Dans Supabase Dashboard, aller dans **SQL Editor**
2. Copier le contenu de `setup_supabase.sql`
3. Exécuter le script SQL
4. Vérifier que la table `legal_chunks` est créée

### 3. Obtenir une clé API OpenAI

1. Aller sur [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Créer une nouvelle clé API
3. Noter la clé (elle ne sera affichée qu'une fois)

### 4. Configurer les variables d'environnement

```bash
# Copier le template
cp .env.example .env

# Éditer .env et remplir vos credentials
```

Exemple de `.env` :
```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
OPENAI_API_KEY=sk-proj-xxxxx
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536
```

## 📝 Utilisation

### Étape 1: Chunking du corpus

Découpe les textes juridiques en chunks de 300-1200 mots :

```bash
python chunker.py
```

**Sortie:** `output/chunks.json` (175 chunks)

### Étape 2: Enrichissement des métadonnées

Ajoute sous-thèmes, mots-clés, chunk_id, etc. :

```bash
python metadata_enricher.py
```

**Sortie:** `output/chunks_enriched.json` (175 chunks enrichis)

### Étape 3: Indexation Supabase

Génère les embeddings et indexe dans Supabase :

```bash
python supabase_indexer.py
```

**Actions:**
- Génère 175 embeddings via OpenAI (~$0.02 avec text-embedding-3-small)
- Insère les chunks dans Supabase avec pgvector
- Crée les index pour recherche vectorielle
- Lance un test de recherche

## 🔍 Recherche Vectorielle

### Via Python

```python
from supabase_indexer import SupabaseIndexer

indexer = SupabaseIndexer()

# Recherche simple
results = indexer.search(
    query="charges récupérables location",
    match_count=5
)

# Recherche avec filtres
results = indexer.search(
    query="assemblée générale copropriété",
    match_count=10,
    filter_domaine="copropriete",
    filter_type="loi"
)
```

### Via Supabase Dashboard

Dans le SQL Editor :

```sql
-- Chercher des chunks similaires
SELECT * FROM search_legal_chunks(
    query_embedding := (
        SELECT embedding FROM legal_chunks
        WHERE chunk_id = 'b4ea569f7faf5671'  -- chunk de référence
    ),
    match_count := 5,
    filter_domaine := 'location'
);
```

## 📊 Statistiques

Après indexation :
- **175 chunks** indexés
- **Domaines:** location (141), transaction (24), copropriete (5), pro_immo (5)
- **Types:** loi (125), code_civil (15), decret (7), fiche (10), etc.

## 💰 Coûts Estimés

### Embeddings (OpenAI text-embedding-3-small)
- 175 chunks × ~500 mots/chunk = ~87,500 mots
- Prix : $0.02 / 1M tokens
- **Coût estimé : ~$0.02** pour l'indexation initiale

### Supabase
- Plan gratuit : 500 MB + 2 GB de bande passante
- **Coût : $0** (suffisant pour V1)

### Total Phase 1
**~$0.02** (uniquement pour les embeddings)

## 🔧 Dépannage

### Erreur: "SUPABASE_URL and SUPABASE_KEY must be set"

→ Vérifier que le fichier `.env` existe et contient les bonnes valeurs

### Erreur: "relation 'legal_chunks' does not exist"

→ Exécuter le script `setup_supabase.sql` dans Supabase SQL Editor

### Erreur: "Failed to generate embedding"

→ Vérifier que `OPENAI_API_KEY` est valide
→ Vérifier le quota de votre compte OpenAI

### Erreur: "vector dimension does not match"

→ Vérifier que `EMBEDDING_DIMENSION` correspond au modèle :
- `text-embedding-3-small` : 1536
- `text-embedding-3-large` : 3072

## 📚 Prochaines Étapes

✅ Phase 1 terminée : Corpus → Chunks → Embeddings → Supabase

🔜 Phase 2 : Backend API
- Créer endpoint `/ask` avec retrieval + Claude API
- Implémenter Layer 4 (pré-questionnement automatique)
- Ajouter système de prompts avec contraintes anti-hallucination

🔜 Phase 3 : Frontend
- Web app (Softr/Glide) ou Bot Telegram
- Interface de question/réponse
- Affichage des sources et citations

## 📖 Ressources

- [Documentation Supabase](https://supabase.com/docs)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
