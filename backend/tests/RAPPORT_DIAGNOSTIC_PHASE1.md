# 🔍 RAPPORT DE DIAGNOSTIC PHASE 1
**My Juridic Assistant - Analyse du système de retrieval**

Date : 2026-02-08
Status : ✅ Diagnostic complet terminé

---

## 📊 RÉSUMÉ EXÉCUTIF

### Verdict Global : 🔴 **RETRIEVAL FAIBLE - Nécessite refonte**

- **Score de précision actuel** : 30.3% (couverture mots-clés)
- **Objectif cible** : 85%+
- **Gap à combler** : ~55 points

### Composants testés
- ✅ Embeddings : Cohérents (768d, text-embedding-3-small)
- 🔴 Retrieval vectoriel : Insuffisant
- ⚠️ Génération : Non testée (Phase 2)

---

## 1️⃣ VÉRIFICATION DES EMBEDDINGS

### ✅ Résultats : CONFORMES

| Métrique | Résultat | Status |
|----------|----------|--------|
| Total chunks en base | 178 | ✅ |
| Chunks avec embeddings | 178 (100%) | ✅ |
| Dimension détectée | 768 | ✅ |
| Dimension attendue | 768 | ✅ |
| Modèle utilisé | text-embedding-3-small | ✅ |

**Conclusion** : Aucun problème d'incohérence de dimension. Le fix `setup_supabase_768.sql` a été correctement appliqué.

---

## 2️⃣ PERFORMANCE DU RETRIEVAL

### 🔴 Résultats : FAIBLE (30.3% de couverture)

#### Statistiques globales

| Métrique | Valeur | Évaluation |
|----------|--------|------------|
| Score de similarité max moyen | 59.40% | 🟡 Moyen |
| Score de similarité moyen | 48.30% | 🟠 Faible |
| Couverture mots-clés moyenne | **30.3%** | 🔴 Très faible |
| Couverture mots-clés min | 0.0% | 🔴 Critique |
| Couverture mots-clés max | 75.0% | 🟢 Bon |

#### Résultats par difficulté

| Difficulté | Couverture | Évaluation |
|------------|------------|------------|
| Questions simples | 38.3% | 🟠 Insuffisant |
| Questions moyennes | 30.0% | 🔴 Faible |
| Questions complexes | **0.0%** | 🔴 Critique |

### Cas problématiques identifiés

#### Exemple 1 : Charges récupérables (LOC_001)
**Question** : "Quelles sont les charges récupérables en location vide ?"

- **Similarité max** : 66.5%
- **Mots-clés attendus** : article 23, loi 1989, décret 1987, charges
- **Mots-clés trouvés** : charges (1/4 = **25%**)
- **Problème** : Trouve la fiche et le décret, mais MANQUE les références juridiques précises

#### Exemple 2 : Assemblée générale copro (COPRO_002)
**Question** : "Comment convoquer une assemblée générale de copropriété ?"

- **Similarité max** : 61.5%
- **Mots-clés attendus** : AG, convocation, syndic, délai
- **Mots-clés trouvés** : **AUCUN (0/4 = 0%)**
- **Problème** : La recherche sémantique ne capture pas les termes juridiques spécifiques

#### Exemple 3 : Trêve hivernale (COMPLEX_001)
**Question** : "Peut-on expulser un locataire pendant la trêve hivernale ?"

- **Similarité max** : 63.6%
- **Mots-clés attendus** : expulsion, trêve hivernale, impayés, procédure
- **Mots-clés trouvés** : **AUCUN (0/4 = 0%)**
- **Problème** : Aucun chunk ne contient les termes exacts

---

## 3️⃣ ANALYSE DES CAUSES RACINES

### Cause #1 : Recherche vectorielle pure ⚠️

**Problème** : La recherche par embeddings capture la sémantique générale, mais RATE les termes juridiques précis.

**Exemple concret** :
- Question : "article 23 loi 1989"
- Chunks trouvés : Parlent de location, mais ne citent pas "article 23" explicitement
- **Résultat** : L'utilisateur reçoit une réponse approximative sans référence juridique précise

### Cause #2 : Calcul de similarité côté client 🐢

**Code actuel (retrieval.py:101)** :
```python
# Récupère TOUS les chunks
response = self.supabase.table('legal_chunks').select('*').execute()

# Calcule la similarité pour chaque chunk en Python
for chunk in response.data:
    similarity = self._cosine_similarity(query_embedding, emb_data)
```

