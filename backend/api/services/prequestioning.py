"""
Service de Pre-Questionnement Automatique (Layer 4)
Qualification juridique avant reponse
"""

import os
import json
from typing import Dict, List, Optional
from openai import OpenAI
from api.prompts.system_prompts import create_prequestioning_prompt


class PreQuestioningService:
    """Service de qualification juridique automatique"""

    def __init__(self):
        """Initialise le service avec l'API OpenAI"""
        api_key = os.getenv('OPENAI_API_KEY')

        if not api_key:
            raise ValueError("OPENAI_API_KEY must be set in environment")

        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o"

    def generate_qualifying_questions(
        self,
        user_question: str
    ) -> Optional[Dict]:
        """
        Genere des questions de qualification juridique

        Args:
            user_question: Question initiale de l'utilisateur

        Returns:
            Dictionnaire avec domaine et questions, ou None si erreur
        """
        try:
            # Creer le prompt
            prompt = create_prequestioning_prompt(user_question)

            # Appeler OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extraire le contenu
            content = response.choices[0].message.content

            # Parser le JSON
            # Extraire le JSON du markdown si present
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            else:
                json_str = content.strip()

            result = json.loads(json_str)

            # Valider la structure
            if not self._validate_questions(result):
                print(f"[WARNING] Invalid questions structure: {result}")
                return None

            return result

        except Exception as e:
            print(f"[ERROR] Failed to generate qualifying questions: {e}")
            return None

    def _validate_questions(self, data: Dict) -> bool:
        """Valide la structure des questions generees"""
        if not isinstance(data, dict):
            return False

        if 'domaine' not in data or 'questions' not in data:
            return False

        if data['domaine'] not in ['location', 'copropriete', 'transaction', 'pro_immo']:
            return False

        if not isinstance(data['questions'], list):
            return False

        for q in data['questions']:
            if not isinstance(q, dict):
                return False
            if 'id' not in q or 'question' not in q or 'type' not in q:
                return False
            if q['type'] not in ['yes_no', 'multiple_choice']:
                return False
            if q['type'] == 'multiple_choice' and 'choices' not in q:
                return False

        return True

    def should_ask_qualifying_questions(
        self,
        user_question: str,
        context_chunks: List[Dict]
    ) -> bool:
        """
        Determine si des questions de qualification sont necessaires

        Args:
            user_question: Question de l'utilisateur
            context_chunks: Chunks recuperes par le retrieval

        Returns:
            True si pre-questionnement necessaire
        """
        # Si aucun contexte trouve, pas de pre-questionnement
        if not context_chunks:
            return False

        # Si la question est tres specifique (contient des details), pas besoin
        specific_keywords = [
            'article', 'loi', 'decret', 'zone tendue', 'bail meuble',
            'bail vide', 'partie commune', 'partie privative'
        ]

        question_lower = user_question.lower()
        if any(kw in question_lower for kw in specific_keywords):
            return False

        # Si les chunks ont des similarites faibles, pre-questionnement utile
        avg_similarity = sum(c.get('similarity', 0) for c in context_chunks) / len(context_chunks)
        if avg_similarity < 0.7:
            return True

        # Si les chunks sont de domaines multiples, clarification necessaire
        domaines = set(c.get('domaine') for c in context_chunks)
        if len(domaines) > 1:
            return True

        return False

    def format_questions_for_response(self, questions_data: Dict) -> Dict:
        """
        Formate les questions pour la reponse API

        Args:
            questions_data: Donnees des questions generees

        Returns:
            Format structure pour l'API
        """
        return {
            "needs_qualification": True,
            "domaine": questions_data['domaine'],
            "questions": questions_data['questions'],
            "message": (
                "Pour vous repondre avec precision, j'ai besoin de quelques "
                "precisions sur votre situation :"
            )
        }


# Instance globale (singleton)
_prequestioning_service = None


def get_prequestioning_service() -> PreQuestioningService:
    """Recupere l'instance du service de pre-questionnement (singleton)"""
    global _prequestioning_service
    if _prequestioning_service is None:
        _prequestioning_service = PreQuestioningService()
    return _prequestioning_service
