"""
Citation Validator - Garde-fou anti-citation hors corpus (STRICT)

Valide que TOUS les articles cités dans la réponse LLM existent dans les chunks récupérés.
Si UN SEUL article est cité sans être dans le corpus, remplace toute la section BASE JURIDIQUE.

TÂCHE 1 : Zéro faux positifs - Normalisation canonique des articles via article_id.py
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Tuple, Set
from datetime import datetime

# Import shared article normalization utilities
from api.utils.article_id import (
    normalize_article_id,
    extract_article_ids_from_base_juridique,
    extract_article_ids
)


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

    def extract_cited_articles_from_response(self, response_text: str) -> List[str]:
        """
        Extracts article references from BASE JURIDIQUE section of response.

        Uses shared article_id.extract_article_ids_from_base_juridique() for
        canonical normalization (TÂCHE 1).

        Args:
            response_text: Full LLM response text

        Returns:
            List of normalized article IDs cited in response
        """
        # Use shared utility for canonical extraction
        return extract_article_ids_from_base_juridique(response_text)

    def extract_articles_from_chunks(self, chunks: List[Dict]) -> Set[str]:
        """
        Extracts all article IDs from retrieved chunks using canonical normalization.

        Uses shared article_id.normalize_article_id() for consistency (TÂCHE 1).

        Args:
            chunks: List of chunk dictionaries with 'articles' metadata

        Returns:
            Set of normalized article IDs present in chunks
        """
        chunk_articles = set()

        for chunk in chunks:
            # Extract articles from metadata
            articles_metadata = chunk.get('articles', [])
            for article_id in articles_metadata:
                normalized = normalize_article_id(str(article_id))
                if normalized:  # Only add non-empty normalized IDs
                    chunk_articles.add(normalized)

        return chunk_articles

    def extract_sensitive_claims(self, response_text: str) -> List[str]:
        """
        TÂCHE 2: Extrait les claims sensibles de la réponse

        Args:
            response_text: Texte de réponse LLM

        Returns:
            Liste des claims sensibles détectés
        """
        sensitive_claims = []

        text_lower = response_text.lower()

        # Patterns de préemption
        preemption_patterns = [
            'droit de préemption',
            'droit de preemption',
            'préemption',
            'preemption',
            'congé vaut offre',
            'conge vaut offre',
            'priorité pour acheter',
            'priorite pour acheter',
            'offre de vente',
            'proposition de vente'
        ]

        for pattern in preemption_patterns:
            if pattern in text_lower:
                sensitive_claims.append(pattern)

        return sensitive_claims

    def verify_claim_proof_in_chunks(
        self,
        claims: List[str],
        chunks: List[Dict]
    ) -> Tuple[bool, List[str]]:
        """
        TÂCHE 2: Vérifie que les claims sensibles sont prouvés dans les chunks

        Args:
            claims: Liste des claims sensibles
            chunks: Chunks récupérés

        Returns:
            Tuple (has_proof, unproven_claims)
        """
        if not claims:
            return True, []

        # Patterns de preuve textuelle pour préemption
        proof_patterns = [
            'offre de vente',
            'priorité pour acheter',
            'droit de préemption',
            'congé vaut offre',
            'proposition de vente'
        ]

        # Chercher la preuve dans le texte des chunks
        has_proof = False
        for chunk in chunks:
            chunk_text = chunk.get('text', '').lower()
            for pattern in proof_patterns:
                if pattern in chunk_text:
                    has_proof = True
                    break
            if has_proof:
                break

        # Si aucune preuve trouvée, tous les claims sont non prouvés
        if not has_proof:
            return False, claims

        return True, []

    def validate_citations(
        self,
        response_text: str,
        chunks: List[Dict],
        question: str
    ) -> Tuple[bool, str, List[str], List[str]]:
        """
        Validates that cited articles exist in retrieved chunks

        NOUVEAU (TÂCHE 2): Vérifie aussi les claims sensibles (préemption)

        Args:
            response_text: LLM response text
            chunks: Retrieved corpus chunks
            question: Original user question

        Returns:
            Tuple of (is_valid, validated_response, cited_articles, missing_articles)
        """
        # Extract citations from response
        cited_articles = self.extract_cited_articles_from_response(response_text)

        # Extract articles from chunks
        chunk_articles = self.extract_articles_from_chunks(chunks)

        # Find missing articles (cited but not in chunks)
        missing_articles = [art for art in cited_articles if art not in chunk_articles]

        # TÂCHE 2: Vérifier les claims sensibles
        sensitive_claims = self.extract_sensitive_claims(response_text)
        has_proof, unproven_claims = self.verify_claim_proof_in_chunks(sensitive_claims, chunks)

        # Validation échoue si:
        # 1. Articles manquants OU
        # 2. Claims de préemption sans preuve
        validation_failed = bool(missing_articles) or not has_proof

        if not validation_failed:
            # Tout est OK
            return True, response_text, cited_articles, []

        # Log mismatch
        self._log_citation_mismatch(
            question=question,
            cited_articles=cited_articles,
            chunk_articles=list(chunk_articles),
            missing_articles=missing_articles,
            source_files=[chunk.get('source_file', 'unknown') for chunk in chunks],
            sensitive_claims=sensitive_claims,
            unproven_claims=unproven_claims
        )

        # TÂCHE 2: Supprimer les paragraphes contenant des claims non prouvés
        validated_response = response_text

        if not has_proof and unproven_claims:
            print(f"[CITATION_VALIDATOR] PRÉEMPTION CLAIM sans preuve détectée - Suppression")
            validated_response = self._remove_preemption_claims(validated_response)

        # TÂCHE 1 (STRICT): Remplacer BASE JURIDIQUE si articles manquants + avertissement
        if missing_articles:
            validated_response = self._replace_base_juridique(validated_response)

            # Ajouter un avertissement visible en fin de réponse
            warning = (
                "\n\n---\n\n"
                "⚠️ **Avertissement de validation** : Certaines références citées dans la réponse "
                "générée ne figurent pas dans les textes indexés renvoyés par la recherche. "
                "La section BASE JURIDIQUE a été remplacée par mesure de sécurité.\n"
            )
            validated_response += warning

        return False, validated_response, cited_articles, missing_articles

    def _remove_preemption_claims(self, response_text: str) -> str:
        """
        TÂCHE 2: Supprime les paragraphes contenant des claims de préemption non prouvés

        Args:
            response_text: Texte de réponse

        Returns:
            Texte nettoyé
        """
        # Patterns à supprimer
        preemption_patterns = [
            r'[^\n]*droit de pr[ée]emption[^\n]*',
            r'[^\n]*cong[ée] vaut offre[^\n]*',
            r'[^\n]*priorit[ée] pour acheter[^\n]*',
            r'[^\n]*offre de vente[^\n]*'
        ]

        cleaned = response_text
        for pattern in preemption_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

        # Nettoyer les lignes vides multiples
        cleaned = re.sub(r'\n\n\n+', '\n\n', cleaned)

        return cleaned

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
        source_files: List[str],
        sensitive_claims: List[str] = None,
        unproven_claims: List[str] = None
    ):
        """
        Logs citation mismatch to file (JSONL format).

        TÂCHE 1 (STRICT): Log exhaustif avec tous les détails pour traçabilité
        TÂCHE 2: Log aussi les claims sensibles non prouvés
        """
        # Extract chunk IDs for detailed tracking
        chunk_ids = [
            f"{sf}:{idx}" for idx, sf in enumerate(source_files)
        ]

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'question': question[:200],  # Truncate long questions
            'cited_articles': cited_articles,
            'allowed_articles': chunk_articles,
            'missing_articles': missing_articles,
            'retrieved_chunk_ids': chunk_ids,
            'top_sources': list(set(source_files))[:5],  # Top 5 unique sources
        }

        # TÂCHE 2: Ajouter les claims sensibles
        if sensitive_claims:
            log_entry['sensitive_claims'] = sensitive_claims
        if unproven_claims:
            log_entry['unproven_claims'] = unproven_claims

        # Append to log file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

        if missing_articles:
            print(f"[CITATION_VALIDATOR] MISMATCH logged: {len(missing_articles)} articles not found in corpus")
            print(f"  Cited articles: {', '.join(cited_articles)}")
            print(f"  Missing: {', '.join(missing_articles)}")
            print(f"  Allowed articles in chunks: {', '.join(chunk_articles)}")

        if unproven_claims:
            print(f"[CITATION_VALIDATOR] PRÉEMPTION CLAIM sans preuve: {', '.join(unproven_claims)}")


# Global instance
_validator_instance = None


def get_citation_validator() -> CitationValidator:
    """Returns singleton citation validator instance"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = CitationValidator()
    return _validator_instance
