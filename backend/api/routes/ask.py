"""
Endpoint /ask - Question-Reponse Juridique avec RAG
Pipeline complet : Pre-questionnement -> Retrieval -> Claude API
"""

import os
from typing import Optional, Dict, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from openai import OpenAI

from api.services.retrieval import get_retrieval_service
from api.services.prequestioning import get_prequestioning_service
# Import V1 (ancien prompt) pour compatibilité
from api.prompts.system_prompts import format_final_response
# Import V2 (nouveau prompt amélioré)
from api.prompts.system_prompts_v2 import (
    SYSTEM_PROMPT_V2,
    create_user_prompt_v2,
    get_generation_config
)


# Router FastAPI
router = APIRouter()


# Models Pydantic pour validation
class AskRequest(BaseModel):
    """Schema de requete pour l'endpoint /ask"""
    question: str = Field(..., min_length=10, max_length=1000)
    domaine: Optional[str] = Field(None, pattern="^(location|copropriete|transaction|pro_immo)$")
    enable_prequestioning: bool = Field(True, description="Activer le pre-questionnement automatique")
    user_answers: Optional[Dict[int, str]] = Field(None, description="Reponses aux questions de qualification")


class AskResponse(BaseModel):
    """Schema de reponse pour l'endpoint /ask"""
    needs_qualification: bool = Field(False, description="Necessite des questions de qualification")
    domaine: Optional[str] = None
    questions: Optional[List[Dict]] = None
    message: Optional[str] = None
    answer: Optional[str] = None
    legal_basis: Optional[str] = None
    sources: Optional[List[str]] = None
    disclaimer: Optional[str] = None
    retrieved_chunks: Optional[int] = None


