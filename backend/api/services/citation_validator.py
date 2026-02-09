"""
Citation Validator - Garde-fou anti-citation hors corpus

Valide que les articles cités dans la réponse LLM existent dans les chunks récupérés.
Si un article est cité sans être dans le corpus, remplace la section BASE JURIDIQUE.
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Tuple, Set
from datetime import datetime


class CitationValidator:
    """Validates legal citations against retrieved corpus chunks"""

    def __init__(self, base_dir: Path = None):
        if base_dir is None:
            # Default: assume we're in backend/api/services/
            base_dir = Path(__file__).parent.parent.parent.parent

        self.base_dir = base_dir
        self.log_file = base_dir / 'backend' / 'reports' / 'citation_mismatch.log'

        # Create log file if doesn't exist
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_file.exists():
            self.log_file.write_text("", encoding='utf-8')

        # Article pattern (comprehensive, same as corpus tools)
        self.article_pattern = re.compile(
            r'(?:Article|Art\.?)\s+('
            r'[LRDCP]\.?\s*[\d][\d\-]*'  # L/R/D/C/P codes
            r'|[\d][\d\-]*[A-Z]?(?:-\d+)?'  # Regular articles
            r')',
            re.IGNORECASE
        )

    def normalize_article_id(self, article_id: str) -> str:
        """Normalizes article ID for consistent matching"""
        # Remove extra spaces
        normalized = re.sub(r'\s+', ' ', article_id.strip())
        # Normalize letter codes (add space after letter+dot if missing)
        normalized = re.sub(r'([LRDCP])\.(\d)', r'\1. \2', normalized)
        # Remove space before dot
        normalized = re.sub(r'([LRDCP])\s+\.', r'\1.', normalized)
        return normalized.lower()

    def extract_cited_articles_from_response(self, response_text: str) -> List[str]:
        """
        Extracts article references from BASE JURIDIQUE section of response

        Args:
            response_text: Full LLM response text

        Returns:
            List of normalized article IDs cited in response
        """
        # Find BASE JURIDIQUE section
        base_match = re.search(
            r'##?\s*BASE JURIDIQUE.*?(?=##|$)',
            response_text,
            re.DOTALL | re.IGNORECASE
        )

        if not base_match:
            return []

        base_section = base_match.group(0)

        # Extract all article references from BASE JURIDIQUE
        cited_articles = []
        for match in self.article_pattern.finditer(base_section):
            article_id = match.group(1).strip()
            normalized = self.normalize_article_id(article_id)
            if normalized not in cited_articles:
                cited_articles.append(normalized)

        return cited_articles

    def extract_articles_from_chunks(self, chunks: List[Dict]) -> Set[str]:
        """
        Extracts all article IDs from retrieved chunks

        Args:
            chunks: List of chunk dictionaries with 'articles' metadata

        Returns:
            Set of normalized article IDs present in chunks
        """
        chunk_articles = set()

        for chunk in chunks:
            articles = chunk.get('articles', [])
            for article_id in articles:
                normalized = self.normalize_article_id(str(article_id))
                chunk_articles.add(normalized)

        return chunk_articles

    def validate_citations(
        self,
        response_text: str,
        chunks: List[Dict],
        question: str
    ) -> Tuple[bool, str, List[str], List[str]]:
        """
        Validates that cited articles exist in retrieved chunks

        Args:
            response_text: LLM response text
            chunks: Retrieved corpus chunks
            question: Original user question

        Returns:
            Tuple of (is_valid, validated_response, cited_articles, missing_articles)
        """
        # Extract citations from response
        cited_articles = self.extract_cited_articles_from_response(response_text)

        # If no citations, nothing to validate
        if not cited_articles:
            return True, response_text, [], []

        # Extract articles from chunks
        chunk_articles = self.extract_articles_from_chunks(chunks)

        # Find missing articles (cited but not in chunks)
        missing_articles = [art for art in cited_articles if art not in chunk_articles]

        # If all citations are valid, return original response
        if not missing_articles:
            return True, response_text, cited_articles, []

        # Log mismatch
        self._log_citation_mismatch(
            question=question,
            cited_articles=cited_articles,
            chunk_articles=list(chunk_articles),
            missing_articles=missing_articles,
            source_files=[chunk.get('source_file', 'unknown') for chunk in chunks]
        )

        # Replace BASE JURIDIQUE section
        validated_response = self._replace_base_juridique(response_text)

        return False, validated_response, cited_articles, missing_articles

    def _replace_base_juridique(self, response_text: str) -> str:
        """Replaces BASE JURIDIQUE section with warning message"""

        # Find BASE JURIDIQUE section
        base_match = re.search(
            r'(##?\s*BASE JURIDIQUE.*?)(?=##|$)',
            response_text,
            re.DOTALL | re.IGNORECASE
        )

        if not base_match:
            # If no BASE JURIDIQUE section, append warning
            return response_text + "\n\n## BASE JURIDIQUE\n\nBase juridique non disponible dans les textes indexés pour cette question.\n"

        # Replace the section
        replacement = """## BASE JURIDIQUE

Base juridique non disponible dans les textes indexés pour cette question.

> **Note de validation** : La réponse générée contenait des références à des articles
> qui ne sont pas présents dans les chunks récupérés du corpus. Par mesure de sécurité,
> la section BASE JURIDIQUE a été remplacée par ce message. Consultez un professionnel
> du droit pour obtenir les références légales précises.
"""

        validated = re.sub(
            r'##?\s*BASE JURIDIQUE.*?(?=##|$)',
            replacement,
            response_text,
            flags=re.DOTALL | re.IGNORECASE,
            count=1
        )

        return validated

    def _log_citation_mismatch(
        self,
        question: str,
        cited_articles: List[str],
        chunk_articles: List[str],
        missing_articles: List[str],
        source_files: List[str]
    ):
        """Logs citation mismatch to file"""

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'question': question[:200],  # Truncate long questions
            'cited_articles': cited_articles,
            'chunk_articles': chunk_articles,
            'missing_articles': missing_articles,
            'source_files': list(set(source_files)),  # Deduplicate
        }

        # Append to log file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

        print(f"[CITATION_VALIDATOR] MISMATCH logged: {len(missing_articles)} articles not found in corpus")
        print(f"  Missing: {', '.join(missing_articles)}")


# Global instance
_validator_instance = None


def get_citation_validator() -> CitationValidator:
    """Returns singleton citation validator instance"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = CitationValidator()
    return _validator_instance