**Problèmes** :
- Télécharge 178 chunks complets à chaque requête
- Calcul O(n) en Python (lent)
- N'utilise pas l'index HNSW de PostgreSQL (pgvector)
- Latence élevée

### Cause #3 : Seuil de similarité trop haut

**Seuil actuel** : 0.4 (40%)
**Observation** : Beaucoup de chunks pertinents ont des scores entre 0.3 et 0.5

**Recommandation** : Implémenter hybrid search plutôt que de baisser encore le seuil

---

## 4️⃣ DIAGNOSTIC DE LA STACK TECHNIQUE

| Composant | Technologie actuelle | Status | Remarques |
|-----------|---------------------|--------|-----------|
| Base de données | Supabase (PostgreSQL 15) | ✅ | pgvector activé |
| Embeddings | OpenAI text-embedding-3-small (768d) | ✅ | Cohérent |
| Recherche vectorielle | pgvector (HNSW) | ⚠️ | Non utilisé (calcul côté client) |
| Recherche full-text | ❌ **ABSENT** | 🔴 | Pas de colonne `search_vector` |
| Hybrid search | ❌ **ABSENT** | 🔴 | Aucune fonction de fusion |
| Génération | OpenAI GPT-4o | ⚠️ | Non testée |
| API | FastAPI | ✅ | Fonctionnelle |

---

## 5️⃣ RECOMMANDATIONS PRIORITAIRES

### 🎯 Priorité 1 : Implémenter Hybrid Search (TÂCHE 2)

**Solution** : Combiner recherche vectorielle + recherche par mots-clés (BM25)

**Approche** :
1. Ajouter colonne `search_vector` (tsvector) à `legal_chunks`
2. Créer index GIN pour recherche full-text en français
3. Créer fonction `hybrid_search_rrf()` avec Reciprocal Rank Fusion
4. Modifier `retrieval.py` pour utiliser hybrid search

**Gain attendu** :
- Couverture mots-clés : 30% → **65-75%**
- Précision globale : **+35-45 points**

### 🎯 Priorité 2 : Améliorer le prompt de génération (TÂCHE 3)

**Problèmes actuels** :
- Prompt système correct mais générique
- Pas de structure de réponse imposée
- Pas de few-shot examples

**Solution** :
- Structurer la réponse (Réponse directe / Explications / Base juridique / Points d'attention)
- Ajouter des exemples (few-shot learning)
- Baisser température à 0.1 pour cohérence juridique

### 🎯 Priorité 3 : Optimiser le calcul de similarité

**Problème actuel** : Calcul côté client (lent, inefficace)

**Solution** : Utiliser la fonction RPC Supabase existante `search_legal_chunks()`
- Calcul côté serveur (PostgreSQL)
- Utilise l'index HNSW
- Latence divisée par 3-5x

---

## 6️⃣ MÉTRIQUES DE SUCCÈS

### Objectifs Phase 2 (après hybrid search)

| Métrique | Actuel | Cible | Gap |
|----------|--------|-------|-----|
| Couverture mots-clés moyenne | 30.3% | **85%+** | +55 pts |
| Couverture questions simples | 38.3% | **90%+** | +52 pts |
| Couverture questions moyennes | 30.0% | **85%+** | +55 pts |
| Couverture questions complexes | 0.0% | **75%+** | +75 pts |
| Latence P95 | Non mesuré | <10s | TBD |

---

## 7️⃣ PROCHAINES ÉTAPES

### ✅ FAIT
- [x] Script de diagnostic complet
- [x] Identification des problèmes de retrieval
- [x] Golden dataset (10 questions)

### 🔜 À FAIRE (PHASE 2)
1. **TÂCHE 2** : Implémenter hybrid search (BM25 + vector)
2. **TÂCHE 3** : Améliorer le prompt de génération
3. **TÂCHE 4** : Étendre le golden dataset à 20 questions
4. **TÂCHE 5** : Rapport comparatif avant/après

---

## 📎 FICHIERS GÉNÉRÉS

- `diagnostic_phase1.py` : Script de diagnostic
- `diagnostic_results.json` : Résultats détaillés (JSON)
- `RAPPORT_DIAGNOSTIC_PHASE1.md` : Ce rapport

---

**Diagnostic réalisé par** : Claude Code (Sonnet 4.5)
**Date** : 2026-02-08
**Durée d'exécution** : ~45 secondes
