# My Juridic Assistant - Backend API

API RAG (Retrieval-Augmented Generation) pour conseils juridiques en immobilier français.

## 🎯 Fonctionnalités

- **Recherche vectorielle** dans 175 chunks juridiques (location, copropriété, transaction, pro immo)
- **Pré-questionnement automatique** (Layer 4) pour qualifier la situation
- **Génération de réponses** avec Claude API (anti-hallucination stricte)
- **Citations obligatoires** des sources juridiques
- **Embeddings locaux gratuits** (sentence-transformers)

## 🏗️ Architecture

```
Pipeline de requête :
1. Retrieval    : Recherche vectorielle (top-5 chunks similaires)
2. Layer 4      : Pré-questionnement si nécessaire (questions de qualification)
3. Generation   : Claude API avec contexte + prompt anti-hallucination
4. Response     : Réponse structurée avec sources citées
```

## 🚀 Installation

### 1. Installer les dépendances

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configurer l'environnement

Créer un fichier `.env` :

```env
# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# Anthropic Claude API
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# API Config
API_HOST=0.0.0.0
API_PORT=8000
```

### 3. Lancer le serveur

```bash
cd backend
python -m api.main
```

L'API sera disponible sur : `http://localhost:8000`

Documentation interactive : `http://localhost:8000/docs`

## 📡 Endpoints

### `GET /`

Health check basique.

```bash
curl http://localhost:8000/
```

**Réponse** :
```json
{
  "status": "ok",
  "service": "My Juridic Assistant API",
  "version": "1.0.0"
}
```

---

### `GET /health`

Health check détaillé avec configuration.

```bash
curl http://localhost:8000/health
```

**Réponse** :
```json
{
  "status": "healthy",
  "supabase_configured": true,
  "anthropic_configured": true
}
```

---

### `GET /api/domains`

Liste des domaines juridiques disponibles.

```bash
curl http://localhost:8000/api/domains
```

**Réponse** :
```json
{
  "domains": [
    {
      "id": "location",
      "name": "Location immobilière",
      "description": "Baux, loyers, charges, réparations, résiliation"
    },
    {
      "id": "copropriete",
      "name": "Copropriété",
      "description": "Charges, travaux, AG, syndic, règlement"
    },
    {
      "id": "transaction",
      "name": "Transaction immobilière",
      "description": "Vente, compromis, diagnostics, vices cachés"
    },
    {
      "id": "pro_immo",
      "name": "Professionnels de l'immobilier",
      "description": "Agents, mandats, honoraires, obligations"
    }
  ]
}
```

---

### `POST /api/ask`

**Endpoint principal** : Poser une question juridique.

#### Requête simple (sans pré-questionnement)

```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quelles sont les charges récupérables en location ?",
    "domaine": "location",
    "enable_prequestioning": false
  }'
```

#### Requête avec pré-questionnement activé

```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Mon propriétaire peut-il augmenter le loyer ?",
    "enable_prequestioning": true
  }'
```

**Réponse (avec questions de qualification)** :
```json
{
  "needs_qualification": true,
  "domaine": "location",
  "questions": [
    {
      "id": 1,
      "question": "Le logement est-il situé en zone tendue ?",
      "type": "yes_no"
    },
    {
      "id": 2,
      "question": "Quel type de bail avez-vous ?",
      "type": "multiple_choice",
      "choices": ["Bail vide", "Bail meublé", "Bail mobilité"]
    }
  ],
  "message": "Pour vous répondre avec précision, j'ai besoin de quelques précisions sur votre situation :"
}
```

#### Requête avec réponses de qualification

```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Mon propriétaire peut-il augmenter le loyer ?",
    "enable_prequestioning": true,
    "user_answers": {
      "1": "Oui",
      "2": "Bail vide"
    }
  }'
```

**Réponse finale** :
```json
{
  "needs_qualification": false,
  "answer": "En zone tendue et pour un bail vide, l'augmentation du loyer est encadrée...",
  "sources": [
    "loi_alur_location.md (similarité: 87%)",
    "encadrement_loyers_zone_tendue.md (similarité: 82%)"
  ],
  "retrieved_chunks": 5,
  "disclaimer": "Cette réponse est basée uniquement sur les textes juridiques indexés dans ma base..."
}
```

---

## 🧪 Tests

### Script de test automatique

```bash
cd backend
python tests/test_api.py
```

### Tests manuels avec curl

Voir le fichier `tests/manual_tests.sh` pour des exemples de requêtes.

---

## 📊 Filtres disponibles

L'endpoint `/api/ask` accepte les filtres suivants :

- **domaine** : `location`, `copropriete`, `transaction`, `pro_immo`
- **enable_prequestioning** : `true` (défaut) ou `false`
- **user_answers** : Objet JSON `{question_id: "réponse"}`

---

## 🔒 Anti-Hallucination

L'API implémente des contraintes strictes :

1. ✅ **Réponse uniquement depuis le contexte** récupéré
2. ✅ **Citations obligatoires** des sources juridiques
3. ✅ **Refus explicite** si information absente
4. ✅ **Disclaimer** sur les limites du système

---

## 💰 Coûts

- **Supabase** : Gratuit (plan free)
- **Embeddings** : Gratuit (modèle local)
- **Claude API** : ~$0.003 par question (Sonnet 4.5)

**Estimation** : 100 questions ≈ $0.30

---

## 🛠️ Développement

### Structure des fichiers

```
backend/
├── api/
│   ├── main.py                 # FastAPI app
│   ├── routes/
│   │   └── ask.py             # Endpoint /ask
│   ├── services/
│   │   ├── retrieval.py       # Recherche vectorielle
│   │   └── prequestioning.py  # Layer 4 pré-questionnement
│   └── prompts/
│       └── system_prompts.py  # Templates anti-hallucination
├── tests/
│   ├── test_api.py            # Tests automatiques
│   └── manual_tests.sh        # Tests manuels curl
├── requirements.txt
├── .env
└── README.md
```

### Ajouter un nouveau domaine

1. Ajouter le domaine dans `Corpus/`
2. Exécuter le pipeline d'indexation
3. Ajouter le domaine dans `get_domains()` (routes/ask.py)

---

## 🐛 Debug

### Activer les logs détaillés

Les logs sont automatiquement affichés dans la console :

```
[ASK] Question: Mon propriétaire peut-il...
[ASK] Domaine filtre: location
[ASK] Retrieved 5 chunks
[ASK] Generating qualifying questions...
[ASK] Generating answer with Claude API...
[ASK] Formatting response...
```

### Erreurs communes

**"ANTHROPIC_API_KEY not configured"**
- Vérifier que `.env` contient `ANTHROPIC_API_KEY=sk-ant-api03-...`

**"No rows returned" (Supabase)**
- Vérifier que la base est indexée (voir `pipeline/`)

**"Failed to generate qualifying questions"**
- Vérifier la clé Anthropic et le quota API

---

## 📝 TODO Phase 3

- [ ] Historique de conversation multi-tour
- [ ] Cache des réponses fréquentes
- [ ] Interface frontend (React/Next.js)
- [ ] Authentification utilisateur
- [ ] Analytics et monitoring

---

## 🎉 Succès Phase 2

✅ Backend API FastAPI opérationnel
✅ Retrieval vectoriel avec filtres
✅ Layer 4 pré-questionnement automatique
✅ Intégration Claude API
✅ Prompts anti-hallucination
✅ Documentation complète

**Prêt pour la Phase 3 : Interface utilisateur** 🚀
