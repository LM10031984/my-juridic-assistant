"""
Test diagnostics immobiliers - 5 questions ciblées
===================================================

Teste la couverture des diagnostics après enrichissement du corpus
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from dotenv import load_dotenv
from openai import OpenAI

from api.services.retrieval import get_retrieval_service
from api.prompts.system_prompts_v2 import (
    SYSTEM_PROMPT_V2,
    create_user_prompt_v2,
    get_generation_config
)

load_dotenv()

# 5 questions diagnostics ciblées
TEST_QUESTIONS_DIAGNOSTICS = [
    {
        "id": "DIAG_01",
        "question": "Quels sont les diagnostics obligatoires pour vendre un appartement de 1985 ?",
        "expected_keywords": ["DPE", "amiante", "plomb", "gaz", "électricité", "ERP"],
        "domaine": "diagnostics"
    },
    {
        "id": "DIAG_02",
        "question": "Mon DPE est classé G, puis-je encore louer mon appartement en 2025 ?",
        "expected_keywords": ["interdit", "2025", "DPE G", "Loi Climat", "travaux"],
        "domaine": "diagnostics"
    },
    {
        "id": "DIAG_03",
        "question": "Quelle est la durée de validité d'un diagnostic amiante ?",
        "expected_keywords": ["illimitée", "absence", "3 ans", "présence"],
        "domaine": "diagnostics"
    },
    {
        "id": "DIAG_04",
        "question": "Mon diagnostiqueur s'est trompé sur le DPE, quels sont mes recours ?",
        "expected_keywords": ["responsabilité", "assurance RC Pro", "recours", "dommages"],
        "domaine": "diagnostics"
    },
    {
        "id": "DIAG_05",
        "question": "Qu'est-ce que l'ERP et est-ce grave si je suis en zone rouge ?",
        "expected_keywords": ["État des Risques", "zone", "inondations", "pas grave", "normes"],
        "domaine": "diagnostics"
    }
]


class DiagnosticsTest:
    """Test spécifique diagnostics immobiliers"""

    def __init__(self):
        self.retrieval_service = get_retrieval_service()
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    def generate_answer(self, question: str, context: str) -> str:
        """Génère une réponse avec prompt V2"""
        user_prompt = create_user_prompt_v2(question, context)
        gen_config = get_generation_config()

        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            temperature=gen_config['temperature'],
            max_tokens=gen_config['max_tokens'],
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_V2},
                {"role": "user", "content": user_prompt}
            ]
        )

        return response.choices[0].message.content

    def test_question(self, test_case: dict) -> dict:
        """Teste une question diagnostics"""
        print(f"\n[{test_case['id']}] {test_case['question']}")

        try:
            # Retrieval
            chunks, method = self.retrieval_service.search(
                query=test_case['question'],
                top_k=5,
                filter_domaine=test_case.get('domaine')
            )

            if not chunks:
                print(f"    ❌ Aucun chunk trouvé")
                return {
                    "test_id": test_case['id'],
                    "status": "no_chunks",
                    "question": test_case['question']
                }

            print(f"    [OK] {len(chunks)} chunks trouvés (méthode: {method})")

            # Génération
            context = self.retrieval_service.format_context_for_llm(chunks, method)
            answer = self.generate_answer(test_case['question'], context)

            # Vérification keywords
            keywords_found = []
            for keyword in test_case['expected_keywords']:
                if keyword.lower() in answer.lower():
                    keywords_found.append(keyword)

            coverage = len(keywords_found) / len(test_case['expected_keywords']) * 100

            # Vérification structure
            has_structure = all([
                '### RÉPONSE DIRECTE' in answer,
                '### EXPLICATIONS DÉTAILLÉES' in answer,
                '### BASE JURIDIQUE' in answer,
                '### POINTS D\'ATTENTION' in answer
            ])

            status = "✅" if (has_structure and coverage >= 60) else "⚠️"
            print(f"    {status} Structure: {has_structure}")
            print(f"    {status} Keywords: {len(keywords_found)}/{len(test_case['expected_keywords'])} ({coverage:.0f}%)")
            print(f"    Keywords trouvés: {', '.join(keywords_found) if keywords_found else 'Aucun'}")

            return {
                "test_id": test_case['id'],
                "question": test_case['question'],
                "status": "success",
                "chunks_found": len(chunks),
                "has_structure": has_structure,
                "keywords_coverage": coverage,
                "keywords_found": keywords_found,
                "answer_preview": answer[:200] + "..."
            }

        except Exception as e:
            print(f"    ❌ Erreur: {str(e)}")
            return {
                "test_id": test_case['id'],
                "status": "error",
                "error": str(e)
            }

    def run_tests(self):
        """Exécute tous les tests diagnostics"""
        print("\n" + "="*70)
        print("TEST DIAGNOSTICS IMMOBILIERS - 5 QUESTIONS")
        print("="*70)
        print(f"\nNombre de questions : {len(TEST_QUESTIONS_DIAGNOSTICS)}\n")

        results = []
        for test_case in TEST_QUESTIONS_DIAGNOSTICS:
            result = self.test_question(test_case)
            results.append(result)

        # Statistiques
        print("\n" + "="*70)
        print("RÉSULTATS")
        print("="*70)

        success = [r for r in results if r['status'] == 'success']
        no_chunks = [r for r in results if r['status'] == 'no_chunks']
        errors = [r for r in results if r['status'] == 'error']

        print(f"\n📊 Succès : {len(success)}/{len(results)}")
        print(f"📊 Pas de chunks : {len(no_chunks)}")
        print(f"📊 Erreurs : {len(errors)}")

        if success:
            with_structure = [r for r in success if r['has_structure']]
            avg_coverage = sum(r['keywords_coverage'] for r in success) / len(success)

            print(f"\n📋 Structure complète : {len(with_structure)}/{len(success)} ({len(with_structure)/len(success)*100:.0f}%)")
            print(f"📋 Couverture keywords moyenne : {avg_coverage:.0f}%")

        if no_chunks:
            print(f"\n⚠️ Questions sans chunks :")
            for r in no_chunks:
                print(f"    - {r['test_id']}: {r['question'][:60]}...")

        return results


if __name__ == "__main__":
    try:
        tester = DiagnosticsTest()
        results = tester.run_tests()

        print("\n" + "="*70)
        print("✅ TESTS DIAGNOSTICS TERMINÉS")
        print("="*70)

    except Exception as e:
        print(f"\n❌ ERREUR : {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
