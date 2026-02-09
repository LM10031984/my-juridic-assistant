# Fiches Proof-First Validation Report

Generated: validate_fiches_proof_first.py

## Summary

**Total fiches validated:** 151
**Status breakdown:**
- ✅ **OK:** 145 (96.0%)
- ⚠️ **Warnings:** 0 (0.0%)
- 🔍 **Needs human:** 6 (4.0%)
- ❌ **Errors:** 0 (0.0%)

**Blocking errors:** 0 (must be 0 for production)

---

## Validation Rules

1. **BASE JURIDIQUE non vide => EXTRAITS non vide**
2. **Chaque article dans BASE JURIDIQUE apparaît dans EXTRAITS**
3. **EXTRAITS ne contiennent pas de bruit Legifrance**

---

## Fiches OK (145)

| File | Domain |
|------|--------|
| Fiche_IA_READY_Charges_Repartition.md | copropriete |
| fiche_IA_ready_decret_1967.md | copropriete |
| Fiche_IA_READY_Syndic_Benevole.md | copropriete |
| Fiche_IA_READY_Syndic_Cas_Pratiques.md | copropriete |
| Fiche_IA_READY_Syndic_Conseil_Syndical.md | copropriete |
| Fiche_IA_READY_Syndic_Contentieux.md | copropriete |
| Fiche_IA_READY_Syndic_Designation.md | copropriete |
| Fiche_IA_READY_Syndic_Jurisprudence.md | copropriete |
| Fiche_IA_READY_Syndic_Missions.md | copropriete |
| Fiche_IA_READY_Syndic_Professionnel.md | copropriete |
| Fiche_IA_READY_Syndic_Remuneration.md | copropriete |
| Fiche_IA_READY_Syndic_Responsabilite.md | copropriete |
| Fiche_IA_READY_Travaux_Amelioration.md | copropriete |
| Fiche_IA_READY_Travaux_Autorisation_Syndic.md | copropriete |
| Fiche_IA_READY_Travaux_Cas_Pratiques.md | copropriete |
| Fiche_IA_READY_Travaux_Conservation.md | copropriete |
| Fiche_IA_READY_Travaux_Financement.md | copropriete |
| Fiche_IA_READY_Travaux_Jurisprudence.md | copropriete |
| Fiche_IA_READY_Travaux_PPT.md | copropriete |
| Fiche_IA_READY_Travaux_Privatifs.md | copropriete |
| ... and 125 more |


---

## Fiches Needs Human (6)

These fiches require manual review but are not blocking errors.

| File | Domain | Reason |
|------|--------|--------|
| Fiche_IA_READY_DPE_04_Erreur_Recours.md | diagnostics | Articles in BASE but not in EXTRAITS (needs_human) |
| Fiche_IA_READY_DPE_05_Travaux_Renovation.md | diagnostics | Articles in BASE but not in EXTRAITS (needs_human) |
| Fiche_IA_READY_Passoires_Energetiques_Interdi | location | Marked for manual review |
| Fiche_IA_READY_Passoires_Energetiques_Interdi | location | Articles in BASE but not in EXTRAITS (needs_human) |
| Fiche_IA_READY_Mandat_Exclusif_Vente_Directe. | pro_immo | Articles in BASE but not in EXTRAITS (needs_human) |
| FICHE IA-READY — Décret 20 juillet 1972.md | transaction | Articles in BASE but not in EXTRAITS (needs_human) |


---

## Fiches with Errors (0)

**BLOCKING**: These must be fixed before production.

✅ **No blocking errors found!**


---

## Recommendations


### Manual Review Required
- Review 6 fiches marked for human validation
- Verify BASE JURIDIQUE and EXTRAITS accuracy
- Complete missing information from primary sources


---

## Next Steps

```bash
# If errors = 0, proceed to indexation
python pipeline/supabase_indexer.py --input backend/exports/legal_chunks_primary.jsonl

# Manual review of needs_human fiches
ls Corpus/clean/fiches_updated/ | grep -f backend/reports/needs_human_list.txt
```
