"""
Service de Retrieval Vectoriel
Recherche de chunks juridiques similaires dans Supabase
"""

import os
from typing import List, Dict, Optional
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
import numpy as np


class RetrievalService:
    """Service de recherche vectorielle pour chunks juridiques"""

    def __init__(self):
        """Initialise le service avec Supabase et le modele d'embeddings local"""
        # Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')

        if not supabase_url or not supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY must be set in environment"
            )

        self.supabase: Client = create_client(supabase_url, supabase_key)

        # Modele d'embeddings local (meme que pour l'indexation)
        print("[...] Loading local embedding model...")
        self.model = SentenceTransformer(
            'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'
        )
        self.embedding_dimension = 768
        print(f"[OK] Embedding model loaded (dimension: {self.embedding_dimension})")

    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding pour une query utilisateur

        Args:
            query: Question de l'utilisateur

        Returns:
            Embedding vector (768 dimensions)
        """
        embedding = self.model.encode([query], show_progress_bar=False)[0]
        return embedding.tolist()

    def search_similar_chunks(
        self,
        query: str,
        top_k: int = 5,
        filter_domaine: Optional[str] = None,
        filter_type: Optional[str] = None,
        filter_layer: Optional[str] = None,
        similarity_threshold: float = 0.5
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
                # Calculer similarite cosine
                emb1 = np.array(query_embedding, dtype=float)

                # Parse embedding if it's a string
                emb_data = chunk['embedding']
                if isinstance(emb_data, str):
                    # Remove brackets and parse
                    emb_data = emb_data.strip('[]').split(',')
                    emb_data = [float(x) for x in emb_data]

                emb2 = np.array(emb_data, dtype=float)
                similarity = np.dot(emb1, emb2) / (
                    np.linalg.norm(emb1) * np.linalg.norm(emb2)
                )

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
