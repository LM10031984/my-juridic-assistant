"""
Stage 4b: Auto-fill Fiches with BASE JURIDIQUE + EXTRAITS
Pre-fills proof sections from primary sources (no invention, no paraphrasing).

TÂCHE 1 (NEW): Block autofill on ambiguous articles to prevent false positives.
Uses shared article_id utilities for canonical normalization.

Outputs:
- Corpus/clean/fiches_autofilled/**/*.md (auto-filled fiches)
- backend/reports/fiches_autofill_report.md (transformation report)
- backend/reports/fiches_autofill_report.json (machine-readable)
"""

import re
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

# Add backend to path to import shared utilities
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Import shared article normalization utilities (TÂCHE 1)
from api.utils.article_id import (
    normalize_article_id,
    is_ambiguous_numeric,
    extract_article_ids
)


class FicheAutofiller:
    """Auto-fills fiches with exact legal references from primary sources"""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.fiches_dir = base_dir / 'Corpus' / 'clean' / 'fiches_with_templates'
        self.primary_dir = base_dir / 'Corpus' / 'clean' / 'primary_cleaned'
        self.output_dir = base_dir / 'Corpus' / 'clean' / 'fiches_autofilled'

        # Index: normalized_article_id -> (source_file, article_text)
        self.article_index: Dict[str, Tuple[str, str]] = {}

        # TÂCHE 1: Track ambiguous articles that should not be autofilled
        self.ambiguous_articles: set = set()

    def extract_article_ids_from_text(self, text: str) -> List[str]:
        """
        Extracts all article IDs from text using shared utilities (TÂCHE 1).
        Returns normalized, deduplicated article IDs.
        """
        # Use shared utility for canonical extraction
        return extract_article_ids(text)

    def build_article_index(self):
        """
        Builds index of all articles from primary cleaned sources.

        TÂCHE 1 (NEW): Uses shared normalize_article_id() for canonical form.
        """
        print("Building article index from primary sources...")

        primary_files = sorted(self.primary_dir.glob('**/*.md'))
        article_count = 0

        # Pattern to split by article headers
        article_header_pattern = re.compile(
            r'(###\s+(?:Article|Art\.?)\s+[^\n]+)',
            re.IGNORECASE
        )

        for file_path in primary_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Split by article headers
            articles = article_header_pattern.split(content)

            for i in range(1, len(articles), 2):
                if i + 1 < len(articles):
                    header = articles[i]
                    body = articles[i + 1]

                    # Extract article IDs from header using shared utility
                    article_ids = extract_article_ids(header)

                    if article_ids:
                        # Use first extracted article ID as primary
                        normalized_id = article_ids[0]
                        article_text = (header + body).strip()

                        # Store in index (keep first occurrence if duplicates)
                        if normalized_id not in self.article_index:
                            self.article_index[normalized_id] = (
                                file_path.name,
                                article_text
                            )
                            article_count += 1

        print(f"  Indexed {article_count} unique articles from {len(primary_files)} files")

    def extract_fiche_content(self, content: str) -> Tuple[str, str, str]:
        """Splits fiche into: main_content, base_juridique_section, extraits_section"""
        # Find BASE JURIDIQUE section
        base_match = re.search(
            r'---\s*##\s*BASE JURIDIQUE.*?(?=---|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )

        # Find EXTRAITS section
        extraits_match = re.search(
            r'---\s*##\s*EXTRAITS.*?(?=---|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )

        if base_match and extraits_match:
            # Extract main content (before BASE JURIDIQUE)
            main_end = base_match.start()
            main_content = content[:main_end].rstrip()

            base_section = content[base_match.start():base_match.end()]
            extraits_section = content[extraits_match.start():extraits_match.end()]

            return main_content, base_section, extraits_section

        # Fallback: return entire content as main
        return content, "", ""

    def generate_base_juridique_section(self, article_ids: List[str], found_articles: Dict[str, Tuple[str, str]]) -> str:
        """Generates BASE JURIDIQUE section with found articles"""
        if not found_articles:
            return """---

## BASE JURIDIQUE

**Références (articles, codes, lois) :**
- [Aucun article indexé trouvé - compléter manuellement]
"""

        references = []
        for article_id in article_ids:
            # article_id is already normalized
            if article_id in found_articles:
                source_file, _ = found_articles[article_id]
                references.append(f"- Article {article_id} (source: {source_file})")
            else:
                references.append(f"- Article {article_id} [NON TROUVÉ - vérifier manuellement]")

        section = f"""---

## BASE JURIDIQUE

**Références (articles, codes, lois) :**
{chr(10).join(references)}

> Ces références ont été extraites automatiquement depuis les textes primaires indexés.
"""
        return section

    def generate_extraits_section(self, found_articles: Dict[str, Tuple[str, str]], max_extraits: int = 2, max_chars: int = 1200) -> str:
        """Generates EXTRAITS section with up to max_extraits excerpts"""
        if not found_articles:
            return """
---

## EXTRAITS (copier-coller exact depuis textes primaires)

**Extrait 1 :**
```
[Aucun article indexé trouvé - compléter manuellement]
```
"""

        extraits = []
        for i, (article_id, (source_file, article_text)) in enumerate(list(found_articles.items())[:max_extraits]):
            # Truncate if too long (keep beginning)
            if len(article_text) > max_chars:
                truncated = article_text[:max_chars] + "\n[...tronqué...]"
            else:
                truncated = article_text

            extraits.append(f"""**Extrait {i + 1} :** (Article {article_id})
```
{truncated}
```
""")

        section = f"""
---

## EXTRAITS (copier-coller exact depuis textes primaires)

{chr(10).join(extraits)}

> Ces extraits ont été copiés automatiquement depuis les sources nettoyées.
> Ils sont exacts et non paraphrasés.
"""
        return section

    def autofill_fiche(self, file_path: Path) -> Dict:
        """
        Auto-fills a single fiche with BASE JURIDIQUE and EXTRAITS.

        TÂCHE 1 (NEW): Skip autofill if ANY article is ambiguous.
        """
        print(f"Processing: {file_path.name}")

        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        # Extract main content (before BASE JURIDIQUE)
        main_content, _, _ = self.extract_fiche_content(original_content)

        # Extract article IDs from main content only
        article_ids = self.extract_article_ids_from_text(main_content)

        if not article_ids:
            print(f"  [MANUAL] No articles detected")
            return {
                'file': file_path.name,
                'domain': file_path.parent.name,
                'status': 'manual_required',
                'reason': 'no_articles_detected',
                'articles_detected': 0,
                'articles_found': 0,
                'autofilled': False,
            }

        # TÂCHE 1 (NEW): Check for ambiguous articles
        ambiguous_articles = [art for art in article_ids if is_ambiguous_numeric(art)]

        if ambiguous_articles:
            print(f"  [MANUAL] {len(ambiguous_articles)} ambiguous articles detected: {', '.join(ambiguous_articles)}")
            # Track globally
            self.ambiguous_articles.update(ambiguous_articles)

            return {
                'file': file_path.name,
                'domain': file_path.parent.name,
                'status': 'manual_required',
                'reason': 'ambiguous_articles',
                'articles_detected': len(article_ids),
                'articles_found': 0,
                'autofilled': False,
                'ambiguous_articles': ambiguous_articles,
            }

        # Look up articles in index (using already normalized IDs)
        found_articles = {}
        for article_id in article_ids:
            # article_id is already normalized from extract_article_ids_from_text()
            if article_id in self.article_index:
                found_articles[article_id] = self.article_index[article_id]

        if not found_articles:
            print(f"  [MANUAL] {len(article_ids)} articles detected but 0 found in index")
            return {
                'file': file_path.name,
                'domain': file_path.parent.name,
                'status': 'manual_required',
                'reason': 'articles_not_in_index',
                'articles_detected': len(article_ids),
                'articles_found': 0,
                'autofilled': False,
                'detected_articles': article_ids,
            }

        # Generate new sections
        base_section = self.generate_base_juridique_section(article_ids, found_articles)
        extraits_section = self.generate_extraits_section(found_articles)

        # Assemble autofilled content
        autofilled_content = main_content + "\n" + base_section + extraits_section

        # Add note at end
        autofilled_content += f"""

---

> **Note d'auto-remplissage** : Ce document a été pré-rempli automatiquement
> à partir des textes primaires indexés. {len(found_articles)}/{len(article_ids)} articles
> ont été trouvés et intégrés. Vérifier la cohérence avant utilisation.
"""

        # Write autofilled fiche
        relative_path = file_path.relative_to(self.fiches_dir)
        output_path = self.output_dir / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(autofilled_content)

        print(f"  [OK] Autofilled: {len(found_articles)}/{len(article_ids)} articles")

        return {
            'file': file_path.name,
            'domain': file_path.parent.name,
            'status': 'autofilled',
            'articles_detected': len(article_ids),
            'articles_found': len(found_articles),
            'autofilled': True,
            'output_path': str(output_path.relative_to(self.base_dir)),
        }

    def autofill_all_fiches(self) -> List[Dict]:
        """Auto-fills all fiches"""
        results = []
        fiche_files = sorted(self.fiches_dir.glob('**/*.md'))

        for file_path in fiche_files:
            result = self.autofill_fiche(file_path)
            results.append(result)

        return results

    def generate_markdown_report(self, results: List[Dict]) -> str:
        """
        Generates markdown report.

        TÂCHE 1 (NEW): Include ambiguous articles statistics.
        """
        total = len(results)
        autofilled = [r for r in results if r['autofilled']]
        manual = [r for r in results if not r['autofilled']]

        total_detected = sum(r['articles_detected'] for r in results)
        total_found = sum(r['articles_found'] for r in results)

        # TÂCHE 1: Count ambiguous articles
        ambiguous_count = len([r for r in manual if r.get('reason') == 'ambiguous_articles'])

        report = f"""# Fiches Auto-fill Report

Generated: corpus_autofill_fiches.py

## Summary

**Total fiches processed:** {total}
**Fiches auto-filled:** {len(autofilled)} ({len(autofilled)/total*100:.1f}%)
**Fiches requiring manual completion:** {len(manual)} ({len(manual)/total*100:.1f}%)

**Article Detection:**
- Total articles detected in fiches: {total_detected}
- Total articles found in primary index: {total_found}
- Match rate: {total_found/total_detected*100:.1f}% ({total_found}/{total_detected})

**TÂCHE 1 - Ambiguous Articles (NEW):**
- Fiches blocked due to ambiguous articles: {ambiguous_count}
- Total unique ambiguous articles found: {len(self.ambiguous_articles)}
- Ambiguous articles: {', '.join(sorted(self.ambiguous_articles)) if self.ambiguous_articles else 'None'}

---

## Auto-filled Fiches ({len(autofilled)})

| File | Domain | Articles Detected | Articles Found | Coverage |
|------|--------|-------------------|----------------|----------|
"""

        for r in autofilled:
            coverage = f"{r['articles_found']}/{r['articles_detected']}"
            report += f"| {r['file'][:45]} | {r['domain']} | {r['articles_detected']} | {r['articles_found']} | {coverage} |\n"

        report += f"""

---

## Fiches Requiring Manual Completion ({len(manual)})

"""

        # Group by reason
        by_reason = defaultdict(list)
        for r in manual:
            by_reason[r['reason']].append(r)

        for reason, fiches in sorted(by_reason.items()):
            report += f"""
### Reason: {reason.replace('_', ' ').title()} ({len(fiches)})

| File | Domain | Articles Detected | Details |
|------|--------|-------------------|---------|
"""
            for r in fiches[:30]:  # Show max 30
                details = ""
                if reason == 'ambiguous_articles' and 'ambiguous_articles' in r:
                    details = f"Ambiguous: {', '.join(r['ambiguous_articles'])}"
                report += f"| {r['file'][:45]} | {r['domain']} | {r['articles_detected']} | {details} |\n"

            if len(fiches) > 30:
                report += f"| ... and {len(fiches) - 30} more |\n"

        report += """

---

## Recommendations

### For Auto-filled Fiches
- ✅ Review generated BASE JURIDIQUE and EXTRAITS sections
- ✅ Verify article references are correct and complete
- ✅ Check that extraits are relevant to the fiche topic

### For Manual-required Fiches
- **No articles detected**: These fiches may be overview/summary documents without specific article references
- **Articles not in index**: The referenced articles may be from external sources not in the corpus, or article IDs may need normalization
- **Ambiguous articles** (TÂCHE 1): Articles like "1", "2", "17" are too ambiguous to autofill safely. Manual review required to determine correct source text.

---

## Next Steps

```bash
# Review autofilled fiches
ls -la Corpus/clean/fiches_autofilled/

# Compare with templates
diff Corpus/clean/fiches_with_templates/location/Fiche_IA_READY_Loi_1989_RapportsLocatifs_20260206.md \\
     Corpus/clean/fiches_autofilled/location/Fiche_IA_READY_Loi_1989_RapportsLocatifs_20260206.md

# Proceed to validation
python backend/tools/corpus_validate_export.py
```
"""

        return report

    def generate_json_report(self, results: List[Dict]) -> Dict:
        """Generates machine-readable JSON report"""
        total = len(results)
        autofilled = [r for r in results if r['autofilled']]
        manual = [r for r in results if not r['autofilled']]

        total_detected = sum(r['articles_detected'] for r in results)
        total_found = sum(r['articles_found'] for r in results)

        return {
            'summary': {
                'total_fiches': total,
                'autofilled': len(autofilled),
                'manual_required': len(manual),
                'autofill_rate': len(autofilled) / total if total else 0,
                'articles_detected': total_detected,
                'articles_found': total_found,
                'match_rate': total_found / total_detected if total_detected else 0,
            },
            'autofilled_fiches': autofilled,
            'manual_required_fiches': manual,
        }


def main():
    """Main execution"""
    base_dir = Path(__file__).parent.parent.parent

    print("=" * 80)
    print("STAGE 4b: AUTO-FILL FICHES WITH BASE JURIDIQUE + EXTRAITS")
    print("=" * 80)
    print()

    autofiller = FicheAutofiller(base_dir)

    # Build article index
    autofiller.build_article_index()

    if not autofiller.article_index:
        print("\n[ERROR] No articles found in primary sources!")
        print("Make sure primary sources are cleaned and contain article headers.")
        return

    print(f"\n[OK] Article index ready: {len(autofiller.article_index)} articles\n")

    # Auto-fill fiches
    print("Auto-filling fiches...")
    results = autofiller.autofill_all_fiches()

    # Generate reports
    reports_dir = base_dir / 'backend' / 'reports'

    # Markdown report
    md_report = autofiller.generate_markdown_report(results)
    md_path = reports_dir / 'fiches_autofill_report.md'
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_report)
    print(f"\n[OK] Markdown report saved: {md_path}")

    # JSON report
    json_report = autofiller.generate_json_report(results)
    json_path = reports_dir / 'fiches_autofill_report.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_report, f, indent=2, ensure_ascii=False)
    print(f"[OK] JSON report saved: {json_path}")

    print("\n" + "=" * 80)
    print("AUTO-FILL COMPLETE")
    print("=" * 80)

    autofilled = len([r for r in results if r['autofilled']])
    manual = len([r for r in results if not r['autofilled']])

    print(f"Auto-filled: {autofilled} / {len(results)} fiches")
    print(f"Manual required: {manual} / {len(results)} fiches")

    total_detected = sum(r['articles_detected'] for r in results)
    total_found = sum(r['articles_found'] for r in results)
    print(f"Article match rate: {total_found}/{total_detected} ({total_found/total_detected*100:.1f}%)")

    print(f"\nOutput: Corpus/clean/fiches_autofilled/")
    print("\nNext step: Review autofilled fiches and proceed to validation")


if __name__ == '__main__':
    main()
