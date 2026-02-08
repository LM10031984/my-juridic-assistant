# My Juridic Assistant 🏛️

**Assistant juridique IA spécialisé en droit immobilier français** avec RAG (Retrieval-Augmented Generation), pré-questionnement automatique et citations de sources obligatoires.

---

## 🎯 Présentation

My Juridic Assistant est une solution complète de conseil juridique en immobilier français basée sur l'IA. Le système utilise une architecture RAG (Retrieval-Augmented Generation) en 4 couches pour fournir des réponses juridiques précises, sourcées et non hallucinées.

### Domaines Couverts

- 🏠 **Location** : Baux, loyers, charges, réparations, résiliation
- 🏢 **Copropriété** : Charges, travaux, AG, syndic, règlement
- 🤝 **Transaction** : Vente, compromis, diagnostics, vices cachés
- 👔 **Pro Immo** : Agents, mandats, honoraires, obligations

---

## 🏗️ Architecture

### Architecture 4 Couches

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 4 : Pré-questionnement Juridique Automatique        │
│  (Qualification de la situation avant réponse)              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3 : Prompt Framework Anti-Hallucination             │
│  (Citations obligatoires, refus hors périmètre)             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  LAYER 2 : Fiches Juridiques IA-Ready                      │
│  (Synthèses optimisées pour embedding)                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1 : Corpus Juridique                                │
│  (Lois, codes, décrets officiels - 175 chunks indexés)      │
└─────────────────────────────────────────────────────────────┘
```

### Stack Technique

**Backend (Python)** :
- FastAPI pour l'API REST
- Supabase (PostgreSQL + pgvector) pour la base vectorielle
- Sentence-Transformers pour les embeddings locaux (gratuit)
- Anthropic Claude Sonnet 4.5 pour la génération

**Frontend (React)** :
- React 18 + Vite
- Tailwind CSS pour le design
- LocalStorage pour l'historique

**Infrastructure** :
- 175 chunks juridiques indexés
- Embeddings 768 dimensions (modèle multilingue)
- Recherche vectorielle par similarité cosine
- Filtres métadonnées (domaine, type, layer)

---

## 🚀 Installation Complète

### Prérequis

- Python 3.9+
- Node.js 16+
- Compte Supabase (gratuit)
- Clé API Anthropic

### Installation Rapide (15 minutes)

#### 1. Cloner le projet

```bash
git clone <repo-url>
cd "My juridic assistant"
```

#### 2. Backend - Indexation (Phase 1)

```bash
cd pipeline
pip install -r requirements.txt
cp .env.example .env
# Éditer .env avec vos credentials Supabase
python supabase_indexer_local.py
```

**Résultat attendu** : 175 chunks indexés dans Supabase

#### 3. Backend - API (Phase 2)

```bash
cd ../backend
pip install -r requirements.txt
cp .env.example .env
# Éditer .env avec votre clé Anthropic
python -m api.main
```

**API disponible sur** : http://localhost:8000

#### 4. Frontend (Phase 3)

```bash
cd ../frontend
npm install
npm run dev
```

**Application disponible sur** : http://localhost:3000

---

## 📖 Documentation

- **CLAUDE.md** : Architecture détaillée du projet
- **PHASE1_INSTRUCTIONS.md** : Guide indexation corpus
- **backend/README.md** : Documentation API backend
- **backend/QUICKSTART.md** : Démarrage rapide backend
- **frontend/README.md** : Documentation frontend
- **frontend/QUICKSTART.md** : Démarrage rapide frontend

---

## 🎬 Utilisation

### Exemple de Conversation

**Question simple** :
```
User: Quelles sont les charges récupérables en location ?