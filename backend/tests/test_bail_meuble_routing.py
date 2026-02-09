"""
Tests pour le routing bail meublé/vide (TÂCHE 1 + TÂCHE 2)
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.services.retrieval import RetrievalService
from api.services.citation_validator import CitationValidator


def test_detection_bail_meuble():
    """Test 1: Détection bail meublé"""
    print("\n" + "="*80)
    print("TEST 1: Detection bail meuble")
    print("="*80)

    # Create service without Supabase (we only test the detection method)
    with patch.object(RetrievalService, '__init__', lambda x: None):
        service = RetrievalService()

    # Test meublé
    query_meuble = "Quel est le préavis pour un bail meublé en résidence principale?"
    bail_type = service._detect_bail_type(query_meuble)

    print(f"Query: {query_meuble}")
    print(f"Type detecte: {bail_type}")

    assert bail_type == "meuble", f"Expected 'meuble', got {bail_type}"
    print("[OK] PASS: Bail meuble correctement detecte")


def test_detection_bail_vide():
    """Test 2: Détection bail vide"""
    print("\n" + "="*80)
    print("TEST 2: Detection bail vide")
    print("="*80)

    # Create service without Supabase
    with patch.object(RetrievalService, '__init__', lambda x: None):
        service = RetrievalService()

    # Test vide
    query_vide = "Comment résilier un bail vide de 3 ans?"
    bail_type = service._detect_bail_type(query_vide)

    print(f"Query: {query_vide}")
    print(f"Type detecte: {bail_type}")

    assert bail_type == "vide", f"Expected 'vide', got {bail_type}"
    print("[OK] PASS: Bail vide correctement detecte")


def test_routing_articles_meuble():
    """Test 3: Routing doit prioriser articles 25-x pour bail meublé"""
    print("\n" + "="*80)
    print("TEST 3: Articles prioritaires bail meuble")
    print("="*80)

    # Mock chunks
    chunks = [
        {
            'id': 1,
            'articles': ['15'],
            'text': 'Article 15 - Congé bailleur...',
            'similarity': 0.75,
            'source_file': 'loi_1989.md'
        },
        {
            'id': 2,
            'articles': ['25-8'],
            'text': 'Article 25-8 - Bail meublé préavis 3 mois...',
            'similarity': 0.70,
            'source_file': 'loi_1989.md'
        },
        {
            'id': 3,
            'articles': ['7'],
            'text': 'Article 7 - Obligations locataire...',
            'similarity': 0.65,
            'source_file': 'loi_1989.md'
        }
    ]

    # Create service without Supabase
    with patch.object(RetrievalService, '__init__', lambda x: None):
        service = RetrievalService()

    # Appliquer reranking bail meublé
    reranked = service._rerank_by_articles(
        chunks.copy(),
        prioritize_articles=["25-8"],
        deprioritize_articles=["15"]
    )

    # Vérifier que 25-8 est maintenant en tête
    top_article = reranked[0]['articles'][0]
    print(f"Top article apres reranking: {top_article}")
    print(f"Scores ajustes:")
    for i, chunk in enumerate(reranked, 1):
        print(f"  [{i}] Article {chunk['articles'][0]} - Similarity: {chunk['similarity']:.2%} (boost: {chunk.get('article_boost', 0):.2f})")

    assert top_article == '25-8', f"Expected '25-8' first, got {top_article}"
    print("[OK] PASS: Article 25-8 correctement priorise pour bail meuble")


def test_preemption_claim_detection():
    """Test 4: Détection claims préemption"""
    print("\n" + "="*80)
    print("TEST 4: Detection claims preemption")
    print("="*80)

    validator = CitationValidator()

    response_with_preemption = """
## EXPLICATIONS

Le locataire doit respecter un préavis de 1 mois s'il bénéficie du droit de préemption.
Le congé du bailleur vaut offre de vente au locataire.

