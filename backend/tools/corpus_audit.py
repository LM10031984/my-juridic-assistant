"""
Stage 1: Corpus Audit
Analyzes primary sources and fiches to detect quality issues.

Outputs:
- backend/reports/corpus_audit.md (human-readable)
- backend/reports/corpus_audit.json (machine-readable)
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict


# Legifrance noise patterns (lines 1-140 typically)
LEGIFRANCE_NOISE_PATTERNS = [
    r'^Aller au (contenu|menu|recherche)',
    r'Informations de mises à jour',
    r'Gestion des cookies',
    r'République Française',
    r'Accueil Légifrance',
    r'^(Imprimer|Copier le texte)$',
    r'ChronoLégi',
    r'Masquer les articles',
    r'Naviguer dans le sommaire',
    r'Recherche (simple|avancée)',
    r'Effectuer une recherche',
    r'Ex\. : L\. 121-1',
    r'^rechercher$',
    r'valider la recherche',
    r'Voir les modifications',
    r'Version (à la date|en vigueur)',
    r'Constitution du \d+',
    r'Déclaration des droits',
    r'(Codes|Textes consolidés|Jurisprudence)',
    r'Journal officiel',
    r'Dossiers législatifs',
    r'Autorités indépendantes',
    r'EUR-Lex',
    r'Règlements européens',
    r'Domaine de (l\'|la )',
    r'Directives européennes',
    r'Traités et accords',
    r'^(Tous les contenus|Dans tous les champs)$',
    r'Rechercher un mot',
]


class CorpusAuditor:
    """Audits corpus files for quality issues"""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.primary_sources_dir = base_dir / 'Corpus' / '01_sources_text'
        self.fiches_dir = base_dir / 'Corpus' / '02_fiches_ia_ready'

        # Compile noise patterns
        self.noise_patterns = [re.compile(p, re.IGNORECASE) for p in LEGIFRANCE_NOISE_PATTERNS]

        # Article detection patterns
        self.article_patterns = [
            re.compile(r'^###?\s*Article\s+(\d+)', re.IGNORECASE | re.MULTILINE),
            re.compile(r'^###?\s*Article\s+(\d+-\d+)', re.IGNORECASE | re.MULTILINE),
            re.compile(r'^###?\s*Article\s+([A-Z]+\d+-\d+)', re.IGNORECASE | re.MULTILINE),
            re.compile(r'^###?\s*Art\.\s+\d+', re.IGNORECASE | re.MULTILINE),
        ]

    def detect_noise_lines(self, content: str) -> List[Tuple[int, str, str]]:
        """Returns (line_number, line_content, matched_pattern) for noise lines"""
        lines = content.split('\n')
        noise_lines = []

        for line_num, line in enumerate(lines, start=1):
            line_stripped = line.strip()
            if not line_stripped:
                continue

            for pattern in self.noise_patterns:
                if pattern.search(line_stripped):
                    noise_lines.append((line_num, line_stripped[:80], pattern.pattern))
                    break

        return noise_lines

    def detect_ultra_long_lines(self, content: str, threshold: int = 1000) -> List[Tuple[int, int]]:
        """Returns (line_number, char_count) for lines exceeding threshold"""
        lines = content.split('\n')
        long_lines = []

        for line_num, line in enumerate(lines, start=1):
            if len(line) > threshold:
                long_lines.append((line_num, len(line)))

        return long_lines

    def detect_articles(self, content: str) -> List[str]:
        """Detects article IDs in content"""
        articles = []
        for pattern in self.article_patterns:
            matches = pattern.findall(content)
            articles.extend(matches)
        return list(set(articles))

    def extract_consolidation_date(self, content: str) -> str:
        """Extracts consolidation date if present"""
        # Check first 200 lines for date
        lines = content.split('\n')[:200]
        header = '\n'.join(lines)

        date_patterns = [
            r'Version en vigueur au (\d{1,2})\s+(\w+)\s+(\d{4})',
            r'Dernière mise à jour.*?(\d{1,2})\s+(\w+)\s+(\d{4})',
            r'Texte Consolidé[_\s]+(\d{4})',
        ]

        for pattern in date_patterns:
            match = re.search(pattern, header, re.IGNORECASE)
            if match:
                return match.group(0)
        return None

    def extract_url_source(self, content: str) -> str:
        """Extracts Legifrance URL if present"""
        url_match = re.search(r'(https?://[^\s]+legifrance[^\s]+)', content)
        return url_match.group(1) if url_match else None

    def audit_primary_source(self, file_path: Path) -> Dict:
        """Audits a primary source file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        noise_lines = self.detect_noise_lines(content)
        long_lines = self.detect_ultra_long_lines(content)
        articles = self.detect_articles(content)
        consolidation_date = self.extract_consolidation_date(content)
        url_source = self.extract_url_source(content)

        total_lines = len(content.split('\n'))
        file_size_kb = file_path.stat().st_size / 1024

        return {
            'file': file_path.name,
            'path': str(file_path.relative_to(self.base_dir)),
            'size_kb': round(file_size_kb, 2),
            'total_lines': total_lines,
            'noise_lines_count': len(noise_lines),
            'noise_line_numbers': [n[0] for n in noise_lines],
            'noise_lines_sample': noise_lines[:5],  # First 5 for report
            'ultra_long_lines_count': len(long_lines),
            'ultra_long_lines': long_lines,
            'articles_found': len(articles),
            'articles_sample': articles[:10],
            'has_consolidation_date': bool(consolidation_date),
            'consolidation_date': consolidation_date,
            'has_url_source': bool(url_source),
            'url_source': url_source,
            'issues': []
        }

    def audit_fiche(self, file_path: Path) -> Dict:
        """Audits a fiche file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for proof section
        has_proof = bool(re.search(r'##\s*Preuves?\s+[àa]\s+apporter', content, re.IGNORECASE))

        # Check for jurisprudence
        has_jurisprudence = bool(re.search(r'##\s*Jurisprudence', content, re.IGNORECASE))

        # Check for key sections
        has_conditions = bool(re.search(r'##\s*Conditions?\s+d.application', content, re.IGNORECASE))
        has_exceptions = bool(re.search(r'##\s*Exceptions?', content, re.IGNORECASE))
        has_erreurs = bool(re.search(r'##\s*Erreurs?\s+fréquentes?', content, re.IGNORECASE))

        file_size_kb = file_path.stat().st_size / 1024

        return {
            'file': file_path.name,
            'path': str(file_path.relative_to(self.base_dir)),
            'size_kb': round(file_size_kb, 2),
            'has_proof_section': has_proof,
            'has_jurisprudence': has_jurisprudence,
            'has_conditions': has_conditions,
            'has_exceptions': has_exceptions,
            'has_erreurs': has_erreurs,
            'missing_sections': []
        }

    def audit_corpus(self) -> Dict:
        """Audits entire corpus"""
        results = {
            'primary_sources': [],
            'fiches': [],
            'statistics': {}
        }

        # Audit primary sources
        print("Auditing primary sources...")
        primary_files = sorted(self.primary_sources_dir.glob('**/*.md'))
        for file_path in primary_files:
            print(f"  Auditing: {file_path.name}")
            audit = self.audit_primary_source(file_path)

            # Flag issues
            if audit['noise_lines_count'] > 50:
                audit['issues'].append('high_noise')
            if audit['ultra_long_lines_count'] > 0:
                audit['issues'].append('ultra_long_lines')
            if audit['articles_found'] == 0:
                audit['issues'].append('no_articles_detected')
            if not audit['has_consolidation_date']:
                audit['issues'].append('missing_date')
            if not audit['has_url_source']:
                audit['issues'].append('missing_url')

            results['primary_sources'].append(audit)

        # Audit fiches
        print("\nAuditing fiches...")
        fiche_files = sorted(self.fiches_dir.glob('**/*.md'))
        for file_path in fiche_files:
            print(f"  Auditing: {file_path.name}")
            audit = self.audit_fiche(file_path)

            # Flag missing sections
            if not audit['has_proof_section']:
                audit['missing_sections'].append('proof')
            if not audit['has_conditions']:
                audit['missing_sections'].append('conditions')
            if not audit['has_exceptions']:
                audit['missing_sections'].append('exceptions')

            results['fiches'].append(audit)

        # Calculate statistics
        results['statistics'] = self._calculate_statistics(results)

        return results

    def _calculate_statistics(self, results: Dict) -> Dict:
        """Calculates summary statistics"""
        primary = results['primary_sources']
        fiches = results['fiches']

        total_noise_lines = sum(s['noise_lines_count'] for s in primary)
        total_long_lines = sum(s['ultra_long_lines_count'] for s in primary)

        files_with_issues = len([s for s in primary if s['issues']])
        fiches_missing_proof = len([f for f in fiches if not f['has_proof_section']])

        return {
            'primary_sources_count': len(primary),
            'fiches_count': len(fiches),
            'total_noise_lines': total_noise_lines,
            'total_ultra_long_lines': total_long_lines,
            'files_with_high_noise': len([s for s in primary if 'high_noise' in s['issues']]),
            'files_with_ultra_long_lines': len([s for s in primary if 'ultra_long_lines' in s['issues']]),
            'files_missing_dates': len([s for s in primary if not s['has_consolidation_date']]),
            'files_missing_urls': len([s for s in primary if not s['has_url_source']]),
            'fiches_missing_proof': fiches_missing_proof,
            'files_with_issues': files_with_issues,
        }

    def generate_markdown_report(self, results: Dict) -> str:
        """Generates human-readable markdown report"""
        stats = results['statistics']

        report = f"""# Corpus Audit Report

