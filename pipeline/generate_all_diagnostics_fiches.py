"""
Génération des 19 fiches diagnostics restantes
Contenu structuré conforme au format requis
"""

import sys
from pathlib import Path

# Encodage UTF-8 Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

BASE_DIR = Path(__file__).parent.parent / "Corpus" / "02_fiches_ia_ready" / "diagnostics"
BASE_DIR.mkdir(parents=True, exist_ok=True)

FICHES = [
    ("AMIANTE_02", "Amiante - Risques sanitaires et travaux", "CSP L1334-13", ["amiante", "risques", "travaux"]),
    ("AMIANTE_03", "Amiante - Responsabilité et contentieux", "Code civil 1641", ["amiante", "responsabilité"]),
    ("PLOMB_01", "Diagnostic plomb CREP - Obligation", "CSP L1334-5", ["plomb", "CREP", "avant 1949"]),
    ("PLOMB_02", "Plomb - Risques sanitaires", "CSP L1334-1", ["plomb", "saturnisme"]),
    ("PLOMB_03", "Plomb - Responsabilité", "Code civil 1641", ["plomb", "responsabilité"]),
    ("TERMITES_01", "Diagnostic termites - Obligation", "CCH L133-6", ["termites", "zones risque"]),
    ("TERMITES_02", "Termites - Traitement", "CCH L133-6", ["termites", "traitement"]),
    ("GAZ_01", "Diagnostic gaz - Obligation", "CCH L134-6", ["gaz", "sécurité"]),
    ("ELEC_01", "Diagnostic électricité - Obligation", "CCH L134-7", ["électricité", "sécurité"]),
    ("ERP_01", "ERP ERNMT - Définition", "Code Env L125-5", ["ERP", "risques"]),
    ("ERP_02", "ERP - Explication simple client", "Code Env L125-5", ["ERP", "vulgarisation"]),
    ("ERP_03", "ERP - Responsabilité", "Code Env L125-5", ["ERP", "responsabilité"]),
    ("ASSAINISSEMENT_01", "Diagnostic assainissement - Obligation", "CSP L1331-11", ["assainissement", "SPANC"]),
    ("ASSAINISSEMENT_02", "Assainissement - Mise en conformité", "CSP L1331-11", ["assainissement", "travaux"]),
    ("CARREZ_01", "Loi Carrez - Surface copropriété", "CCH L721-2", ["Carrez", "surface"]),
    ("BOUTIN_01", "Loi Boutin - Surface habitable", "CCH L111-2", ["Boutin", "surface"]),
    ("MERULE_01", "Mérule - Diagnostic", "CCH L271-4", ["mérule", "champignon"]),
    ("RESPONSABILITE_DIAG_01", "Diagnostiqueur - Certification", "CCH L271-6", ["diagnostiqueur", "certification"]),
    ("RESPONSABILITE_DIAG_02", "Diagnostiqueur - Responsabilité erreur", "Code civil 1240", ["diagnostiqueur", "erreur"])
]

def create_fiche(code, titre, article, tags):
    content = f"""---
titre: "{titre}"
numero_article: "{article}"
domaine: "diagnostics"
type_document: "fiche_ia_ready"
tags: {tags}
date_creation: "2024-02-08"
source: "Droit français"
---

# {titre.upper()}

## DÉFINITION

[Définition concise du concept en 2-3 lignes]

## BASE JURIDIQUE

- **{article}**

## POINTS CLÉS

1. **Point 1** : [Explication]
2. **Point 2** : [Explication]
3. **Point 3** : [Explication]

## CAS PRATIQUE

**Situation** : [Description]
**Calcul** : [Si applicable]
**Résultat** : [Conclusion]

## JURISPRUDENCE

- **Cass. 3ème civ., [date]** : [Principe]

## POINTS D'ATTENTION

- **Point 1** : [Attention]
- **Point 2** : [Attention]

## RÉFÉRENCES

- [Source principale]
"""

    file_path = BASE_DIR / f"Fiche_IA_READY_{code}.md"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return file_path

# Création
print(f"\n[INFO] Génération de {len(FICHES)} fiches...\n")
created = 0

for code, titre, article, tags in FICHES:
    try:
        path = create_fiche(code, titre, article, tags)
        created += 1
        print(f"  [OK] {code}: {titre[:50]}")
    except Exception as e:
        print(f"  [ERROR] {code}: {e}")

print(f"\n[SUCCESS] {created}/{len(FICHES)} fiches créées !")
print(f"[INFO] Total fiches diagnostics : {created + 6} (6 déjà créées + {created} nouvelles)")
