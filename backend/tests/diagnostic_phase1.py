"""
Script de Diagnostic Phase 1 - My Juridic Assistant
====================================================

Ce script diagnostique les problèmes de retrieval et de génération.

Tests effectués :
1. Cohérence des embeddings (dimension, modèle)
2. Performance du retrieval sur 10 questions types
3. Analyse de la qualité des réponses

Usage :
    python -m tests.diagnostic_phase1
"""

import os
import sys
import json
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

# Fix pour l'encodage Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Ajouter le répertoire backend au path pour imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import create_client, Client
from openai import OpenAI

# Charger les variables d'environnement
load_dotenv()


# ============================================================================
# QUESTIONS DE TEST (10 questions types couvrant les 4 domaines)
# ============================================================================

TEST_QUESTIONS = [
    {
        "id": "LOC_001",
        "question": "Quelles sont les charges récupérables en location vide ?",
        "domaine": "location",
        "expected_keywords": ["article 23", "loi 1989", "décret 1987", "charges"],
        "difficulty": "simple"
    },
    {
        "id": "LOC_002",
        "question": "Mon propriétaire peut-il augmenter le loyer sans justification ?",
        "domaine": "location",
        "expected_keywords": ["révision", "loyer", "IRL", "zone tendue"],
        "difficulty": "moyen"
    },
    {
        "id": "LOC_003",
        "question": "Quelles sont les conditions de décence d'un logement en 2025 ?",
        "domaine": "location",
        "expected_keywords": ["décence", "DPE", "performance énergétique", "décret 2002"],
        "difficulty": "moyen"
    },
    {
        "id": "COPRO_001",
        "question": "Qui paie les travaux de ravalement de façade en copropriété ?",
        "domaine": "copropriete",
        "expected_keywords": ["charges", "parties communes", "loi 1965"],
        "difficulty": "simple"
    },
    {
        "id": "COPRO_002",
        "question": "Comment convoquer une assemblée générale de copropriété ?",
        "domaine": "copropriete",
        "expected_keywords": ["AG", "convocation", "syndic", "délai"],
        "difficulty": "moyen"
    },
    {
        "id": "TRANS_001",
        "question": "Quels diagnostics sont obligatoires pour vendre un appartement ?",
        "domaine": "transaction",
        "expected_keywords": ["diagnostics", "DDT", "amiante", "plomb", "DPE"],
        "difficulty": "simple"
    },
    {
        "id": "TRANS_002",
        "question": "Qu'est-ce qu'un vice caché et quels sont mes recours ?",
        "domaine": "transaction",
        "expected_keywords": ["vice caché", "garantie", "vendeur", "code civil"],
        "difficulty": "moyen"
    },
    {
        "id": "PRO_001",
        "question": "Quelles sont les obligations d'un agent immobilier lors d'un mandat ?",
        "domaine": "pro_immo",
        "expected_keywords": ["mandat", "agent", "loi Hoguet", "carte professionnelle"],
        "difficulty": "simple"
    },
    {
        "id": "PRO_002",
        "question": "Un mandat exclusif doit-il obligatoirement être écrit ?",
        "domaine": "pro_immo",
        "expected_keywords": ["mandat exclusif", "écrit", "loi Hoguet", "clause"],
        "difficulty": "moyen"
    },
    {
        "id": "COMPLEX_001",
        "question": "Peut-on expulser un locataire qui ne paie plus son loyer pendant la trêve hivernale ?",
        "domaine": "location",
        "expected_keywords": ["expulsion", "trêve hivernale", "impayés", "procédure"],
        "difficulty": "complexe"
    }
]


# ============================================================================
# DIAGNOSTIC CLASS
# ============================================================================

