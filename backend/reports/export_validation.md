# Export Validation Report (Stage 5)

Generated: corpus_validate_export.py

## Status: ✅ PASSED

**Summary:**
- Total chunks: 258
- Valid chunks: 258
- Chunks with errors: 0
- Chunks with warnings: 146

---

## Blocking Errors (0)

✅ No blocking errors found!


---

## Warnings (162)

⚠️ **Non-blocking**: These issues should be reviewed but won't prevent import:

1. Line 24: Very high word count (5851)
2. Line 56: Missing 'version_date' (consolidation date)
3. Line 57: Missing 'version_date' (consolidation date)
4. Line 58: Missing 'version_date' (consolidation date)
5. Line 59: Missing 'version_date' (consolidation date)
6. Line 60: Missing 'version_date' (consolidation date)
7. Line 61: Missing 'version_date' (consolidation date)
8. Line 62: Missing 'version_date' (consolidation date)
9. Line 63: Missing 'version_date' (consolidation date)
10. Line 64: Missing 'version_date' (consolidation date)
11. Line 65: Missing 'version_date' (consolidation date)
12. Line 66: Very low word count (31)
13. Line 66: Missing 'version_date' (consolidation date)
14. Line 66: No article references found
15. Line 67: Missing 'version_date' (consolidation date)
16. Line 68: Missing 'version_date' (consolidation date)
17. Line 69: Missing 'version_date' (consolidation date)
18. Line 86: No article references found
19. Line 99: Missing 'version_date' (consolidation date)
20. Line 100: Missing 'version_date' (consolidation date)
21. Line 101: Missing 'version_date' (consolidation date)
22. Line 102: Missing 'version_date' (consolidation date)
23. Line 103: Missing 'version_date' (consolidation date)
24. Line 104: Missing 'version_date' (consolidation date)
25. Line 105: Missing 'version_date' (consolidation date)
26. Line 106: Missing 'version_date' (consolidation date)
27. Line 107: Missing 'version_date' (consolidation date)
28. Line 108: Missing 'version_date' (consolidation date)
29. Line 109: Missing 'version_date' (consolidation date)
30. Line 110: Missing 'version_date' (consolidation date)
31. Line 111: Missing 'version_date' (consolidation date)
32. Line 111: No article references found
33. Line 112: Missing 'version_date' (consolidation date)
34. Line 113: Missing 'version_date' (consolidation date)
35. Line 114: Missing 'version_date' (consolidation date)
36. Line 115: Missing 'version_date' (consolidation date)
37. Line 116: Missing 'version_date' (consolidation date)
38. Line 117: Missing 'version_date' (consolidation date)
39. Line 118: Missing 'version_date' (consolidation date)
40. Line 119: Missing 'version_date' (consolidation date)
41. Line 119: No article references found
42. Line 120: Missing 'version_date' (consolidation date)
43. Line 121: Missing 'version_date' (consolidation date)
44. Line 122: Missing 'version_date' (consolidation date)
45. Line 122: No article references found
46. Line 123: Missing 'version_date' (consolidation date)
47. Line 123: No article references found
48. Line 124: Missing 'version_date' (consolidation date)
49. Line 125: Missing 'version_date' (consolidation date)
50. Line 126: Missing 'version_date' (consolidation date)

... and 112 more warnings


---

## Validation Criteria

### Required Fields (Blocking)
- ✓ `text` (string, 100-50000 chars)
- ✓ `metadata.layer` (string)
- ✓ `metadata.type` (string)
- ✓ `metadata.domaine` (string, must be valid domain)
- ✓ `metadata.source_file` (string)
- ✓ `metadata.articles` (array)
- ✓ `metadata.word_count` (integer)
- ✓ `metadata.has_context` (boolean)

### Recommended Fields (Non-blocking)
- ⚠️ `metadata.version_date` (consolidation date)
- ⚠️ `metadata.articles` (should not be empty)
- ⚠️ `metadata.section_title` (source name)

---

## Next Steps

✅ **Validation successful! Ready for Supabase import.**

```bash
# Import to Supabase
python pipeline/supabase_indexer.py --input backend/exports/legal_chunks_primary.jsonl

# Verify import
python backend/tests/check_hybrid_available.py
```

### Post-Import Verification

1. Check chunk count in Supabase matches export (258 expected)
2. Test vector search with sample queries
3. Verify article filters work correctly
4. Test hybrid search (RRF) functionality