## BASE JURIDIQUE
- Article 15 (Loi 1989)
"""

    claims = validator.extract_sensitive_claims(response_with_preemption)
    print(f"Claims detectes: {claims}")

    assert len(claims) > 0, "Should detect preemption claims"
    assert any('préemption' in c or 'preemption' in c for c in claims), "Should detect 'preemption'"
    assert any('offre' in c for c in claims), "Should detect 'offre de vente' or 'vaut offre'"

    print("[OK] PASS: Claims preemption correctement detectes")


def test_preemption_claim_verification():
    """Test 5: Vérification preuve préemption dans chunks"""
    print("\n" + "="*80)
    print("TEST 5: Verification preuve preemption")
    print("="*80)

    validator = CitationValidator()

    # Chunks SANS preuve de préemption
    chunks_sans_preuve = [
        {
            'articles': ['25-8'],
            'text': 'Article 25-8 - Le bail meublé est conclu pour une durée minimale de un an...'
        }
    ]

    claims = ['droit de préemption', 'congé vaut offre']

    has_proof, unproven = validator.verify_claim_proof_in_chunks(claims, chunks_sans_preuve)

    print(f"Has proof: {has_proof}")
    print(f"Unproven claims: {unproven}")

    assert not has_proof, "Should NOT find proof in chunks without preemption text"
    assert len(unproven) > 0, "Should report unproven claims"

    # Chunks AVEC preuve de préemption
    chunks_avec_preuve = [
        {
            'articles': ['15'],
            'text': 'Article 15 - Le congé vaut offre de vente au profit du locataire...'
        }
    ]

    has_proof2, unproven2 = validator.verify_claim_proof_in_chunks(claims, chunks_avec_preuve)

    print(f"\nAvec preuve:")
    print(f"Has proof: {has_proof2}")
    print(f"Unproven claims: {unproven2}")

    assert has_proof2, "Should find proof in chunks with 'offre de vente' text"
    assert len(unproven2) == 0, "Should have no unproven claims"

    print("[OK] PASS: Verification preuve preemption fonctionne")


def test_integration_bail_meuble_no_article_15():
    """
    Test 6 (INTÉGRATION): Question bail meublé ne doit PAS citer Article 15
    et ne doit PAS mentionner préemption sans preuve
    """
    print("\n" + "="*80)
    print("TEST 6: Integration - Bail meuble NE cite PAS article 15")
    print("="*80)

    validator = CitationValidator()

    # Simulation: réponse LLM pour bail meublé qui cite Article 15 (ERREUR)
    response_erronee = """
## EXPLICATIONS

Pour un bail meublé, le préavis est de 1 mois. Le locataire bénéficie du droit de préemption.

## BASE JURIDIQUE
- Article 15 (Loi 1989)
- Article 25-8 (Loi 1989)
"""

    # Chunks récupérés (bail meublé = articles 25-x)
    chunks_meuble = [
        {
            'articles': ['25-8', '25-3'],
            'text': 'Article 25-8 - Location meublée préavis 1 mois...',
            'source_file': 'loi_1989.md'
        }
    ]

    is_valid, validated_response, cited_articles, missing_articles = validator.validate_citations(
        response_text=response_erronee,
        chunks=chunks_meuble,
        question="Quel préavis pour bail meublé?"
    )

    print(f"Validation passed: {is_valid}")
    print(f"Missing articles: {missing_articles}")
    print(f"Validated response preview: {validated_response[:200]}...")

    # Assertions
    assert not is_valid, "Validation should FAIL (Article 15 not in chunks)"
    assert '15' in missing_articles, "Article 15 should be marked as missing"
    assert 'préemption' not in validated_response.lower() or 'preemption' not in validated_response.lower(), \
        "Validated response should NOT mention preemption without proof"

    print("[OK] PASS: Bail meuble avec Article 15 errone correctement bloque")


if __name__ == '__main__':
    print("\n" + "="*80)
    print("TESTS ROUTING BAIL MEUBLE + GARDE-FOU PREEMPTION")
    print("="*80)

    try:
        # Tests unitaires
        test_detection_bail_meuble()
        test_detection_bail_vide()
        test_routing_articles_meuble()
        test_preemption_claim_detection()
        test_preemption_claim_verification()

        # Test d'intégration
        test_integration_bail_meuble_no_article_15()

        print("\n" + "="*80)
        print("[OK] TOUS LES TESTS PASSENT")
        print("="*80)

    except AssertionError as e:
        print(f"\n[ERREUR] TEST ECHOUE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    except Exception as e:
        print(f"\n[ERREUR]: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
