"""
Stage 2: Clean Primary Sources
Removes noise, normalizes long lines, formats articles as headers.

Outputs:
- Corpus/clean/primary_cleaned/**/*.md (cleaned files)
- backend/reports/cleaning_log.md (transformation report)
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Tuple


class PrimarySourceCleaner:
    """Cleans primary source legal documents"""

    def __init__(self, base_dir: Path, audit_data: Dict):
        self.base_dir = base_dir
        self.audit_data = audit_data
        self.primary_sources_dir = base_dir / 'Corpus' / '01_sources_text'
        self.output_dir = base_dir / 'Corpus' / 'clean' / 'primary_cleaned'

        # Compile noise patterns from Stage 1
        self.noise_patterns = [
            re.compile(r'^Aller au (contenu|menu|recherche)', re.IGNORECASE),
            re.compile(r'Informations de mises à jour', re.IGNORECASE),
            re.compile(r'Gestion des cookies', re.IGNORECASE),
            re.compile(r'République Française', re.IGNORECASE),
            re.compile(r'Accueil Légifrance', re.IGNORECASE),
            re.compile(r'^(Imprimer|Copier le texte)$', re.IGNORECASE),
            re.compile(r'ChronoLégi', re.IGNORECASE),
            re.compile(r'Masquer les articles', re.IGNORECASE),
            re.compile(r'Naviguer dans le sommaire', re.IGNORECASE),
            re.compile(r'Recherche (simple|avancée)', re.IGNORECASE),
            re.compile(r'Effectuer une recherche', re.IGNORECASE),
            re.compile(r'^rechercher$', re.IGNORECASE),
            re.compile(r'valider la recherche', re.IGNORECASE),
            re.compile(r'Voir les modifications', re.IGNORECASE),
            re.compile(r'Version (à la date|en vigueur)', re.IGNORECASE),
            re.compile(r'Constitution du \d+', re.IGNORECASE),
            re.compile(r'Journal officiel', re.IGNORECASE),
            re.compile(r'EUR-Lex', re.IGNORECASE),
            re.compile(r'Domaine de (l\'|la )', re.IGNORECASE),
            re.compile(r'^(Tous les contenus|Dans tous les champs)$', re.IGNORECASE),
            re.compile(r'Replier(Titre|Chapitre)', re.IGNORECASE),
            re.compile(r'^(Versions|Liens relatifs|Informations pratiques)\s*$', re.IGNORECASE),
        ]

        # Article detection patterns (enhanced)
        self.article_pattern = re.compile(
            r'^(Article|Art\.?)\s+([\d\-]+(?:[A-Z])?(?:-\d+)?)',
            re.IGNORECASE
        )

        # Date extraction patterns
        self.date_patterns = [
            re.compile(r'Version en vigueur au (\d{1,2})\s+(\w+)\s+(\d{4})', re.IGNORECASE),
            re.compile(r'Dernière mise à jour.*?(\d{1,2})\s+(\w+)\s+(\d{4})', re.IGNORECASE),
            re.compile(r'Texte Consolidé[_\s]+(\d{4})', re.IGNORECASE),
        ]

    def identify_first_content_line(self, lines: List[str]) -> int:
        """Finds first real legal content after Legifrance noise"""
        for i, line in enumerate(lines):
            line_stripped = line.strip()

            # Skip empty lines
            if not line_stripped:
                continue

            # First Article/Chapitre/Titre usually marks real content
            if re.match(r'^(Article|Chapitre|Titre|Art\.)', line_stripped, re.IGNORECASE):
                return i

            # Or a line longer than 50 chars that's NOT noise
            if len(line_stripped) > 50:
                is_noise = any(pattern.search(line_stripped) for pattern in self.noise_patterns)
                if not is_noise:
                    return i

        # Fallback: assume content starts after line 140 (typical Legifrance export)
        return min(140, len(lines) - 1)

    def remove_noise_lines(self, content: str) -> Tuple[str, int]:
        """Removes Legifrance navigation noise"""
        lines = content.split('\n')

        # Find first content line
        first_content = self.identify_first_content_line(lines)

        # Keep everything from first content onwards
        cleaned_lines = lines[first_content:]

        # Also filter out remaining noise patterns in the content
        final_lines = []
        removed_count = first_content

        for line in cleaned_lines:
            line_stripped = line.strip()

            # Skip noise patterns
            is_noise = any(pattern.search(line_stripped) for pattern in self.noise_patterns)

            # Also skip very short lines that look like UI elements
            if is_noise or (len(line_stripped) < 3 and line_stripped.isdigit()):
                removed_count += 1
                continue

            final_lines.append(line)

        return '\n'.join(final_lines), removed_count

    def normalize_long_lines(self, content: str, max_length: int = 500) -> Tuple[str, int]:
        """Splits ultra-long lines at sentence boundaries"""
        lines = content.split('\n')
        normalized_lines = []
        split_count = 0

        for line in lines:
            if len(line) <= max_length:
                normalized_lines.append(line)
                continue

            # Line is too long - split at sentence boundaries
            # Find sentence endings: '. ', '! ', '? ', '; '
            sentence_endings = ['. ', '! ', '? ', '; ']

            current_chunk = ''
            words = line.split(' ')

            for word in words:
                test_chunk = current_chunk + ' ' + word if current_chunk else word

                if len(test_chunk) > max_length:
                    # Check if current chunk ends with sentence ending
                    if current_chunk.rstrip().endswith(('.', '!', '?', ';')):
                        normalized_lines.append(current_chunk.strip())
                        current_chunk = word
                        split_count += 1
                    else:
                        # Force split even without sentence ending
                        normalized_lines.append(current_chunk.strip())
                        current_chunk = word
                        split_count += 1
                else:
                    current_chunk = test_chunk

            if current_chunk:
                normalized_lines.append(current_chunk.strip())

        return '\n'.join(normalized_lines), split_count

    def format_article_headers(self, content: str) -> Tuple[str, int]:
        """Converts 'Article X' → '### Article X' for markdown parsing"""
        lines = content.split('\n')
        formatted_lines = []
        format_count = 0

        for line in lines:
            line_stripped = line.strip()

            # Check if line starts with Article/Art.
            match = self.article_pattern.match(line_stripped)

            if match and not line_stripped.startswith('#'):
                # Format as markdown header
                formatted_lines.append(f'### {line_stripped}')
                format_count += 1
            else:
                formatted_lines.append(line)

        return '\n'.join(formatted_lines), format_count

    def extract_metadata_header(self, content: str) -> str:
        """Extracts consolidation date and URL to preserve at file start"""
        lines = content.split('\n')[:50]  # Check first 50 lines
        header = '\n'.join(lines)

        metadata_lines = []

        # Extract consolidation date
        for pattern in self.date_patterns:
            match = pattern.search(header)
            if match:
                metadata_lines.append(f"<!-- Consolidation: {match.group(0)} -->")
                break

        # Extract URL source
        url_match = re.search(r'(https?://[^\s]+legifrance[^\s]+)', header)
        if url_match:
            metadata_lines.append(f"<!-- Source: {url_match.group(1)} -->")

        if metadata_lines:
            return '\n'.join(metadata_lines) + '\n\n'
        return ''

    def clean_file(self, file_path: Path) -> Dict:
        """Cleans a single primary source file"""
        print(f"Cleaning: {file_path.name}")

        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        original_lines = len(original_content.split('\n'))

        # Extract metadata to preserve
        metadata_header = self.extract_metadata_header(original_content)

        # Step 1: Remove noise lines
        content, noise_removed = self.remove_noise_lines(original_content)

        # Step 2: Normalize ultra-long lines
        content, lines_split = self.normalize_long_lines(content)

        # Step 3: Format articles as markdown headers
        content, articles_formatted = self.format_article_headers(content)

        # Prepend metadata
        final_content = metadata_header + content

        # Determine output path (preserve domain structure)
        relative_path = file_path.relative_to(self.primary_sources_dir)
        output_path = self.output_dir / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write cleaned file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_content)

        final_lines = len(final_content.split('\n'))

        return {
            'file': file_path.name,
            'domain': relative_path.parts[0] if len(relative_path.parts) > 1 else 'unknown',
            'original_lines': original_lines,
            'final_lines': final_lines,
            'noise_lines_removed': noise_removed,
            'long_lines_split': lines_split,
            'articles_formatted': articles_formatted,
            'output_path': str(output_path.relative_to(self.base_dir)),
        }

    def clean_all_primary_sources(self) -> List[Dict]:
        """Cleans all primary source files"""
        results = []
        primary_files = sorted(self.primary_sources_dir.glob('**/*.md'))

        for file_path in primary_files:
            result = self.clean_file(file_path)
            results.append(result)

        return results

    def generate_cleaning_report(self, results: List[Dict]) -> str:
        """Generates markdown cleaning report"""
        total_noise = sum(r['noise_lines_removed'] for r in results)
        total_splits = sum(r['long_lines_split'] for r in results)
        total_articles = sum(r['articles_formatted'] for r in results)

        report = f"""# Corpus Cleaning Report (Stage 2)

