PRD — My Juridic Assistant (France)
Assistant juridique immobilier premium (RAG + multi-canal)

1. Résumé exécutif
My Juridic Assistant est un assistant juridique spécialisé en droit immobilier français destiné aux professionnels de l’immobilier (réseau, agents, gestion locative, syndic). Le produit fournit des réponses fiables et structurées, fondées sur un corpus juridique interne, avec références (articles / textes) et garde-fous anti-hallucination.

Le produit est conçu pour être déployé en réseau, avec contrôle d’accès, journalisation (logs), suivi qualité et mise à jour continue du corpus. Le canal principal recommandé est une web app avec login, complétée optionnellement par Telegram pour un pilote fermé ou une utilisation “question rapide”.

2. Problème à résoudre
- Les professionnels doivent répondre vite à des questions juridiques récurrentes (copro, location, transaction, loi Hoguet).
- Les LLM génériques sans corpus donnent des réponses parfois inexactes, incomplètes ou mal nuancées (dates, seuils, délais, exceptions).
- Le réseau veut limiter le risque juridique et homogénéiser la qualité des réponses.

3. Objectifs
3.1 Objectifs produit
- Réponses juridiques générales, fiables, structurées, adaptées au terrain immobilier.
- Réduction drastique des hallucinations via une contrainte “répondre uniquement à partir du corpus”.
- Citations systématiques (références d’articles / textes) quand applicable.
- Expérience “outil métier” (login, traçabilité, analytics).
- Anti-copie : le corpus et le moteur restent côté serveur, non exportables.

3.2 KPI cibles
- Précision validée sur un set de tests métier : 95 %+
- Réponses avec références pertinentes : 90 %+
- Hallucination (affirmation non supportée) : ~0 %
- Latence P95 : < 10 s (web) ; < 12 s (Telegram)
- Coût moyen par requête : optimisé (top-k faible, extraits compacts)

4. Non-objectifs
- Conseil juridique personnalisé (interdit).
- Rédaction d’actes engageants.
- Couverture exhaustive de tout le droit immobilier (V1 bornée).
- Jurisprudence exhaustive (V1 : jurisprudence ciblée seulement).

5. Utilisateurs
- Agents (transaction, mandat, honoraires, information).
- Gestion locative (baux, charges, dépôt, congés, décence, DPE).
- Syndic / copropriété (AG, PV, contestation, charges, travaux, syndic).
- Managers réseau (validation rapide, réduction risque).

6. Périmètre juridique V1
Blocs inclus
- Copropriété : loi 1965 + décret 1967 + règles de liaison
- Professions immobilières : loi Hoguet 1970 + décret 1972 + règles de liaison
- Transaction : code civil (vente, vices cachés, responsabilité), responsabilité agent
- Location : loi 1989 + décret charges 1987 + décret décence 2002 + CCH (DPE / performance)

Format corpus
- Chunks (unités) 300–1200 mots, stables, avec métadonnées
- Types : articles, fiches IA-ready, règles de liaison, jurisprudence ciblée
Métadonnées minimales
- source (texte)
- type (loi/décret/code/fiche/jurisprudence)
- domaine (copro/location/transaction/pro)
- sous-thème
- articles (liste)
- version_date (si applicable)
- texte

7. Stratégie canal (recommandation)
7.1 Canal principal (production réseau)
Web app avec login (Softr ou Glide)
- Avantages : adoption, branding, contrôle d’accès, dashboard, historique, admin
- Fonctions V1 : champ question, réponse, historique, notation qualité, export logs (admin)
- Auth : email + domaine, éventuellement SSO plus tard

7.2 Canal secondaire (pilote / usage rapide)
Telegram (bot privé)
- Accès via whitelist + token backend
- Utilité : testeurs, managers, questions rapides
- Limite : pas le canal principal “outil métier”

8. Architecture technique (haute)
- Front web (Softr/Glide) et/ou Telegram
- Backend privé /ask (cerveau)
  - auth + whitelist
  - routage (domaine/sous-thème)
  - retrieval top-k (index vectoriel + filtres)
  - appel Claude via API avec prompt contraignant
  - réponse + citations + logs
- Index vectoriel : Supabase (pgvector) ou équivalent
- Pipeline corpus : Claude Code (extraction, chunking, métadonnées, indexation)

9. Contraintes anti-hallucination (exigences)
- Le modèle doit répondre uniquement à partir des extraits fournis.
- Si l’information n’est pas dans le corpus : répondre “information absente du corpus”.
- La réponse doit demander les informations manquantes nécessaires (date bail, type bail, etc.).
- Refus clair si hors périmètre.
- Disclaimer fixe en fin de réponse.

10. Fonctionnalités V1
10.1 Utilisateur
- poser une question
- recevoir une réponse structurée
- références (textes / articles) si disponibles
- question de clarification si nécessaire
- refus si hors périmètre

10.2 Admin
- gérer whitelist utilisateurs
- voir logs (questions, domaines, chunks, latence, coûts)
- lancer re-indexation corpus
- suivre métriques de qualité (notes, erreurs)

11. Sécurité et anti-copie
- aucune exposition du corpus via Drive public
- prompts et règles côté serveur uniquement
- contrôle accès (whitelist + auth)
- limitation d’exfiltration : pas de dump massif des textes, extraits limités

12. Plan de réalisation (no-code + Claude Code)
Phase 1 : MVP premium (1–2 semaines selon rythme)
- pipeline corpus : PDF → texte → chunks → index
- backend /ask minimal (template guidé)
- front web simple (Softr/Glide) + login
- tests : 100 questions, scoring, corrections corpus

Phase 2 : durcissement qualité (itératif)
- règles de liaison enrichies
- jurisprudence ciblée (20–50 décisions phares)
- améliorations routage + clarification questions

Phase 3 : déploiement réseau
- onboard utilisateurs + formation
- tableau de bord admin
- process de mise à jour mensuel

13. Critères d’acceptation V1
- réponses sourcées, structurées
- pas d’hallucination sur le set de tests
- refus correct hors périmètre
- contrôle d’accès fonctionnel
- logs exploitables
- canal web opérationnel, Telegram optionnel

14. Risques et mitigations
- corpus incomplet : tests + ajout chunks pivots
- obsolescence : routine mise à jour + re-index
- mauvaise adoption canal : canal web prioritaire + Telegram en bonus
- interprétation “conseil” : disclaimer + refus personnalisation

15. Décisions à prendre (prioritaires)
- canal principal : web app (recommandé) vs Telegram only (pilot)
- modèle : Claude Sonnet vs autre (coût/qualité)
- index : Supabase (simple) vs autre
- calendrier mise à jour corpus

