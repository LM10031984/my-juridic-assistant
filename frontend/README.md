# My Juridic Assistant - Frontend

Interface web moderne pour poser des questions juridiques en immobilier français.

## 🎨 Fonctionnalités

- ✅ **Interface de chat conversationnelle** élégante et intuitive
- ✅ **Pré-questionnement automatique** (Layer 4) avec questions de qualification
- ✅ **Affichage des sources** juridiques citées
- ✅ **Historique de conversation** persisté dans localStorage
- ✅ **Design responsive** (mobile, tablet, desktop)
- ✅ **Auto-scroll** vers les nouveaux messages
- ✅ **États de chargement** animés
- ✅ **Gestion d'erreurs** élégante

## 🛠️ Technologies

- **React 18** - Framework UI
- **Vite** - Build tool ultra-rapide
- **Tailwind CSS** - Styling utility-first
- **Proxy API** - Communication avec le backend sur localhost:8000

## 🚀 Installation

### 1. Installer les dépendances

```bash
cd frontend
npm install
```

### 2. Lancer le serveur de développement

```bash
npm run dev
```

L'application sera disponible sur : **http://localhost:3000**

### 3. Build pour production

```bash
npm run build
```

Les fichiers seront générés dans `frontend/dist/`

### 4. Preview du build

```bash
npm run preview
```

## 📋 Prérequis

- **Node.js** version 16 ou supérieure
- **npm** ou **yarn**
- **Backend API** doit tourner sur localhost:8000

## 🎯 Utilisation

### Démarrage complet (Backend + Frontend)

**Terminal 1 - Backend** :
```bash
cd backend
python -m api.main
```

**Terminal 2 - Frontend** :
```bash
cd frontend
npm run dev
```

Puis ouvrez : **http://localhost:3000**

## 📱 Flux Utilisateur

### 1. Question Simple (Sans Pré-questionnement)

```
User: "Quelles sont les charges récupérables en location ?"
  ↓
API : Retrieval + Claude API
  ↓
Assistant: Répond avec sources citées
```

### 2. Question Ambiguë (Avec Pré-questionnement)

```
User: "Mon propriétaire peut-il augmenter le loyer ?"
  ↓
API : Détecte besoin de qualification
  ↓
Assistant: Pose 2-3 questions
  ↓
User: Répond aux questions (Oui/Non ou choix multiples)
  ↓
API : Retrieval avec contexte enrichi + Claude API
  ↓
Assistant: Répond avec précision + sources
```

## 🧩 Architecture des Composants

```
src/
├── App.jsx                      # Composant principal (orchestration)
├── components/
│   ├── ChatMessage.jsx          # Affichage d'un message (user/assistant)
│   ├── ChatInput.jsx            # Input pour poser une question
│   ├── LoadingIndicator.jsx    # Animation de chargement
│   └── QualifyingQuestions.jsx # Questions de qualification (Layer 4)
├── services/
│   └── api.js                   # Communication avec le backend
└── utils/
    └── conversationHistory.js   # Gestion de l'historique (localStorage)
```

## 🎨 Design System

### Couleurs Principales

- **Primary Blue** : `#0ea5e9` (boutons, liens)
- **Gray Scale** : Du `gray-50` au `gray-900`
- **Success Green** : Pour les validations
- **Error Red** : Pour les erreurs

### Responsive Breakpoints

- **Mobile** : < 640px
- **Tablet** : 640px - 1024px
- **Desktop** : > 1024px

## 💾 Stockage Local

L'historique de conversation est sauvegardé dans **localStorage** :

- **Clé** : `juridic_assistant_history`
- **Format** : JSON array de messages
- **Persistance** : Survit aux rechargements de page
- **Effacement** : Bouton "Effacer" dans le header

## 🔌 Configuration API

Le proxy Vite redirige automatiquement `/api/*` vers `http://localhost:8000`.

Pour changer le backend URL, modifier `vite.config.js` :

```javascript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://VOTRE_BACKEND_URL',
        changeOrigin: true,
      }
    }
  }
})
```

## 🧪 Tests

### Test Manuel

1. Lancer backend + frontend
2. Poser une question simple
3. Vérifier la réponse avec sources
4. Poser une question ambiguë
5. Vérifier les questions de qualification
6. Répondre et vérifier la réponse finale
7. Vérifier l'historique
8. Effacer l'historique

### Checklist de Test

- [ ] Interface s'affiche correctement
- [ ] Envoi d'une question simple fonctionne
- [ ] Affichage des sources citées
- [ ] Pré-questionnement s'active si nécessaire
- [ ] Questions yes/no fonctionnent
- [ ] Questions à choix multiples fonctionnent
- [ ] Réponse finale avec contexte enrichi
- [ ] Historique persisté après reload
- [ ] Bouton "Effacer" fonctionne
- [ ] Responsive sur mobile
- [ ] États de chargement affichés
- [ ] Erreurs gérées élégamment

## 📊 Performance

- **First Load** : < 2s
- **Interaction** : Instantanée
- **API Response** : 2-5s (dépend de Claude API)

## 🎓 Exemples de Questions

**Location :**
- "Quelles sont les charges récupérables ?"
- "Mon propriétaire peut-il augmenter le loyer ?"
- "Comment résilier un bail ?"

**Copropriété :**
- "Qui paie les travaux de toiture ?"
- "Comment se déroule une AG ?"

**Transaction :**
- "Quels diagnostics sont obligatoires ?"
- "Qu'est-ce qu'un vice caché ?"

**Professionnels :**
- "Quelles sont les obligations d'un agent immobilier ?"

## 🐛 Debugging

### Problème : API non accessible

**Symptôme** : Erreurs de connexion
**Solution** : Vérifier que le backend tourne sur localhost:8000

```bash
curl http://localhost:8000/health
```

### Problème : Tailwind CSS ne fonctionne pas

**Solution** : Vérifier que `postcss` et `tailwindcss` sont installés

```bash
npm install -D tailwindcss postcss autoprefixer
```

### Problème : Historique ne persiste pas

**Solution** : Vérifier la console browser pour erreurs localStorage

## 🚀 Déploiement

### Build Production

```bash
npm run build
```

### Servir avec un serveur statique

```bash
npm install -g serve
serve -s dist
```

### Déploiement Vercel/Netlify

1. Connecter le repo GitHub
2. Build command : `npm run build`
3. Publish directory : `dist`
4. Configurer les variables d'environnement

## 📝 TODO Futures Améliorations

- [ ] Dark mode
- [ ] Export de conversation en PDF
- [ ] Favoris / signets de réponses
- [ ] Recherche dans l'historique
- [ ] Multi-langues (EN, ES)
- [ ] Voice input (reconnaissance vocale)
- [ ] Suggestions de questions

## 🎉 Phase 3 - Succès !

✅ Interface web React complète
✅ Composants réutilisables et maintenables
✅ Design responsive moderne
✅ Intégration backend API
✅ Pré-questionnement automatique
✅ Historique de conversation
✅ Documentation complète

**Projet complet prêt à utiliser !** 🚀
