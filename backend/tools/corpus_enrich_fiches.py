"""
Stage 4: Enrich Fiches with Proof-First Templates
Adds BASE JURIDIQUE and EXTRAITS sections to fiches that lack them.

Outputs:
- Corpus/clean/fiches_with_templates/**/*.md (enriched fiches, originals preserved)
- backend/reports/fiches_missing_proof.md (list of fiches needing enrichment)
- backend/reports/fiches_enrichment_log.md (transformation report)
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple


class FicheEnricher:
    """Enriches fiches with BASE JURIDIQUE and EXTRAITS templates"""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.fiches_dir = base_dir / 'Corpus' / '02_fiches_ia_ready'
        self.output_dir = base_dir / 'Corpus' / 'clean' / 'fiches_with_templates'

        # Template to add at end of file
        self.template = """

---

## BASE JURIDIQUE

**Références (articles, codes, lois) :**
- [À compléter manuellement depuis les textes primaires]

---

## EXTRAITS (copier-coller exact depuis textes primaires)

**Extrait 1 :**
```
[À compléter : copier-coller du texte légal exact]
```

**Extrait 2 :**
```
[À compléter : copier-coller du texte légal exact]
```

**Extrait 3 :**
```
[À compléter : si nécessaire]
```

---

> **Note** : Ces sections doivent être complétées UNIQUEMENT avec des extraits exacts
> des textes primaires présents dans `Corpus/01_sources_text/`. Ne jamais inventer
> ou paraphraser. L'objectif est de garantir que l'assistant ne cite que des articles
> réellement indexés dans le corpus.
"""

    def has_base_juridique_section(self, content: str) -> bool:
        """Checks if fiche already has BASE JURIDIQUE section"""
        return bool(re.search(r'^##?\s*BASE JURIDIQUE', content, re.IGNORECASE | re.MULTILINE))

    def has_extraits_section(self, content: str) -> bool:
        """Checks if fiche already has EXTRAITS section"""
        return bool(re.search(r'^##?\s*EXTRAITS', content, re.IGNORECASE | re.MULTILINE))

    def needs_enrichment(self, content: str) -> Tuple[bool, str]:
        """Determines if fiche needs enrichment"""
        has_base = self.has_base_juridique_section(content)
        has_extraits = self.has_extraits_section(content)

        if has_base and has_extraits:
            return False, 'has_both'
        elif has_base and not has_extraits:
            return True, 'missing_extraits'
        elif not has_base and has_extraits:
            return True, 'missing_base'
        else:
            return True, 'missing_both'

    def enrich_fiche(self, file_path: Path) -> Dict:
        """Adds template sections to a fiche if needed"""
        print(f"Processing: {file_path.name}")

        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        needs_enrichment, status = self.needs_enrichment(original_content)

        if not needs_enrichment:
            print(f"  [OK] Already has BASE JURIDIQUE and EXTRAITS sections")
            return {
                'file': file_path.name,
                'domain': file_path.parent.name,
                'status': status,
                'enriched': False,
                'sections_added': [],
            }

        # Add template at end
        enriched_content = original_content.rstrip() + self.template

        # Determine output path (preserve domain structure)
        relative_path = file_path.relative_to(self.fiches_dir)
        output_path = self.output_dir / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write enriched fiche
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(enriched_content)

        sections_added = []
        if status in ['missing_base', 'missing_both']:
            sections_added.append('BASE JURIDIQUE')
        if status in ['missing_extraits', 'missing_both']:
            sections_added.append('EXTRAITS')

        print(f"  [OK] Added sections: {', '.join(sections_added)}")

        return {
            'file': file_path.name,
            'domain': file_path.parent.name,
            'status': status,
            'enriched': True,
            'sections_added': sections_added,
            'output_path': str(output_path.relative_to(self.base_dir)),
        }

    def enrich_all_fiches(self) -> List[Dict]:
        """Enriches all fiches"""
        results = []
        fiche_files = sorted(self.fiches_dir.glob('**/*.md'))

        for file_path in fiche_files:
            result = self.enrich_fiche(file_path)
            results.append(result)

        return results

    def generate_missing_proof_report(self, results: List[Dict]) -> str:
        """Generates report of fiches missing proof sections BEFORE enrichment"""
        missing = [r for r in results if r['enriched']]

        if not missing:
            return """# Fiches Missing Proof Report (Stage 4)

✅ **All fiches already have BASE JURIDIQUE and EXTRAITS sections!**

No enrichment needed.
"""

        report = f"""# Fiches Missing Proof Report (Stage 4)

Generated: corpus_enrich_fiches.py (BEFORE enrichment)

## Summary

**Fiches needing enrichment:** {len(missing)} / {len(results)}

---

## Fiches by Status

"""

        # Group by status
        by_status = {
            'missing_both': [],
            'missing_base': [],
            'missing_extraits': [],
        }

        for r in missing:
            status = r['status']
            if status in by_status:
                by_status[status].append(r)

        # Missing both sections
        if by_status['missing_both']:
            report += f"""
### Missing Both Sections ({len(by_status['missing_both'])})

These fiches lack both BASE JURIDIQUE and EXTRAITS sections:

| File | Domain |
|------|--------|
"""
            for r in by_status['missing_both']:
                report += f"| {r['file'][:50]} | {r['domain']} |\n"

        # Missing only BASE JURIDIQUE
        if by_status['missing_base']:
            report += f"""
### Missing BASE JURIDIQUE Only ({len(by_status['missing_base'])})

These fiches have EXTRAITS but lack BASE JURIDIQUE:

| File | Domain |
|------|--------|
"""
            for r in by_status['missing_base']:
                report += f"| {r['file'][:50]} | {r['domain']} |\n"

        # Missing only EXTRAITS
        if by_status['missing_extraits']:
            report += f"""
