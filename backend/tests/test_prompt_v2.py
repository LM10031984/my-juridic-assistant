"""
Test du nouveau prompt V2 vs V1
================================

Compare la qualité des réponses générées avec :
- V1 : Prompt actuel (température par défaut)
- V2 : Prompt amélioré (format imposé + few-shot + température 0.1)

Usage :
    python -m tests.test_prompt_v2
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from dotenv import load_dotenv
from openai import OpenAI

from api.services.retrieval import get_retrieval_service
from api.prompts.system_prompts import SYSTEM_PROMPT, create_user_prompt
from api.prompts.system_prompts_v2 import (
    SYSTEM_PROMPT_V2,
    create_user_prompt_v2,
    get_generation_config
)

load_dotenv()

# Questions de test (3 questions variées)
TEST_QUESTIONS = [
    {
        "id": "Q1",
        "question": "Quelles sont les charges récupérables en location vide ?",
        "domaine": "location"
    },
    {
        "id": "Q2",
        "question": "Qui paie les travaux de ravalement de façade en copropriété ?",
        "domaine": "copropriete"
    },
    {
        "id": "Q3",
        "question": "Un mandat exclusif doit-il obligatoirement être écrit ?",
        "domaine": "pro_immo"
    }
]


class PromptTester:
    """Classe pour tester les prompts V1 vs V2"""

    def __init__(self):
        self.retrieval_service = get_retrieval_service()
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": []
        }

    def generate_answer_v1(self, question: str, context: str) -> str:
        """Génère une réponse avec le prompt V1"""
        user_prompt = create_user_prompt(question, context)

        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            max_tokens=2048,
            # Pas de température spécifiée = défaut OpenAI (probablement 1.0)
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        )

        return response.choices[0].message.content

    def generate_answer_v2(self, question: str, context: str) -> str:
        """Génère une réponse avec le prompt V2"""
        user_prompt = create_user_prompt_v2(question, context)
        gen_config = get_generation_config()

        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            temperature=gen_config['temperature'],  # 0.1
            max_tokens=gen_config['max_tokens'],
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_V2},
                {"role": "user", "content": user_prompt}
            ]
        )

        return response.choices[0].message.content

    def analyze_response_quality(self, response: str) -> dict:
        """Analyse la qualité d'une réponse"""
        metrics = {}

        # 1. Structure : vérifier la présence des sections
        metrics['has_direct_answer'] = '### RÉPONSE DIRECTE' in response
        metrics['has_detailed_explanation'] = '### EXPLICATIONS DÉTAILLÉES' in response
        metrics['has_legal_basis'] = '### BASE JURIDIQUE' in response
        metrics['has_attention_points'] = '### POINTS D\'ATTENTION' in response
        metrics['has_disclaimer'] = 'Disclaimer' in response or 'disclaimer' in response.lower()

        # 2. Citations : compter les références juridiques
        citations_markers = ['Article', 'Loi', 'Décret', 'Code']
        metrics['citation_count'] = sum(response.count(marker) for marker in citations_markers)

        # 3. Longueur
        metrics['length'] = len(response)
        metrics['word_count'] = len(response.split())

        # 4. Score de structure (0-100)
        structure_score = 0
        if metrics['has_direct_answer']:
            structure_score += 25
        if metrics['has_detailed_explanation']:
            structure_score += 25
        if metrics['has_legal_basis']:
            structure_score += 25
        if metrics['has_attention_points']:
            structure_score += 15
        if metrics['has_disclaimer']:
            structure_score += 10

        metrics['structure_score'] = structure_score

        return metrics

    def test_question(self, test_case: dict) -> dict:
        """Teste une question avec V1 et V2"""
        print(f"\n{'='*70}")
        print(f"Test : {test_case['id']} - {test_case['question'][:60]}...")
        print(f"{'='*70}")

        # 1. Retrieval (commun pour V1 et V2)
        print("\n[1/3] Retrieval...")
        chunks, method = self.retrieval_service.search(
            query=test_case['question'],
            top_k=5,
            filter_domaine=test_case['domaine']
        )

        if not chunks:
            print("   ❌ Aucun chunk trouvé, test abandonné")
            return None

        context = self.retrieval_service.format_context_for_llm(chunks, method)
        print(f"   ✅ {len(chunks)} chunks récupérés")

        # 2. Génération V1
        print("\n[2/3] Génération V1 (prompt actuel)...")
        answer_v1 = self.generate_answer_v1(test_case['question'], context)
        metrics_v1 = self.analyze_response_quality(answer_v1)
        print(f"   Structure score : {metrics_v1['structure_score']}/100")
        print(f"   Citations : {metrics_v1['citation_count']}")
        print(f"   Longueur : {metrics_v1['word_count']} mots")

        # 3. Génération V2
        print("\n[3/3] Génération V2 (prompt amélioré)...")
        answer_v2 = self.generate_answer_v2(test_case['question'], context)
        metrics_v2 = self.analyze_response_quality(answer_v2)
        print(f"   Structure score : {metrics_v2['structure_score']}/100")
        print(f"   Citations : {metrics_v2['citation_count']}")
        print(f"   Longueur : {metrics_v2['word_count']} mots")

        # 4. Comparaison
        print("\n📊 Comparaison :")
        struct_diff = metrics_v2['structure_score'] - metrics_v1['structure_score']
        cite_diff = metrics_v2['citation_count'] - metrics_v1['citation_count']

        if struct_diff > 0:
            print(f"   Structure : +{struct_diff} points ✅")
        elif struct_diff < 0:
            print(f"   Structure : {struct_diff} points ❌")
        else:
            print(f"   Structure : identique")

        if cite_diff > 0:
            print(f"   Citations : +{cite_diff} ✅")
        elif cite_diff < 0:
            print(f"   Citations : {cite_diff} ❌")
        else:
            print(f"   Citations : identique")

        return {
            "test_id": test_case['id'],
            "question": test_case['question'],
            "v1": {
                "answer": answer_v1,
                "metrics": metrics_v1
            },
            "v2": {
                "answer": answer_v2,
                "metrics": metrics_v2
            },
            "improvement": {
                "structure_score": struct_diff,
                "citation_count": cite_diff
            }
        }

    def run_all_tests(self):
        """Exécute tous les tests"""
        print("\n" + "="*70)
        print("TEST PROMPT V2 vs V1")
        print("="*70)

        for test_case in TEST_QUESTIONS:
            result = self.test_question(test_case)
            if result:
                self.results["tests"].append(result)

        # Statistiques globales
        self.generate_statistics()

        # Sauvegarder
        self.save_results()

    def generate_statistics(self):
        """Génère les statistiques globales"""
        print("\n" + "="*70)
        print("STATISTIQUES GLOBALES")
        print("="*70)

        if not self.results["tests"]:
            print("❌ Aucun test valide")
            return

        # Scores moyens
        v1_scores = [t['v1']['metrics']['structure_score'] for t in self.results["tests"]]
        v2_scores = [t['v2']['metrics']['structure_score'] for t in self.results["tests"]]

        v1_avg = sum(v1_scores) / len(v1_scores)
        v2_avg = sum(v2_scores) / len(v2_scores)

        # Citations moyennes
        v1_citations = [t['v1']['metrics']['citation_count'] for t in self.results["tests"]]
        v2_citations = [t['v2']['metrics']['citation_count'] for t in self.results["tests"]]

        v1_cite_avg = sum(v1_citations) / len(v1_citations)
        v2_cite_avg = sum(v2_citations) / len(v2_citations)

        print(f"\n📊 Scores de structure :")
        print(f"   V1 : {v1_avg:.1f}/100")
        print(f"   V2 : {v2_avg:.1f}/100")
        print(f"   Gain : {v2_avg - v1_avg:+.1f} points")

        print(f"\n📊 Citations juridiques :")
        print(f"   V1 : {v1_cite_avg:.1f}")
        print(f"   V2 : {v2_cite_avg:.1f}")
        print(f"   Gain : {v2_cite_avg - v1_cite_avg:+.1f}")

        print(f"\n🎯 VERDICT :")
        if v2_avg > v1_avg + 10:
            print(f"   ✅ AMÉLIORATION SIGNIFICATIVE")
        elif v2_avg > v1_avg:
            print(f"   🟢 AMÉLIORATION LÉGÈRE")
        elif v2_avg == v1_avg:
            print(f"   🟡 IDENTIQUE")
        else:
            print(f"   🔴 RÉGRESSION")

        self.results["statistics"] = {
            "v1": {"avg_structure_score": v1_avg, "avg_citations": v1_cite_avg},
            "v2": {"avg_structure_score": v2_avg, "avg_citations": v2_cite_avg},
            "improvement": {
                "structure_score": v2_avg - v1_avg,
                "citations": v2_cite_avg - v1_cite_avg
            }
        }

    def save_results(self):
        """Sauvegarde les résultats"""
        output_path = Path(__file__).parent / "prompt_v2_comparison.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Résultats sauvegardés : {output_path}")


if __name__ == "__main__":
    try:
        tester = PromptTester()
        tester.run_all_tests()

        print("\n" + "="*70)
        print("✅ TESTS TERMINÉS")
        print("="*70)

    except Exception as e:
        print(f"\n❌ ERREUR : {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
