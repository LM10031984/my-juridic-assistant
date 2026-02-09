"""
Fix 16 Error Fiches - Manual Correction Script
Corrects fiches that were populated with articles from wrong source texts.

Strategy:
- Map each fiche to its expected source texts based on fiche name + domain
- Re-extract articles from fiche content
- Find chunks ONLY from expected sources
- Regenerate BASE JURIDIQUE + EXTRAITS sections
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict


class FicheFixer:
    """Fixes fiches with wrong source attributions"""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.fiches_dir = base_dir / 'Corpus' / 'clean' / 'fiches_updated'
        self.jsonl_path = base_dir / 'backend' / 'exports' / 'legal_chunks_primary.jsonl'

        # Article pattern
        self.article_pattern = re.compile(
            r'(?:Article|Art\.?)\s+('
            r'[LRDCP]\.?\s*[\d][\d\-]*'
            r'|[\d][\d\-]*[A-Z]?(?:-\d+)?'
            r')',
            re.IGNORECASE
        )

        # Source mapping rules based on fiche name patterns
        self.source_mapping = {
            # Copropriété
            'Charges_Repartition': ['loi_1965', 'decret_1967'],
            'decret_1967': ['decret_1967'],
            'loi_10_juillet_1965': ['loi_1965'],

            # Location
            'Loi_1989': ['loi_1989'],
            'CCH_DPE': ['cch_'],
            'Decence_Energetique': ['decence', 'cch_', 'loi_climat'],
            'Passoires_Energetiques': ['loi_climat', 'cch_', 'decence'],

            # Diagnostics
            'DPE': ['cch_', 'loi_climat', 'decence'],

            # Pro immo
            'Loi Hoguet': ['loi_hoguet', 'hoguet'],
            'Loi_Hoguet': ['loi_hoguet', 'hoguet'],
            'DECRET_1972': ['decret_1972'],
            'Décret 20 juillet 1972': ['decret_1972'],
            'Mandat': ['code_civil'],

            # Transaction
            'transaction': ['code_civil', 'code_conso'],
            'Vices_Caches': ['code_civil'],
        }

        # Load all chunks indexed by (normalized_article, source_file)
        self.chunks_by_article_source: Dict[tuple, List[Dict]] = defaultdict(list)
        self.all_chunks: List[Dict] = []

    def normalize_article_id(self, article_id: str) -> str:
        """Normalizes article ID"""
        normalized = re.sub(r'\s+', ' ', article_id.strip())
        normalized = re.sub(r'([LRDCP])\.(\d)', r'\1. \2', normalized)
        normalized = re.sub(r'([LRDCP])\s+\.', r'\1.', normalized)
        return normalized.lower()

    def load_chunks_index(self):
        """Loads chunks with source-aware indexing"""
        print("Loading chunks from JSONL...")

        with open(self.jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    chunk = json.loads(line)
                    self.all_chunks.append(chunk)

                    source_file = chunk.get('metadata', {}).get('source_file', '')
                    articles = chunk.get('metadata', {}).get('articles', [])

                    # Index by (article_id, source_file)
                    for article_id in articles:
                        normalized = self.normalize_article_id(str(article_id))
                        key = (normalized, source_file)
                        self.chunks_by_article_source[key].append(chunk)

                except json.JSONDecodeError:
                    continue

        print(f"  Loaded {len(self.all_chunks)} chunks")
        print(f"  Indexed {len(self.chunks_by_article_source)} (article, source) pairs")

    def get_expected_sources(self, fiche_name: str, domain: str) -> List[str]:
        """Returns expected source file patterns for a fiche"""
        # Check specific name patterns first
        for pattern, sources in self.source_mapping.items():
            if pattern.lower() in fiche_name.lower():
                return sources

        # Fallback to domain defaults
        domain_defaults = {
            'copropriete': ['loi_1965', 'decret_1967'],
            'location': ['loi_1989', 'decret_charges', 'decret_decence', 'cch_'],
            'diagnostics': ['cch_', 'loi_climat', 'decence'],
            'pro_immo': ['loi_hoguet', 'decret_1972', 'code_civil'],
            'transaction': ['code_civil', 'code_conso', 'cch_'],
        }

        return domain_defaults.get(domain, [])

    def source_matches_expected(self, source_file: str, expected_patterns: List[str]) -> bool:
        """Checks if source file matches any expected pattern"""
        source_lower = source_file.lower()
        return any(pattern.lower() in source_lower for pattern in expected_patterns)

    def extract_articles_from_fiche(self, content: str) -> List[str]:
        """Extracts article IDs from fiche main content"""
        # Extract main content (before BASE JURIDIQUE)
        base_match = re.search(r'---\s*##?\s*BASE JURIDIQUE', content, re.IGNORECASE)
        if base_match:
            main_content = content[:base_match.start()]
        else:
            main_content = content

        # Extract articles
        articles = []
        for match in self.article_pattern.finditer(main_content):
            article_id = match.group(1).strip()
            normalized = self.normalize_article_id(article_id)
            if normalized not in articles:
                articles.append(normalized)

        return articles

    def find_chunks_for_articles(
        self,
        article_ids: List[str],
        expected_sources: List[str]
    ) -> List[Dict]:
        """Finds chunks for articles, filtering by expected sources"""
        found_chunks = []

        for article_id in article_ids:
            # Search through all source files
            for (indexed_article, source_file), chunks in self.chunks_by_article_source.items():
                if indexed_article == article_id:
                    # Check if source matches expected patterns
                    if self.source_matches_expected(source_file, expected_sources):
                        # Add first matching chunk
                        if chunks and chunks[0] not in found_chunks:
                            found_chunks.append(chunks[0])
                            break

        return found_chunks

    def generate_base_juridique_section(self, chunks: List[Dict], max_chars: int = 2000) -> str:
        """
        Generates BASE JURIDIQUE section

        CRITICAL: Only lists articles that are ACTUALLY VISIBLE in the chunk texts
        (respecting truncation at max_chars) to ensure BASE JURIDIQUE ⊆ EXTRAITS
        """
        if not chunks:
            return """---