### Missing EXTRAITS Only ({len(by_status['missing_extraits'])})

These fiches have BASE JURIDIQUE but lack EXTRAITS:

| File | Domain |
|------|--------|
"""
            for r in by_status['missing_extraits']:
                report += f"| {r['file'][:50]} | {r['domain']} |\n"

        return report

    def generate_enrichment_log(self, results: List[Dict]) -> str:
        """Generates enrichment transformation log"""
        enriched = [r for r in results if r['enriched']]
        total_sections = sum(len(r['sections_added']) for r in enriched)

        report = f"""# Fiches Enrichment Log (Stage 4)

Generated: corpus_enrich_fiches.py

## Summary

**Total fiches processed:** {len(results)}
**Fiches enriched:** {len(enriched)}
**Sections added:** {total_sections}

**Output:** All enriched fiches saved to `Corpus/clean/fiches_with_templates/`
**Originals preserved:** `Corpus/02_fiches_ia_ready/` (unchanged)

---

## Enrichment Results

| File | Domain | Status | Sections Added |
|------|--------|--------|----------------|
"""

        for r in results:
            if r['enriched']:
                sections = ', '.join(r['sections_added']) if r['sections_added'] else 'none'
                report += f"| {r['file'][:40]} | {r['domain']} | {r['status']} | {sections} |\n"
            else:
                report += f"| {r['file'][:40]} | {r['domain']} | {r['status']} | (already complete) |\n"

        report += f"""

---

## Domain Breakdown

"""

        # Group by domain
        by_domain = {}
        for r in results:
            domain = r['domain']
            if domain not in by_domain:
                by_domain[domain] = {'total': 0, 'enriched': 0, 'sections': 0}
            by_domain[domain]['total'] += 1
            if r['enriched']:
                by_domain[domain]['enriched'] += 1
                by_domain[domain]['sections'] += len(r['sections_added'])

        for domain, stats in sorted(by_domain.items()):
            report += f"""
### {domain.title()}
- Total fiches: {stats['total']}
- Enriched: {stats['enriched']}
- Sections added: {stats['sections']}
"""

        report += """

---

## Next Steps

### Manual Completion Required

The enriched fiches now have template sections for BASE JURIDIQUE and EXTRAITS.
**These MUST be manually completed** with:

1. **BASE JURIDIQUE**: List exact article references from primary sources
   - Example: `Article 23 de la Loi du 6 juillet 1989`
   - Example: `Article 3 du Décret n° 87-713`

2. **EXTRAITS**: Copy-paste exact legal text from primary sources
   - Navigate to `Corpus/01_sources_text/[domain]/`
   - Find the relevant article
   - Copy the EXACT text (word-for-word)
   - Paste into the EXTRAITS section

### Pipeline Continuation

```bash
# After manual completion of proof sections, run Stage 5
python backend/tools/corpus_validate_export.py

# Verify chunks include article references
cat backend/reports/chunk_stats.md
```

### Quality Verification

To verify enrichment:

```bash
# Compare original and enriched versions
diff Corpus/02_fiches_ia_ready/location/Fiche_IA_READY_Loi_1989_RapportsLocatifs_20260206.md \\
     Corpus/clean/fiches_with_templates/location/Fiche_IA_READY_Loi_1989_RapportsLocatifs_20260206.md
```

Expected changes:
- Template sections added at end of file
- Original content preserved
- Clear instructions for manual completion
"""

        return report


def main():
    """Main execution"""
    base_dir = Path(__file__).parent.parent.parent

    print("=" * 80)
    print("STAGE 4: ENRICH FICHES WITH PROOF-FIRST TEMPLATES")
    print("=" * 80)
    print()

    enricher = FicheEnricher(base_dir)

    # First, generate "before" report
    print("Analyzing fiches...")
    temp_results = []
    fiche_files = sorted(enricher.fiches_dir.glob('**/*.md'))

    for file_path in fiche_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        needs_enrichment, status = enricher.needs_enrichment(content)
        temp_results.append({
            'file': file_path.name,
            'domain': file_path.parent.name,
            'status': status,
            'enriched': needs_enrichment,
            'sections_added': [],
        })

    # Generate missing proof report (before enrichment)
    missing_report = enricher.generate_missing_proof_report(temp_results)
    reports_dir = base_dir / 'backend' / 'reports'
    missing_path = reports_dir / 'fiches_missing_proof.md'
    with open(missing_path, 'w', encoding='utf-8') as f:
        f.write(missing_report)
    print(f"[OK] Missing proof report saved: {missing_path}")

    # Now perform enrichment
    print("\nEnriching fiches...")
    results = enricher.enrich_all_fiches()

    # Generate enrichment log
    log = enricher.generate_enrichment_log(results)
    log_path = reports_dir / 'fiches_enrichment_log.md'
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(log)
    print(f"\n[OK] Enrichment log saved: {log_path}")

    print("\n" + "=" * 80)
    print("ENRICHMENT COMPLETE")
    print("=" * 80)

    enriched = [r for r in results if r['enriched']]
    total_sections = sum(len(r['sections_added']) for r in enriched)

    print(f"Enriched {len(enriched)} / {len(results)} fiches")
    print(f"Added {total_sections} template sections")
    print(f"\nOutput: Corpus/clean/fiches_with_templates/")
    print(f"Originals preserved: Corpus/02_fiches_ia_ready/")
    print("\n[!] MANUAL ACTION REQUIRED:")
    print("    Complete BASE JURIDIQUE and EXTRAITS sections with exact legal text")
    print("\nNext step: python backend/tools/corpus_validate_export.py")


if __name__ == '__main__':
    main()
