#!/usr/bin/env python3
"""
Script de test pour valider les correctifs du Hybrid Search
Teste les endpoints /ask et /ask/debug avec différentes questions
"""

import requests
import json
from typing import Dict, Any


API_BASE_URL = "http://localhost:8000/api"


def print_separator(title: str):
    """Affiche un séparateur visuel"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def test_debug_endpoint(question: str, domaine: str = None) -> Dict[str, Any]:
    """
    Teste l'endpoint /ask/debug

    Args:
        question: Question à poser
        domaine: Domaine optionnel (location, copropriete, transaction, pro_immo)

    Returns:
        Réponse JSON de l'API
    """
    payload = {"question": question}
    if domaine:
        payload["domaine"] = domaine

    print(f"📝 Question: {question}")
    if domaine:
        print(f"🎯 Domaine: {domaine}")
    print()

    try:
        response = requests.post(f"{API_BASE_URL}/ask/debug", json=payload)
        response.raise_for_status()

        data = response.json()

        # Afficher les résultats
        print(f"✅ Méthode utilisée: {data['method_used'].upper()}")
        print(f"📊 Chunks trouvés: {data['chunks_found']}")
        print(f"🔧 Hybrid disponible: {data['hybrid_available']}")
        print()

        if data['chunks']:
            print("🔍 Top 3 chunks:")
            for chunk in data['chunks'][:3]:
                print(f"\n  [{chunk['rank']}] {chunk['source_file']}")
                print(f"      Domaine: {chunk['domaine']} | Type: {chunk['type']}")

                scores = chunk['scores']
                if data['method_used'] == 'hybrid':
                    print(f"      ✨ Vector similarity: {scores['vector_similarity']:.2%}")
                    print(f"      🎲 RRF score: {scores['rrf_score']:.4f}")
                    print(f"      📈 Vector rank: {scores.get('vector_rank', 'N/A')}")
                    print(f"      📊 Fulltext rank: {scores.get('fulltext_rank', 'N/A')}")
                else:
                    print(f"      ✨ Similarity: {scores['similarity']:.2%}")

                # Preview du texte
                preview = chunk['text_preview']
                if len(preview) > 100:
                    preview = preview[:100] + "..."
                print(f"      📄 Preview: {preview}")

        return data

    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur API: {e}")
        return None


def test_ask_endpoint(question: str, domaine: str = None) -> Dict[str, Any]:
    """
    Teste l'endpoint /ask (génération complète de réponse)

    Args:
        question: Question à poser
        domaine: Domaine optionnel

    Returns:
        Réponse JSON de l'API
    """
    payload = {
        "question": question,
        "enable_prequestioning": False  # Désactiver pour les tests
    }
    if domaine:
        payload["domaine"] = domaine

    print(f"📝 Question: {question}")
    if domaine:
        print(f"🎯 Domaine: {domaine}")
    print()

    try:
        response = requests.post(f"{API_BASE_URL}/ask", json=payload)
        response.raise_for_status()

        data = response.json()

        # Afficher les résultats
        if data.get('needs_qualification'):
            print("⚠️  Pre-questionnement nécessaire")
            print(f"Questions: {len(data.get('questions', []))}")
            return data

        print(f"✅ Réponse générée")
        print(f"📊 Chunks utilisés: {data.get('retrieved_chunks', 0)}")
        print()

        # Afficher les sources (le point critique du fix)
        if data.get('sources'):
            print("📚 Sources citées (format corrigé):")
            for i, source in enumerate(data['sources'][:3], 1):
                print(f"  [{i}] {source}")

                # Vérifier que le score n'est PAS "2%" ou "3%"
                if "2%" in source or "3%" in source or "4%" in source:
                    if "(vector)" not in source:
                        print("      ⚠️  WARNING: Score suspect (devrait être > 50% normalement)")

        print()

        # Afficher un extrait de la réponse
        if data.get('answer'):
            answer = data['answer']
            if len(answer) > 300:
                answer = answer[:300] + "..."
            print(f"💬 Réponse (extrait):")
            print(f"   {answer}")

        return data

    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur API: {e}")
        return None


def main():
    """Tests de validation des correctifs"""

    print_separator("TEST 1: Endpoint /ask/debug - Question Transaction")
    test_debug_endpoint(
        question="Quelles sont les obligations du vendeur concernant les diagnostics immobiliers ?",
        domaine="transaction"
    )

    print_separator("TEST 2: Endpoint /ask/debug - Question Location")
    test_debug_endpoint(
        question="Quelles charges peut récupérer le bailleur sur le locataire ?",
        domaine="location"
    )

    print_separator("TEST 3: Endpoint /ask/debug - Sans filtre domaine")
    test_debug_endpoint(
        question="Quelles sont les règles sur les charges en copropriété ?"
    )

    print_separator("TEST 4: Endpoint /ask - Réponse complète avec sources")
    test_ask_endpoint(
        question="Le bailleur peut-il récupérer les frais de syndic sur le locataire ?",
        domaine="location"
    )

    print_separator("TEST 5: Endpoint /ask - Vérification articles (pas de duplication)")
    test_ask_endpoint(
        question="Quels sont les délais de préavis pour un congé de location ?",
        domaine="location"
    )

    print_separator("✅ TESTS TERMINÉS")
    print("\n📋 Checklist de validation:")
    print("  ☐ Les scores sont affichés en % lisible (70-95%) et non en 2-4%")
    print("  ☐ En mode hybrid, le format est 'XX% (vector) | RRF: 0.XXXX'")
    print("  ☐ En mode vector pur, le format est 'XX%'")
    print("  ☐ Pas de 'Article Article X' dans les sources")
    print("  ☐ Les logs serveur affichent les top 3 chunks avec détails")
    print("  ☐ L'endpoint /ask/debug retourne les scores complets")
    print("\n💡 Vérifiez aussi les logs dans la console du serveur API !")
    print()


if __name__ == "__main__":
    # Vérifier que l'API est accessible
    try:
        response = requests.get("http://localhost:8000/health")
        response.raise_for_status()
        print("✅ API accessible\n")
        main()
    except requests.exceptions.RequestException:
        print("❌ Erreur: L'API n'est pas accessible sur http://localhost:8000")
        print("   Démarrez l'API avec: cd backend && python -m api.main")
        exit(1)