@router.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    Endpoint principal pour poser une question juridique

    Pipeline :
    1. Retrieval : recherche de chunks similaires
    2. Pre-questionnement (optionnel) : questions de qualification
    3. Generation : appel Claude API avec contexte
    4. Formatage : reponse structuree

    Args:
        request: Question et parametres

    Returns:
        Reponse structuree avec sources
    """
    try:
        # Etape 1 : Retrieval (avec hybrid search si disponible)
        print(f"\n[ASK] Question: {request.question}")
        print(f"[ASK] Domaine filtre: {request.domaine}")

        retrieval_service = get_retrieval_service()

        # Utiliser la méthode unifiée (détection automatique hybrid/vector)
        chunks, method_used = retrieval_service.search(
            query=request.question,
            top_k=5,
            filter_domaine=request.domaine,
            use_hybrid=True
        )

        print(f"[ASK] Retrieved {len(chunks)} chunks using {method_used} search")

        # Logs de diagnostic détaillés (top 3 chunks)
        if chunks:
            print("\n[DIAGNOSTIC] Top 3 chunks retrieved:")
            for i, chunk in enumerate(chunks[:3], 1):
                print(f"  [{i}] {chunk.get('source_file', 'unknown')}")
                print(f"      Domaine: {chunk.get('domaine', 'N/A')} | Type: {chunk.get('type', 'N/A')}")
                print(f"      Method: {method_used}")
                if method_used == "hybrid":
                    print(f"      Vector similarity: {chunk.get('vector_similarity', 0.0):.2%}")
                    print(f"      RRF score: {chunk.get('rrf_score', 0.0):.4f}")
                    print(f"      Vector rank: {chunk.get('vector_rank', 'N/A')}")
                    print(f"      Fulltext rank: {chunk.get('fulltext_rank', 'N/A')}")
                else:
                    print(f"      Similarity: {chunk.get('similarity', 0.0):.2%}")
                print()

        # Si aucun chunk trouve
        if not chunks:
            return AskResponse(
                needs_qualification=False,
                answer=(
                    "Je n'ai pas trouve d'information pertinente dans ma base "
                    "juridique pour repondre a cette question. "
                    "Verifiez que votre question concerne bien le droit "
                    "immobilier francais (location, copropriete, transaction, "
                    "professionnels immobiliers)."
                ),
                sources=[],
                disclaimer=(
                    "Cette reponse indique l'absence d'information dans ma base. "
                    "Consultez un professionnel du droit pour obtenir un conseil "
                    "juridique personnalise."
                )
            )

        # Etape 2 : Pre-questionnement (si active et pas de reponses)
        if request.enable_prequestioning and not request.user_answers:
            prequestioning_service = get_prequestioning_service()

            # Verifier si pre-questionnement necessaire
            if prequestioning_service.should_ask_qualifying_questions(
                request.question,
                chunks
            ):
                print("[ASK] Generating qualifying questions...")

                questions_data = prequestioning_service.generate_qualifying_questions(
                    request.question
                )

                if questions_data:
                    formatted = prequestioning_service.format_questions_for_response(
                        questions_data
                    )
                    return AskResponse(
                        needs_qualification=True,
                        domaine=formatted['domaine'],
                        questions=formatted['questions'],
                        message=formatted['message']
                    )

        # Etape 3 : Generation de la reponse
        print("[ASK] Generating answer with OpenAI API...")

        # Formater le contexte (avec indication de la méthode utilisée)
        context = retrieval_service.format_context_for_llm(chunks, method_used)

        # Enrichir la question avec les reponses de qualification si presentes
        enriched_question = request.question
        if request.user_answers:
            enriched_question += "\n\nPrecisions sur ma situation :\n"
            for q_id, answer in request.user_answers.items():
                enriched_question += f"- Question {q_id}: {answer}\n"

        # Creer le prompt utilisateur V2 (avec format imposé + few-shot)
        user_prompt = create_user_prompt_v2(enriched_question, context)

        # Récupérer la configuration optimisée (température, max_tokens)
        gen_config = get_generation_config()

        # Appeler OpenAI API
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="OPENAI_API_KEY not configured"
            )

        client = OpenAI(api_key=api_key)

        print(f"[ASK] Using temperature={gen_config['temperature']} for juridical coherence")

        response = client.chat.completions.create(
            model="gpt-4o",
            temperature=gen_config['temperature'],  # 0.1 pour cohérence juridique
            max_tokens=gen_config['max_tokens'],
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT_V2  # Nouveau prompt avec format imposé
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )

        # Extraire la reponse
        answer_text = response.choices[0].message.content

        # Formater les sources de maniere professionnelle
        sources = []
        for chunk in chunks:
            # Construire la reference juridique
            source_parts = []

            # Type de texte
            if chunk.get('type') == 'loi':
                source_parts.append("Loi")
            elif chunk.get('type') == 'decret':
                source_parts.append("Décret")
            elif chunk.get('type') == 'code_civil':
                source_parts.append("Code civil")
            elif chunk.get('type') == 'fiche':
                source_parts.append("Fiche technique")

            # Articles si disponibles (éviter "Article Article X")
            if chunk.get('articles') and len(chunk['articles']) > 0:
                formatted_articles = []
                for art in chunk['articles']:
                    # Si l'article commence déjà par "Article", ne pas le répéter
                    if str(art).strip().startswith("Article"):
                        formatted_articles.append(str(art))
                    else:
                        formatted_articles.append(f"Article {art}")
                articles_str = ", ".join(formatted_articles)
                source_parts.append(f"({articles_str})")

            # Si pas d'info structurée, utiliser le nom de fichier nettoyé
            if not source_parts:
                filename = chunk['source_file'].replace('_', ' ').replace('.md', '')
                source_parts.append(filename)

            source_ref = " ".join(source_parts)

            # Afficher le score selon la méthode utilisée
            if method_used == "hybrid":
                # En hybrid : afficher vector_similarity (lisible) et optionnellement rrf_score (technique)
                vector_sim = chunk.get('vector_similarity', chunk.get('similarity', 0.0))
                pertinence_str = f"Pertinence: {vector_sim:.0%} (vector)"
                # Optionnel : afficher le score RRF si présent (pour debug)
                if chunk.get('rrf_score'):
                    pertinence_str += f" | RRF: {chunk['rrf_score']:.4f}"
            else:
                # En vector pur : afficher similarity normalement
                pertinence_str = f"Pertinence: {chunk['similarity']:.0%}"

            sources.append(f"{source_ref} - {pertinence_str}")

        # Dédupliquer les sources
        sources = list(dict.fromkeys(sources))

        # Etape 4 : Formater la reponse finale
        print("[ASK] Formatting response...")

        return AskResponse(
            needs_qualification=False,
            answer=answer_text,
            sources=sources,
            retrieved_chunks=len(chunks),
            disclaimer=(
                "Cette reponse est basee uniquement sur les textes juridiques "
                "indexes dans ma base. Elle ne constitue pas un conseil juridique "
                "personnalise. En cas de doute, consultez un professionnel du droit."
            )
        )

    except Exception as e:
        print(f"[ERROR] Ask endpoint failed: {e}")
        import traceback
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/ask/debug")
async def ask_debug(request: AskRequest):
    """
    Endpoint de diagnostic pour analyser le retrieval sans générer de réponse

    Retourne les détails complets des chunks trouvés :
    - Méthode utilisée (hybrid/vector)
    - Scores détaillés (vector_similarity, rrf_score, ranks)
    - Métadonnées complètes (domaine, type, source_file)
    - Preview du texte (200 premiers caractères)

    Utile pour :
    - Diagnostiquer les problèmes de pertinence
    - Comparer hybrid vs vector search
    - Vérifier les scores et rankings
    """
    try:
        print(f"\n[DEBUG] Question: {request.question}")
        print(f"[DEBUG] Domaine filtre: {request.domaine}")

        retrieval_service = get_retrieval_service()

        # Récupérer les chunks avec la méthode unifiée
        chunks, method_used = retrieval_service.search(
            query=request.question,
            top_k=5,
            filter_domaine=request.domaine,
            use_hybrid=True
        )

        # Construire la réponse de diagnostic
        chunks_details = []
        for i, chunk in enumerate(chunks, 1):
            chunk_detail = {
                "rank": i,
                "source_file": chunk.get('source_file', 'unknown'),
                "domaine": chunk.get('domaine', 'N/A'),
                "type": chunk.get('type', 'N/A'),
                "layer": chunk.get('layer', 'N/A'),
                "sous_themes": chunk.get('sous_themes', []),
                "articles": chunk.get('articles', []),
                "text_preview": chunk.get('text', '')[:200] + "...",
                "method_used": method_used
            }

            # Ajouter les scores selon la méthode
            if method_used == "hybrid":
                chunk_detail["scores"] = {
                    "vector_similarity": chunk.get('vector_similarity', 0.0),
                    "rrf_score": chunk.get('rrf_score', 0.0),
                    "vector_rank": chunk.get('vector_rank', None),
                    "fulltext_rank": chunk.get('fulltext_rank', None)
                }
            else:
                chunk_detail["scores"] = {
                    "similarity": chunk.get('similarity', 0.0)
                }

            chunks_details.append(chunk_detail)

        return {
            "query": request.question,
            "domaine_filter": request.domaine,
            "method_used": method_used,
            "hybrid_available": retrieval_service.hybrid_search_available,
            "embedding_dimension": retrieval_service.embedding_dimension,
            "chunks_found": len(chunks),
            "chunks": chunks_details
        }

    except Exception as e:
        print(f"[ERROR] Debug endpoint failed: {e}")
        import traceback
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"Debug failed: {str(e)}"
        )


@router.get("/domains")
async def get_domains():
    """Retourne la liste des domaines juridiques disponibles"""
    return {
        "domains": [
            {
                "id": "location",
                "name": "Location immobiliere",
                "description": "Baux, loyers, charges, reparations, resiliation"
            },
            {
                "id": "copropriete",
                "name": "Copropriete",
                "description": "Charges, travaux, AG, syndic, reglement"
            },
            {
                "id": "transaction",
                "name": "Transaction immobiliere",
                "description": "Vente, compromis, diagnostics, vices caches"
            },
            {
                "id": "pro_immo",
                "name": "Professionnels de l'immobilier",
                "description": "Agents, mandats, honoraires, obligations"
            }
        ]
    }
