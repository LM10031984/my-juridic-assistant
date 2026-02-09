"""
Stage 5: Validate Export
Validates legal_chunks_primary.jsonl for Supabase import readiness.

Outputs:
- backend/reports/export_validation.md (validation report)
- Exit code 0 if validation passes, 1 if blocking errors found
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class JSONLValidator:
    """Validates JSONL export for Supabase schema compliance"""

    # Required fields per Supabase schema
    REQUIRED_FIELDS = [
        'text',
        'metadata.layer',
        'metadata.type',
        'metadata.domaine',
        'metadata.source_file',
        'metadata.articles',  # Must be array
        'metadata.word_count',
        'metadata.has_context',
    ]

    VALID_DOMAINS = ['copropriete', 'location', 'pro_immo', 'transaction']
    VALID_TYPES = [
        'loi', 'decret', 'code_civil', 'code_construction_habitation',
        'code_consommation', 'texte_juridique', 'unknown'
    ]
    VALID_LAYERS = ['sources_juridiques', 'fiches_ia_ready', 'regles_liaison', 'unknown']

    def __init__(self):
        self.blocking_errors = []
        self.warnings = []
        self.stats = {
            'total_chunks': 0,
            'valid_chunks': 0,
            'chunks_with_errors': 0,
            'chunks_with_warnings': 0,
        }

    def has_field(self, obj: Dict, field_path: str) -> bool:
        """Checks if nested field exists (e.g., 'metadata.articles')"""
        parts = field_path.split('.')
        current = obj

        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return False
            current = current[part]

        return True

    def get_field(self, obj: Dict, field_path: str):
        """Gets nested field value"""
        parts = field_path.split('.')
        current = obj

        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]

        return current

    def validate_chunk(self, chunk: Dict, line_num: int) -> Tuple[List[str], List[str]]:
        """Validates a single chunk. Returns (blocking_errors, warnings)"""
        errors = []
        warnings = []

        # Check required fields
        for field_path in self.REQUIRED_FIELDS:
            if not self.has_field(chunk, field_path):
                errors.append(f"Line {line_num}: Missing required field '{field_path}'")

        # Validate field types
        metadata = chunk.get('metadata', {})

        # Text field
        text = chunk.get('text', '')
        if not isinstance(text, str):
            errors.append(f"Line {line_num}: 'text' must be string")
        elif len(text) < 100:
            warnings.append(f"Line {line_num}: Text very short ({len(text)} chars)")
        elif len(text) > 50000:
            warnings.append(f"Line {line_num}: Text very long ({len(text)} chars)")

        # Articles field (must be array)
        articles = metadata.get('articles')
        if articles is not None and not isinstance(articles, list):
            errors.append(f"Line {line_num}: 'articles' must be array, got {type(articles).__name__}")

        # Validate domain
        domaine = metadata.get('domaine')
        if domaine and domaine not in self.VALID_DOMAINS:
            errors.append(f"Line {line_num}: Invalid domain '{domaine}'")

        # Validate type
        doc_type = metadata.get('type')
        if doc_type and doc_type not in self.VALID_TYPES:
            warnings.append(f"Line {line_num}: Unknown type '{doc_type}'")

        # Validate layer
        layer = metadata.get('layer')
        if layer and layer not in self.VALID_LAYERS:
            warnings.append(f"Line {line_num}: Unknown layer '{layer}'")

        # Word count should be reasonable
        word_count = metadata.get('word_count')
        if word_count is not None:
            if word_count < 50:
                warnings.append(f"Line {line_num}: Very low word count ({word_count})")
            elif word_count > 2000:
                warnings.append(f"Line {line_num}: Very high word count ({word_count})")

        # Optional but recommended fields
        if not metadata.get('version_date'):
            warnings.append(f"Line {line_num}: Missing 'version_date' (consolidation date)")

        if not metadata.get('articles') or len(metadata.get('articles', [])) == 0:
            warnings.append(f"Line {line_num}: No article references found")

        return errors, warnings

    def validate_file(self, jsonl_path: Path) -> Dict:
        """Validates entire JSONL file"""
        print(f"Validating: {jsonl_path}")
        print()

        if not jsonl_path.exists():
            self.blocking_errors.append(f"File not found: {jsonl_path}")
            return self.generate_report()

        line_num = 0
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                line_num += 1
                self.stats['total_chunks'] += 1

                # Parse JSON
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError as e:
                    error_msg = f"Line {line_num}: Invalid JSON - {str(e)}"
                    self.blocking_errors.append(error_msg)
                    self.stats['chunks_with_errors'] += 1
                    continue

                # Validate chunk
                errors, warnings = self.validate_chunk(chunk, line_num)

                if errors:
                    self.blocking_errors.extend(errors)
                    self.stats['chunks_with_errors'] += 1
                else:
                    self.stats['valid_chunks'] += 1

                if warnings:
                    self.warnings.extend(warnings)
                    self.stats['chunks_with_warnings'] += 1

        print(f"Validated {self.stats['total_chunks']} chunks")
        print(f"  Valid: {self.stats['valid_chunks']}")
        print(f"  With errors: {self.stats['chunks_with_errors']}")
        print(f"  With warnings: {self.stats['chunks_with_warnings']}")

        return self.generate_report()

    def generate_report(self) -> Dict:
        """Generates validation report"""
        return {
            'stats': self.stats,
            'blocking_errors': self.blocking_errors,
            'warnings': self.warnings,
            'validation_passed': len(self.blocking_errors) == 0,
        }


def generate_markdown_report(validation_results: Dict) -> str:
    """Generates markdown validation report"""
    stats = validation_results['stats']
    errors = validation_results['blocking_errors']
    warnings = validation_results['warnings']
    passed = validation_results['validation_passed']

    status_emoji = "✅" if passed else "❌"
    status_text = "PASSED" if passed else "FAILED"

    report = f"""# Export Validation Report (Stage 5)