## BASE JURIDIQUE

**Références (articles, codes, lois) :**
- [Aucun article trouvé dans les sources attendues]

> **Statut** : needs_human - Vérification manuelle requise
"""

        # Extract articles from VISIBLE chunk texts (respecting truncation)
        articles_found = {}  # normalized -> (original, source)

        for chunk in chunks[:2]:  # Only use top 2 chunks (same as EXTRAITS)
            chunk_text = chunk.get('text', '')
            source_file = chunk.get('metadata', {}).get('source_file', 'unknown')

            # Apply same truncation as EXTRAITS section
            visible_text = chunk_text[:max_chars] if len(chunk_text) > max_chars else chunk_text

            # Only extract articles from visible text
            for match in self.article_pattern.finditer(visible_text):
                article_id = match.group(1).strip()
                normalized = self.normalize_article_id(article_id)

                if normalized not in articles_found:
                    articles_found[normalized] = (article_id, source_file)

        if not articles_found:
            return """---

## BASE JURIDIQUE

**Références (articles, codes, lois) :**
- [Aucun article identifié dans les extraits]

> **Statut** : needs_human - Vérification manuelle requise
"""

        # Build references
        references = []
        for normalized, (original, source) in sorted(articles_found.items()):
            references.append(f"- Article {original} (source: {source})")

        section = f"""---

## BASE JURIDIQUE

**Références (articles, codes, lois) :**
{chr(10).join(references)}

> Ces références ont été extraites automatiquement depuis les textes primaires indexés.
"""
        return section

    def generate_extraits_section(self, chunks: List[Dict], max_chars: int = 2000) -> str:
        """Generates EXTRAITS section"""
        if not chunks:
            return """
---

## EXTRAITS (copier-coller exact depuis textes primaires)

**Extrait 1 :**
```
[Aucun extrait disponible]
```

> **Statut** : needs_human - Vérification manuelle requise
"""

        extraits = []
        for i, chunk in enumerate(chunks[:2]):
            text = chunk.get('text', '')
            articles = chunk.get('metadata', {}).get('articles', [])
            source_file = chunk.get('metadata', {}).get('source_file', 'unknown')

            # Truncate if needed
            if len(text) > max_chars:
                text = text[:max_chars] + "\n[...tronqué...]"

            article_str = ", ".join([f"Article {a}" for a in articles]) if articles else "N/A"

            extraits.append(f"""**Extrait {i + 1} :** ({article_str} - {source_file})
