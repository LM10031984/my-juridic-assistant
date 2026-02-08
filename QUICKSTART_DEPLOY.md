# 🚀 Déploiement Ultra-Rapide (15 minutes)

Guide simplifié pour déployer en production GRATUITEMENT.

---

## ⚡ Option Recommandée : Render + Vercel (100% Gratuit)

### Prérequis
- [ ] Compte GitHub
- [ ] Code pushé sur GitHub
- [ ] Clés API (Supabase + OpenAI)

---

## Étape 1 : Préparer le Code (2 min)

### 1.1 Créer un repo GitHub
```bash
cd "My juridic assistant"
git init
git add .
git commit -m "Initial commit - My Juridic Assistant"

# Créer un repo sur GitHub, puis :
git remote add origin https://github.com/VOTRE_USERNAME/juridic-assistant.git
git branch -M main
git push -u origin main
```

✅ **Votre code est maintenant sur GitHub !**

---

## Étape 2 : Déployer le Backend (5 min)

### 2.1 Aller sur Render.com
👉 https://render.com → Sign Up (avec GitHub)

### 2.2 Créer un Web Service
1. Cliquer sur **"New +"** → **"Web Service"**
2. Connecter votre repo GitHub `juridic-assistant`
3. Configuration :

| Champ | Valeur |
|-------|--------|
| Name | `juridic-assistant-api` |
| Region | `Frankfurt (EU Central)` |
| Branch | `main` |
| Root Directory | `backend` |
| Runtime | `Python 3` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn api.main:app --host 0.0.0.0 --port $PORT` |
| Instance Type | **Free** |

### 2.3 Ajouter les Variables d'Environnement

Cliquer sur **"Environment"** → **"Add Environment Variable"** :

```
SUPABASE_URL=https://zbzawsjnuqmbrpehphmd.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
OPENAI_API_KEY=sk-proj-IBdbu4A50cV_IhcDtEfXItxxS2fjwdwrNYF5t96J...
```

### 2.4 Déployer
Cliquer sur **"Create Web Service"** → Attendre 5-10 min

✅ **Votre API sera sur** : `https://juridic-assistant-api.onrender.com`

**Tester** : `https://juridic-assistant-api.onrender.com/health`

---

## Étape 3 : Déployer le Frontend (5 min)

### 3.1 Configurer l'URL de l'API

Créer `frontend/.env.production` :
```env
VITE_API_URL=https://juridic-assistant-api.onrender.com
```

Modifier `frontend/src/services/api.js` (ligne 5) :
```javascript
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'
```

### 3.2 Commit les changements
```bash
git add .
git commit -m "Configure production API URL"
git push
```

### 3.3 Aller sur Vercel
👉 https://vercel.com → Sign Up (avec GitHub)

### 3.4 Importer le Projet
1. Cliquer sur **"Add New..."** → **"Project"**
2. Importer votre repo `juridic-assistant`
3. Configuration :

| Champ | Valeur |
|-------|--------|
| Framework Preset | `Vite` |
| Root Directory | `frontend` |
| Build Command | `npm run build` |
| Output Directory | `dist` |

4. **Environment Variables** :
```
VITE_API_URL=https://juridic-assistant-api.onrender.com
```

### 3.5 Déployer
Cliquer sur **"Deploy"** → Attendre 2-3 min

✅ **Votre app sera sur** : `https://juridic-assistant.vercel.app`

---

## Étape 4 : Tester l'Application (3 min)

### 4.1 Ouvrir l'application
👉 `https://juridic-assistant.vercel.app`

### 4.2 Poser une question
Exemple : *"Quelles sont les charges récupérables en location ?"*

### 4.3 Vérifier
- [ ] La réponse s'affiche (peut prendre 30s au premier appel si Render était en veille)
- [ ] Les sources sont citées
- [ ] L'historique fonctionne

---

## 🎉 Déploiement Terminé !

**Votre application est en ligne** :
- 🌐 Frontend : `https://juridic-assistant.vercel.app`
- 🔌 API : `https://juridic-assistant-api.onrender.com`
- 📚 Docs : `https://juridic-assistant-api.onrender.com/docs`

---

## 📱 Partager l'Application

Envoyez simplement l'URL :
👉 `https://juridic-assistant.vercel.app`

**Accessible depuis** :
- Ordinateur (Chrome, Firefox, Safari, Edge)
- Smartphone (iOS, Android)
- Tablette

---

## ⚙️ Configuration Avancée (Optionnel)

### Domaine Personnalisé

**Vercel** (Frontend) :
1. Settings → Domains → Add Domain
2. Ajouter `monassistant.com`
3. Configurer les DNS selon les instructions

**Render** (Backend) :
1. Settings → Custom Domain → Add
2. Ajouter `api.monassistant.com`

### Auto-Deploy

✅ **Déjà activé !** Chaque `git push` sur `main` redéploie automatiquement.

---

## 🐛 Problèmes Fréquents

### Backend ne répond pas (504 Timeout)
**Cause** : Render Free s'endort après 15min d'inactivité
**Solution** : Attendre 30s au premier appel, le service redémarre

### Frontend ne se connecte pas à l'API
**Vérifier** :
1. `VITE_API_URL` dans Vercel Environment Variables
2. CORS activé dans le backend
3. URL de l'API correcte (avec `https://`)

### Erreur 401 OpenAI
**Cause** : Clé API invalide
**Solution** : Vérifier `OPENAI_API_KEY` dans Render Environment

---

## 💰 Coûts

- **Render Free** : 0€ (750h/mois)
- **Vercel Free** : 0€ (100GB bandwidth)
- **Supabase Free** : 0€ (500MB DB)
- **OpenAI** : ~$10-30/mois selon usage

**Total** : **~$10-30/mois** (uniquement OpenAI)

---

## 📊 Monitoring

### Logs Backend (Render)
Dashboard → Logs → View Live Logs

### Analytics Frontend (Vercel)
Dashboard → Analytics (gratuit inclus)

### Usage OpenAI
https://platform.openai.com/usage

---

## 🔄 Mettre à Jour

```bash
# Faire vos modifications
git add .
git commit -m "Update: description"
git push

# ✅ Auto-deploy activé !
# Frontend : ~2 min
# Backend : ~5 min
```

---

## ✅ Checklist Finale

- [ ] Backend déployé sur Render
- [ ] Frontend déployé sur Vercel
- [ ] Variables d'environnement configurées
- [ ] Application testée en ligne
- [ ] URL partagée avec les utilisateurs

---

**🎉 Félicitations ! Votre application est en production !** 🚀

Support : Voir `DEPLOYMENT_GUIDE.md` pour plus de détails
