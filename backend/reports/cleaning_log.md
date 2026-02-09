# Corpus Cleaning Report (Stage 2)

Generated: corpus_clean_primary.py

## Summary

**Transformations Applied:**
- 🧹 **1567 noise lines removed** across 15 files
- ✂️ **486 ultra-long lines split** at sentence boundaries
- 📑 **1260 articles formatted** as markdown headers (### Article X)

**Output:** All cleaned files saved to `Corpus/clean/primary_cleaned/`

---

## Cleaning Results by File

| File | Domain | Original Lines | Final Lines | Noise Removed | Lines Split | Articles Formatted |
|------|--------|----------------|-------------|---------------|-------------|--------------------|
| Decret_1967_Copropriete_TexteC | copropriete | 1736 | 1744 | 9 | 15 | 216 |
| Loi_1965_Copropriete_Texte_Con | copropriete | 1261 | 1313 | 3 | 53 | 172 |
| cch_dpe_obligations.md | location | 1 | 23 | 0 | 22 | 0 |
| code_civil_bail.md | location | 463 | 305 | 158 | 0 | 67 |
| decence_energetique_passoires. | location | 190 | 179 | 16 | 5 | 12 |
| decret_charges_1987.md | location | 333 | 326 | 10 | 3 | 5 |
| decret_decence_2002.md | location | 203 | 189 | 19 | 5 | 12 |
| loi_1989.md | location | 1877 | 1692 | 262 | 77 | 93 |
| loi_climat_resilience_2021_ext | location | 5315 | 5101 | 461 | 247 | 305 |
| Decret_1972.md | pro_immo | 885 | 913 | 5 | 31 | 138 |
| Loi_hoguet.md | pro_immo | 465 | 472 | 4 | 9 | 53 |
| cch_ventes_dpe_extraits.md | transaction | 122 | 101 | 31 | 8 | 0 |
| code_civil_responsabilite.md | transaction | 206 | 189 | 17 | 0 | 0 |
| code_civil_vente.md | transaction | 1188 | 805 | 384 | 1 | 187 |
| code_conso_credit_immo_extrait | transaction | 745 | 567 | 188 | 10 | 0 |


---

## Domain Breakdown


### Copropriete
- Files cleaned: 2
- Noise lines removed: 12
- Long lines split: 68
- Articles formatted: 388

### Location
- Files cleaned: 7
- Noise lines removed: 926
- Long lines split: 359
- Articles formatted: 494

### Pro_Immo
- Files cleaned: 2
- Noise lines removed: 9
- Long lines split: 40
- Articles formatted: 191

### Transaction
- Files cleaned: 4
- Noise lines removed: 620
- Long lines split: 19
- Articles formatted: 187


---

## Next Steps

```bash
# Run Stage 3: Chunk with enhanced metadata
python backend/tools/corpus_chunk_primary.py

# Verify chunks
cat backend/reports/chunk_stats.md
```

## Quality Verification

To verify cleaning quality, compare original and cleaned files:

```bash
# Example: Check loi_1989.md
diff Corpus/01_sources_text/location/loi_1989.md Corpus/clean/primary_cleaned/location/loi_1989.md
```

Expected changes:
- First ~60-140 lines (Legifrance noise) removed
- Ultra-long lines split at sentence boundaries
- Articles now start with `### Article X`
- Metadata comments added at file start
