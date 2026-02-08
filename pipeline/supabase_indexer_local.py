"""
Indexeur Supabase avec embeddings locaux GRATUITS

Utilise sentence-transformers pour générer des embeddings sans API externe.
"""

import json
import os
import time
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

try:
    from supabase import create_client, Client
except ImportError:
    print("Error: Please install supabase-py:")
    print("  pip install supabase")
    exit(1)

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
except ImportError:
    print("Error: Please install sentence-transformers:")
    print("  pip install sentence-transformers")
    exit(1)


class LocalSupabaseIndexer:
    """Indexe les chunks juridiques dans Supabase avec embeddings locaux"""

    def __init__(self):
        # Charger les variables d'environnement
        load_dotenv()

        # Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')

        if not supabase_url or not supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY must be set in .env file"
            )

        self.supabase: Client = create_client(supabase_url, supabase_key)

        # Charger le modèle d'embeddings local
        print("\n[...] Loading local embedding model (first time: ~400MB download)...")
        self.model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')
        self.embedding_dimension = 768  # Dimension du modèle

        print(f"[OK] Connected to Supabase: {supabase_url}")
        print(f"[OK] Using local embedding model: paraphrase-multilingual-mpnet-base-v2")
        print(f"[OK] Embedding dimension: {self.embedding_dimension}")

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Génère des embeddings localement (gratuit)"""
        print(f"  Generating {len(texts)} embeddings locally...", end='', flush=True)

        # Générer tous les embeddings en une fois
        embeddings = self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)

        # Convertir en liste de listes
        embeddings_list = [emb.tolist() for emb in embeddings]

        print(" Done!")
        return embeddings_list

    def prepare_chunk_for_db(self, chunk: Dict, embedding: List[float]) -> Dict:
        """Prépare un chunk pour l'insertion dans la DB"""
        metadata = chunk['metadata']

        return {
            'chunk_id': metadata['chunk_id'],
            'text': chunk['text'],
            'embedding': embedding,
            'layer': metadata['layer'],
            'type': metadata['type'],
            'domaine': metadata['domaine'],
            'source_file': metadata['source_file'],
            'articles': metadata.get('articles', []),
            'sous_themes': metadata.get('sous_themes', []),
            'keywords': metadata.get('keywords', []),
            'word_count': metadata['word_count'],
            'has_context': metadata['has_context'],
            'version_date': metadata.get('version_date'),
            'section_title': metadata.get('section_title'),
        }

    def index_chunks(self, chunks: List[Dict], batch_size: int = 50):
        """Indexe les chunks dans Supabase"""
        total = len(chunks)
        print(f"\n{'=' * 80}")
        print(f"INDEXING {total} CHUNKS TO SUPABASE")
        print(f"{'=' * 80}\n")

        # Étape 1: Générer tous les embeddings
        print(f"[1/2] Generating embeddings locally (FREE)...")
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.generate_embeddings_batch(texts)
        print(f"[OK] Generated {len(embeddings)} embeddings\n")

        # Étape 2: Insérer dans Supabase par batch
        print(f"[2/2] Inserting chunks into Supabase...")

        inserted_count = 0
        error_count = 0

        for i in range(0, total, batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batch_embeddings = embeddings[i:i + batch_size]

            # Préparer les données
            db_records = [
                self.prepare_chunk_for_db(chunk, emb)
                for chunk, emb in zip(batch_chunks, batch_embeddings)
            ]

            # Insérer dans Supabase
            try:
                response = self.supabase.table('legal_chunks').upsert(
                    db_records,
                    on_conflict='chunk_id'
                ).execute()

                inserted_count += len(db_records)
                print(f"  Inserted batch {i // batch_size + 1}/{(total + batch_size - 1) // batch_size} "
                      f"({inserted_count}/{total} chunks)", end='\r')

            except Exception as e:
                error_count += len(db_records)
                print(f"\n[ERROR] Batch {i // batch_size + 1} failed: {e}")
                continue

        print()  # New line
        print(f"\n[OK] Indexing complete!")
        print(f"  - Successfully indexed: {inserted_count}")
        print(f"  - Errors: {error_count}")

    def search(
        self,
        query: str,
        match_count: int = 5,
        filter_domaine: Optional[str] = None,
        filter_type: Optional[str] = None,
        filter_layer: Optional[str] = None
    ) -> List[Dict]:
        """Recherche des chunks similaires avec filtres métadonnées"""
        # Générer l'embedding de la requête
        print(f"\nSearching for: '{query}'")
        query_embedding = self.model.encode([query], show_progress_bar=False)[0].tolist()

        # Appeler la fonction Supabase (mais adapter pour 768 dimensions)
        # Note: Il faudra recréer la fonction SQL avec la bonne dimension
        try:
            # Pour l'instant, faire une recherche simple sans la fonction
            # car la fonction est configurée pour 1536 dimensions
            response = self.supabase.table('legal_chunks').select('*').execute()

            # Calculer la similarité côté client
            results = []
            for chunk in response.data:
                if chunk['embedding']:
                    # Calculer similarité cosine
                    emb1 = np.array(query_embedding)
                    emb2 = np.array(chunk['embedding'])
                    similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))

                    # Appliquer les filtres
                    if filter_domaine and chunk['domaine'] != filter_domaine:
                        continue
                    if filter_type and chunk['type'] != filter_type:
                        continue
                    if filter_layer and chunk['layer'] != filter_layer:
                        continue

                    chunk['similarity'] = float(similarity)
                    results.append(chunk)

            # Trier par similarité et limiter
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:match_count]

        except Exception as e:
            print(f"[ERROR] Search failed: {e}")
            return []

    def get_stats(self) -> Dict:
        """Récupère les statistiques de la base de données"""
        try:
            response = self.supabase.table('legal_chunks').select('*').execute()

            total = len(response.data)
            domaines = {}
            types = {}

            for record in response.data:
                dom = record['domaine']
                domaines[dom] = domaines.get(dom, 0) + 1

                t = record['type']
                types[t] = types.get(t, 0) + 1

            return {
                'total': total,
                'by_domaine': domaines,
                'by_type': types
            }

        except Exception as e:
            print(f"[ERROR] Failed to get stats: {e}")
            return {}