```
{text}
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

    def fix_fiche(self, file_path: Path) -> Dict:
        """Fixes a single fiche"""
        print(f"\n[FIX] {file_path.name}")

        # Read fiche
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove ALL existing BASE JURIDIQUE sections (both manual and auto-generated)
        # Split by the first occurrence of BASE JURIDIQUE section
        parts = re.split(r'##?\s*BASE JURIDIQUE', content, maxsplit=1, flags=re.IGNORECASE)

        if len(parts) > 1:
            # Take content before first BASE JURIDIQUE
            main_content = parts[0].rstrip()

            # Remove trailing separator if present
            main_content = re.sub(r'\n---\s*$', '', main_content)
        else:
            main_content = content

        # Get expected sources
        domain = file_path.parent.name
        expected_sources = self.get_expected_sources(file_path.name, domain)
        print(f"  Expected sources: {expected_sources}")

        # Extract articles
        articles = self.extract_articles_from_fiche(main_content)
        print(f"  Detected {len(articles)} articles")

        if not articles:
            print("  [SKIP] No articles detected")
            return {'status': 'skipped', 'reason': 'no_articles'}

        # Find chunks from expected sources
        found_chunks = self.find_chunks_for_articles(articles, expected_sources)
        print(f"  Found {len(found_chunks)} matching chunks from expected sources")

        if not found_chunks:
            print("  [SKIP] No chunks found in expected sources")
            return {'status': 'skipped', 'reason': 'no_chunks_in_expected_sources'}

        # Generate sections (use same max_chars to ensure consistency)
        # Increased to 2000 to capture more articles
        max_chars = 2000
        base_section = self.generate_base_juridique_section(found_chunks, max_chars=max_chars)
        extraits_section = self.generate_extraits_section(found_chunks, max_chars=max_chars)

        # Assemble
        updated_content = main_content + "\n" + base_section + extraits_section
        updated_content += f"""

---

> **Note de correction** : {len(found_chunks)}/{len(articles)} articles
> trouvés dans les sources attendues. Méthode: correction manuelle avec filtrage par source.
"""

        # Write
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        print(f"  [OK] Fixed and saved")

        return {
            'status': 'fixed',
            'articles_detected': len(articles),
            'chunks_found': len(found_chunks),
            'expected_sources': expected_sources,
        }

    def fix_all_error_fiches(self):
        """Fixes all error fiches (original 16 + new 9)"""
        error_fiches = [
            # Original 16
            'copropriete/Fiche_IA_READY_Charges_Repartition.md',
            'copropriete/fiche_IA_ready_decret_1967.md',
            'copropriete/Fiche_IA_readyloi_10_juillet_1965.md',
            'diagnostics/Fiche_IA_READY_DPE_04_Erreur_Recours.md',
            'diagnostics/Fiche_IA_READY_DPE_05_Travaux_Renovation.md',
            'location/Fiche_IA_READY_CCH_DPE_PerformanceEnergetique.md',
            'location/Fiche_IA_READY_Decence_Energetique.md',
            'location/Fiche_IA_READY_Loi_1989_RapportsLocatifs_20260206.md',
            'location/Fiche_IA_READY_Passoires_Energetiques_Interdiction.md',
            'pro_immo/FICHE IA-READY — Loi Hoguet.md',
            'pro_immo/FICHE IA_READY_DECRET_1972.md',
            'pro_immo/Fiche_IA_READY_Mandat_Exclusif_Vente_Directe.md',
            'transaction/FICHE IA-READY — Décret 20 juillet 1972.md',
            'transaction/fiche_IA_ready_transaction.md',
            'transaction/Fiche_IA_READY_Vices_Caches_Delais.md',
            'transaction/Fiche_IA_READY_Vices_Caches_Types.md',
            # Additional 9 with remaining errors
            'location/Fiche_IA_READY_Colocation_Bail_Unique_vs_Individuel.md',
            'location/Fiche_IA_READY_Colocation_Cas_Pratiques.md',
            'location/Fiche_IA_READY_Colocation_Clause_Solidarite.md',
            'location/Fiche_IA_READY_Colocation_Depart_Colocataire.md',
        ]

        results = []
        for fiche_rel_path in error_fiches:
            file_path = self.fiches_dir / fiche_rel_path

            if not file_path.exists():
                # Try glob pattern for truncated names
                domain = fiche_rel_path.split('/')[0]
                pattern = fiche_rel_path.split('/')[-1][:30] + '*'
                matches = list((self.fiches_dir / domain).glob(pattern))

                if matches:
                    file_path = matches[0]
                else:
                    print(f"\n[SKIP] File not found: {fiche_rel_path}")
                    continue

            result = self.fix_fiche(file_path)
            result['file'] = file_path.name
            results.append(result)

        return results


def main():
    """Main execution"""
    base_dir = Path(__file__).parent.parent.parent

    print("=" * 80)
    print("FIX 16 ERROR FICHES - Manual Correction with Source Filtering")
    print("=" * 80)

    fixer = FicheFixer(base_dir)
    fixer.load_chunks_index()

    print("\n" + "=" * 80)
    print("FIXING FICHES")
    print("=" * 80)

    results = fixer.fix_all_error_fiches()

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    fixed = sum(1 for r in results if r['status'] == 'fixed')
    skipped = sum(1 for r in results if r['status'] == 'skipped')

    print(f"Fixed: {fixed}")
    print(f"Skipped: {skipped}")
    print(f"Total: {len(results)}")

    print("\n[OK] Re-run validation: python backend/tools/validate_fiches_proof_first.py")


if __name__ == '__main__':
    main()
