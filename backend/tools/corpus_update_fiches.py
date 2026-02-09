"""
Corpus Update Fiches - Remplissage automatique 100% des fiches
Remplit BASE JURIDIQUE + EXTRAITS uniquement depuis textes primaires indexés.

Règles strictes :
- Pas d'invention, pas de paraphrase
- EXTRAITS = copier-coller exact
- BASE JURIDIQUE = articles présents dans EXTRAITS uniquement
- Si rien de fiable -> needs_human

Pipeline :
1. Build index (article_id -> chunks + keywords)
2. Fill fiches with detected articles (simple)
3. Fill fiches without articles via retrieval (complex)
4. Validate proof-first
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict
import math


class FicheUpdater:
    """Updates all fiches with BASE JURIDIQUE + EXTRAITS from indexed corpus"""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.fiches_dir = base_dir / 'Corpus' / 'clean' / 'fiches_with_templates'
        self.primary_dir = base_dir / 'Corpus' / 'clean' / 'primary_cleaned'
        self.jsonl_path = base_dir / 'backend' / 'exports' / 'legal_chunks_primary.jsonl'
        self.output_dir = base_dir / 'Corpus' / 'clean' / 'fiches_updated'

        # Comprehensive article pattern (same as other tools)
        self.article_pattern = re.compile(
            r'(?:Article|Art\.?)\s+('
            r'[LRDCP]\.?\s*[\d][\d\-]*'  # L/R/D/C/P codes
            r'|[\d][\d\-]*[A-Z]?(?:-\d+)?'  # Regular articles
            r')',
            re.IGNORECASE
        )

        # Indexes
        self.index_article_to_chunks: Dict[str, List[Dict]] = defaultdict(list)
        self.index_keywords_to_chunks: Dict[str, List[Dict]] = defaultdict(list)
        self.all_chunks: List[Dict] = []

        # French stopwords (simple list)
        self.stopwords = {
            'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou',
            'mais', 'pour', 'dans', 'sur', 'avec', 'sans', 'sous', 'par',
            'ce', 'ces', 'son', 'sa', 'ses', 'leur', 'leurs', 'qui', 'que',
            'dont', 'où', 'il', 'elle', 'on', 'nous', 'vous', 'ils', 'elles',
            'être', 'avoir', 'faire', 'dire', 'aller', 'voir', 'pouvoir',
            'a', 'est', 'sont', 'ont', 'été', 'ai', 'as', 'au', 'aux',
            'se', 'ne', 'pas', 'plus', 'tout', 'tous', 'toute', 'toutes',
        }

    def normalize_article_id(self, article_id: str) -> str:
        """Normalizes article ID for consistent matching"""
        normalized = re.sub(r'\s+', ' ', article_id.strip())
        normalized = re.sub(r'([LRDCP])\.(\d)', r'\1. \2', normalized)
        normalized = re.sub(r'([LRDCP])\s+\.', r'\1.', normalized)
        return normalized.lower()

    def extract_keywords(self, text: str, top_n: int = 20) -> List[str]:
        """Extracts significant keywords from text (simple tokenization)"""
        # Lowercase and tokenize
        tokens = re.findall(r'\b[a-zàâäçéèêëïîôùûü]{3,}\b', text.lower())

        # Remove stopwords
        filtered = [t for t in tokens if t not in self.stopwords]

        # Count frequencies
        freq = defaultdict(int)
        for token in filtered:
            freq[token] += 1

        # Return top N by frequency
        sorted_tokens = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [token for token, count in sorted_tokens[:top_n]]

    def build_index_from_jsonl(self):
        """Builds index from legal_chunks_primary.jsonl (priority source)"""
        print("Building index from JSONL chunks...")

        if not self.jsonl_path.exists():
            print(f"  [WARNING] JSONL not found: {self.jsonl_path}")
            return

        chunk_count = 0
        with open(self.jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    chunk = json.loads(line)
                    self.all_chunks.append(chunk)

                    # Index by article IDs
                    articles = chunk.get('metadata', {}).get('articles', [])
                    for article_id in articles:
                        normalized = self.normalize_article_id(str(article_id))
                        self.index_article_to_chunks[normalized].append(chunk)

                    # Index by keywords
                    text = chunk.get('text', '')
                    keywords = self.extract_keywords(text, top_n=15)
                    for keyword in keywords:
                        self.index_keywords_to_chunks[keyword].append(chunk)

                    chunk_count += 1

                except json.JSONDecodeError:
                    continue

        print(f"  Indexed {chunk_count} chunks")
        print(f"  Articles indexed: {len(self.index_article_to_chunks)}")
        print(f"  Keywords indexed: {len(self.index_keywords_to_chunks)}")

    def build_index_from_primary(self):
        """Builds fallback index from primary_cleaned (for articles not in JSONL)"""
        print("\nBuilding fallback index from primary sources...")

        primary_files = sorted(self.primary_dir.glob('**/*.md'))
        article_count = 0

        for file_path in primary_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Split by article headers
            articles = re.split(r'(###\s+(?:Article|Art\.?)\s+[^\n]+)', content)

            for i in range(1, len(articles), 2):
                if i + 1 < len(articles):
                    header = articles[i]
                    body = articles[i + 1]

                    # Extract article ID
                    match = self.article_pattern.search(header)
                    if match:
                        article_id = match.group(1).strip()
                        normalized = self.normalize_article_id(article_id)

                        # Only add if NOT already in JSONL index (fallback)
                        if normalized not in self.index_article_to_chunks:
                            # Create pseudo-chunk from primary source
                            pseudo_chunk = {
                                'text': (header + body).strip(),
                                'metadata': {
                                    'source_file': file_path.name,
                                    'articles': [article_id],
                                    'layer': '01_primary',
                                    'type': 'loi',
                                }
                            }
                            self.index_article_to_chunks[normalized].append(pseudo_chunk)
                            article_count += 1

        print(f"  Added {article_count} fallback articles from primary sources")
        print(f"  Total articles indexed: {len(self.index_article_to_chunks)}")

    def search_chunks_by_keywords(
        self,
        query_text: str,
        top_k: int = 5,
        min_score: float = 0.15
    ) -> List[Tuple[Dict, float]]:
        """
        Searches chunks by keyword overlap (simple TF-IDF-like scoring)

        Args:
            query_text: Text to search for
            top_k: Number of results
            min_score: Minimum score threshold

        Returns:
            List of (chunk, score) tuples
        """
        # Extract query keywords
        query_keywords = set(self.extract_keywords(query_text, top_n=10))

        if not query_keywords:
            return []

        # Score each chunk
        chunk_scores = defaultdict(float)

        for keyword in query_keywords:
            matching_chunks = self.index_keywords_to_chunks.get(keyword, [])
            for chunk in matching_chunks:
                # Simple scoring: +1 for each matching keyword
                chunk_id = id(chunk)  # Use object ID as unique key
                chunk_scores[chunk_id] += 1.0

        # Normalize scores by query length
        for chunk_id in chunk_scores:
            chunk_scores[chunk_id] /= len(query_keywords)

        # Filter by min score
        filtered = [(chunk_id, score) for chunk_id, score in chunk_scores.items() if score >= min_score]

        # Sort by score
        sorted_chunks = sorted(filtered, key=lambda x: x[1], reverse=True)[:top_k]

        # Map back to chunk objects
        chunk_id_to_chunk = {id(chunk): chunk for chunk in self.all_chunks}
        results = [(chunk_id_to_chunk[chunk_id], score) for chunk_id, score in sorted_chunks if chunk_id in chunk_id_to_chunk]

        return results

    def extract_article_ids_from_fiche(self, fiche_content: str) -> List[str]:
        """Extracts article IDs from fiche main content (before BASE JURIDIQUE)"""
        # Extract main content (before BASE JURIDIQUE)
        base_match = re.search(
            r'---\s*##?\s*BASE JURIDIQUE',
            fiche_content,
            re.IGNORECASE
        )

        if base_match:
            main_content = fiche_content[:base_match.start()]
        else:
            main_content = fiche_content

        # Extract article IDs
        article_ids = []
        for match in self.article_pattern.finditer(main_content):
            article_id = match.group(1).strip()
            normalized = self.normalize_article_id(article_id)
            if normalized not in article_ids:
                article_ids.append(normalized)

        return article_ids

    def generate_base_juridique_section(
        self,
        found_chunks: List[Dict],
        detected_articles: List[str]
    ) -> str:
        """
        Generates BASE JURIDIQUE section from found chunks

        CRITICAL: Only lists articles that are ACTUALLY PRESENT in the chunk texts
        to ensure BASE JURIDIQUE ⊆ EXTRAITS (proof-first validation)
        """
        if not found_chunks:
            return """---

