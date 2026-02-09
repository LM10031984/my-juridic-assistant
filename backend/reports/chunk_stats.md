# Chunk Statistics Report (Stage 3)

Generated: corpus_chunk_primary.py

## Summary

**Total Chunks:** 258

**Quality Metrics:**
- ✅ **94.2%** chunks have article references (243/258)
- 📅 **44.2%** chunks have consolidation dates (114/258)
- 🔗 **43.0%** chunks have URL sources (111/258)

**Content Statistics:**
- Total articles referenced: 2049
- Average words per chunk: 987.8
- Min words: 31
- Max words: 5851

---

## Domain Breakdown


### Copropriete
- Chunks: 55
- Article coverage: 100.0% (55/55)
- Date coverage: 100.0% (55/55)
- URL coverage: 0.0% (0/55)

### Location
- Chunks: 154
- Article coverage: 94.2% (145/154)
- Date coverage: 18.8% (29/154)
- URL coverage: 72.1% (111/154)

### Pro_Immo
- Chunks: 28
- Article coverage: 100.0% (28/28)
- Date coverage: 100.0% (28/28)
- URL coverage: 0.0% (0/28)

### Transaction
- Chunks: 21
- Article coverage: 71.4% (15/21)
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