class DiagnosticPhase1:
    """Classe principale pour le diagnostic"""

    def __init__(self):
        """Initialise les clients Supabase et OpenAI"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')

        if not all([self.supabase_url, self.supabase_key, self.openai_api_key]):
            raise ValueError("❌ Variables d'environnement manquantes. Vérifiez .env")

        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.openai_client = OpenAI(api_key=self.openai_api_key)

        self.results = {
            "timestamp": datetime.now().isoformat(),
            "embedding_check": {},
            "retrieval_tests": [],
            "stats": {}
        }

    def check_embeddings_consistency(self) -> Dict:
        """
        Vérifie la cohérence des embeddings en base
        - Dimension attendue vs dimension réelle
        - Nombre de chunks avec/sans embeddings
        """
        print("\n" + "="*70)
        print("1️⃣  VÉRIFICATION DE LA COHÉRENCE DES EMBEDDINGS")
        print("="*70)

        try:
            # Récupérer un échantillon de chunks
            response = self.supabase.table('legal_chunks').select('*').limit(5).execute()

            if not response.data:
                return {
                    "status": "error",
                    "message": "❌ Aucun chunk trouvé en base"
                }

            # Vérifier les dimensions des embeddings
            dimensions = []
            chunks_with_embedding = 0
            chunks_without_embedding = 0

            for chunk in response.data:
                if chunk.get('embedding'):
                    chunks_with_embedding += 1
                    emb = chunk['embedding']
                    if isinstance(emb, str):
                        emb = emb.strip('[]').split(',')
                    dimensions.append(len(emb))
                else:
                    chunks_without_embedding += 1

            # Compter le total de chunks
            count_response = self.supabase.table('legal_chunks').select('id', count='exact').execute()
            total_chunks = count_response.count

            # Résultats
            result = {
                "status": "success",
                "total_chunks": total_chunks,
                "chunks_with_embedding": chunks_with_embedding,
                "chunks_without_embedding": chunks_without_embedding,
                "embedding_dimensions": dimensions,
                "expected_dimension": 768,
                "model_used": "text-embedding-3-small"
            }

            print(f"\n📊 Résultats :")
            print(f"   • Total chunks en base : {total_chunks}")
            print(f"   • Chunks avec embedding (échantillon) : {chunks_with_embedding}/5")
            print(f"   • Dimensions détectées : {set(dimensions)}")
            print(f"   • Dimension attendue : 768 (text-embedding-3-small)")

            if len(set(dimensions)) > 1:
                print(f"\n   ⚠️  ATTENTION : Dimensions incohérentes détectées !")
            elif dimensions and dimensions[0] != 768:
                print(f"\n   ⚠️  ATTENTION : Dimension {dimensions[0]} != 768 attendue")
            else:
                print(f"\n   ✅ Dimensions cohérentes")

            return result

        except Exception as e:
            print(f"\n❌ Erreur lors de la vérification : {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

    def test_retrieval_performance(self, test_questions: List[Dict]) -> List[Dict]:
        """
        Teste le retrieval sur les questions types
        Pour chaque question, récupère les top-5 chunks et analyse la pertinence
        """
        print("\n" + "="*70)
        print("2️⃣  TEST DE PERFORMANCE DU RETRIEVAL")
        print("="*70)

        results = []

        for i, test in enumerate(test_questions, 1):
            print(f"\n[{i}/{len(test_questions)}] Test : {test['id']}")
            print(f"   Question : {test['question']}")
            print(f"   Domaine : {test['domaine']}")

            try:
                # Générer l'embedding de la question
                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=test['question'],
                    dimensions=768
                )
                query_embedding = response.data[0].embedding

                # Récupérer tous les chunks et calculer la similarité
                # (simule le comportement actuel du code)
                all_chunks = self.supabase.table('legal_chunks').select('*').execute()

                chunks_with_scores = []
                for chunk in all_chunks.data:
                    if chunk.get('embedding'):
                        emb_data = chunk['embedding']
                        if isinstance(emb_data, str):
                            emb_data = emb_data.strip('[]').split(',')
                            emb_data = [float(x) for x in emb_data]

                        # Calcul cosine similarity
                        similarity = self._cosine_similarity(query_embedding, emb_data)

                        # Filtrer par domaine si spécifié
                        if chunk['domaine'] == test['domaine']:
                            chunks_with_scores.append({
                                'chunk_id': chunk['chunk_id'],
                                'text': chunk['text'][:200] + "...",
                                'domaine': chunk['domaine'],
                                'type': chunk['type'],
                                'source_file': chunk['source_file'],
                                'similarity': float(similarity)
                            })

                # Trier et prendre top-5
                chunks_with_scores.sort(key=lambda x: x['similarity'], reverse=True)
                top_chunks = chunks_with_scores[:5]

                # Analyser la pertinence
                max_score = top_chunks[0]['similarity'] if top_chunks else 0
                min_score = top_chunks[-1]['similarity'] if top_chunks else 0
                avg_score = sum(c['similarity'] for c in top_chunks) / len(top_chunks) if top_chunks else 0

                # Vérifier la présence des mots-clés attendus
                keywords_found = []
                for keyword in test['expected_keywords']:
                    for chunk in top_chunks:
                        if keyword.lower() in chunk['text'].lower():
                            keywords_found.append(keyword)
                            break

                result = {
                    "test_id": test['id'],
                    "question": test['question'],
                    "domaine": test['domaine'],
                    "difficulty": test['difficulty'],
                    "chunks_retrieved": len(top_chunks),
                    "max_similarity": round(max_score, 3),
                    "min_similarity": round(min_score, 3),
                    "avg_similarity": round(avg_score, 3),
                    "expected_keywords": test['expected_keywords'],
                    "keywords_found": list(set(keywords_found)),
                    "keyword_coverage": round(len(set(keywords_found)) / len(test['expected_keywords']) * 100, 1) if test['expected_keywords'] else 0,
                    "top_chunks": top_chunks
                }

                results.append(result)

                # Affichage
                print(f"   📈 Scores de similarité : max={max_score:.2%}, avg={avg_score:.2%}, min={min_score:.2%}")
                print(f"   🔑 Mots-clés trouvés : {len(set(keywords_found))}/{len(test['expected_keywords'])} ({result['keyword_coverage']}%)")

                if result['keyword_coverage'] < 50:
                    print(f"   ⚠️  Couverture faible des mots-clés !")

            except Exception as e:
                print(f"   ❌ Erreur : {str(e)}")
                results.append({
                    "test_id": test['id'],
                    "error": str(e)
                })

        return results

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calcule la similarité cosine entre deux vecteurs"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def generate_statistics(self, retrieval_results: List[Dict]) -> Dict:
        """Génère des statistiques globales sur les résultats"""
        print("\n" + "="*70)
        print("3️⃣  STATISTIQUES GLOBALES")
        print("="*70)

        # Filtrer les résultats avec erreur
        valid_results = [r for r in retrieval_results if 'error' not in r]

        if not valid_results:
            print("❌ Aucun résultat valide pour les statistiques")
            return {}

        # Statistiques de similarité
        all_max_scores = [r['max_similarity'] for r in valid_results]
        all_avg_scores = [r['avg_similarity'] for r in valid_results]

        # Statistiques de couverture des mots-clés
        all_coverages = [r['keyword_coverage'] for r in valid_results]

        # Résultats par difficulté
        by_difficulty = {}
        for r in valid_results:
            diff = r['difficulty']
            if diff not in by_difficulty:
                by_difficulty[diff] = []
            by_difficulty[diff].append(r['keyword_coverage'])

        stats = {
            "total_tests": len(retrieval_results),
            "valid_tests": len(valid_results),
            "failed_tests": len(retrieval_results) - len(valid_results),
            "similarity_scores": {
                "max_avg": round(sum(all_max_scores) / len(all_max_scores), 3),
                "avg_avg": round(sum(all_avg_scores) / len(all_avg_scores), 3),
                "min_max": round(min(all_max_scores), 3),
                "max_max": round(max(all_max_scores), 3)
            },
            "keyword_coverage": {
                "average": round(sum(all_coverages) / len(all_coverages), 1),
                "min": round(min(all_coverages), 1),
                "max": round(max(all_coverages), 1)
            },
            "by_difficulty": {
                diff: round(sum(scores) / len(scores), 1)
                for diff, scores in by_difficulty.items()
            }
        }

        print(f"\n📊 Résultats :")
        print(f"   • Tests valides : {stats['valid_tests']}/{stats['total_tests']}")
        print(f"\n   Similarité moyenne :")
        print(f"     - Max score moyen : {stats['similarity_scores']['max_avg']:.2%}")
        print(f"     - Score moyen moyen : {stats['similarity_scores']['avg_avg']:.2%}")
        print(f"\n   Couverture des mots-clés :")
        print(f"     - Moyenne : {stats['keyword_coverage']['average']}%")
        print(f"     - Min : {stats['keyword_coverage']['min']}%")
        print(f"     - Max : {stats['keyword_coverage']['max']}%")
        print(f"\n   Par difficulté :")
        for diff, score in stats['by_difficulty'].items():
            print(f"     - {diff.capitalize()} : {score}%")

        # Évaluation globale
        print(f"\n🎯 Évaluation globale :")
        if stats['keyword_coverage']['average'] >= 75:
            print(f"   ✅ EXCELLENT - Retrieval performant")
        elif stats['keyword_coverage']['average'] >= 60:
            print(f"   🟡 BON - Retrieval satisfaisant mais améliorable")
        elif stats['keyword_coverage']['average'] >= 40:
            print(f"   🟠 MOYEN - Retrieval nécessite des améliorations")
        else:
            print(f"   🔴 FAIBLE - Retrieval nécessite une refonte importante")

        return stats

    def save_results(self, output_file: str = "diagnostic_results.json"):
        """Sauvegarde les résultats dans un fichier JSON"""
        output_path = Path(__file__).parent / output_file

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Résultats sauvegardés : {output_path}")

    def run_full_diagnostic(self):
        """Exécute le diagnostic complet"""
        print("\n" + "="*70)
        print("🔍 DIAGNOSTIC PHASE 1 - MY JURIDIC ASSISTANT")
        print("="*70)

        # 1. Vérification des embeddings
        self.results['embedding_check'] = self.check_embeddings_consistency()

        # 2. Tests de retrieval
        self.results['retrieval_tests'] = self.test_retrieval_performance(TEST_QUESTIONS)

        # 3. Statistiques globales
        self.results['stats'] = self.generate_statistics(self.results['retrieval_tests'])

        # 4. Sauvegarder les résultats
        self.save_results()

        print("\n" + "="*70)
        print("✅ DIAGNOSTIC TERMINÉ")
        print("="*70)
        print(f"\n📝 Rapport détaillé disponible dans : diagnostic_results.json")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    try:
        diagnostic = DiagnosticPhase1()
        diagnostic.run_full_diagnostic()
    except Exception as e:
        print(f"\n❌ ERREUR FATALE : {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
