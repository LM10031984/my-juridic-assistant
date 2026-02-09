"""
Stage 3: Chunk Primary Sources with Enhanced Metadata
Extends existing chunker with article IDs, dates, and URL sources.

Outputs:
- backend/exports/legal_chunks_primary.jsonl (final export)
- backend/reports/chunk_stats.md (statistics)
- backend/reports/missing_metadata.md (quality report)
"""

import re
import json
import sys
from pathlib import Path
from typing import Dict, List
from datetime import datetime

# Import existing chunker
sys.path.append(str(Path(__file__).parent.parent.parent))
from pipeline.chunker import LegalChunker


# French month mapping
FRENCH_MONTHS = {
    'janvier': '01', 'février': '02', 'fevrier': '02', 'mars': '03',
    'avril': '04', 'mai': '05', 'juin': '06', 'juillet': '07',
    'août': '08', 'aout': '08', 'septembre': '09', 'octobre': '10',
    'novembre': '11', 'décembre': '12', 'decembre': '12'
}


class EnhancedLegalChunker(LegalChunker):
    """Extends LegalChunker with enhanced metadata extraction"""

    def __init__(self, min_words=300, max_words=1200):
        super().__init__(min_words, max_words)

        # Comprehensive article pattern (supports all legal code formats)
        # Matches:
        #   - ### Article 3, ### Article 3-2, ### Art. 3
        #   - ### Article L. 213-2, ### Article L213-2, ### L. 213-2
        #   - ### Article R. 123-4, ### R. 123-4
        #   - Article L313-1 (without ###)
        self.enhanced_article_pattern = re.compile(
            r'###?\s*(?:'
            r'(?:Article|Art\.?)\s+([LRDCP]\.?\s*[\d][\d\-]*)'  # L/R/D/C/P codes
            r'|(?:Article|Art\.?)\s+([\d][\d\-]*[A-Z]?(?:-\d+)?)'  # Regular articles
            r'|([LRDCP]\.)\s+([\d][\d\-]*)'  # Standalone L./R./D./C./P. refs
            r')',
            re.IGNORECASE | re.MULTILINE
        )

        # Date extraction patterns
        self.date_patterns = [
            re.compile(r'Version en vigueur au (\d{1,2})\s+(\w+)\s+(\d{4})', re.IGNORECASE),
            re.compile(r'Dernière mise à jour.*?(\d{1,2})\s+(\w+)\s+(\d{4})', re.IGNORECASE),
            re.compile(r'Consolidation:\s*.*?(\d{1,2})\s+(\w+)\s+(\d{4})', re.IGNORECASE),
        ]

    def parse_french_date(self, day: str, month_name: str, year: str) -> str:
        """Converts French date to ISO format (YYYY-MM-DD)"""
        month_num = FRENCH_MONTHS.get(month_name.lower())
        if month_num:
            return f"{year}-{month_num}-{day.zfill(2)}"
        return None

    def extract_consolidation_date(self, content: str) -> str:
        """Extracts consolidation date from file header"""
        # Check first 100 lines for date
        lines = content.split('\n')[:100]
        header = '\n'.join(lines)

        for pattern in self.date_patterns:
            match = pattern.search(header)
            if match:
                groups = match.groups()
                if len(groups) >= 3:
                    return self.parse_french_date(groups[0], groups[1], groups[2])

        return None

    def extract_url_source(self, content: str) -> str:
        """Extracts Legifrance URL from file header"""
        # Check first 100 lines
        lines = content.split('\n')[:100]
        header = '\n'.join(lines)

        # Look for URL in metadata comment
        url_match = re.search(r'<!--\s*Source:\s*(https?://[^\s]+)', header)
        if url_match:
            return url_match.group(1)

        # Fallback: search for raw URL
        url_match = re.search(r'(https?://[^\s]+legifrance[^\s]+)', header)
        if url_match:
            return url_match.group(1)

        return None

    def extract_source_name(self, file_path: Path) -> str:
        """Extracts clean source name from filename"""
        # Remove .md extension and clean up
        name = file_path.stem

        # Remove common prefixes/suffixes
        name = re.sub(r'_Texte_Consolide_\d{4}', '', name)
        name = re.sub(r'_TexteConsolide_\d{4}', '', name)
        name = re.sub(r'_\d{8}', '', name)  # Remove dates

        # Clean underscores
        name = name.replace('_', ' ')

        return name.strip()

    def extract_article_ids(self, text: str) -> List[str]:
        """Extracts all article IDs from text (comprehensive for all legal codes)"""
        articles = []

        # Find all article headers (using enhanced pattern)
        for match in self.enhanced_article_pattern.finditer(text):
            # The pattern returns multiple groups, find the non-empty one
            article_id = None
            for group in match.groups():
                if group:
                    article_id = group.strip()
                    break
            if article_id:
                articles.append(article_id)

        # Also check for inline article references (e.g., "l'article 23", "l'article L. 213-2")
        inline_pattern = re.compile(
            r"l'article\s+("
            r"[LRDCP]\.?\s*[\d][\d\-]*"  # L/R/D/C/P codes
            r"|[\d][\d\-]*[A-Z]?(?:-\d+)?"  # Regular articles
            r")",
            re.IGNORECASE
        )
        inline_matches = inline_pattern.findall(text)
        articles.extend([match.strip() for match in inline_matches])

        # Deduplicate while preserving order
        seen = set()
        unique_articles = []
        for art in articles:
            # Normalize: remove extra spaces
            art_normalized = re.sub(r'\s+', ' ', art)
            if art_normalized not in seen:
                seen.add(art_normalized)
                unique_articles.append(art_normalized)

        return unique_articles

    def extract_enhanced_metadata(self, file_path: Path, content: str) -> Dict:
        """Extracts enhanced metadata including dates and URLs"""
        # Get base metadata from parent class
        base_metadata = self.extract_metadata_from_path(file_path)

        # Extract enhanced metadata
        consolidation_date = self.extract_consolidation_date(content)
        url_source = self.extract_url_source(content)
        source_name = self.extract_source_name(file_path)

        return {
            **base_metadata,
            'date_consolidation': consolidation_date,
            'url_source': url_source,
            'source_name': source_name,
        }

    def chunk_text_enhanced(self, content: str, file_path: Path) -> List[Dict]:
        """Generates chunks with full enhanced metadata"""
        # Extract enhanced metadata
        enhanced_metadata = self.extract_enhanced_metadata(file_path, content)

        # Use parent class chunking logic
        base_chunks = self.chunk_text(content, enhanced_metadata)

        # Enhance each chunk with article IDs
        for chunk in base_chunks:
            article_ids = self.extract_article_ids(chunk['text'])
            chunk['metadata']['article_ids'] = article_ids
            chunk['metadata']['articles'] = article_ids  # Supabase schema field
            chunk['metadata']['date_consolidation'] = enhanced_metadata['date_consolidation']
            chunk['metadata']['url_source'] = enhanced_metadata['url_source']
            chunk['metadata']['source_name'] = enhanced_metadata['source_name']

        return base_chunks

    def process_file_enhanced(self, file_path: Path) -> List[Dict]:
        """Processes a file with enhanced chunking"""
        print(f"Processing: {file_path.name}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        chunks = self.chunk_text_enhanced(content, file_path)
        print(f"  -> Generated {len(chunks)} chunks")

        return chunks


def export_to_jsonl(chunks: List[Dict], output_path: Path):
    """Exports chunks to JSONL format (Supabase-ready)"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        for chunk in chunks:
            # Map to Supabase schema
            record = {
                'text': chunk['text'],
                'metadata': {
                    'layer': chunk['metadata']['layer'],
                    'type': chunk['metadata']['type'],
                    'domaine': chunk['metadata']['domaine'],
                    'source_file': chunk['metadata']['source_file'],
                    'articles': chunk['metadata'].get('articles', []),
                    'word_count': chunk['metadata']['word_count'],
                    'has_context': chunk['metadata']['has_context'],
                    'version_date': chunk['metadata'].get('date_consolidation'),  # Map here
                    'section_title': chunk['metadata'].get('source_name'),  # Store source name
                    'sous_themes': chunk['metadata'].get('sous_themes', []),
                    'keywords': chunk['metadata'].get('keywords', []),
                    # Note: url_source stored separately for now
                    'url_source': chunk['metadata'].get('url_source'),  # Include for reference
                }
            }
            f.write(json.dumps(record, ensure_ascii=False) + '\n')


def generate_statistics_report(chunks: List[Dict]) -> str:
    """Generates chunk statistics report"""
    total_chunks = len(chunks)
    chunks_with_articles = len([c for c in chunks if c['metadata'].get('articles')])
    chunks_with_dates = len([c for c in chunks if c['metadata'].get('date_consolidation')])
    chunks_with_urls = len([c for c in chunks if c['metadata'].get('url_source')])

    # Word count stats
    word_counts = [c['metadata']['word_count'] for c in chunks]
    avg_words = sum(word_counts) / len(word_counts) if word_counts else 0

    # Article coverage
    total_articles = sum(len(c['metadata'].get('articles', [])) for c in chunks)
    article_coverage_pct = (chunks_with_articles / total_chunks * 100) if total_chunks else 0

    # Metadata coverage
    date_coverage_pct = (chunks_with_dates / total_chunks * 100) if total_chunks else 0
    url_coverage_pct = (chunks_with_urls / total_chunks * 100) if total_chunks else 0

    # By domain
    by_domain = {}
    for c in chunks:
        domain = c['metadata']['domaine']
        if domain not in by_domain:
            by_domain[domain] = {'count': 0, 'articles': 0, 'dates': 0, 'urls': 0}
        by_domain[domain]['count'] += 1
        if c['metadata'].get('articles'):
            by_domain[domain]['articles'] += 1
        if c['metadata'].get('date_consolidation'):
            by_domain[domain]['dates'] += 1
        if c['metadata'].get('url_source'):
            by_domain[domain]['urls'] += 1

    report = f"""# Chunk Statistics Report (Stage 3)

Generated: corpus_chunk_primary.py

## Summary

**Total Chunks:** {total_chunks}

**Quality Metrics:**
- ✅ **{article_coverage_pct:.1f}%** chunks have article references ({chunks_with_articles}/{total_chunks})
- 📅 **{date_coverage_pct:.1f}%** chunks have consolidation dates ({chunks_with_dates}/{total_chunks})
- 🔗 **{url_coverage_pct:.1f}%** chunks have URL sources ({chunks_with_urls}/{total_chunks})

**Content Statistics:**
- Total articles referenced: {total_articles}
- Average words per chunk: {avg_words:.1f}
- Min words: {min(word_counts)}
- Max words: {max(word_counts)}

---

## Domain Breakdown

"""

    for domain, stats in sorted(by_domain.items()):
        art_pct = (stats['articles'] / stats['count'] * 100) if stats['count'] else 0
        date_pct = (stats['dates'] / stats['count'] * 100) if stats['count'] else 0
        url_pct = (stats['urls'] / stats['count'] * 100) if stats['count'] else 0

        report += f"""
### {domain.title()}
- Chunks: {stats['count']}
- Article coverage: {art_pct:.1f}% ({stats['articles']}/{stats['count']})
- Date coverage: {date_pct:.1f}% ({stats['dates']}/{stats['count']})
- URL coverage: {url_pct:.1f}% ({stats['urls']}/{stats['count']})
"""

    report += """

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
"""

    return report


def generate_missing_metadata_report(chunks: List[Dict]) -> str:
    """Generates report of chunks missing metadata"""
    chunks_no_articles = [c for c in chunks if not c['metadata'].get('articles')]
    chunks_no_dates = [c for c in chunks if not c['metadata'].get('date_consolidation')]
    chunks_no_urls = [c for c in chunks if not c['metadata'].get('url_source')]

    report = f"""# Missing Metadata Report (Stage 3)

## Chunks Missing Articles ({len(chunks_no_articles)})

"""

    if chunks_no_articles:
        report += "| Source File | Domain | Word Count |\n"
        report += "|-------------|--------|------------|\n"
        for c in chunks_no_articles[:20]:
            report += f"| {c['metadata']['source_file'][:40]} | {c['metadata']['domaine']} | {c['metadata']['word_count']} |\n"
        if len(chunks_no_articles) > 20:
            report += f"| ... and {len(chunks_no_articles) - 20} more |\n"
    else:
        report += "✅ All chunks have article references!\n"

    report += f"""

---

## Chunks Missing Consolidation Dates ({len(chunks_no_dates)})

"""

    if chunks_no_dates:
        report += "| Source File | Domain |\n"
        report += "|-------------|--------|\n"
        for c in chunks_no_dates[:20]:
            report += f"| {c['metadata']['source_file'][:40]} | {c['metadata']['domaine']} |\n"
        if len(chunks_no_dates) > 20:
            report += f"| ... and {len(chunks_no_dates) - 20} more |\n"
    else:
        report += "✅ All chunks have consolidation dates!\n"

    report += f"""

---

## Chunks Missing URL Sources ({len(chunks_no_urls)})

"""

    if chunks_no_urls:
        report += "| Source File | Domain |\n"
        report += "|-------------|--------|\n"
        for c in chunks_no_urls[:20]:
            report += f"| {c['metadata']['source_file'][:40]} | {c['metadata']['domaine']} |\n"
        if len(chunks_no_urls) > 20:
            report += f"| ... and {len(chunks_no_urls) - 20} more |\n"
    else:
        report += "✅ All chunks have URL sources!\n"

    report += """

---

## Recommendations

- **Missing articles**: Verify file contains article headers (### Article X)
- **Missing dates**: Manually add consolidation dates to file headers
- **Missing URLs**: Add Legifrance URLs in metadata comments if available
"""

    return report


def main():
    """Main execution"""
    base_dir = Path(__file__).parent.parent.parent
    cleaned_dir = base_dir / 'Corpus' / 'clean' / 'primary_cleaned'
    output_dir = base_dir / 'backend' / 'exports'
    reports_dir = base_dir / 'backend' / 'reports'

    if not cleaned_dir.exists():
        print("ERROR: Cleaned primary sources not found. Run Stage 2 first:")
        print("  python backend/tools/corpus_clean_primary.py")
        return

    print("=" * 80)
    print("STAGE 3: CHUNK PRIMARY SOURCES WITH ENHANCED METADATA")
    print("=" * 80)
    print()

    # Initialize enhanced chunker
    chunker = EnhancedLegalChunker(min_words=300, max_words=1200)

    # Process all cleaned files
    all_chunks = []
    cleaned_files = sorted(cleaned_dir.glob('**/*.md'))

    print(f"Found {len(cleaned_files)} cleaned files\n")

    for file_path in cleaned_files:
        chunks = chunker.process_file_enhanced(file_path)
        all_chunks.extend(chunks)

    print(f"\n[OK] Generated {len(all_chunks)} total chunks")

    # Export to JSONL
    jsonl_path = output_dir / 'legal_chunks_primary.jsonl'
    export_to_jsonl(all_chunks, jsonl_path)
    print(f"[OK] Exported to: {jsonl_path}")

    # Generate statistics report
    stats_report = generate_statistics_report(all_chunks)
    stats_path = reports_dir / 'chunk_stats.md'
    with open(stats_path, 'w', encoding='utf-8') as f:
        f.write(stats_report)
    print(f"[OK] Statistics saved: {stats_path}")

    # Generate missing metadata report
    missing_report = generate_missing_metadata_report(all_chunks)
    missing_path = reports_dir / 'missing_metadata.md'
    with open(missing_path, 'w', encoding='utf-8') as f:
        f.write(missing_report)
    print(f"[OK] Missing metadata report: {missing_path}")

    print("\n" + "=" * 80)
    print("CHUNKING COMPLETE")
    print("=" * 80)
    print(f"Total chunks: {len(all_chunks)}")

    chunks_with_articles = len([c for c in all_chunks if c['metadata'].get('articles')])
    article_pct = (chunks_with_articles / len(all_chunks) * 100) if all_chunks else 0
    print(f"Article coverage: {article_pct:.1f}% ({chunks_with_articles}/{len(all_chunks)})")

    print("\nNext step: python backend/tools/corpus_validate_export.py")


if __name__ == '__main__':
    main()
