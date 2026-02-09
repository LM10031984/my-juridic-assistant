"""
Test d'intégration pour le système de validation des citations (TÂCHE 1)

Simule un scénario où l'LLM cite des articles qui ne sont pas dans les chunks récupérés.
Vérifie que le guard-rail fonctionne et que le log est créé correctement.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from api.services.citation_validator import CitationValidator


def test_citation_mismatch():
    """Test de validation avec articles manquants"""
    print("\n" + "=" * 80)
    print("TEST D'INTEGRATION - CITATION MISMATCH (TÂCHE 1)")
    print("=" * 80)

    # Setup validator
    validator = CitationValidator(base_dir=backend_dir.parent)

    # Simulated LLM response with articles cited in BASE JURIDIQUE
    llm_response = """
## RÉPONSE

Le locataire doit payer son loyer conformément à l'article L. 213-2.
En cas de défaut, l'article R. 999-9 s'applique (cet article n'existe pas dans le corpus).

## BASE JURIDIQUE

- Article L. 213-2 (Loi 1989)
- Article R. 999-9 (Décret fictif - NE DOIT PAS ÊTRE VALIDÉ)
- Article 25-8 (Article numérique)

## SOURCES

- Loi 1989
"""

    # Simulated chunks retrieved from corpus
    # Seul L. 213-2 est réellement dans les chunks (R. 999-9 et 25-8 sont absents)
    chunks = [
        {
            'source_file': 'Loi_1989_RapportsLocatifs.md',
            'domaine': 'location',
            'type': 'loi',
            'articles': ['L. 213-2', 'L. 213-3', 'L. 214-1'],
            'text': 'Article L. 213-2 : Le locataire doit payer le loyer...'
        },
        {
            'source_file': 'Decret_1987_Charges.md',
            'domaine': 'location',
            'type': 'decret',
            'articles': ['D. 1-1', 'D. 1-2'],
            'text': 'Décret sur les charges récupérables...'
        }
    ]

    question = "Que se passe-t-il si le locataire ne paie pas son loyer ?"

    # Validate citations
    print("\n[1] Validation des citations...")
    is_valid, validated_response, cited_articles, missing_articles = validator.validate_citations(
        response_text=llm_response,
        chunks=chunks,
        question=question
    )

    # Print results
    print(f"\n[2] Résultats de validation:")
    print(f"  - Valid: {is_valid}")
    print(f"  - Articles cités: {cited_articles}")
    print(f"  - Articles manquants: {missing_articles}")

    # Check that validation failed (as expected)
    if not is_valid:
        print("\n  [PASS] Validation a échoué comme attendu (articles manquants détectés)")
    else:
        print("\n  [FAIL] Validation a réussi alors qu'elle aurait dû échouer")
        return False

    # Check that missing articles were detected
    expected_missing = ['R999-9', '25-8']  # Normalized forms
    all_missing_detected = all(art in missing_articles for art in expected_missing)

    if all_missing_detected:
        print(f"  [PASS] Tous les articles manquants détectés: {expected_missing}")
    else:
        print(f"  [FAIL] Articles manquants non détectés correctement")
        print(f"    Expected: {expected_missing}")
        print(f"    Got: {missing_articles}")
        return False

    # Check that BASE JURIDIQUE was replaced
    if "Base juridique non disponible" in validated_response:
        print("  [PASS] BASE JURIDIQUE remplacée par le message de sécurité")
    else:
        print("  [FAIL] BASE JURIDIQUE n'a pas été remplacée")
        return False

    # Check that warning was added
    if "Avertissement de validation" in validated_response or "Certaines références" in validated_response:
        print("  [PASS] Avertissement ajouté à la réponse")
    else:
        print("  [FAIL] Avertissement manquant dans la réponse")
        return False

    # Check log file
    print("\n[3] Vérification du log...")
    log_file = validator.log_file

    if log_file.exists():
        print(f"  [PASS] Log file exists: {log_file}")

        # Read last log entry
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if lines:
                last_entry = json.loads(lines[-1])
                print(f"\n  Dernière entrée du log:")
                print(f"    - Timestamp: {last_entry.get('timestamp')}")
                print(f"    - Question: {last_entry.get('question')[:60]}...")
                print(f"    - Cited articles: {last_entry.get('cited_articles')}")
                print(f"    - Missing articles: {last_entry.get('missing_articles')}")
                print(f"    - Top sources: {last_entry.get('top_sources')}")

                # Verify log contains expected data
                if last_entry.get('missing_articles') == missing_articles:
                    print(f"\n  [PASS] Log contient les articles manquants corrects")
                else:
                    print(f"\n  [FAIL] Log ne contient pas les articles manquants corrects")
                    return False
            else:
                print("  [FAIL] Log file is empty")
                return False
    else:
        print(f"  [FAIL] Log file not found: {log_file}")
        return False

    return True


def test_valid_citations():
    """Test de validation avec tous les articles présents dans les chunks"""
    print("\n" + "=" * 80)
    print("TEST D'INTEGRATION - VALID CITATIONS (CONTRÔLE)")
    print("=" * 80)

    validator = CitationValidator(base_dir=Path(__file__).parent.parent.parent)

    # LLM response with only articles present in chunks
    llm_response = """
## RÉPONSE

Le locataire doit payer son loyer conformément à l'article L. 213-2.

## BASE JURIDIQUE

- Article L. 213-2 (Loi 1989)
- Article D. 1-1 (Décret 1987)
"""

    chunks = [
        {
            'source_file': 'Loi_1989_RapportsLocatifs.md',
            'articles': ['L. 213-2'],
            'text': 'Article L. 213-2...'
        },
        {
            'source_file': 'Decret_1987_Charges.md',
            'articles': ['D. 1-1'],
            'text': 'Article D. 1-1...'
        }
    ]

    question = "Que doit payer le locataire ?"

    # Validate
    is_valid, validated_response, cited_articles, missing_articles = validator.validate_citations(
        response_text=llm_response,
        chunks=chunks,
        question=question
    )

    print(f"\n[1] Résultats:")
    print(f"  - Valid: {is_valid}")
    print(f"  - Articles cités: {cited_articles}")
    print(f"  - Articles manquants: {missing_articles}")

    if is_valid and len(missing_articles) == 0:
        print("\n  [PASS] Validation réussie (tous les articles présents dans le corpus)")
        return True
    else:
        print("\n  [FAIL] Validation aurait dû réussir")
        return False


def main():
    """Run integration tests"""
    print("=" * 80)
    print("CITATION VALIDATOR - INTEGRATION TESTS (TÂCHE 1)")
    print("=" * 80)

    results = []

    # Test 1: Mismatch detection
    results.append(("Citation mismatch detection", test_citation_mismatch()))

    # Test 2: Valid citations
    results.append(("Valid citations (control)", test_valid_citations()))

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  [{status}]: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n[PASS] ALL INTEGRATION TESTS PASSED")
        return 0
    else:
        print(f"\n[FAIL] {total - passed} TEST(S) FAILED")
        return 1


if __name__ == '__main__':
    exit(main())
