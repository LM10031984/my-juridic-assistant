# Corpus Audit Report

Generated: corpus_audit.py

## Executive Summary

**Critical Issues Found:**
- 🔴 **187 noise lines** detected across 2 files
- 🔴 **37 ultra-long lines** (>1000 chars) in 5 files
- ⚠️ **9 files** missing consolidation dates
- ⚠️ **14 files** missing URL sources
- ⚠️ **152 fiches** missing proof sections

**Files Analyzed:**
- Primary sources: 15
- Fiches: 153

---

## Primary Sources Analysis

### Issues by File

| File | Size (KB) | Noise Lines | Long Lines | Articles | Date | URL | Issues |
|------|-----------|-------------|------------|----------|------|-----|--------|
| Decret_1967_Copropriete_TexteC | 198.26 | 4 | 0 | 0 | ✓ | ✗ | no_articles_detected, missing_url |
| Loi_1965_Copropriete_Texte_Con | 211.03 | 3 | 3 | 0 | ✓ | ✗ | ultra_long_lines, no_articles_detected, missing_url |
| cch_dpe_obligations.md | 11.32 | 0 | 1 | 0 | ✗ | ✗ | ultra_long_lines, no_articles_detected, missing_date, missing_url |
| code_civil_bail.md | 26.17 | 0 | 0 | 0 | ✗ | ✗ | no_articles_detected, missing_date, missing_url |
| decence_energetique_passoires. | 16.28 | 1 | 0 | 0 | ✗ | ✗ | no_articles_detected, missing_date, missing_url |
| decret_charges_1987.md | 14.62 | 1 | 0 | 0 | ✗ | ✗ | no_articles_detected, missing_date, missing_url |
| decret_decence_2002.md | 17.53 | 1 | 0 | 0 | ✗ | ✗ | no_articles_detected, missing_date, missing_url |
| loi_1989.md | 181.43 | 60 | 9 | 0 | ✓ | ✗ | high_noise, ultra_long_lines, no_articles_detected, missing_url |
| loi_climat_resilience_2021_ext | 641.62 | 86 | 22 | 0 | ✗ | ✓ | high_noise, ultra_long_lines, no_articles_detected, missing_date |
| Decret_1972.md | 135.69 | 5 | 0 | 0 | ✓ | ✗ | no_articles_detected, missing_url |
| Loi_hoguet.md | 55.52 | 4 | 0 | 0 | ✓ | ✗ | no_articles_detected, missing_url |
| cch_ventes_dpe_extraits.md | 12.16 | 2 | 2 | 0 | ✓ | ✗ | ultra_long_lines, no_articles_detected, missing_url |
| code_civil_responsabilite.md | 12.55 | 17 | 0 | 18 | ✗ | ✗ | missing_date, missing_url |
| code_civil_vente.md | 66.02 | 3 | 0 | 0 | ✗ | ✗ | no_articles_detected, missing_date, missing_url |
| code_conso_credit_immo_extrait | 57.27 | 0 | 0 | 0 | ✗ | ✗ | no_articles_detected, missing_date, missing_url |


### Noise Lines Distribution

Top noise line numbers (typical Legifrance export patterns):

**Decret_1967_Copropriete_TexteConsolide_2026.md**: Lines [2, 3, 9, 1367]
Sample noise lines:
- Line 2: `République Française. Liberté, Égalité, Fraternité....`
- Line 3: `Accueil Légifrance.fr - le service public de la diff usion d...`
- Line 9: `Version en vigueur au 06 février 2026...`
- Line 1367: `Le garde des sceaux, ministre de la justice, le ministre d'E...`

**Loi_1965_Copropriete_Texte_Consolide_2026.md**: Lines [2, 3, 10]
Sample noise lines:
- Line 2: `République Française. Liberté, Égalité, Fraternité....`
- Line 3: `Accueil Légifrance.fr - le service public de la diff usion d...`
- Line 10: `Version en vigueur au 06 février 2026...`


### Ultra-Long Lines

Files with lines exceeding 1000 characters:

**Loi_1965_Copropriete_Texte_Consolide_2026.md**:
- Line 401: 1,272 characters
- Line 451: 1,071 characters
- Line 810: 1,047 characters

**cch_dpe_obligations.md**:
- Line 1: 11,167 characters

**loi_1989.md**:
- Line 435: 1,414 characters
- Line 437: 1,199 characters
- Line 677: 1,041 characters
- Line 761: 1,738 characters
- Line 1055: 1,135 characters

**loi_climat_resilience_2021_extraits.md**:
- Line 221: 1,053 characters
- Line 417: 1,041 characters
- Line 524: 1,307 characters
- Line 569: 1,314 characters
- Line 614: 1,194 characters

**cch_ventes_dpe_extraits.md**:
- Line 51: 1,101 characters
- Line 94: 1,222 characters


---

## Fiches Analysis

### Missing Proof Sections

**152 fiches** lack generic proof templates:

- Fiche_IA_READY_Charges_Repartition.md
- fiche_IA_ready_decret_1967.md
- Fiche_IA_READY_Syndic_Benevole.md
- Fiche_IA_READY_Syndic_Cas_Pratiques.md
- Fiche_IA_READY_Syndic_Conseil_Syndical.md
- Fiche_IA_READY_Syndic_Contentieux.md
- Fiche_IA_READY_Syndic_Designation.md
- Fiche_IA_READY_Syndic_Jurisprudence.md
- Fiche_IA_READY_Syndic_Missions.md
- Fiche_IA_READY_Syndic_Professionnel.md
- ... and 142 more


---

## Recommendations

### Stage 2: Clean Primary Sources
1. Remove ~1,200 noise lines (lines 1-140 typically)
2. Normalize ~150 ultra-long lines (split at sentence boundaries)
3. Format ~400 articles as markdown headers (`### Article X`)
4. Extract and preserve consolidation dates
5. Extract and preserve URL sources

### Stage 3: Chunk with Enhanced Metadata
1. Use cleaned files for chunking
2. Extract article IDs with enhanced patterns (L-codes, R-codes)
3. Map consolidation dates to `version_date`
4. Store URL sources (schema extension or temp mapping)

### Stage 4: Enrich Fiches
1. Add generic proof templates to ~80 fiches
2. Do NOT invent specific legal requirements
3. Use generic CPC Article 9 template

---

## Next Steps

```bash
# Run Stage 2: Clean primary sources
python backend/tools/corpus_clean_primary.py

# Verify cleaning
cat backend/reports/cleaning_log.md
```
