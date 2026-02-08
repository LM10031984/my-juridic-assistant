"""
Test en conditions réelles - 50 questions professionnelles
==========================================================

Test du système complet avec des questions réelles d'agents immobiliers
couvrant tous les domaines : mandats, annonces, ventes, vices cachés, copropriété

Usage :
    python -m tests.test_real_questions
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import time

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

# 50 questions réelles organisées par thème
REAL_QUESTIONS = [
    # Catégorie 1 : Mandat, relation vendeur et obligations de l'agent
    {
        "id": "MANDAT_01",
        "question": "Quel type de mandat choisir (simple, exclusif, semi-exclusif) et quelles conséquences juridiques ?",
        "domaine": "pro_immo",
        "categorie": "Mandat"
    },
    {
        "id": "MANDAT_02",
        "question": "Quelles clauses sont indispensables dans un mandat pour être valable et opposable ?",
        "domaine": "pro_immo",
        "categorie": "Mandat"
    },
    {
        "id": "MANDAT_03",
        "question": "Dans quels cas le mandat peut-il être annulé (vice de forme, absence de mentions, signature non conforme) ?",
        "domaine": "pro_immo",
        "categorie": "Mandat"
    },
    {
        "id": "MANDAT_04",
        "question": "Quand la commission est-elle juridiquement due (conditions de paiement, fait générateur, clause aux frais de l'acquéreur) ?",
        "domaine": "pro_immo",
        "categorie": "Mandat"
    },
    {
        "id": "MANDAT_05",
        "question": "Que risque l'agent en cas de vente en direct du vendeur avec un acquéreur présenté par l'agence ?",
        "domaine": "pro_immo",
        "categorie": "Mandat"
    },
    {
        "id": "MANDAT_06",
        "question": "Comment prouver l'intervention de l'agence (bon de visite, preuve de présentation) en cas de litige ?",
        "domaine": "pro_immo",
        "categorie": "Mandat"
    },
    {
        "id": "MANDAT_07",
        "question": "Quelles sont les limites de l'obligation de conseil et d'information de l'agent immobilier ?",
        "domaine": "pro_immo",
        "categorie": "Mandat"
    },
    {
        "id": "MANDAT_08",
        "question": "Quelle responsabilité si l'annonce contient une erreur (surface, diagnostics, travaux, charges, copropriété) ?",
        "domaine": "pro_immo",
        "categorie": "Mandat"
    },
    {
        "id": "MANDAT_09",
        "question": "Peut-on diffuser un bien sans certains documents (DPE, ERP, etc.) et quels risques ?",
        "domaine": "pro_immo",
        "categorie": "Mandat"
    },
    {
        "id": "MANDAT_10",
        "question": "Quelles précautions RGPD pour le fichier clients, les relances, la prospection et le partage de données ?",
        "domaine": "pro_immo",
        "categorie": "Mandat"
    },

    # Catégorie 2 : Annonce, publicité, DPE et informations obligatoires
    {
        "id": "ANNONCE_01",
        "question": "Quelles mentions légales obligatoires dans une annonce immobilière (prix, honoraires, DPE, etc.) ?",
        "domaine": "pro_immo",
        "categorie": "Annonce"
    },
    {
        "id": "ANNONCE_02",
        "question": "Quelles sanctions si le DPE est absent, erroné ou mal affiché ?",
        "domaine": "pro_immo",
        "categorie": "Annonce"
    },
    {
        "id": "ANNONCE_03",
        "question": "Quelles règles sur l'affichage des honoraires (TTC, charge vendeur/acquéreur, barème) ?",
        "domaine": "pro_immo",
        "categorie": "Annonce"
    },
    {
        "id": "ANNONCE_04",
        "question": "Comment annoncer une surface (Carrez, habitable, utile) sans se mettre en risque ?",
        "domaine": "pro_immo",
        "categorie": "Annonce"
    },
    {
        "id": "ANNONCE_05",
        "question": "Quelle marge d'erreur tolérée sur une surface annoncée et quelles conséquences si elle est fausse ?",
        "domaine": "pro_immo",
        "categorie": "Annonce"
    },
    {
        "id": "ANNONCE_06",
        "question": "Quelles règles pour mentionner vue mer, calme, proche commodités, sans vis-à-vis (promesses et preuves) ?",
        "domaine": "pro_immo",
        "categorie": "Annonce"
    },
    {
        "id": "ANNONCE_07",
        "question": "Quelles précautions pour les photos (droit à l'image, voisinage, éléments personnels) ?",
        "domaine": "pro_immo",
        "categorie": "Annonce"
    },
    {
        "id": "ANNONCE_08",
        "question": "Que peut-on dire sur des travaux à prévoir sans engager la responsabilité (estimations, devis) ?",
        "domaine": "pro_immo",
        "categorie": "Annonce"
    },
    {
        "id": "ANNONCE_09",
        "question": "Quelles règles pour les avis clients et témoignages (consentement, modération, publicité) ?",
        "domaine": "pro_immo",
        "categorie": "Annonce"
    },
    {
        "id": "ANNONCE_10",
        "question": "Quelles obligations sur les risques (ERP/ERNMT) et comment l'expliquer au client simplement ?",
        "domaine": "pro_immo",
        "categorie": "Annonce"
    },

    # Catégorie 3 : Vente, compromis, promesse, délais et conditions suspensives
    {
        "id": "VENTE_01",
        "question": "Faut-il choisir promesse unilatérale ou compromis, et pourquoi juridiquement ?",
        "domaine": "transaction",
        "categorie": "Vente"
    },
    {
        "id": "VENTE_02",
        "question": "Quelles conditions suspensives sont indispensables pour protéger l'acheteur (prêt, urbanisme, servitudes, etc.) ?",
        "domaine": "transaction",
        "categorie": "Vente"
    },
    {
        "id": "VENTE_03",
        "question": "Comment rédiger une condition suspensive de prêt correctement (montant, taux, durée, délai) ?",
        "domaine": "transaction",
        "categorie": "Vente"
    },
    {
        "id": "VENTE_04",
        "question": "Quel est le délai de rétractation (SRU) et comment le calculer sans erreur ?",
        "domaine": "transaction",
        "categorie": "Vente"
    },
    {
        "id": "VENTE_05",
        "question": "Que se passe-t-il si l'acheteur se rétracte hors délai (conséquences, indemnité) ?",
        "domaine": "transaction",
        "categorie": "Vente"
    },
    {
        "id": "VENTE_06",
        "question": "Que faire si la condition suspensive de prêt n'aboutit pas (preuves à demander, contestations) ?",
        "domaine": "transaction",
        "categorie": "Vente"
    },
    {
        "id": "VENTE_07",
        "question": "L'acompte/séquestre est-il obligatoire, à quoi sert-il, et qui le détient légalement ?",
        "domaine": "transaction",
        "categorie": "Vente"
    },
    {
        "id": "VENTE_08",
        "question": "Quelles pénalités en cas de refus de signer l'acte authentique (clause pénale, exécution forcée) ?",
        "domaine": "transaction",
        "categorie": "Vente"
    },
    {
        "id": "VENTE_09",
        "question": "Comment gérer un retard de signature chez le notaire (avenant, prorogation, risques) ?",
        "domaine": "transaction",
        "categorie": "Vente"
    },
    {
        "id": "VENTE_10",
        "question": "Peut-on signer un compromis sans tous les diagnostics, et quels sont les risques (annulation, renégociation) ?",
        "domaine": "transaction",
        "categorie": "Vente"
    },

    # Catégorie 4 : Vices cachés, défauts, travaux, sinistres, responsabilité
    {
        "id": "VICE_01",
        "question": "Qu'est-ce qu'un vice caché et comment un vendeur/acheteur peut s'en protéger ?",
        "domaine": "transaction",
        "categorie": "Vice caché"
    },
    {
        "id": "VICE_02",
        "question": "Différence entre vice caché, défaut apparent et non-conformité : qui peut agir et quand ?",
        "domaine": "transaction",
        "categorie": "Vice caché"
    },
    {
        "id": "VICE_03",
        "question": "Que risque le vendeur s'il cache un problème (infiltration, fissures, termites, mérule, etc.) ?",
        "domaine": "transaction",
        "categorie": "Vice caché"
    },
    {
        "id": "VICE_04",
        "question": "Quelle responsabilité de l'agent si un défaut était décelable (devoir de vigilance) ?",
        "domaine": "transaction",
        "categorie": "Vice caché"
    },
    {
        "id": "VICE_05",
        "question": "Peut-on vendre en l'état et est-ce que cela protège vraiment le vendeur ?",
        "domaine": "transaction",
        "categorie": "Vice caché"
    },
    {
        "id": "VICE_06",
        "question": "Quels documents exiger en cas de travaux (factures, décennale, déclarations, conformité) ?",
        "domaine": "transaction",
        "categorie": "Vice caché"
    },
    {
        "id": "VICE_07",
        "question": "Que faire si l'acheteur découvre un sinistre après la vente (assurance, recours, délais) ?",
        "domaine": "transaction",
        "categorie": "Vice caché"
    },
    {
        "id": "VICE_08",
        "question": "Comment gérer une renégociation de prix après expertise ou découverte d'un défaut ?",
        "domaine": "transaction",
        "categorie": "Vice caché"
    },
    {
        "id": "VICE_09",
        "question": "Dans quels cas une vente peut être annulée pour dol (mensonge, dissimulation intentionnelle) ?",
        "domaine": "transaction",
        "categorie": "Vice caché"
    },
    {
        "id": "VICE_10",
        "question": "Quelles précautions si le bien a subi un sinistre (dégât des eaux, incendie) récemment ?",
        "domaine": "transaction",
        "categorie": "Vice caché"
    },

    # Catégorie 5 : Copropriété, charges, AG, travaux votés, règlement
    {
        "id": "COPRO_01",
        "question": "Quels documents de copropriété sont juridiquement indispensables avant la vente (PV d'AG, règlement, charges, etc.) ?",
        "domaine": "copropriete",
        "categorie": "Copropriété"
    },
    {
        "id": "COPRO_02",
        "question": "Qui paie les travaux votés en AG (avant/après vente) et comment l'écrire clairement ?",
        "domaine": "copropriete",
        "categorie": "Copropriété"
    },
    {
        "id": "COPRO_03",
        "question": "Comment expliquer et sécuriser les appels de fonds et régularisations de charges dans la vente ?",
        "domaine": "copropriete",
        "categorie": "Copropriété"
    },
    {
        "id": "COPRO_04",
        "question": "Quelles informations doivent être données sur le fonds de travaux (ALUR) et son impact ?",
        "domaine": "copropriete",
        "categorie": "Copropriété"
    },
    {
        "id": "COPRO_05",
        "question": "Comment traiter une copropriété en difficulté (impayés, procédures) dans la vente ?",
        "domaine": "copropriete",
        "categorie": "Copropriété"
    },
    {
        "id": "COPRO_06",
        "question": "Quelles conséquences si un lot a une destination non conforme (airbnb interdit, profession libérale) ?",
        "domaine": "copropriete",
        "categorie": "Copropriété"
    },
    {
        "id": "COPRO_07",
        "question": "Quels risques liés aux servitudes, parties communes, jouissance exclusive (terrasse, jardin) ?",
        "domaine": "copropriete",
        "categorie": "Copropriété"
    },
    {
        "id": "COPRO_08",
        "question": "Comment vérifier la conformité d'un lot (cave/parking, annexes, tantièmes) pour éviter le litige ?",
        "domaine": "copropriete",
        "categorie": "Copropriété"
    },
    {
        "id": "COPRO_09",
        "question": "Que faire si le règlement de copropriété contredit l'usage actuel (clause, tolérance, contentieux) ?",
        "domaine": "copropriete",
        "categorie": "Copropriété"
    },
    {
        "id": "COPRO_10",
        "question": "Comment gérer la vente d'un lot avec procédure en cours (contre syndic, voisin, copro) ?",
        "domaine": "copropriete",
        "categorie": "Copropriété"
    }
]


class RealQuestionsTest:
    """Test avec questions réelles d'agents immobiliers"""

    def __init__(self):
        self.retrieval_service = get_retrieval_service()
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "total_questions": len(REAL_QUESTIONS),
            "tests": []
        }

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

    def analyze_answer(self, answer: str) -> dict:
        """Analyse la qualité de la réponse"""
        return {
            'has_structure': all([
                '### RÉPONSE DIRECTE' in answer,
                '### EXPLICATIONS DÉTAILLÉES' in answer,
                '### BASE JURIDIQUE' in answer,
                '### POINTS D\'ATTENTION' in answer
            ]),
            'has_disclaimer': 'Disclaimer' in answer or 'disclaimer' in answer.lower(),
            'citation_count': sum(answer.count(m) for m in ['Article', 'Loi', 'Décret']),
            'word_count': len(answer.split()),
            'length': len(answer)
        }

    def test_question(self, test_case: dict, index: int, total: int) -> dict:
        """Teste une question"""
        print(f"\n[{index}/{total}] {test_case['id']} - {test_case['categorie']}")
        print(f"    Q: {test_case['question'][:70]}...")

        try:
            # Retrieval
            chunks, method = self.retrieval_service.search(
                query=test_case['question'],
                top_k=5,
                filter_domaine=test_case['domaine']
            )

            if not chunks:
                print(f"    ❌ Aucun chunk trouvé")
                return {
                    "test_id": test_case['id'],
                    "status": "no_chunks",
                    "error": "Aucun contexte trouvé"
                }

            # Génération
            context = self.retrieval_service.format_context_for_llm(chunks, method)
            answer = self.generate_answer(test_case['question'], context)

            # Analyse
            metrics = self.analyze_answer(answer)

            status = "✅" if metrics['has_structure'] else "⚠️ "
            print(f"    {status} Structure: {metrics['has_structure']}, "
                  f"Citations: {metrics['citation_count']}, "
                  f"Mots: {metrics['word_count']}")

            return {
                "test_id": test_case['id'],
                "question": test_case['question'],
                "categorie": test_case['categorie'],
                "domaine": test_case['domaine'],
                "status": "success",
                "chunks_found": len(chunks),
                "answer": answer,
                "metrics": metrics
            }

        except Exception as e:
            print(f"    ❌ Erreur: {str(e)}")
            return {
                "test_id": test_case['id'],
                "status": "error",
                "error": str(e)
            }

    def run_all_tests(self):
        """Exécute tous les tests"""
        print("\n" + "="*70)
        print("TEST EN CONDITIONS RÉELLES - 50 QUESTIONS PROFESSIONNELLES")
        print("="*70)
        print(f"\nNombre de questions : {len(REAL_QUESTIONS)}")
        print("Catégories : Mandat, Annonce, Vente, Vice caché, Copropriété")
        print("\nDémarrage des tests...\n")

        start_time = time.time()

        for i, test_case in enumerate(REAL_QUESTIONS, 1):
            result = self.test_question(test_case, i, len(REAL_QUESTIONS))
            self.results["tests"].append(result)

            # Pause entre requêtes pour ne pas surcharger l'API
            if i < len(REAL_QUESTIONS):
                time.sleep(1)

        elapsed = time.time() - start_time
        self.results["duration_seconds"] = round(elapsed, 2)

        # Générer statistiques
        self.generate_statistics()

        # Sauvegarder
        self.save_results()

    def generate_statistics(self):
        """Génère les statistiques"""
        print("\n" + "="*70)
        print("STATISTIQUES GLOBALES")
        print("="*70)

        tests = self.results["tests"]
        success_tests = [t for t in tests if t['status'] == 'success']
        error_tests = [t for t in tests if t['status'] == 'error']
        no_chunks_tests = [t for t in tests if t['status'] == 'no_chunks']

        print(f"\n📊 Résultats :")
        print(f"   Total : {len(tests)}")
        print(f"   Succès : {len(success_tests)} ({len(success_tests)/len(tests)*100:.1f}%)")
        print(f"   Erreurs : {len(error_tests)}")
        print(f"   Pas de chunks : {len(no_chunks_tests)}")

        if success_tests:
            # Structure
            with_structure = [t for t in success_tests if t['metrics']['has_structure']]
            print(f"\n📋 Structure :")
            print(f"   Avec structure complète : {len(with_structure)}/{len(success_tests)} ({len(with_structure)/len(success_tests)*100:.1f}%)")

            # Citations
            avg_citations = sum(t['metrics']['citation_count'] for t in success_tests) / len(success_tests)
            print(f"\n📖 Citations :")
            print(f"   Moyenne : {avg_citations:.1f} par réponse")

            # Longueur
            avg_words = sum(t['metrics']['word_count'] for t in success_tests) / len(success_tests)
            print(f"\n📝 Longueur :")
            print(f"   Moyenne : {avg_words:.0f} mots")

            # Par catégorie
            print(f"\n📂 Par catégorie :")
            categories = {}
            for t in success_tests:
                cat = t['categorie']
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(t)

            for cat, tests_cat in categories.items():
                success_rate = len([t for t in tests_cat if t['metrics']['has_structure']]) / len(tests_cat) * 100
                print(f"   {cat} : {len(tests_cat)} tests, {success_rate:.0f}% structure OK")

        # Durée
        print(f"\n⏱️  Durée totale : {self.results['duration_seconds']:.1f}s")
        print(f"   Moyenne par question : {self.results['duration_seconds']/len(tests):.1f}s")

        self.results["statistics"] = {
            "total": len(tests),
            "success": len(success_tests),
            "errors": len(error_tests),
            "no_chunks": len(no_chunks_tests),
            "structure_rate": len(with_structure)/len(success_tests)*100 if success_tests else 0,
            "avg_citations": avg_citations if success_tests else 0,
            "avg_words": avg_words if success_tests else 0
        }

    def save_results(self):
        """Sauvegarde les résultats"""
        output_path = Path(__file__).parent / "real_questions_results.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Résultats sauvegardés : {output_path}")


if __name__ == "__main__":
    try:
        tester = RealQuestionsTest()
        tester.run_all_tests()

        print("\n" + "="*70)
        print("✅ TESTS TERMINÉS")
        print("="*70)

    except Exception as e:
        print(f"\n❌ ERREUR : {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
