"""
Service de Retrieval Vectoriel + Hybrid Search
Recherche de chunks juridiques similaires dans Supabase

Version améliorée avec :
- Hybrid search (vector + full-text) via RRF
- Fallback sur recherche vectorielle pure si SQL non appliqué
- Détection automatique de la méthode disponible
"""

import os
from typing import List, Dict, Optional, Tuple
from supabase import create_client, Client
from openai import OpenAI


class RetrievalService:
    """Service de recherche vectorielle et hybride pour chunks juridiques"""

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
        self.embedding_dimension = 768  # text-embedding-3-small dimension

        # Vérifier si hybrid search est disponible
        self.hybrid_search_available = self._check_hybrid_search_available()

        if self.hybrid_search_available:
            print("[OK] RetrievalService initialized with HYBRID SEARCH (vector + full-text)")
        else:
            print("[OK] RetrievalService initialized with vector search only")
            print("     [INFO] Pour activer hybrid search, exécutez setup_hybrid_search.sql")

    def _check_hybrid_search_available(self) -> bool:
        """Vérifie si la fonction hybrid_search_rrf est disponible en base"""
        try:
            # Tenter d'appeler la fonction avec des paramètres vides
            # Si elle existe, elle retournera un résultat vide mais pas d'erreur
            test_embedding = [0.0] * 768
            result = self.supabase.rpc(
                'hybrid_search_rrf',
                {
                    'query_text': 'test',
                    'query_embedding': test_embedding,
                    'match_count': 1
                }
            ).execute()
            return True
        except Exception as e:
            # Si la fonction n'existe pas, on aura une erreur
            if 'function' in str(e).lower() or 'does not exist' in str(e).lower():
                return False
            # Autres erreurs : on considère que c'est disponible
            return True

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

    def hybrid_search_rrf(
        self,
        query: str,
        top_k: int = 5,
        filter_domaine: Optional[str] = None,
        filter_type: Optional[str] = None,
        filter_layer: Optional[str] = None,
        similarity_threshold: float = 0.3,  # Baissé à 0.3 pour hybrid search
        rrf_k: int = 60
    ) -> List[Dict]:
        """
        Recherche hybride (vector + full-text) avec Reciprocal Rank Fusion

        Cette méthode combine :
        - Recherche vectorielle (sémantique)
        - Recherche full-text (mots-clés exacts)
        - Fusion intelligente des résultats (RRF)

        Args:
            query: Question de l'utilisateur
            top_k: Nombre de resultats a retourner
            filter_domaine: Filtrer par domaine
            filter_type: Filtrer par type
            filter_layer: Filtrer par layer
            similarity_threshold: Score minimum de similarite vectorielle
            rrf_k: Constante RRF (60 par défaut)

        Returns:
            Liste de chunks avec scores combinés

        Raises:
            RuntimeError: Si hybrid search non disponible
        """
        if not self.hybrid_search_available:
            print("[WARNING] Hybrid search non disponible, fallback sur recherche vectorielle")
            return self.search_similar_chunks(
                query=query,
                top_k=top_k,
                filter_domaine=filter_domaine,
                filter_type=filter_type,
                filter_layer=filter_layer,
                similarity_threshold=similarity_threshold
            )

        # Générer l'embedding de la query
        query_embedding = self.generate_query_embedding(query)

        # Appeler la fonction RPC hybrid_search_rrf
        try:
            response = self.supabase.rpc(
                'hybrid_search_rrf',
                {
                    'query_text': query,
                    'query_embedding': query_embedding,
                    'match_count': top_k,
                    'filter_domaine': filter_domaine,
                    'filter_type': filter_type,
                    'filter_layer': filter_layer,
                    'similarity_threshold': similarity_threshold,
                    'rrf_k': rrf_k
                }
            ).execute()

            results = []
            for chunk in response.data:
                # Stocker le score RRF séparément (ne pas écraser similarity)
                chunk['rrf_score'] = chunk.get('combined_score', 0.0)
                chunk['vector_similarity'] = chunk.get('vector_similarity', 0.0)
                chunk['fulltext_rank'] = chunk.get('fulltext_rank', 0.0)
                chunk['vector_rank'] = chunk.get('vector_rank', None)

                # Garder vector_similarity comme score principal en hybrid
                chunk['similarity'] = chunk.get('vector_similarity', 0.0)
                results.append(chunk)

            return results

        except Exception as e:
            print(f"[ERROR] Hybrid search failed: {str(e)}")
            print("[INFO] Fallback sur recherche vectorielle")
            return self.search_similar_chunks(
                query=query,
                top_k=top_k,
                filter_domaine=filter_domaine,
                filter_type=filter_type,
                filter_layer=filter_layer,
                similarity_threshold=similarity_threshold
            )

    def _detect_bail_type(self, query: str) -> Optional[str]:
        """
        Détecte le type de bail (meublé/vide) dans la question

        Args:
            query: Question de l'utilisateur

        Returns:
            "meuble" si bail meublé détecté
            "vide" si bail vide/non meublé détecté
            None si indéterminé
        """
        query_lower = query.lower()

        # Signaux bail meublé
        meuble_signals = [
            'meublé', 'meublee', 'bail meublé', 'location meublée',
            'logement meublé', '1 an', 'lmnp'
        ]

        # Signaux bail vide
        vide_signals = [
            'vide', 'non meublé', 'non meublee', 'bail vide',
            'location vide', '3 ans'
        ]

        has_meuble = any(signal in query_lower for signal in meuble_signals)
        has_vide = any(signal in query_lower for signal in vide_signals)

        if has_meuble and not has_vide:
            return "meuble"
        elif has_vide and not has_meuble:
            return "vide"

        return None

    def _rerank_by_articles(
        self,
        chunks: List[Dict],
        prioritize_articles: List[str],
        deprioritize_articles: List[str]
    ) -> List[Dict]:
        """
        Réordonne les chunks en fonction des articles prioritaires/dépriorisés

        Args:
            chunks: Liste de chunks à réordonner
            prioritize_articles: Articles à prioriser (ex: ["25-8", "25-3"])
            deprioritize_articles: Articles à déprioriser (ex: ["15"])

        Returns:
            Chunks réordonnés
        """
        def get_boost_score(chunk: Dict) -> float:
            """Calcule un score de boost basé sur les articles du chunk"""
            articles = chunk.get('articles', [])
            if not articles:
                return 0.0

            score = 0.0

            for article in articles:
                article_str = str(article).lower()

                # Boost pour articles prioritaires
                for priority in prioritize_articles:
                    if priority.lower() in article_str:
                        score += 0.2  # +20% boost
                        break

                # Pénalité pour articles dépriorisés
                for depriority in deprioritize_articles:
                    if article_str == depriority.lower():
                        score -= 0.15  # -15% pénalité
                        break

            return score

        # Ajouter le boost score à chaque chunk
        for chunk in chunks:
            boost = get_boost_score(chunk)
            chunk['article_boost'] = boost

            # Ajuster le score de similarité/RRF avec le boost
            if 'similarity' in chunk:
                chunk['similarity'] = max(0.0, min(1.0, chunk['similarity'] + boost))

        # Réordonner par similarité ajustée
        chunks.sort(key=lambda x: x.get('similarity', 0.0), reverse=True)

        return chunks

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_domaine: Optional[str] = None,
        filter_type: Optional[str] = None,
        filter_layer: Optional[str] = None,
        use_hybrid: bool = True
    ) -> Tuple[List[Dict], str]:
        """
        Méthode unifiée de recherche (détection automatique)

        NOUVEAU: Routing automatique bail meublé/vide

        Args:
            query: Question de l'utilisateur
            top_k: Nombre de résultats
            filter_domaine: Filtre domaine
            filter_type: Filtre type
            filter_layer: Filtre layer
            use_hybrid: Utiliser hybrid search si disponible

        Returns:
            Tuple (chunks, method_used)
            - chunks: Liste de chunks trouvés
            - method_used: "hybrid" ou "vector" + "_meuble"/"_vide" si détecté
        """
        # TÂCHE 1: Détecter le type de bail
        bail_type = self._detect_bail_type(query)

        # Récupérer les chunks (top_k * 2 pour avoir de la marge pour le reranking)
        retrieve_k = top_k * 2 if bail_type else top_k

        if use_hybrid and self.hybrid_search_available:
            chunks = self.hybrid_search_rrf(
                query=query,
                top_k=retrieve_k,
                filter_domaine=filter_domaine,
                filter_type=filter_type,
                filter_layer=filter_layer
            )
            method = "hybrid"
        else:
            chunks = self.search_similar_chunks(
                query=query,
                top_k=retrieve_k,
                filter_domaine=filter_domaine,
                filter_type=filter_type,
                filter_layer=filter_layer
            )
            method = "vector"

        # TÂCHE 1: Appliquer le routing si bail détecté
        if bail_type == "meuble":
            print(f"[ROUTING] Bail meublé détecté - Priorisation articles 25-x, dépriorisation article 15")
            chunks = self._rerank_by_articles(
                chunks,
                prioritize_articles=["25-8", "25-3", "25-4", "25-5", "25-6", "25-7", "25-9", "25-10", "25-11"],
                deprioritize_articles=["15"]
            )
            method += "_meuble"

            # Log des articles top retournés
            top_articles = []
            for chunk in chunks[:top_k]:
                top_articles.extend(chunk.get('articles', []))
            print(f"[ROUTING] Top articles après reranking: {', '.join(str(a) for a in top_articles[:5])}")

        elif bail_type == "vide":
            print(f"[ROUTING] Bail vide détecté - Priorisation article 15")
            chunks = self._rerank_by_articles(
                chunks,
                prioritize_articles=["15"],
                deprioritize_articles=["25-8"]
            )
            method += "_vide"

        # Retourner uniquement top_k résultats
        return chunks[:top_k], method

    def format_context_for_llm(self, chunks: List[Dict], method_used: str = "vector") -> str:
        """
        Formate les chunks recuperes en contexte pour le LLM

        Args:
            chunks: Liste de chunks avec metadata
            method_used: Méthode utilisée ("hybrid" ou "vector")

        Returns:
            Contexte formate en markdown
        """
        if not chunks:
            return "Aucun contexte juridique disponible."

        context_parts = []
        context_parts.append("# CONTEXTE JURIDIQUE\n")

        # Indiquer la méthode de recherche utilisée
        if method_used == "hybrid":
            context_parts.append("*Recherche : Hybrid (vector + full-text)*\n")
        else:
            context_parts.append("*Recherche : Vectorielle uniquement*\n")

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

            # Afficher les scores (différent selon la méthode)
            if method_used == "hybrid" and 'combined_score' in chunk:
                context_parts.append(f"**Score combiné:** {chunk['similarity']:.2%}")
                if chunk.get('vector_similarity'):
                    context_parts.append(f"  - Similarité vectorielle: {chunk['vector_similarity']:.2%}")
                if chunk.get('fulltext_rank'):
                    context_parts.append(f"  - Pertinence full-text: {chunk['fulltext_rank']:.3f}")
            else:
                context_parts.append(f"**Similarite:** {chunk['similarity']:.2%}")

            context_parts.append(f"\n{chunk['text']}\n")
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
