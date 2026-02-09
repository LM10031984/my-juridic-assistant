"""
Validate Fiches Proof-First - TÂCHE 4
Vérifie que toutes les fiches respectent les règles strictes :
- Si BASE JURIDIQUE non vide => EXTRAITS non vide
- Chaque article dans BASE JURIDIQUE apparaît dans EXTRAITS
- EXTRAITS ne contiennent pas de bruit
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple


class FicheProofValidator:
    """Validates fiches for proof-first compliance"""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.fiches_dir = base_dir / 'Corpus' / 'clean' / 'fiches_updated'

        # Article pattern
        self.article_pattern = re.compile(
            r'(?:Article|Art\.?)\s+('
            r'[LRDCP]\.?\s*[\d][\d\-]*'
            r'|[\d][\d\-]*[A-Z]?(?:-\d+)?'
            r')',
            re.IGNORECASE
        )

        # Noise patterns (Legifrance artifacts)
        self.noise_patterns = [
            re.compile(r'Aller au (contenu|menu|recherche)', re.IGNORECASE),
            re.compile(r'Informations de mises à jour', re.IGNORECASE),
            re.compile(r'République Française', re.IGNORECASE),
            re.compile(r'ChronoLégi', re.IGNORECASE),
            re.compile(r'Naviguer dans le sommaire', re.IGNORECASE),
        ]

    def normalize_article_id(self, article_id: str) -> str:
        """Normalizes article ID"""
        normalized = re.sub(r'\s+', ' ', article_id.strip())
        normalized = re.sub(r'([LRDCP])\.(\d)', r'\1. \2', normalized)
        normalized = re.sub(r'([LRDCP])\s+\.', r'\1.', normalized)
        return normalized.lower()

    def extract_section(self, content: str, section_name: str) -> str:
        """Extracts a section from fiche"""
        # For EXTRAITS, stop at "---" separator or next top-level section (##), not at ### inside code blocks
        if 'EXTRAITS' in section_name.upper():
            pattern = rf'##\s*{section_name}.*?(?=\n---|\n##\s+[^#]|$)'
        else:
            pattern = rf'##?\s*{section_name}.*?(?=\n---|\n##\s+|$)'

        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        return match.group(0) if match else ""

    def extract_articles_from_base_juridique(self, base_section: str) -> List[str]:
        """Extracts article IDs from BASE JURIDIQUE section"""
        articles = []
        for match in self.article_pattern.finditer(base_section):
            article_id = match.group(1).strip()
            normalized = self.normalize_article_id(article_id)
            if normalized not in articles:
                articles.append(normalized)
        return articles

    def extract_articles_from_extraits(self, extraits_section: str) -> List[str]:
        """Extracts article IDs from EXTRAITS section"""
        articles = []
        for match in self.article_pattern.finditer(extraits_section):
            article_id = match.group(1).strip()
            normalized = self.normalize_article_id(article_id)
            if normalized not in articles:
                articles.append(normalized)
        return articles

    def check_noise_in_extraits(self, extraits_section: str) -> List[str]:
        """Checks for Legifrance noise in EXTRAITS"""
        found_noise = []
        for pattern in self.noise_patterns:
            if pattern.search(extraits_section):
                found_noise.append(pattern.pattern)
        return found_noise

    def validate_fiche(self, file_path: Path) -> Dict:
        """Validates a single fiche"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract sections
        base_section = self.extract_section(content, 'BASE JURIDIQUE')
        extraits_section = self.extract_section(content, 'EXTRAITS')

        errors = []
        warnings = []

        # Check if marked as needs_human (⚠️ NEEDS HUMAN REVIEW marker)
        is_needs_human = 'needs_human' in content.lower() or 'needs human review' in content.lower()

        # Rule 1: If BASE JURIDIQUE non-empty => EXTRAITS non-empty
        base_has_content = base_section and len(base_section.strip()) > 50
        extraits_has_content = extraits_section and len(extraits_section.strip()) > 50

        if base_has_content and not extraits_has_content:
            errors.append("BASE JURIDIQUE present but EXTRAITS empty")

        # Rule 2: Each article in BASE JURIDIQUE must appear in EXTRAITS
        if base_has_content and extraits_has_content:
            base_articles = self.extract_articles_from_base_juridique(base_section)
            extraits_articles = self.extract_articles_from_extraits(extraits_section)

            missing_articles = [a for a in base_articles if a not in extraits_articles]

            if missing_articles and not is_needs_human:
                # Only error if not marked as needs_human
                errors.append(f"Articles in BASE but not in EXTRAITS: {', '.join(missing_articles[:5])}")
            elif missing_articles:
                warnings.append(f"Articles in BASE but not in EXTRAITS (needs_human): {len(missing_articles)}")

        # Rule 3: EXTRAITS should not contain noise
        if extraits_has_content:
            noise_found = self.check_noise_in_extraits(extraits_section)
            if noise_found:
                errors.append(f"Noise detected in EXTRAITS: {len(noise_found)} patterns")

        # Determine status
        if errors:
            status = 'ERROR'
        elif is_needs_human:
            status = 'needs_human'
        elif warnings:
            status = 'warning'
        else:
            status = 'OK'

        return {
            'file': file_path.name,
            'domain': file_path.parent.name,
            'status': status,
            'errors': errors,
            'warnings': warnings,
            'base_has_content': base_has_content,
            'extraits_has_content': extraits_has_content,
            'needs_human': is_needs_human,
        }

    def validate_all_fiches(self) -> List[Dict]:
        """Validates all fiches"""
        results = []
        fiche_files = sorted(self.fiches_dir.glob('**/*.md'))

        print(f"Validating {len(fiche_files)} fiches...\n")

        for file_path in fiche_files:
            result = self.validate_fiche(file_path)
            results.append(result)

            # Print status
            status_icon = {
                'OK': '[OK]',
                'warning': '[WARN]',
                'needs_human': '[HUMAN]',
                'ERROR': '[ERROR]'
            }
            print(f"  {status_icon[result['status']]} {file_path.name[:50]}")

            if result['errors']:
                for error in result['errors']:
                    print(f"        ERROR: {error}")

        return results

    def generate_validation_report(self, results: List[Dict]) -> str:
        """Generates validation report"""
        total = len(results)
        by_status = {}
        for r in results:
            by_status[r['status']] = by_status.get(r['status'], 0) + 1

        errors_count = by_status.get('ERROR', 0)
        needs_human_count = by_status.get('needs_human', 0)
        ok_count = by_status.get('OK', 0)
        warning_count = by_status.get('warning', 0)

        report = f"""# Fiches Proof-First Validation Report

Generated: validate_fiches_proof_first.py

## Summary

**Total fiches validated:** {total}
**Status breakdown:**
- ✅ **OK:** {ok_count} ({ok_count/total*100:.1f}%)
- ⚠️ **Warnings:** {warning_count} ({warning_count/total*100:.1f}%)
- 🔍 **Needs human:** {needs_human_count} ({needs_human_count/total*100:.1f}%)
- ❌ **Errors:** {errors_count} ({errors_count/total*100:.1f}%)

**Blocking errors:** {errors_count} (must be 0 for production)

---

## Validation Rules

1. **BASE JURIDIQUE non vide => EXTRAITS non vide**
2. **Chaque article dans BASE JURIDIQUE apparaît dans EXTRAITS**
3. **EXTRAITS ne contiennent pas de bruit Legifrance**

---

## Fiches OK ({ok_count})

"""

        ok_fiches = [r for r in results if r['status'] == 'OK']
        if ok_fiches:
            report += "| File | Domain |\n"
            report += "|------|--------|\n"
            for r in ok_fiches[:20]:
                report += f"| {r['file'][:45]} | {r['domain']} |\n"
            if len(ok_fiches) > 20:
                report += f"| ... and {len(ok_fiches) - 20} more |\n"
        else:
            report += "No fiches with OK status.\n"

        report += f"""

---

## Fiches Needs Human ({needs_human_count})

These fiches require manual review but are not blocking errors.

| File | Domain | Reason |
|------|--------|--------|
"""

        needs_human_fiches = [r for r in results if r['status'] == 'needs_human']
        for r in needs_human_fiches[:30]:
            reason = r['warnings'][0] if r['warnings'] else 'Marked for manual review'
            report += f"| {r['file'][:45]} | {r['domain']} | {reason[:50]} |\n"

        if len(needs_human_fiches) > 30:
            report += f"| ... and {len(needs_human_fiches) - 30} more |\n"

        report += f"""

---

## Fiches with Errors ({errors_count})

**BLOCKING**: These must be fixed before production.

"""

        error_fiches = [r for r in results if r['status'] == 'ERROR']
        if error_fiches:
            report += "| File | Domain | Error |\n"
            report += "|------|--------|-------|\n"
            for r in error_fiches:
                error_str = '; '.join(r['errors'][:2])
                report += f"| {r['file'][:45]} | {r['domain']} | {error_str[:60]} |\n"
        else:
            report += "✅ **No blocking errors found!**\n"

        report += f"""

---

## Recommendations

"""

        if errors_count > 0:
            report += f"""
### Critical (Fix Now)
- Fix {errors_count} fiches with blocking errors
- Re-run validation after fixes
"""

        if needs_human_count > 0:
            report += f"""
### Manual Review Required
- Review {needs_human_count} fiches marked for human validation
- Verify BASE JURIDIQUE and EXTRAITS accuracy
- Complete missing information from primary sources
"""

        if ok_count == total:
            report += """
### Ready for Production
- ✅ All fiches pass validation
- ✅ No blocking errors
- ✅ Ready for indexation
"""

        report += """

---

## Next Steps

```bash
# If errors = 0, proceed to indexation
python pipeline/supabase_indexer.py --input backend/exports/legal_chunks_primary.jsonl

# Manual review of needs_human fiches
ls Corpus/clean/fiches_updated/ | grep -f backend/reports/needs_human_list.txt
```
"""

        return report


def main():
    """Main execution"""
    base_dir = Path(__file__).parent.parent.parent

    print("=" * 80)
    print("FICHES PROOF-FIRST VALIDATION")
    print("=" * 80)
    print()

    validator = FicheProofValidator(base_dir)
    results = validator.validate_all_fiches()

    # Generate report
    reports_dir = base_dir / 'backend' / 'reports'
    report = validator.generate_validation_report(results)
    report_path = reports_dir / 'fiches_proof_validation.md'

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n[OK] Validation report saved: {report_path}")

    print("\n" + "=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80)

    by_status = {}
    for r in results:
        by_status[r['status']] = by_status.get(r['status'], 0) + 1

    print(f"OK: {by_status.get('OK', 0)}")
    print(f"Warnings: {by_status.get('warning', 0)}")
    print(f"Needs human: {by_status.get('needs_human', 0)}")
    print(f"Errors: {by_status.get('ERROR', 0)}")

    if by_status.get('ERROR', 0) > 0:
        print("\n[!] BLOCKING ERRORS FOUND - Fix before production")
    else:
        print("\n[OK] No blocking errors - Ready for production")


if __name__ == '__main__':
    main()
