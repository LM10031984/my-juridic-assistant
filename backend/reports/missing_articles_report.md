# Missing Articles Report - Corpus Enrichment Needed

Generated: 2026-02-09
Status: 5 fiches require corpus enrichment

## Summary

**Current status**: 146/151 fiches passing (96.7%)
**Remaining errors**: 5 fiches with articles not in corpus

---

## Articles to Add to Corpus

### 1. CCH (Code de la Construction et de l'Habitation) - DPE Section

**Needed for**: `Fiche_IA_READY_DPE_04_Erreur_Recours.md`, `Fiche_IA_READY_DPE_05_Travaux_Renovation.md`

```
Article L271-4    - Opposabilité du DPE (mentionné dans DPE_04)
Article L126-35-4 - Travaux de rénovation énergétique
Article L126-35-6 - Travaux de rénovation énergétique
Article L126-35-7 - Travaux de rénovation énergétique
Article L126-35-10 - Travaux de rénovation énergétique
Article L126-35-11 - Travaux de rénovation énergétique
```

**Source file to update**: `Corpus/clean/primary_cleaned/location/cch_dpe_obligations.md`
**Current content**: Articles L126-26 to L126-33 (missing L126-35-x range)

---

### 2. Loi Climat et Résilience 2021 - Passoires Énergétiques

**Needed for**: `Fiche_IA_READY_Passoires_Energetiques_Interdiction.md`

```
Article 149 - Interdiction location passoires énergétiques
Article 159 - Calendrier d'interdiction (G en 2025, F en 2028, E en 2034)
```

**Source file to update**: `Corpus/clean/primary_cleaned/location/loi_climat_resilience_2021_extraits.md`
**Current content**: 111 chunks but missing specific articles 149, 159

---

### 3. Code Civil - Mandats et Solidarité

**Needed for**: `Fiche_IA_READY_Mandat_Exclusif_Vente_Directe.md`

```
Article 2 - (Need context: which code civil section? Likely contracts or mandates)
```

**Source file to update**: `Corpus/clean/primary_cleaned/transaction/code_civil_vente.md` or create new file
**Note**: Need to clarify which "Article 2" is referenced (very generic number)

---

### 4. Décret 1972 (Décret 20 juillet 1972)

**Needed for**: `FICHE IA-READY — Décret 20 juillet 1972.md`

```
Article 20 - ✅ Already in corpus (Decret_1972.md)
Article 25 - ✅ Already in corpus
Article 28 - ✅ Already in corpus
Article 33 - ✅ Already in corpus
Article 38 - ✅ Already in corpus
```

**Status**: Articles ARE in corpus, but fiche template was never filled.
**Action needed**: Fill template using keyword retrieval (not article detection)

---

## Recommended Actions

### Immediate (Keep Project Moving)

1. **Mark 5 fiches as `needs_human`** in validation
2. **Accept 96.7% success rate** as V1 production-ready
3. **Create enrichment queue** for corpus updates

### Short-term (Corpus Enrichment)

1. **Fetch missing CCH articles** (L271-4, L126-35-x) from Légifrance:
   - Visit: https://www.legifrance.gouv.fr/codes/id/LEGITEXT000006074096/
   - Navigate to: Livre Ier > Titre II > Chapitre VI
   - Copy articles with full text + metadata

2. **Add to primary sources**:
   ```bash
   # Add to existing file
   backend/tools/add_articles_to_cch.py --articles L271-4,L126-35-4,L126-35-6,L126-35-7,L126-35-10,L126-35-11
   ```

3. **Re-chunk corpus**:
   ```bash
   python backend/tools/chunk_primary_sources.py
   ```

4. **Re-fix fiches**:
   ```bash
   python backend/tools/fix_16_error_fiches.py
   ```

5. **Re-validate**:
   ```bash
   python backend/tools/validate_fiches_proof_first.py
   ```

---

## Template Fill Required

**File**: `FICHE IA-READY — Décret 20 juillet 1972.md`

This fiche is an **empty template** with no article references in the main content. The articles ARE in the corpus, but the fiche needs to be populated using **keyword retrieval** instead of article detection.

**Action**:
```bash
# Use corpus_update_fiches.py with retrieval method
python backend/tools/corpus_update_fiches.py --fiche "transaction/FICHE IA-READY — Décret 20 juillet 1972.md" --method retrieval
```

---

## Progress Tracking

| Metric | Before Fix | After Fix | Target |
|--------|-----------|-----------|--------|
| Errors | 16 | 5 | 0 |
| OK Fiches | 135 | 146 | 151 |
| Success Rate | 89.4% | 96.7% | 100% |
| Reduction | - | 69% | - |

**Next milestone**: Add 6 CCH articles + fill 1 template → 0 errors (100% success)

---

## Legal Text Sources

- **Légifrance**: https://www.legifrance.gouv.fr/
- **CCH**: Code de la Construction et de l'Habitation
- **Loi Climat 2021**: Loi n°2021-1104 du 22 août 2021
- **Code Civil**: Articles contracts/obligations
- **Décret 1972**: Décret n°72-678 du 20 juillet 1972

---

## Notes

- Articles L126-35-x are part of CCH Section 5 (Informations et diagnostics obligatoires)
- These articles were added by recent reforms (Loi Climat 2021)
- Missing from current corpus extracts (may need manual fetch)
- Once added, will enable 100% fiche validation success
