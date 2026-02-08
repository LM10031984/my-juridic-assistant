# Quick Start - Frontend

## ⚡ Démarrage Ultra-Rapide (2 minutes)

### 1. Installer Node.js

Si pas déjà installé : https://nodejs.org/ (version LTS recommandée)

### 2. Installer les dépendances

```bash
cd frontend
npm install
```

**Attendez** : Installation des packages (~1 minute)

### 3. Lancer le frontend

```bash
npm run dev
```

**Succès** si vous voyez :
```
  VITE v5.0.8  ready in 523 ms

  ➜  Local:   http://localhost:3000/
  ➜  press h + enter to show help
```

### 4. Lancer le backend (dans un autre terminal)

```bash
cd backend
python -m api.main
```

### 5. Ouvrir dans le navigateur

🌐 **http://localhost:3000**

---

## ✅ Ça Marche ?

Vous devriez voir :
- ✅ Page blanche avec header "My Juridic Assistant"
- ✅ Message de bienvenue
- ✅ Zone de texte pour poser une question
- ✅ Pas d'erreurs dans la console

---

## 🎯 Premier Test

1. **Posez une question** : "Quelles sont les charges récupérables en location ?"
2. **Attendez 2-5 secondes** (loading...)
3. **Voyez la réponse** avec sources juridiques citées

**Si erreur** : Vérifiez que le backend tourne (localhost:8000)

---

## 🐛 Problèmes ?

### "npm not found"

**Installez Node.js** : https://nodejs.org/

### "Cannot connect to API"

**Lancez le backend** :
```bash
cd backend
python -m api.main
```

Vérifiez : http://localhost:8000/health

### "Port 3000 déjà utilisé"

**Utilisez un autre port** :
```bash
npm run dev -- --port 3001
```

---

## 📚 Documentation Complète

Voir **README.md** pour :
- Architecture détaillée
- Configuration avancée
- Déploiement production

---

## 🎉 C'est Parti !

Vous pouvez maintenant :
- ✅ Poser des questions juridiques
- ✅ Recevoir des réponses avec sources
- ✅ Voir le pré-questionnement en action
- ✅ Consulter l'historique de conversation