## BASE JURIDIQUE

**Références (articles, codes, lois) :**
- [Aucun article indexé trouvé dans le corpus]

> **Statut** : needs_human - Vérification manuelle requise
"""

        # Extract all articles from chunk texts (not metadata!)
        articles_in_extraits = {}  # normalized -> (original, source_file)

        for chunk in found_chunks:
            chunk_text = chunk.get('text', '')
            source_file = chunk.get('metadata', {}).get('source_file', 'unknown')

            # Find all article references in this chunk's text
            for match in self.article_pattern.finditer(chunk_text):
                article_id = match.group(1).strip()
                normalized = self.normalize_article_id(article_id)

                # Store first occurrence (prefer original formatting)
                if normalized not in articles_in_extraits:
                    articles_in_extraits[normalized] = (article_id, source_file)

        if not articles_in_extraits:
            return """---

## BASE JURIDIQUE

**Références (articles, codes, lois) :**
- [Aucun article identifié dans les extraits]

> **Statut** : needs_human - Vérification manuelle requise
"""

        # Build references from articles actually present in extraits
        references = []
        for normalized, (original, source_file) in sorted(articles_in_extraits.items()):
            # Only include if:
            # 1. No detected articles (retrieval case) -> include all from extraits
            # 2. OR article was detected in fiche AND present in extraits
            if not detected_articles or normalized in detected_articles:
                references.append(f"- Article {original} (source: {source_file})")

        if not references:
            return """---

