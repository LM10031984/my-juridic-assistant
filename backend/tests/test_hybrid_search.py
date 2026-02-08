"""
Test Hybrid Search vs Vector Search
====================================

Ce script compare les performances de :
- Recherche vectorielle pure (ancien système)
- Recherche hybride (vector + full-text + RRF)

Usage :
    python -m tests.test_hybrid_search
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire backend au path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Fix encodage Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from dotenv import load_dotenv
from api.services.retrieval import get_retrieval_service

# Charger variables d'environnement
load_dotenv()


# Questions de test (mêmes que diagnostic_phase1.py)
TEST_QUESTIONS = [
    {
        "id": "LOC_001",
        "question": "Quelles sont les charges récupérables en location vide ?",
        "domaine": "location",
        "expected_keywords": ["article 23", "loi 1989", "décret 1987", "charges"],
    },
    {
        "id": "LOC_002",
        "question": "Mon propriétaire peut-il augmenter le loyer sans justification ?",
        "domaine": "location",
        "expected_keywords": ["révision", "loyer", "IRL", "zone tendue"],
    },
    {
        "id": "LOC_003",
        "question": "Quelles sont les conditions de décence d'un logement en 2025 ?",
        "domaine": "location",
        "expected_keywords": ["décence", "DPE", "performance énergétique", "décret 2002"],
    },
    {
        "id": "COPRO_001",
        "question": "Qui paie les travaux de ravalement de façade en copropriété ?",
        "domaine": "copropriete",
        "expected_keywords": ["charges", "parties communes", "loi 1965"],
    },
    {
        "id": "COPRO_002",
        "question": "Comment convoquer une assemblée générale de copropriété ?",
        "domaine": "copropriete",
        "expected_keywords": ["AG", "convocation", "syndic", "délai"],
    },
    {
        "id": "TRANS_001",
        "question": "Quels diagnostics sont obligatoires pour vendre un appartement ?",
        "domaine": "transaction",
        "expected_keywords": ["diagnostics", "DDT", "amiante", "plomb", "DPE"],
    },
    {
        "id": "TRANS_002",
        "question": "Qu'est-ce qu'un vice caché et quels sont mes recours ?",
        "domaine": "transaction",
        "expected_keywords": ["vice caché", "garantie", "vendeur", "code civil"],
    },
    {
        "id": "PRO_001",
        "question": "Quelles sont les obligations d'un agent immobilier lors d'un mandat ?",
        "domaine": "pro_immo",
        "expected_keywords": ["mandat", "agent", "loi Hoguet", "carte professionnelle"],
    },
    {
        "id": "PRO_002",
        "question": "Un mandat exclusif doit-il obligatoirement être écrit ?",
        "domaine": "pro_immo",
        "expected_keywords": ["mandat exclusif", "écrit", "loi Hoguet", "clause"],
    },
    {
        "id": "COMPLEX_001",
        "question": "Peut-on expulser un locataire qui ne paie plus son loyer pendant la trêve hivernale ?",
        "domaine": "location",
        "expected_keywords": ["expulsion", "trêve hivernale", "impayés", "procédure"],
    }
]


class HybridSearchTester:
    """Classe pour tester hybrid search vs vector search"""

    def __init__(self):
        self.retrieval_service = get_retrieval_service()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "hybrid_available": self.retrieval_service.hybrid_search_available,
            "tests": []
        }

    def test_single_question(self, test_case: dict) -> dict:
        """Teste une question avec les deux méthodes"""
        print(f"\n{'='*70}")
        print(f"Test : {test_case['id']}")
        print(f"Question : {test_case['question']}")
        print(f"{'='*70}")

        result = {
            "test_id": test_case["id"],
            "question": test_case["question"],
            "domaine": test_case["domaine"],
            "expected_keywords": test_case["expected_keywords"],
        }

        # Test 1 : Recherche vectorielle pure
        print("\n[1/2] Recherche vectorielle pure...")
        try:
            vector_chunks = self.retrieval_service.search_similar_chunks(
                query=test_case["question"],
                top_k=5,
                filter_domaine=test_case["domaine"]
            )

            vector_keywords = self._count_keywords(vector_chunks, test_case["expected_keywords"])
            vector_coverage = len(vector_keywords) / len(test_case["expected_keywords"]) * 100

            result["vector"] = {
                "chunks_count": len(vector_chunks),
                "keywords_found": vector_keywords,
                "keyword_coverage": round(vector_coverage, 1),
                "avg_similarity": round(
                    sum(c['similarity'] for c in vector_chunks) / len(vector_chunks),
                    3
                ) if vector_chunks else 0.0
            }

            print(f"   Chunks trouvés : {len(vector_chunks)}")
            print(f"   Mots-clés : {len(vector_keywords)}/{len(test_case['expected_keywords'])} ({vector_coverage:.1f}%)")

        except Exception as e:
            print(f"   ❌ Erreur : {str(e)}")
            result["vector"] = {"error": str(e)}

        # Test 2 : Recherche hybride
        print("\n[2/2] Recherche hybride (vector + full-text)...")
        if not self.retrieval_service.hybrid_search_available:
            print("   ⚠️  Hybrid search non disponible (SQL non appliqué)")
            result["hybrid"] = {"error": "not_available", "message": "SQL setup required"}
        else:
            try:
                hybrid_chunks = self.retrieval_service.hybrid_search_rrf(
                    query=test_case["question"],
                    top_k=5,
                    filter_domaine=test_case["domaine"]
                )

                hybrid_keywords = self._count_keywords(hybrid_chunks, test_case["expected_keywords"])
                hybrid_coverage = len(hybrid_keywords) / len(test_case["expected_keywords"]) * 100

                result["hybrid"] = {
                    "chunks_count": len(hybrid_chunks),
                    "keywords_found": hybrid_keywords,
                    "keyword_coverage": round(hybrid_coverage, 1),
                    "avg_combined_score": round(
                        sum(c.get('similarity', 0) for c in hybrid_chunks) / len(hybrid_chunks),
                        3
                    ) if hybrid_chunks else 0.0
                }

                print(f"   Chunks trouvés : {len(hybrid_chunks)}")
                print(f"   Mots-clés : {len(hybrid_keywords)}/{len(test_case['expected_keywords'])} ({hybrid_coverage:.1f}%)")

                # Afficher le gain
                if "vector" in result and "keyword_coverage" in result["vector"]:
                    gain = hybrid_coverage - result["vector"]["keyword_coverage"]
                    if gain > 0:
                        print(f"   📈 Gain : +{gain:.1f}% de couverture")
                    elif gain < 0:
                        print(f"   📉 Perte : {gain:.1f}% de couverture")
                    else:
                        print(f"   ➡️  Identique")

            except Exception as e:
                print(f"   ❌ Erreur : {str(e)}")
                result["hybrid"] = {"error": str(e)}

        return result

    def _count_keywords(self, chunks: list, expected_keywords: list) -> list:
        """Compte les mots-clés trouvés dans les chunks"""
        found = []
        for keyword in expected_keywords:
            for chunk in chunks:
                if keyword.lower() in chunk['text'].lower():
                    found.append(keyword)
                    break
        return found

    def run_all_tests(self):
        """Exécute tous les tests"""
        print("\n" + "="*70)
        print("TEST HYBRID SEARCH vs VECTOR SEARCH")
        print("="*70)
        print(f"\nHybrid search disponible : {'✅ OUI' if self.results['hybrid_available'] else '❌ NON'}")

        if not self.results['hybrid_available']:
            print("\n⚠️  ATTENTION : Hybrid search non disponible.")
            print("   Pour l'activer, exécutez : setup_hybrid_search.sql dans Supabase")
            print("\n   Les tests vont quand même s'exécuter pour comparaison.")

        # Exécuter tous les tests
        for test_case in TEST_QUESTIONS:
            result = self.test_single_question(test_case)
            self.results["tests"].append(result)

        # Générer les statistiques
        self.generate_statistics()

        # Sauvegarder les résultats
        self.save_results()

    def generate_statistics(self):
        """Génère les statistiques comparatives"""
        print("\n" + "="*70)
        print("STATISTIQUES COMPARATIVES")
        print("="*70)

        vector_coverages = []
        hybrid_coverages = []

        for test in self.results["tests"]:
            if "vector" in test and "keyword_coverage" in test["vector"]:
                vector_coverages.append(test["vector"]["keyword_coverage"])

            if "hybrid" in test and "keyword_coverage" in test["hybrid"]:
                hybrid_coverages.append(test["hybrid"]["keyword_coverage"])

        # Statistiques vector
        if vector_coverages:
            vector_avg = sum(vector_coverages) / len(vector_coverages)
            print(f"\n📊 Recherche vectorielle :")
            print(f"   Couverture moyenne : {vector_avg:.1f}%")
            print(f"   Min : {min(vector_coverages):.1f}%")
            print(f"   Max : {max(vector_coverages):.1f}%")

        # Statistiques hybrid
        if hybrid_coverages:
            hybrid_avg = sum(hybrid_coverages) / len(hybrid_coverages)
            print(f"\n📊 Recherche hybride :")
            print(f"   Couverture moyenne : {hybrid_avg:.1f}%")
            print(f"   Min : {min(hybrid_coverages):.1f}%")
            print(f"   Max : {max(hybrid_coverages):.1f}%")

            # Gain
            if vector_coverages:
                gain = hybrid_avg - vector_avg
                gain_pct = (gain / vector_avg * 100) if vector_avg > 0 else 0

                print(f"\n🎯 GAIN AVEC HYBRID SEARCH :")
                print(f"   +{gain:.1f} points de couverture")
                print(f"   +{gain_pct:.1f}% d'amélioration relative")

                if gain >= 30:
                    print(f"   ✅ EXCELLENT - Objectif atteint !")
                elif gain >= 20:
                    print(f"   🟢 TRÈS BON - Amélioration significative")
                elif gain >= 10:
                    print(f"   🟡 BON - Amélioration notable")
                elif gain > 0:
                    print(f"   🟠 FAIBLE - Amélioration modeste")
                else:
                    print(f"   🔴 AUCUN GAIN - Investiguer")

        self.results["statistics"] = {
            "vector": {
                "avg_coverage": round(vector_avg, 1) if vector_coverages else None,
                "min_coverage": round(min(vector_coverages), 1) if vector_coverages else None,
                "max_coverage": round(max(vector_coverages), 1) if vector_coverages else None
            },
            "hybrid": {
                "avg_coverage": round(hybrid_avg, 1) if hybrid_coverages else None,
                "min_coverage": round(min(hybrid_coverages), 1) if hybrid_coverages else None,
                "max_coverage": round(max(hybrid_coverages), 1) if hybrid_coverages else None
            } if hybrid_coverages else None,
            "gain": {
                "absolute": round(gain, 1) if vector_coverages and hybrid_coverages else None,
                "relative_pct": round(gain_pct, 1) if vector_coverages and hybrid_coverages else None
            } if vector_coverages and hybrid_coverages else None
        }

    def save_results(self):
        """Sauvegarde les résultats"""
        output_path = Path(__file__).parent / "hybrid_search_comparison.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Résultats sauvegardés : {output_path}")


if __name__ == "__main__":
    try:
        tester = HybridSearchTester()
        tester.run_all_tests()

        print("\n" + "="*70)
        print("✅ TESTS TERMINÉS")
        print("="*70)

    except Exception as e:
        print(f"\n❌ ERREUR : {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
