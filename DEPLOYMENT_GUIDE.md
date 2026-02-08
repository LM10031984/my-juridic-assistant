# Guide de Déploiement - My Juridic Assistant

Guide complet pour déployer l'application en production.

---

## 📋 Table des Matières

1. [Architecture de Déploiement](#architecture)
2. [Option 1 : Déploiement Gratuit (Recommandé)](#option-1-gratuit)
3. [Option 2 : Déploiement Cloud Complet](#option-2-cloud)
4. [Option 3 : Déploiement VPS](#option-3-vps)
5. [Configuration Production](#configuration)
6. [Sécurité](#sécurité)
7. [Monitoring](#monitoring)

---

## 🏗️ Architecture de Déploiement

```
┌─────────────────────────────────────────────────────────────┐
│                        INTERNET                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Frontend (React)                                            │
│  Hébergement : Vercel / Netlify / GitHub Pages (GRATUIT)    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Backend API (FastAPI)                                       │
│  Hébergement : Render / Railway / Fly.io (GRATUIT)          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Base de Données (Supabase - PostgreSQL + pgvector)         │
│  Hébergement : Supabase (GRATUIT)                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🆓 Option 1 : Déploiement Gratuit (Recommandé)

### Coût Total : **0€/mois** + coûts OpenAI (~$10-30/mois selon usage)

### A. Backend sur Render.com (Gratuit)

**1. Créer un compte Render**
- Aller sur : https://render.com
- S'inscrire gratuitement (GitHub recommandé)

**2. Créer un nouveau Web Service**
```bash
New → Web Service
```

**3. Connecter votre repository GitHub**
- Si pas encore de repo : créer un repo GitHub et pusher le code
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/VOTRE_USERNAME/juridic-assistant.git
git push -u origin main
```

**4. Configuration Render**

| Paramètre | Valeur |
|-----------|--------|
| **Name** | `juridic-assistant-api` |
| **Region** | `Frankfurt (EU Central)` |
| **Branch** | `main` |
| **Root Directory** | `backend` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn api.main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | `Free` |

**5. Variables d'environnement**

Aller dans `Environment` et ajouter :
```
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=votre_supabase_anon_key
OPENAI_API_KEY=votre_openai_key
API_HOST=0.0.0.0
API_PORT=10000
```

**6. Déployer**
- Cliquer sur `Create Web Service`
- Attendre 5-10 minutes pour le déploiement
- Votre API sera disponible sur : `https://juridic-assistant-api.onrender.com`

**⚠️ Note Render Free** : Le service s'endort après 15 min d'inactivité (redémarre en ~30s au premier appel)

---

### B. Frontend sur Vercel (Gratuit)

**1. Préparer le build frontend**

Créer `frontend/.env.production` :
```env
VITE_API_URL=https://juridic-assistant-api.onrender.com
```

Modifier `frontend/src/services/api.js` :
```javascript
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'
```

**2. Créer un compte Vercel**
- Aller sur : https://vercel.com
- S'inscrire avec GitHub

**3. Déployer**

**Option A : Via CLI (Recommandé)**
```bash
# Installer Vercel CLI
npm install -g vercel

# Se connecter
vercel login

# Déployer
cd frontend
vercel --prod
```

**Option B : Via Dashboard**
- Cliquer sur `New Project`
- Importer votre repo GitHub
- Configurer :
  - **Framework Preset** : Vite
  - **Root Directory** : `frontend`
  - **Build Command** : `npm run build`
  - **Output Directory** : `dist`
  - **Environment Variables** :
    ```
    VITE_API_URL=https://juridic-assistant-api.onrender.com
    ```

**4. Déployer**
- Cliquer sur `Deploy`
- Votre app sera sur : `https://juridic-assistant.vercel.app`

---

### C. Base de Données Supabase

✅ **Déjà configuré !** Votre Supabase est déjà en production.

Pour sécuriser :
1. Aller dans Supabase Dashboard → Settings → API
2. Vérifier que RLS est bien désactivé (ou configurer les policies)
3. Régénérer les clés API si elles ont été exposées

---

## 💻 Option 2 : Déploiement Cloud Complet

### Backend sur Railway.app

**Avantages** :
- Pas de "cold start" (toujours actif)
- $5/mois pour 500h
- Plus rapide que Render

**Configuration** :
1. Aller sur https://railway.app
2. Connecter GitHub
3. Déployer le repo (détection automatique Python)
4. Ajouter les variables d'environnement
5. Votre API sera sur : `https://xxx.railway.app`

### Frontend sur Netlify

**Similaire à Vercel** :
1. https://netlify.com
2. Connecter GitHub
3. Build settings :
   - Build command : `npm run build`
   - Publish directory : `dist`
4. Variables d'environnement : `VITE_API_URL`

---

## 🖥️ Option 3 : VPS (Serveur Dédié)

### Pour un contrôle total (OVH, Scaleway, DigitalOcean)

**Coût** : ~5-10€/mois

**1. Créer un VPS Ubuntu 22.04**

**2. Connexion SSH**
```bash
ssh root@VOTRE_IP
```

**3. Installation**
```bash
# Mise à jour
apt update && apt upgrade -y

# Python + Node.js
apt install python3-pip python3-venv nodejs npm nginx -y

# Cloner le repo
git clone https://github.com/VOTRE_USERNAME/juridic-assistant.git
cd juridic-assistant
```

**4. Backend avec Gunicorn + Systemd**

```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# Créer service systemd
sudo nano /etc/systemd/system/juridic-api.service
```

Contenu :
```ini
[Unit]
Description=Juridic Assistant API
After=network.target

[Service]
User=root
WorkingDirectory=/root/juridic-assistant/backend
Environment="PATH=/root/juridic-assistant/backend/venv/bin"
ExecStart=/root/juridic-assistant/backend/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.main:app --bind 0.0.0.0:8000

[Install]
WantedBy=multi-user.target
```

```bash
# Activer le service
systemctl enable juridic-api
systemctl start juridic-api
systemctl status juridic-api
```

**5. Frontend (Build statique)**

```bash
cd ../frontend
npm install
npm run build

# Copier vers Nginx
cp -r dist/* /var/www/html/
```

**6. Configuration Nginx**

```bash
sudo nano /etc/nginx/sites-available/juridic-assistant
```

Contenu :
```nginx
server {
    listen 80;
    server_name VOTRE_DOMAINE.com;

    # Frontend
    location / {
        root /var/www/html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Activer le site
ln -s /etc/nginx/sites-available/juridic-assistant /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

**7. HTTPS avec Let's Encrypt**

```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d VOTRE_DOMAINE.com
```

✅ **Application accessible sur** : `https://VOTRE_DOMAINE.com`

---

## 🔧 Configuration Production

### 1. Sécurité Backend

Créer `backend/.env.production` :
```env
# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=votre_key

# OpenAI
OPENAI_API_KEY=votre_key

# Production
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
ALLOWED_ORIGINS=https://votredomaine.com
```

Modifier `backend/api/main.py` :
```python
import os

# CORS pour production
origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Spécifier les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. Optimisation Frontend

**Build optimisé** :
```bash
cd frontend
npm run build
```

**Analyse du bundle** :
```bash
npm install -D rollup-plugin-visualizer
npm run build -- --mode production
```

### 3. Variables d'environnement

**Frontend** (`frontend/.env.production`) :
```env
VITE_API_URL=https://votre-api.com
VITE_APP_NAME=My Juridic Assistant
```

**Backend** (sur la plateforme de déploiement) :
```env
SUPABASE_URL=...
SUPABASE_KEY=...
OPENAI_API_KEY=...
```

---

## 🔒 Sécurité

### 1. Protéger les Clés API

**Ne JAMAIS** commiter :
- `.env` dans Git
- Les clés API dans le code

Créer `.gitignore` :
```
.env
.env.local
.env.production
__pycache__/
*.pyc
node_modules/
dist/
```

### 2. Rate Limiting

Ajouter dans `backend/api/main.py` :
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/ask")
@limiter.limit("10/minute")  # Max 10 questions par minute
async def ask_question(request: Request, ...):
    ...
```

### 3. Regenerer les Clés

**⚠️ IMPORTANT** : Après avoir exposé vos clés dans la conversation :

1. **Supabase** :
   - Dashboard → Settings → API → Reset anon key

2. **OpenAI** :
   - https://platform.openai.com/api-keys → Revoke key → Create new

3. **Mettre à jour** sur toutes les plateformes de déploiement

---

## 📊 Monitoring

### 1. Logs Backend (Render/Railway)

Voir les logs en temps réel :
```bash
# Render
render logs -t <service-id>

# Railway
railway logs
```

### 2. Analytics Frontend

Ajouter Google Analytics dans `frontend/index.html` :
```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

### 3. Monitoring OpenAI Usage

Dashboard OpenAI : https://platform.openai.com/usage

---

## 💰 Coûts Prévisionnels

### Option Gratuite
| Service | Coût | Limites |
|---------|------|---------|
| Render (Backend) | 0€ | 750h/mois, sleep après 15min |
| Vercel (Frontend) | 0€ | 100GB bandwidth |
| Supabase | 0€ | 500MB DB, 2GB transfer |
| OpenAI GPT-4o | ~$10-30/mois | Selon usage (~1000-3000 questions) |
| **TOTAL** | **~$10-30/mois** | |

### Option Payante (Sans limits)
| Service | Coût |
|---------|------|
| Railway (Backend) | $5/mois |
| Vercel Pro | $20/mois (optionnel) |
| Supabase Pro | $25/mois (optionnel) |
| OpenAI | $10-50/mois |
| **TOTAL** | **$40-100/mois** |

---

## 🚀 Checklist de Déploiement

- [ ] Code pusher sur GitHub
- [ ] Variables d'environnement configurées
- [ ] Backend déployé (Render/Railway)
- [ ] Frontend déployé (Vercel/Netlify)
- [ ] Domaine personnalisé configuré (optionnel)
- [ ] HTTPS activé
- [ ] CORS configuré correctement
- [ ] Clés API régénérées (sécurité)
- [ ] Rate limiting activé
- [ ] Monitoring configuré
- [ ] Tests end-to-end effectués

---

## 🎯 Commandes Rapides

### Déploiement Vercel (Frontend)
```bash
cd frontend
npm run build
vercel --prod
```

### Déploiement Manuel (Backend)
```bash
cd backend
git add .
git commit -m "Deploy to production"
git push origin main
```

### Mise à jour Production
```bash
# Frontend
cd frontend
npm run build
vercel --prod

# Backend (auto-deploy sur Render/Railway via Git)
git push origin main
```

---

## 📝 Support

**En cas de problème** :
1. Vérifier les logs du service
2. Tester l'API via : `https://votre-api.com/health`
3. Vérifier les variables d'environnement
4. Consulter la documentation de la plateforme

---

## 🎉 Prêt pour la Production !

Votre application est maintenant déployée et accessible publiquement !

**URLs de production** :
- Frontend : `https://juridic-assistant.vercel.app`
- Backend API : `https://juridic-assistant-api.onrender.com`
- Documentation : `https://juridic-assistant-api.onrender.com/docs`

**Profitez de votre assistant juridique en ligne !** 🚀
