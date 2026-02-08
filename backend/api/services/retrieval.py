"""
Service de Retrieval Vectoriel
Recherche de chunks juridiques similaires dans Supabase
"""

import os
from typing import List, Dict, Optional
from supabase import create_client, Client
from openai import OpenAI


class RetrievalService:
    """Service de recherche vectorielle pour chunks juridiques"""

    def __init__(self):
        """Initialise le service avec Supabase et OpenAI"""
        # Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        openai_key = os.getenv('OPENAI_API_KEY')

        if not supabase_url or not supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY must be set in environment"
            )

        if not openai_key:
            raise ValueError("OPENAI_API_KEY must be set in environment")

        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.openai_client = OpenAI(api_key=openai_key)
        self.embedding_dimension = 768  # Same as sentence-transformers for compatibility
        print("[OK] RetrievalService initialized with OpenAI embeddings")

    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding pour une query utilisateur avec OpenAI

        Args:
            query: Question de l'utilisateur

        Returns:
            Embedding vector (768 dimensions pour compatibilite avec DB)
        """
        response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=query,
            dimensions=768  # Match sentence-transformers dimension
        )
        return response.data[0].embedding

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calcule la similarite cosine entre deux vecteurs (sans numpy)

        Args:
            vec1: Premier vecteur
            vec2: Deuxieme vecteur

        Returns:
            Similarite cosine (entre -1 et 1)
        """
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def search_similar_chunks(
        self,
        query: str,
        top_k: int = 5,
        filter_domaine: Optional[str] = None,
        filter_type: Optional[str] = None,
        filter_layer: Optional[str] = None,
        similarity_threshold: float = 0.4  # Lowered from 0.5 to include more relevant chunks
    ) -> List[Dict]:
        """
        Recherche les chunks les plus similaires a la query

        Args:
            query: Question de l'utilisateur
            top_k: Nombre de resultats a retourner
            filter_domaine: Filtrer par domaine (location, copropriete, etc.)
            filter_type: Filtrer par type (loi, code_civil, fiche, etc.)
            filter_layer: Filtrer par layer (01_sources_text, 02_fiches_ia_ready, etc.)
            similarity_threshold: Score minimum de similarite (0-1)

        Returns:
            Liste de chunks avec scores de similarite
        """
        # Generer l'embedding de la query
        query_embedding = self.generate_query_embedding(query)

        # Recuperer tous les chunks (on calculera la similarite cote client)
        # Note: En production, on pourrait utiliser une fonction RPC Supabase pour
        # calculer la similarite cote serveur (plus efficace)
        response = self.supabase.table('legal_chunks').select('*').execute()

        # Calculer la similarite pour chaque chunk
        results = []
        for chunk in response.data:
            if chunk['embedding']:
                # Parse embedding if it's a string
                emb_data = chunk['embedding']
                if isinstance(emb_data, str):
                    # Remove brackets and parse
                    emb_data = emb_data.strip('[]').split(',')
                    emb_data = [float(x) for x in emb_data]

                # Calculer similarite cosine (sans numpy)
                similarity = self._cosine_similarity(query_embedding, emb_data)

                # Appliquer les filtres
                if filter_domaine and chunk['domaine'] != filter_domaine:
                    continue
                if filter_type and chunk['type'] != filter_type:
                    continue
                if filter_layer and chunk['layer'] != filter_layer:
                    continue

                # Verifier le seuil de similarite
                if similarity < similarity_threshold:
                    continue

                chunk['similarity'] = float(similarity)
                results.append(chunk)

        # Trier par similarite decroissante
        results.sort(key=lambda x: x['similarity'], reverse=True)

        # Retourner top-k resultats
        return results[:top_k]

    def format_context_for_llm(self, chunks: List[Dict]) -> str:
        """
        Formate les chunks recuperes en contexte pour le LLM

        Args:
            chunks: Liste de chunks avec metadata

        Returns:
            Contexte formate en markdown
        """
        if not chunks:
            return "Aucun contexte juridique disponible."

        context_parts = []
        context_parts.append("# CONTEXTE JURIDIQUE\n")

        for i, chunk in enumerate(chunks, 1):
            context_parts.append(f"\n## Source {i}")
            context_parts.append(f"**Domaine:** {chunk['domaine']}")
            context_parts.append(f"**Type:** {chunk['type']}")
            context_parts.append(f"**Source:** {chunk['source_file']}")

            if chunk.get('articles'):
                context_parts.append(f"**Articles:** {', '.join(chunk['articles'])}")

            if chunk.get('sous_themes'):
                context_parts.append(
                    f"**Themes:** {', '.join(chunk['sous_themes'][:3])}"
                )

            context_parts.append(f"**Similarite:** {chunk['similarity']:.2%}\n")
            context_parts.append(f"{chunk['text']}\n")
            context_parts.append("---")

        return "\n".join(context_parts)


# Instance globale (singleton)
_retrieval_service = None


def get_retrieval_service() -> RetrievalService:
    """Recupere l'instance du service de retrieval (singleton)"""
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service
