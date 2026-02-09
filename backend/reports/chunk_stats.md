# Chunk Statistics Report (Stage 3)

Generated: corpus_chunk_primary.py

## Summary

**Total Chunks:** 259

**Quality Metrics:**
- ✅ **99.6%** chunks have article references (258/259)
- 📅 **44.4%** chunks have consolidation dates (115/259)
- 🔗 **42.9%** chunks have URL sources (111/259)

**Content Statistics:**
- Total articles referenced: 3202
- Average words per chunk: 984.7
- Min words: 31
- Max words: 5851

---

## Domain Breakdown


### Copropriete
- Chunks: 56
- Article coverage: 100.0% (56/56)
- Date coverage: 100.0% (56/56)
- URL coverage: 0.0% (0/56)

### Location
- Chunks: 154
- Article coverage: 99.4% (153/154)
- Date coverage: 18.8% (29/154)
- URL coverage: 72.1% (111/154)

### Pro_Immo
- Chunks: 28
- Article coverage: 100.0% (28/28)
- Date coverage: 100.0% (28/28)
- URL coverage: 0.0% (0/28)

### Transaction
- Chunks: 21
- Article coverage: 100.0% (21/21)
- Date coverage: 9.5% (2/21)
- URL coverage: 0.0% (0/21)


---

## Success Criteria

✅ **Article coverage >95%**: PASS if above threshold
✅ **Date coverage >60%**: PASS if above threshold
⚠️ **URL coverage**: Informational (many files lack URLs)

## Next Steps

```bash
# Run Stage 5: Validate export
python backend/tools/corpus_validate_export.py

# If validation passes, import to Supabase
python pipeline/supabase_indexer.py --input backend/exports/legal_chunks_primary.jsonl
```
