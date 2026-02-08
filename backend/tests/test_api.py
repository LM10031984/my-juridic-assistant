"""
Tests automatiques pour l'API My Juridic Assistant
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"


def print_section(title):
    """Affiche une section de test"""
    print(f"\n{'=' * 80}")
    print(f"{title}")
    print(f"{'=' * 80}\n")


def test_health_check():
    """Test du health check"""
    print_section("TEST 1: Health Check")

    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200

    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))

    assert data["status"] == "healthy"
    assert data["supabase_configured"] is True
    assert data["anthropic_configured"] is True

    print("[OK] Health check passed")


def test_get_domains():
    """Test de la liste des domaines"""
    print_section("TEST 2: Get Domains")

    response = requests.get(f"{API_URL}/domains")
    assert response.status_code == 200

    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))

    assert len(data["domains"]) == 4
    domain_ids = [d["id"] for d in data["domains"]]
    assert "location" in domain_ids
    assert "copropriete" in domain_ids

    print("[OK] Domains list valid")


def test_ask_simple_question():
    """Test d'une question simple sans pre-questionnement"""
    print_section("TEST 3: Ask Simple Question (No Pre-Questioning)")

    payload = {
        "question": "Quelles sont les charges recuperables en location ?",
        "domaine": "location",
        "enable_prequestioning": False
    }

    print(f"Question: {payload['question']}\n")

    response = requests.post(
        f"{API_URL}/ask",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 200

    data = response.json()
    print(f"Needs qualification: {data.get('needs_qualification')}")
    print(f"Retrieved chunks: {data.get('retrieved_chunks')}")
    print(f"\nAnswer:\n{data.get('answer')}\n")
    print(f"Sources ({len(data.get('sources', []))}):")
    for source in data.get('sources', []):
        print(f"  - {source}")

    assert data["needs_qualification"] is False
    assert data["answer"] is not None
    assert len(data.get("sources", [])) > 0

    print("\n[OK] Simple question answered successfully")


def test_ask_with_prequestioning():
    """Test du pre-questionnement automatique"""
    print_section("TEST 4: Ask with Pre-Questioning")

    payload = {
        "question": "Mon proprietaire peut-il augmenter le loyer ?",
        "enable_prequestioning": True
    }

    print(f"Question: {payload['question']}\n")

    response = requests.post(
        f"{API_URL}/ask",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 200

    data = response.json()

    if data.get("needs_qualification"):
        print(f"[INFO] Pre-questioning triggered")
        print(f"Domaine detected: {data.get('domaine')}")
        print(f"Message: {data.get('message')}\n")
        print(f"Questions ({len(data.get('questions', []))}):")

        for q in data.get('questions', []):
            print(f"\n  Q{q['id']}: {q['question']}")
            print(f"  Type: {q['type']}")
            if q['type'] == 'multiple_choice':
                print(f"  Choices: {', '.join(q['choices'])}")

        print("\n[OK] Pre-questioning generated successfully")

    else:
        print(f"[INFO] No pre-questioning needed")
        print(f"Answer: {data.get('answer')[:200]}...")
        print("[OK] Direct answer provided")


def test_ask_with_qualification_answers():
    """Test avec reponses aux questions de qualification"""
    print_section("TEST 5: Ask with Qualification Answers")

    payload = {
        "question": "Mon proprietaire peut-il augmenter le loyer ?",
        "enable_prequestioning": True,
        "user_answers": {
            "1": "Oui",  # Zone tendue
            "2": "Bail vide"
        }
    }

    print(f"Question: {payload['question']}")
    print(f"User answers: {payload['user_answers']}\n")

    response = requests.post(
        f"{API_URL}/ask",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 200

    data = response.json()

    print(f"Needs qualification: {data.get('needs_qualification')}")
    print(f"Retrieved chunks: {data.get('retrieved_chunks')}")
    print(f"\nAnswer:\n{data.get('answer')}\n")
    print(f"Sources ({len(data.get('sources', []))}):")
    for source in data.get('sources', []):
        print(f"  - {source}")

    assert data["needs_qualification"] is False
    assert data["answer"] is not None

    print("\n[OK] Question with qualification answered successfully")


def test_out_of_scope_question():
    """Test d'une question hors perimetre"""
    print_section("TEST 6: Out of Scope Question")

    payload = {
        "question": "Comment calculer mes impots sur le revenu ?",
        "enable_prequestioning": False
    }

    print(f"Question: {payload['question']}\n")

    response = requests.post(
        f"{API_URL}/ask",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 200

    data = response.json()

    print(f"Answer:\n{data.get('answer')}\n")
    print(f"Sources: {len(data.get('sources', []))}")

    # Devrait retourner peu ou pas de chunks pertinents
    assert len(data.get("sources", [])) <= 2

    print("[OK] Out of scope question handled correctly")


def run_all_tests():
    """Execute tous les tests"""
    print("\n" + "=" * 80)
    print("MY JURIDIC ASSISTANT - API TESTS")
    print("=" * 80)

    print(f"\nBase URL: {BASE_URL}")
    print(f"API URL: {API_URL}\n")

    print("[INFO] Make sure the API is running on localhost:8000")
    print("[INFO] Command: python -m api.main\n")

    time.sleep(1)

    try:
        # Test 1: Health
        test_health_check()
        time.sleep(0.5)

        # Test 2: Domains
        test_get_domains()
        time.sleep(0.5)

        # Test 3: Simple question
        test_ask_simple_question()
        time.sleep(1)

        # Test 4: Pre-questioning
        test_ask_with_prequestioning()
        time.sleep(1)

        # Test 5: With answers
        test_ask_with_qualification_answers()
        time.sleep(1)

        # Test 6: Out of scope
        test_out_of_scope_question()

        # Summary
        print_section("ALL TESTS PASSED")
        print("[OK] API is working correctly!")
        print("\nReady for production")

    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Cannot connect to API")
        print("Make sure the server is running: python -m api.main")

    except AssertionError as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()

    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