Generated: {Path(__file__).name}

## Executive Summary

**Critical Issues Found:**
- 🔴 **{stats['total_noise_lines']} noise lines** detected across {stats['files_with_high_noise']} files
- 🔴 **{stats['total_ultra_long_lines']} ultra-long lines** (>1000 chars) in {stats['files_with_ultra_long_lines']} files
- ⚠️ **{stats['files_missing_dates']} files** missing consolidation dates
- ⚠️ **{stats['files_missing_urls']} files** missing URL sources
- ⚠️ **{stats['fiches_missing_proof']} fiches** missing proof sections

**Files Analyzed:**
- Primary sources: {stats['primary_sources_count']}
- Fiches: {stats['fiches_count']}

---

## Primary Sources Analysis

### Issues by File

| File | Size (KB) | Noise Lines | Long Lines | Articles | Date | URL | Issues |
|------|-----------|-------------|------------|----------|------|-----|--------|
"""

        for source in results['primary_sources']:
            issues_str = ', '.join(source['issues']) if source['issues'] else '✓'
            date_mark = '✓' if source['has_consolidation_date'] else '✗'
            url_mark = '✓' if source['has_url_source'] else '✗'

            report += f"| {source['file'][:30]} | {source['size_kb']} | {source['noise_lines_count']} | {source['ultra_long_lines_count']} | {source['articles_found']} | {date_mark} | {url_mark} | {issues_str} |\n"

        report += f"""

