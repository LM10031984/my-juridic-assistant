RÈGLES DE LIAISON — DOSSIER TRANSACTION (routeur juridique)

Principe fondamental
Toute question en transaction doit être traitée par qualification du sujet, puis consultation ciblée du bon corpus :

vente immobilière : Code civil (vente)

responsabilité / litiges : Code civil (responsabilité)

DPE / information énergétique : CCH (DPE)

crédit immobilier / financement : Code de la consommation (crédit immo)

Règle 1 — Interdiction de réponse “au feeling”
L’outil ne doit pas répondre “en général” si la question suppose une condition légale, un délai, une preuve ou une obligation d’information.
Dans ces cas, il doit :

qualifier le thème

citer les articles/extraits du fichier correspondant

lister les pièces à vérifier

répondre de façon conditionnelle si une pièce manque

Règle 2 — Routage par intention (déclencheurs → fichier à ouvrir)

A) DPE / information énergétique → cch_ventes_dpe_extraits.md
Déclencheurs typiques :

“DPE obligatoire ?”

“à quel moment fournir le DPE ?”

“annonce / affichage DPE”

“audit énergétique”

“sanctions si DPE absent / erroné”

“validité DPE / date”
Sortie attendue :

obligation (quoi, quand, sur quel support)

responsabilités (vendeur/mandataire)

conséquences en cas de manquement (nullité, réduction, responsabilité, etc. selon extraits)

B) Vente / compromis / obligations vendeur-acquéreur → code_civil_vente.md
Déclencheurs typiques :

“promesse/compromis : que vaut quoi ?”

“conditions suspensives”

“vice caché / conformité”

“obligations du vendeur / délivrance”

“prix, dépôt de garantie, clause pénale”

“rétractation (attention : souvent Code conso / CCH selon cas, à router finement)”
Sortie attendue :

qualification du contrat (vente, promesse, etc.)

obligations principales + effets

conditions de validité / preuve si présentes dans tes extraits

C) Litige / faute / dommages / recours → code_civil_responsabilite.md
Déclencheurs typiques :

“responsabilité de l’agent / du vendeur”

“préjudice”

“erreur d’information”

“perte de chance”

“dommages-intérêts”

“faute / causalité”
Sortie attendue :

triptyque (faute / préjudice / lien de causalité) si tes extraits le couvrent

standard de preuve

recommandations de pièces à collecter

D) Crédit immobilier / offre de prêt / TAEG / délais → code_conso_credit_immo_extraits.md
Déclencheurs typiques :

“délai offre de prêt”

“conditions suspensives de financement”

“TAEG, assurance, fiche standardisée”

“rétractation, réflexion”

“intermédiation, pratiques commerciales”
Sortie attendue :

chronologie légale (délais, étapes)

obligations d’information

points de vigilance (TAEG, assurance, clauses)

Règle 3 — Hiérarchie en cas de chevauchement (un sujet touche plusieurs fichiers)
Certaines questions sont mixtes. Priorité de consultation :

texte spécial lié au sujet (ex : DPE → CCH ; crédit → Code conso)

règles de vente (Code civil vente)

responsabilité (Code civil responsabilité) pour la conséquence/recours

Exemples de chevauchement gérés par la règle :

“DPE absent : que risque le vendeur / l’agent ?”

CCH (obligation et manquement)

Code civil vente (effets sur la vente si présent)

Code civil responsabilité (recours / réparation)

“Compromis + financement : délais et sécurité”

Code conso crédit immo (délais/étapes)

Code civil vente (conditions suspensives / mécanique contractuelle)

Règle 4 — Checklists obligatoires avant conclusion (garde-fous)

Avant toute réponse sur DPE :

type de bien + date des diagnostics

support concerné (annonce, visite, compromis, acte)

présence de l’audit énergétique si applicable (selon extraits)

preuve de remise (mail, annexe compromis, etc.)

Avant toute réponse sur vente/compromis :

stade (annonce / offre / compromis / acte)

clauses présentes (conditions suspensives, pénale, dépôt)

documents signés et datés

qui supporte quoi (vendeur/acquéreur/mandataire)

Avant toute réponse sur crédit :

présence d’une condition suspensive de prêt et ses paramètres (montant, taux, durée, délai)

état (dossier déposé ? offre reçue ? refus ?)

pièces (offre de prêt, refus bancaire, échanges)

Avant toute réponse sur responsabilité :

fait générateur précis

preuve du manquement

préjudice chiffrable

lien de causalité plausible

chronologie documentée

Règle 5 — Format de réponse imposé (pour que ton outil réponde “comme il faut”)
Chaque réponse doit sortir avec ces blocs, dans cet ordre :

qualification : thème + sous-thème + pourquoi

corpus consulté : fichier(s) + extraits mobilisés

règle(s) applicable(s) : synthèse courte

articles à citer : liste

points à vérifier : checklist

conclusion : réponse conditionnelle si info manquante + action recommandée

Règle 6 — Gestion de l’incertitude (anti-hallucination)
Si l’outil ne trouve pas l’extrait exact dans le fichier correspondant :

il doit le dire explicitement

proposer la liste des infos nécessaires pour retrouver l’article

ne pas inventer un numéro d’article