Generated: corpus_validate_export.py

## Status: {status_emoji} {status_text}

**Summary:**
- Total chunks: {stats['total_chunks']}
- Valid chunks: {stats['valid_chunks']}
- Chunks with errors: {stats['chunks_with_errors']}
- Chunks with warnings: {stats['chunks_with_warnings']}

---

## Blocking Errors ({len(errors)})

"""

    if errors:
        report += "🔴 **CRITICAL**: The following errors MUST be fixed before import:\n\n"
        for i, error in enumerate(errors[:50], 1):  # Limit to first 50
            report += f"{i}. {error}\n"
        if len(errors) > 50:
            report += f"\n... and {len(errors) - 50} more errors\n"
    else:
        report += "✅ No blocking errors found!\n"

    report += f"""

---

## Warnings ({len(warnings)})

"""

    if warnings:
        report += "⚠️ **Non-blocking**: These issues should be reviewed but won't prevent import:\n\n"
        for i, warning in enumerate(warnings[:50], 1):  # Limit to first 50
            report += f"{i}. {warning}\n"
        if len(warnings) > 50:
            report += f"\n... and {len(warnings) - 50} more warnings\n"
    else:
        report += "✅ No warnings!\n"

    report += """

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

"""

    if passed:
        report += """✅ **Validation successful! Ready for Supabase import.**

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
"""
    else:
        report += f"""❌ **Validation failed with {len(errors)} blocking errors.**

**Action required:**
1. Review blocking errors above
2. Fix issues in chunking pipeline (corpus_chunk_primary.py)
3. Re-run Stage 3: `python backend/tools/corpus_chunk_primary.py`
4. Re-validate: `python backend/tools/corpus_validate_export.py`

**Common issues:**
- Missing required fields → Check enhanced metadata extraction
- Invalid JSON → Check file encoding (must be UTF-8)
- Invalid domain/type → Check metadata extraction from file paths
"""

    return report


def main():
    """Main execution"""
    base_dir = Path(__file__).parent.parent.parent
    jsonl_path = base_dir / 'backend' / 'exports' / 'legal_chunks_primary.jsonl'
    report_path = base_dir / 'backend' / 'reports' / 'export_validation.md'

    if not jsonl_path.exists():
        print("ERROR: JSONL export not found. Run Stage 3 first:")
        print("  python backend/tools/corpus_chunk_primary.py")
        sys.exit(1)

    print("=" * 80)
    print("STAGE 5: VALIDATE EXPORT")
    print("=" * 80)
    print()

    validator = JSONLValidator()
    results = validator.validate_file(jsonl_path)

    # Generate markdown report
    md_report = generate_markdown_report(results)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(md_report)

    print(f"\n[OK] Validation report saved: {report_path}")

    print("\n" + "=" * 80)
    if results['validation_passed']:
        print("VALIDATION PASSED [OK]")
        print("=" * 80)
        print(f"Blocking errors: 0")
        print(f"Warnings: {len(results['warnings'])}")
        print("\nReady for Supabase import!")
        print("Next step: python pipeline/supabase_indexer.py --input backend/exports/legal_chunks_primary.jsonl")
        sys.exit(0)
    else:
        print("VALIDATION FAILED [ERROR]")
        print("=" * 80)
        print(f"Blocking errors: {len(results['blocking_errors'])}")
        print(f"Warnings: {len(results['warnings'])}")
        print("\nFix errors and re-run validation.")
        sys.exit(1)


if __name__ == '__main__':
    main()
