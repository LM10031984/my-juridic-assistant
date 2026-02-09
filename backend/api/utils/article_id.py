"""
Article ID Normalization Utilities
Provides canonical normalization and extraction for legal article identifiers.

Used across:
- /ask endpoint (citation validation)
- corpus_autofill_fiches (article matching)
- corpus_chunk_primary (article extraction)

Ensures consistent article matching to prevent false positives.
"""

import re
from typing import List, Set


def normalize_article_id(article_id: str) -> str:
    """
    Normalizes article ID to canonical form for consistent matching.

    Canonical form examples:
    - "Article L. 213-2" -> "L213-2"
    - "L. 213-2" -> "L213-2"
    - "L213-2" -> "L213-2"
    - "R. 123-4" -> "R123-4"
    - "D. 1-1" -> "D1-1"
    - "Article 25-8" -> "25-8"
    - "Art. 3" -> "3"
    - "Article 3-2" -> "3-2"

    Args:
        article_id: Raw article identifier (e.g., "Article L. 213-2")

    Returns:
        Canonical normalized form (e.g., "L213-2")
    """
    if not article_id:
        return ""

    # Convert to string and strip whitespace
    normalized = str(article_id).strip()

    # Remove "Article" and "Art." prefixes
    normalized = re.sub(r'^(?:Article|Art\.?)\s+', '', normalized, flags=re.IGNORECASE)

    # Remove ALL spaces and dots
    # "L. 213-2" -> "L213-2"
    # "L . 213 - 2" -> "L213-2"
    normalized = normalized.replace(' ', '').replace('.', '')

    # Normalize hyphens (keep them, they're significant)
    # "L213‐2" (en dash) -> "L213-2" (hyphen)
    normalized = normalized.replace('–', '-').replace('—', '-').replace('‐', '-')

    return normalized


def is_ambiguous_numeric(article_id: str) -> bool:
    """
    Determines if an article ID is ambiguous (short numeric without letter code).

    Ambiguous articles are:
    - No letter prefix (L/R/D/C/P)
    - No hyphen
    - Length <= 3 digits

    Examples:
    - "1" -> True (ambiguous)
    - "2" -> True (ambiguous)
    - "17" -> True (ambiguous)
    - "123" -> True (ambiguous)
    - "L213-2" -> False (has letter code)
    - "25-8" -> False (has hyphen)
    - "1234" -> False (too long, likely specific)

    Args:
        article_id: Normalized article identifier

    Returns:
        True if ambiguous, False otherwise
    """
    if not article_id:
        return True

    # Normalize first
    normalized = normalize_article_id(article_id)

    # Check if starts with letter code
    if re.match(r'^[LRDCP]', normalized, re.IGNORECASE):
        return False

    # Check if contains hyphen
    if '-' in normalized:
        return False

    # Check if pure numeric and short
    if re.match(r'^\d+$', normalized) and len(normalized) <= 3:
        return True

    return False


def extract_article_ids(text: str) -> List[str]:
    """
    Extracts all article IDs from text and returns them in canonical normalized form.

    Patterns covered:
    - "Article L. 213-2" / "Article L213-2" -> "L213-2"
    - "Article R. 123-4" / "R. 123-4" -> "R123-4"
    - "D. 1-1" / "D.1-1" -> "D1-1"
    - "Article 25-8" -> "25-8"
    - "Art. 3" / "Article 3" -> "3"
    - "Article 3-2" -> "3-2"
    - "l'article L. 213-2" -> "L213-2" (inline references)

    Args:
        text: Source text containing article references

    Returns:
        List of normalized article IDs (deduplicated, order preserved)
    """
    if not text:
        return []

    article_ids = []
    seen: Set[str] = set()

    # Pattern 1: Header-level articles with letter codes
    # "### Article L. 213-2" or "## Article L213-2"
    pattern_header_letter = re.compile(
        r'###?\s*(?:Article|Art\.?)\s+([LRDCP]\.?\s*[\d][\d\-]*)',
        re.IGNORECASE | re.MULTILINE
    )

    for match in pattern_header_letter.finditer(text):
        raw_id = match.group(1)
        normalized = normalize_article_id(raw_id)
        if normalized and normalized not in seen:
            article_ids.append(normalized)
            seen.add(normalized)

    # Pattern 2: Header-level articles without letter codes
    # "### Article 25-8" or "## Article 3"
    pattern_header_numeric = re.compile(
        r'###?\s*(?:Article|Art\.?)\s+([\d][\d\-]*[A-Z]?(?:-\d+)?)',
        re.IGNORECASE | re.MULTILINE
    )

    for match in pattern_header_numeric.finditer(text):
        raw_id = match.group(1)
        normalized = normalize_article_id(raw_id)
        if normalized and normalized not in seen:
            article_ids.append(normalized)
            seen.add(normalized)

    # Pattern 3: Inline references with letter codes
    # "l'article L. 213-2" or "conformément à l'article R. 123-4"
    pattern_inline_letter = re.compile(
        r"(?:l'article|article|art\.?)\s+([LRDCP]\.?\s*[\d][\d\-]*)",
        re.IGNORECASE
    )

    for match in pattern_inline_letter.finditer(text):
        raw_id = match.group(1)
        normalized = normalize_article_id(raw_id)
        if normalized and normalized not in seen:
            article_ids.append(normalized)
            seen.add(normalized)

    # Pattern 4: Inline references without letter codes
    # "l'article 25-8" or "selon l'article 3"
    pattern_inline_numeric = re.compile(
        r"(?:l'article|article|art\.?)\s+([\d][\d\-]*[A-Z]?(?:-\d+)?)",
        re.IGNORECASE
    )

    for match in pattern_inline_numeric.finditer(text):
        raw_id = match.group(1)
        normalized = normalize_article_id(raw_id)
        if normalized and normalized not in seen:
            article_ids.append(normalized)
            seen.add(normalized)

    # Pattern 5: Standalone letter code references
    # "L. 213-2" or "R.123-4" (without "Article" prefix)
    pattern_standalone_letter = re.compile(
        r'\b([LRDCP]\.?\s*[\d][\d\-]*)\b',
        re.IGNORECASE
    )

    for match in pattern_standalone_letter.finditer(text):
        raw_id = match.group(1)
        normalized = normalize_article_id(raw_id)
        if normalized and normalized not in seen:
            # Only add if not already found (avoid duplicates from inline refs)
            article_ids.append(normalized)
            seen.add(normalized)

    return article_ids


def extract_article_ids_from_base_juridique(response_text: str) -> List[str]:
    """
    Extracts article IDs specifically from the BASE JURIDIQUE section of an LLM response.

    This is more restrictive than extract_article_ids() and focuses only on the
    citation section to validate what the LLM explicitly claims as legal basis.

    Args:
        response_text: Full LLM response text

    Returns:
        List of normalized article IDs found in BASE JURIDIQUE section
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

    # Extract articles from BASE JURIDIQUE section only
    return extract_article_ids(base_section)