def main():
    """Point d'entrée principal"""
    base_dir = Path(__file__).parent
    input_file = base_dir / 'output' / 'chunks_enriched.json'

    print("=" * 80)
    print("MY JURIDIC ASSISTANT - SUPABASE INDEXER (LOCAL EMBEDDINGS)")
    print("=" * 80)

    # Vérifier que le fichier existe
    if not input_file.exists():
        print(f"\n[ERROR] Input file not found: {input_file}")
        print("Please run chunker.py and metadata_enricher.py first")
        return

    # Charger les chunks
    print(f"\nLoading chunks from: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    print(f"[OK] Loaded {len(chunks)} chunks")

    # Initialiser l'indexeur
    try:
        indexer = LocalSupabaseIndexer()
    except ValueError as e:
        print(f"\n[ERROR] Configuration error:")
        print(f"  {e}")
        return

    # Indexer les chunks
    try:
        indexer.index_chunks(chunks, batch_size=50)
    except Exception as e:
        print(f"\n[ERROR] Indexing failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Afficher les statistiques
    print(f"\n{'=' * 80}")
    print("DATABASE STATISTICS")
    print(f"{'=' * 80}")

    stats = indexer.get_stats()
    if stats:
        print(f"\nTotal chunks in database: {stats['total']}")

        print("\nBy domain:")
        for domain, count in sorted(stats['by_domaine'].items()):
            print(f"  {domain}: {count}")

        print("\nBy type:")
        for doc_type, count in sorted(stats['by_type'].items()):
            print(f"  {doc_type}: {count}")

    # Test de recherche
    print(f"\n{'=' * 80}")
    print("TEST SEARCH")
    print(f"{'=' * 80}")

    test_query = "charges récupérables location"
    print(f"\nTest query: '{test_query}'")
    print(f"Searching in domain 'location'...")

    results = indexer.search(
        query=test_query,
        match_count=3,
        filter_domaine='location'
    )

    if results:
        print(f"\n[OK] Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Similarity: {result['similarity']:.4f}")
            print(f"   Source: {result['source_file']}")
            print(f"   Type: {result['type']}")
            print(f"   Sous-themes: {', '.join(result['sous_themes'][:3])}")
            print(f"   Text preview: {result['text'][:200]}...")
    else:
        print("[WARNING] No results found")

    print(f"\n{'=' * 80}")
    print("[OK] INDEXING COMPLETE!")
    print(f"{'=' * 80}\n")


if __name__ == '__main__':
    main()