Generated: corpus_clean_primary.py

## Summary

**Transformations Applied:**
- 🧹 **{total_noise} noise lines removed** across {len(results)} files
- ✂️ **{total_splits} ultra-long lines split** at sentence boundaries
- 📑 **{total_articles} articles formatted** as markdown headers (### Article X)

**Output:** All cleaned files saved to `Corpus/clean/primary_cleaned/`

---

## Cleaning Results by File

| File | Domain | Original Lines | Final Lines | Noise Removed | Lines Split | Articles Formatted |
|------|--------|----------------|-------------|---------------|-------------|--------------------|
"""

        for r in results:
            report += f"| {r['file'][:30]} | {r['domain']} | {r['original_lines']} | {r['final_lines']} | {r['noise_lines_removed']} | {r['long_lines_split']} | {r['articles_formatted']} |\n"

        report += f"""

---

## Domain Breakdown

"""

        # Group by domain
        by_domain = {}
        for r in results:
            domain = r['domain']
            if domain not in by_domain:
                by_domain[domain] = {'files': 0, 'noise': 0, 'splits': 0, 'articles': 0}
            by_domain[domain]['files'] += 1
            by_domain[domain]['noise'] += r['noise_lines_removed']
            by_domain[domain]['splits'] += r['long_lines_split']
            by_domain[domain]['articles'] += r['articles_formatted']

        for domain, stats in sorted(by_domain.items()):
            report += f"""
### {domain.title()}
- Files cleaned: {stats['files']}
- Noise lines removed: {stats['noise']}
- Long lines split: {stats['splits']}
- Articles formatted: {stats['articles']}
"""

        report += """

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
"""

        return report


def main():
    """Main execution"""
    base_dir = Path(__file__).parent.parent.parent
    audit_json_path = base_dir / 'backend' / 'reports' / 'corpus_audit.json'

    # Load audit data
    if not audit_json_path.exists():
        print("ERROR: corpus_audit.json not found. Run Stage 1 first:")
        print("  python backend/tools/corpus_audit.py")
        return

    with open(audit_json_path, 'r', encoding='utf-8') as f:
        audit_data = json.load(f)

    print("=" * 80)
    print("STAGE 2: CLEAN PRIMARY SOURCES")
    print("=" * 80)
    print()

    cleaner = PrimarySourceCleaner(base_dir, audit_data)
    results = cleaner.clean_all_primary_sources()

    # Generate report
    report_path = base_dir / 'backend' / 'reports' / 'cleaning_log.md'
    report = cleaner.generate_cleaning_report(results)

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n[OK] Cleaning report saved: {report_path}")

    print("\n" + "=" * 80)
    print("CLEANING COMPLETE")
    print("=" * 80)

    total_noise = sum(r['noise_lines_removed'] for r in results)
    total_splits = sum(r['long_lines_split'] for r in results)
    total_articles = sum(r['articles_formatted'] for r in results)

    print(f"Removed {total_noise} noise lines")
    print(f"Split {total_splits} ultra-long lines")
    print(f"Formatted {total_articles} articles as headers")
    print(f"\nOutput: Corpus/clean/primary_cleaned/")
    print("\nNext step: python backend/tools/corpus_chunk_primary.py")


if __name__ == '__main__':
    main()