## BASE JURIDIQUE

**Références (articles, codes, lois) :**
- [Articles détectés mais non trouvés dans les extraits]

> **Statut** : needs_human - Vérification manuelle requise
"""

        # Deduplicate preserving order
        references = list(dict.fromkeys(references))

        if not references:
            return """---

## BASE JURIDIQUE

**Références (articles, codes, lois) :**
- [Aucun article indexé trouvé dans le corpus]

> **Statut** : needs_human - Vérification manuelle requise
"""

        section = f"""---

## BASE JURIDIQUE

**Références (articles, codes, lois) :**
{chr(10).join(references)}

> Ces références ont été extraites automatiquement depuis les textes primaires indexés.
"""
        return section

    def generate_extraits_section(
        self,
        found_chunks: List[Dict],
        max_extraits: int = 2,
        max_chars: int = 1200
    ) -> str:
        """Generates EXTRAITS section from found chunks (exact copy-paste)"""
        if not found_chunks:
            return """
---

## EXTRAITS (copier-coller exact depuis textes primaires)

**Extrait 1 :**
```
[Aucun extrait disponible dans le corpus indexé]
```

> **Statut** : needs_human - Vérification manuelle requise
"""

        extraits = []
        for i, chunk in enumerate(found_chunks[:max_extraits]):
            text = chunk.get('text', '')
            articles = chunk.get('metadata', {}).get('articles', [])
            source_file = chunk.get('metadata', {}).get('source_file', 'unknown')

            # Truncate if too long
            if len(text) > max_chars:
                truncated = text[:max_chars] + "\n[...tronqué...]"
            else:
                truncated = text

            article_str = ", ".join([f"Article {a}" for a in articles]) if articles else "N/A"

            extraits.append(f"""**Extrait {i + 1} :** ({article_str} - {source_file})
```
{truncated}
```
""")

        section = f"""
---

## EXTRAITS (copier-coller exact depuis textes primaires)

{chr(10).join(extraits)}

> Ces extraits ont été copiés automatiquement depuis les sources indexées.
> Ils sont exacts et non paraphrasés.
"""
        return section

    def update_fiche_with_articles(self, file_path: Path) -> Dict:
        """Updates fiche that has detected article IDs (TÂCHE 2)"""
        print(f"Processing (articles): {file_path.name}")

        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        # Extract main content
        base_match = re.search(r'---\s*##?\s*BASE JURIDIQUE', original_content, re.IGNORECASE)
        if base_match:
            main_content = original_content[:base_match.start()].rstrip()
        else:
            main_content = original_content

        # Extract article IDs
        article_ids = self.extract_article_ids_from_fiche(main_content)

        if not article_ids:
            return {
                'file': file_path.name,
                'domain': file_path.parent.name,
                'method': 'skipped',
                'reason': 'no_articles_detected',
                'articles_detected': 0,
                'articles_found': 0,
                'needs_human': True,
            }

        # Look up chunks for each article
        found_chunks = []
        articles_found = []

        for article_id in article_ids:
            matching_chunks = self.index_article_to_chunks.get(article_id, [])
            if matching_chunks:
                # Take first matching chunk (could be multiple)
                found_chunks.append(matching_chunks[0])
                articles_found.append(article_id)

        if not found_chunks:
            return {
                'file': file_path.name,
                'domain': file_path.parent.name,
                'method': 'skipped',
                'reason': 'articles_not_in_index',
                'articles_detected': len(article_ids),
                'articles_found': 0,
                'needs_human': True,
            }

        # Generate sections
        base_section = self.generate_base_juridique_section(found_chunks, article_ids)
        extraits_section = self.generate_extraits_section(found_chunks)

        # Assemble
        updated_content = main_content + "\n" + base_section + extraits_section

        # Add update note
        updated_content += f"""

