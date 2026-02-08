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

            # Articles si disponibles
            if chunk.get('articles') and len(chunk['articles']) > 0:
                articles_str = ", ".join([f"Article {art}" for art in chunk['articles']])
                source_parts.append(f"({articles_str})")

            # Si pas d'info structurée, utiliser le nom de fichier nettoyé
            if not source_parts:
                filename = chunk['source_file'].replace('_', ' ').replace('.md', '')
                source_parts.append(filename)

            source_ref = " ".join(source_parts)
            sources.append(f"{source_ref} - Pertinence: {chunk['similarity']:.0%}")

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
