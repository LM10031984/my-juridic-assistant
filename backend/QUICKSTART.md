# Quick Start - Backend API

## ⚡ Démarrage Rapide (5 minutes)

### 1. Installer les dépendances

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configurer la clé Anthropic

Éditer `backend/.env` et ajouter votre clé API :

```env
ANTHROPIC_API_KEY=sk-ant-api03-VOTRE_CLE_ICI
```

Pour obtenir une clé : https://console.anthropic.com/settings/keys

### 3. Lancer le serveur

```bash
python -m api.main
```

Sortie attendue :
```
Starting My Juridic Assistant API on 0.0.0.0:8000
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 4. Tester l'API

**Dans un nouveau terminal :**

```bash
# Test health check
curl http://localhost:8000/health

# Test question simple
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quelles sont les charges recuperables en location ?",
    "domaine": "location",
    "enable_prequestioning": false
  }'
```

**Ou via navigateur :**

Documentation interactive : http://localhost:8000/docs

### 5. Tester avec le script automatique

```bash
cd backend
python tests/test_api.py
```

---

## 🎯 Premier Test Réussi ?

Vous devriez voir :
- ✅ Health check retourne `{"status": "healthy"}`
- ✅ La question retourne une réponse avec sources citées
- ✅ Le script de test affiche `ALL TESTS PASSED`

---

## 🐛 Problèmes Courants

### "ANTHROPIC_API_KEY not configured"

**Solution** : Vérifier que `.env` contient votre clé API :
```bash
cat backend/.env | grep ANTHROPIC
```

### "Cannot connect to API"

**Solution** : Vérifier que le serveur tourne :
```bash
# Dans un terminal
cd backend
python -m api.main

# Dans un autre terminal
curl http://localhost:8000/health
```

### "No rows returned" (Supabase)

**Solution** : Vérifier que la base est indexée (Phase 1) :
```bash
cd pipeline
python supabase_indexer_local.py
```

---

## 📚 Prochaines Étapes

- Lire le **README.md** pour la documentation complète
- Tester les différents endpoints (voir `/docs`)
- Essayer le pré-questionnement automatique
- Explorer les filtres par domaine

---

## 💡 Exemples de Questions

**Location :**
- "Quelles sont les charges récupérables ?"
- "Mon propriétaire peut-il augmenter le loyer ?"
- "Comment résilier un bail de location ?"

**Copropriété :**
- "Qui paie les travaux de toiture ?"
- "Comment se déroule une assemblée générale ?"

**Transaction :**
- "Quels diagnostics sont obligatoires pour une vente ?"
- "Qu'est-ce qu'un vice caché ?"

**Professionnels :**
- "Quelles sont les obligations d'un agent immobilier ?"
- "Comment calculer les honoraires d'agence ?"

---

## 🎉 Prêt à Utiliser !

L'API est maintenant opérationnelle. Consultez le README.md pour plus de détails.