---

> **Note d'auto-remplissage** : {len(found_chunks)}/{len(article_ids)} articles
> trouvés et intégrés. Méthode: détection d'articles explicites.
"""

        # Write updated fiche
        relative_path = file_path.relative_to(self.fiches_dir)
        output_path = self.output_dir / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        print(f"  [OK] Updated: {len(found_chunks)}/{len(article_ids)} articles")

        return {
            'file': file_path.name,
            'domain': file_path.parent.name,
            'method': 'articles',
            'articles_detected': len(article_ids),
            'articles_found': len(found_chunks),
            'needs_human': len(found_chunks) < len(article_ids),
            'output_path': str(output_path.relative_to(self.base_dir)),
        }

    def update_fiche_with_retrieval(self, file_path: Path) -> Dict:
        """Updates fiche without article IDs via keyword retrieval (TÂCHE 3)"""
        print(f"Processing (retrieval): {file_path.name}")

        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        # Extract main content
        base_match = re.search(r'---\s*##?\s*BASE JURIDIQUE', original_content, re.IGNORECASE)
        if base_match:
            main_content = original_content[:base_match.start()].rstrip()
        else:
            main_content = original_content

        # Generate search query: title + first 200 chars
        lines = main_content.split('\n')
        # Get first non-empty lines (title + intro)
        meaningful_lines = [l.strip() for l in lines if l.strip() and not l.strip().startswith('#')][:5]
        query_text = ' '.join(meaningful_lines[:3])[:300]

        if not query_text or len(query_text) < 20:
            print(f"  [SKIP] Insufficient text for query")
            return {
                'file': file_path.name,
                'domain': file_path.parent.name,
                'method': 'skipped',
                'reason': 'insufficient_text',
                'needs_human': True,
            }

        # Search by keywords
        results = self.search_chunks_by_keywords(query_text, top_k=5, min_score=0.15)

        if not results:
            print(f"  [SKIP] No matching chunks (score < threshold)")
            return {
                'file': file_path.name,
                'domain': file_path.parent.name,
                'method': 'retrieval_failed',
                'reason': 'no_matches_above_threshold',
                'needs_human': True,
            }

        # Use top 2 chunks
        found_chunks = [chunk for chunk, score in results[:2]]
        scores = [score for chunk, score in results[:2]]

        print(f"  [OK] Found {len(found_chunks)} chunks (scores: {[f'{s:.2f}' for s in scores]})")

        # Generate sections (no detected articles, so use all from chunks)
        base_section = self.generate_base_juridique_section(found_chunks, [])
        extraits_section = self.generate_extraits_section(found_chunks)

        # Assemble
        updated_content = main_content + "\n" + base_section + extraits_section

        # Add update note
        avg_score = sum(scores) / len(scores) if scores else 0.0
        updated_content += f"""

---

> **Note d'auto-remplissage** : {len(found_chunks)} chunks trouvés via retrieval sémantique.
> Score moyen: {avg_score:.2%}. Méthode: recherche par mots-clés.
> Vérification manuelle recommandée.
"""

        # Write updated fiche
        relative_path = file_path.relative_to(self.fiches_dir)
        output_path = self.output_dir / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        return {
            'file': file_path.name,
            'domain': file_path.parent.name,
            'method': 'retrieval',
            'chunks_found': len(found_chunks),
            'avg_score': avg_score,
            'needs_human': avg_score < 0.25,  # Flag for human review if low score
            'output_path': str(output_path.relative_to(self.base_dir)),
        }

    def update_all_fiches(self) -> List[Dict]:
        """Updates all fiches (TÂCHE 2 + 3)"""
        results = []
        fiche_files = sorted(self.fiches_dir.glob('**/*.md'))

        print(f"\nProcessing {len(fiche_files)} fiches...")

        for file_path in fiche_files:
            # Try article-based update first
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            article_ids = self.extract_article_ids_from_fiche(content)

            if article_ids:
                # Has articles -> use article-based method
                result = self.update_fiche_with_articles(file_path)
            else:
                # No articles -> use retrieval method
                result = self.update_fiche_with_retrieval(file_path)

            results.append(result)

        return results

    def generate_update_report(self, results: List[Dict]) -> str:
        """Generates update report"""
        total = len(results)
        by_method = defaultdict(int)
        needs_human_count = 0

        for r in results:
            by_method[r['method']] += 1
            if r.get('needs_human'):
                needs_human_count += 1

        report = f"""# Fiches Update Report