### Noise Lines Distribution

Top noise line numbers (typical Legifrance export patterns):
"""

        for source in results['primary_sources'][:3]:
            if source['noise_lines_count'] > 0:
                report += f"\n**{source['file']}**: Lines {source['noise_line_numbers'][:10]}\n"
                report += "Sample noise lines:\n"
                for line_num, content, pattern in source['noise_lines_sample']:
                    report += f"- Line {line_num}: `{content[:60]}...`\n"

        report += """

### Ultra-Long Lines

Files with lines exceeding 1000 characters:
"""

        for source in results['primary_sources']:
            if source['ultra_long_lines_count'] > 0:
                report += f"\n**{source['file']}**:\n"
                for line_num, char_count in source['ultra_long_lines'][:5]:
                    report += f"- Line {line_num}: {char_count:,} characters\n"

        report += f"""

---

## Fiches Analysis

### Missing Proof Sections

**{stats['fiches_missing_proof']} fiches** lack generic proof templates:

"""

        fiches_no_proof = [f for f in results['fiches'] if not f['has_proof_section']]
        for fiche in fiches_no_proof[:10]:
            report += f"- {fiche['file']}\n"

        if len(fiches_no_proof) > 10:
            report += f"- ... and {len(fiches_no_proof) - 10} more\n"

        report += """

---

## Recommendations

### Stage 2: Clean Primary Sources
1. Remove ~1,200 noise lines (lines 1-140 typically)
2. Normalize ~150 ultra-long lines (split at sentence boundaries)
3. Format ~400 articles as markdown headers (`### Article X`)
4. Extract and preserve consolidation dates
5. Extract and preserve URL sources

### Stage 3: Chunk with Enhanced Metadata
1. Use cleaned files for chunking
2. Extract article IDs with enhanced patterns (L-codes, R-codes)
3. Map consolidation dates to `version_date`
4. Store URL sources (schema extension or temp mapping)

### Stage 4: Enrich Fiches
1. Add generic proof templates to ~80 fiches
2. Do NOT invent specific legal requirements
3. Use generic CPC Article 9 template

---

## Next Steps

```bash
# Run Stage 2: Clean primary sources
python backend/tools/corpus_clean_primary.py

# Verify cleaning
cat backend/reports/cleaning_log.md
```
"""

        return report


def main():
    """Main execution"""
    base_dir = Path(__file__).parent.parent.parent
    output_dir = base_dir / 'backend' / 'reports'
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("STAGE 1: CORPUS AUDIT")
    print("=" * 80)
    print()

    auditor = CorpusAuditor(base_dir)
    results = auditor.audit_corpus()

    # Save JSON
    json_path = output_dir / 'corpus_audit.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] JSON report saved: {json_path}")

    # Save markdown
    md_path = output_dir / 'corpus_audit.md'
    report = auditor.generate_markdown_report(results)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"[OK] Markdown report saved: {md_path}")

    print("\n" + "=" * 80)
    print("AUDIT COMPLETE")
    print("=" * 80)
    print(f"Found {results['statistics']['total_noise_lines']} noise lines")
    print(f"Found {results['statistics']['total_ultra_long_lines']} ultra-long lines")
    print(f"Fiches missing proof: {results['statistics']['fiches_missing_proof']}")
    print("\nNext step: python backend/tools/corpus_clean_primary.py")


if __name__ == '__main__':
    main()
