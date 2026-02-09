"""
Test du Citation Validator
Vérifie que les citations hors corpus sont bien détectées et remplacées
"""

from pathlib import Path
import sys

# Add parent to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from api.services.citation_validator import CitationValidator


def test_citation_validation():
    """Test validation des citations"""

    validator = CitationValidator()

    # Test 1: Response avec articles présents dans les chunks
    print("=" * 80)
    print("TEST 1: Articles présents dans les chunks (VALID)")
    print("=" * 80)

    response_valid = """
## RÉPONSE

Le dépôt de garantie est encadré par l'article 22 de la loi de 1989.

## BASE JURIDIQUE

- Article 22 de la Loi du 6 juillet 1989
- Article 3 du Décret 1987

## SOURCES

Loi 1989, Décret 1987
"""

    chunks_valid = [
        {
            'source_file': 'loi_1989.md',
            'articles': ['22', '23', '15'],
            'text': 'Article 22...'
        },
        {
            'source_file': 'decret_1987.md',
            'articles': ['1', '2', '3'],
            'text': 'Article 3...'
        }
    ]

    is_valid, validated, cited, missing = validator.validate_citations(
        response_text=response_valid,
        chunks=chunks_valid,
        question="Question sur le dépôt de garantie"
    )

    print(f"Valid: {is_valid}")
    print(f"Cited articles: {cited}")
    print(f"Missing articles: {missing}")
    assert is_valid, "Should be valid - all articles present"
    assert len(missing) == 0, "Should have no missing articles"
    print("[OK] TEST 1 PASSED\n")

    # Test 2: Response avec articles ABSENTS des chunks
    print("=" * 80)
    print("TEST 2: Articles absents des chunks (INVALID - citation mismatch)")
    print("=" * 80)

    response_invalid = """
## RÉPONSE

Le congé pour vente est régi par l'article 15 de la loi de 1989.

## BASE JURIDIQUE

- Article 15 de la Loi du 6 juillet 1989
- Article 1644 du Code civil
- Article L. 213-2 du CCH

## SOURCES

Loi 1989, Code civil
"""

    chunks_invalid = [
        {
            'source_file': 'loi_1989.md',
            'articles': ['22', '23'],  # Article 15 absent !
            'text': 'Article 22...'
        }
    ]

    is_valid, validated, cited, missing = validator.validate_citations(
        response_text=response_invalid,
        chunks=chunks_invalid,
        question="Question sur le congé pour vente"
    )

    print(f"Valid: {is_valid}")
    print(f"Cited articles: {cited}")
    print(f"Missing articles: {missing}")
    print(f"\nValidated response preview:")
    print(validated[:500])

    assert not is_valid, "Should be invalid - articles missing"
    assert len(missing) == 3, "Should have 3 missing articles (15, 1644, L. 213-2)"
    assert "Base juridique non disponible" in validated, "Should replace BASE JURIDIQUE"
    print("\n[OK] TEST 2 PASSED\n")

    # Test 3: Response sans section BASE JURIDIQUE
    print("=" * 80)
    print("TEST 3: Response sans BASE JURIDIQUE (no validation needed)")
    print("=" * 80)

    response_no_base = """
## RÉPONSE

Voici ma réponse sans BASE JURIDIQUE.

## SOURCES

Loi 1989
"""

    is_valid, validated, cited, missing = validator.validate_citations(
        response_text=response_no_base,
        chunks=chunks_valid,
        question="Question générale"
    )

    print(f"Valid: {is_valid}")
    print(f"Cited articles: {cited}")
    print(f"Missing articles: {missing}")

    assert is_valid, "Should be valid - no citations to validate"
    assert len(cited) == 0, "Should have no cited articles"
    print("[OK] TEST 3 PASSED\n")

    print("=" * 80)
    print("ALL TESTS PASSED [OK]")
    print("=" * 80)
    print(f"\nLog file location: {validator.log_file}")


if __name__ == '__main__':
    test_citation_validation()