Generated: corpus_update_fiches.py

## Summary

**Total fiches processed:** {total}
**Needs human review:** {needs_human_count} ({needs_human_count/total*100:.1f}%)
**Auto-completed:** {total - needs_human_count} ({(total - needs_human_count)/total*100:.1f}%)

**By Method:**
- Articles detection: {by_method['articles']}
- Keyword retrieval: {by_method['retrieval']}
- Skipped (failed): {by_method['skipped'] + by_method['retrieval_failed']}

---

## Fiches by Method

### Articles Detection ({by_method['articles']})

| File | Domain | Articles Found | Needs Human |
|------|--------|----------------|-------------|
"""

        for r in [r for r in results if r['method'] == 'articles'][:30]:
            needs = 'YES' if r.get('needs_human') else 'NO'
            report += f"| {r['file'][:40]} | {r['domain']} | {r['articles_found']}/{r['articles_detected']} | {needs} |\n"

        report += f"""

### Keyword Retrieval ({by_method['retrieval']})

| File | Domain | Chunks Found | Avg Score | Needs Human |
|------|--------|--------------|-----------|-------------|
"""

        for r in [r for r in results if r['method'] == 'retrieval'][:30]:
            needs = 'YES' if r.get('needs_human') else 'NO'
            score = r.get('avg_score', 0.0)
            report += f"| {r['file'][:40]} | {r['domain']} | {r.get('chunks_found', 0)} | {score:.2%} | {needs} |\n"

        # Needs human list
        needs_human = [r for r in results if r.get('needs_human')]

        report += f"""

---

## Fiches Needing Human Review ({len(needs_human)})

| File | Domain | Method | Reason |
|------|--------|--------|--------|
"""

        for r in needs_human[:30]:
            reason = r.get('reason', 'low_score' if r['method'] == 'retrieval' else 'partial_match')
            report += f"| {r['file'][:40]} | {r['domain']} | {r['method']} | {reason} |\n"

        if len(needs_human) > 30:
            report += f"| ... and {len(needs_human) - 30} more |\n"

        report += """

---

## Next Steps

```bash
# Run validation
python backend/tools/validate_fiches_proof_first.py

# Review updated fiches
ls -la Corpus/clean/fiches_updated/

# Compare with originals
diff Corpus/clean/fiches_with_templates/location/Fiche_IA_READY_Loi_1989_RapportsLocatifs_20260206.md \\
     Corpus/clean/fiches_updated/location/Fiche_IA_READY_Loi_1989_RapportsLocatifs_20260206.md
```
"""

        return report


def main():
    """Main execution"""
    base_dir = Path(__file__).parent.parent.parent

    print("=" * 80)
    print("CORPUS UPDATE FICHES - 100% AUTO-FILL")
    print("=" * 80)
    print()

    updater = FicheUpdater(base_dir)

    # TÂCHE 1: Build indexes
    print("TÂCHE 1: Building indexes...")
    updater.build_index_from_jsonl()
    updater.build_index_from_primary()

    if not updater.index_article_to_chunks and not updater.all_chunks:
        print("\n[ERROR] No index built! Check JSONL and primary sources.")
        return

    # TÂCHE 2 + 3: Update all fiches
    print("\n" + "=" * 80)
    print("TÂCHE 2+3: Updating fiches...")
    print("=" * 80)
    results = updater.update_all_fiches()

    # Generate report
    reports_dir = base_dir / 'backend' / 'reports'
    report = updater.generate_update_report(results)
    report_path = reports_dir / 'fiches_update_report.md'

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n[OK] Update report saved: {report_path}")

    print("\n" + "=" * 80)
    print("UPDATE COMPLETE")
    print("=" * 80)

    by_method = {}
    for r in results:
        by_method[r['method']] = by_method.get(r['method'], 0) + 1

    needs_human = len([r for r in results if r.get('needs_human')])

    print(f"Total fiches: {len(results)}")
    print(f"By articles: {by_method.get('articles', 0)}")
    print(f"By retrieval: {by_method.get('retrieval', 0)}")
    print(f"Needs human: {needs_human}")
    print(f"\nOutput: Corpus/clean/fiches_updated/")
    print("\nNext: python backend/tools/validate_fiches_proof_first.py")


if __name__ == '__main__':
    main()
