"""
Indexeur Supabase pour My Juridic Assistant

Ce script :
1. Charge les chunks enrichis
2. Génère les embeddings via OpenAI
3. Insère les chunks dans Supabase avec pgvector
4. Permet la recherche vectorielle avec filtres métadonnées
"""

import json
import os
import time
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

try:
    from supabase import create_client, Client
    from openai import OpenAI
except ImportError as e:
    print(f"Error: Missing dependencies. Please install requirements:")
    print(f"  pip install -r requirements.txt")
    print(f"\nMissing: {e}")
    exit(1)


class SupabaseIndexer:
    """Indexe les chunks juridiques dans Supabase avec embeddings"""

    def __init__(self):
        # Charger les variables d'environnement
        load_dotenv()

        # Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')

        if not supabase_url or not supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY must be set in .env file\n"
                "Copy .env.example to .env and fill in your credentials"
            )

        self.supabase: Client = create_client(supabase_url, supabase_key)

        # OpenAI client for embeddings
        openai_key = os.getenv('OPENAI_API_KEY')
        if not openai_key:
            raise ValueError(
                "OPENAI_API_KEY must be set in .env file\n"
                "Get your API key from https://platform.openai.com/api-keys"
            )

        self.openai_client = OpenAI(api_key=openai_key)
        self.embedding_model = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
        self.embedding_dimension = int(os.getenv('EMBEDDING_DIMENSION', '1536'))

        print(f"[OK] Connected to Supabase: {supabase_url}")
        print(f"[OK] Using embedding model: {self.embedding_model}")

    def generate_embedding(self, text: str) -> List[float]:
        """Génère un embedding pour un texte via OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"\n[ERROR] Failed to generate embedding: {e}")
            raise

    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Génère des embeddings par batch pour économiser les API calls"""
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            print(f"  Generating embeddings for batch {i // batch_size + 1} ({len(batch)} texts)...", end='\r')

            try:
                response = self.openai_client.embeddings.create(
                    model=self.embedding_model,
                    input=batch
                )
                batch_embeddings = [data.embedding for data in response.data]
                embeddings.extend(batch_embeddings)

                # Rate limiting
                time.sleep(0.5)

            except Exception as e:
                print(f"\n[ERROR] Batch {i // batch_size + 1} failed: {e}")
                raise

        print()  # New line after progress
        return embeddings

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

    def index_chunks(self, chunks: List[Dict], batch_size: int = 100):
        """Indexe les chunks dans Supabase"""
        total = len(chunks)
        print(f"\n{'=' * 80}")
        print(f"INDEXING {total} CHUNKS TO SUPABASE")
        print(f"{'=' * 80}\n")

        # Étape 1: Générer tous les embeddings
        print(f"[1/2] Generating embeddings...")
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.generate_embeddings_batch(texts, batch_size=batch_size)
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
        query_embedding = self.generate_embedding(query)

        # Appeler la fonction Supabase
        try:
            response = self.supabase.rpc(
                'search_legal_chunks',
                {
                    'query_embedding': query_embedding,
                    'match_count': match_count,
                    'filter_domaine': filter_domaine,
                    'filter_type': filter_type,
                    'filter_layer': filter_layer
                }
            ).execute()

            return response.data

        except Exception as e:
            print(f"[ERROR] Search failed: {e}")
            return []

    def get_stats(self) -> Dict:
        """Récupère les statistiques de la base de données"""
        try:
            # Compter le total
            total_response = self.supabase.table('legal_chunks')\
                .select('id', count='exact')\
                .execute()
            total = total_response.count

            # Compter par domaine
            domaine_response = self.supabase.table('legal_chunks')\
                .select('domaine')\
                .execute()

            domaines = {}
            for record in domaine_response.data:
                dom = record['domaine']
                domaines[dom] = domaines.get(dom, 0) + 1

            # Compter par type
            type_response = self.supabase.table('legal_chunks')\
                .select('type')\
                .execute()

            types = {}
            for record in type_response.data:
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
    print("MY JURIDIC ASSISTANT - SUPABASE INDEXER")
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
        indexer = SupabaseIndexer()
    except ValueError as e:
        print(f"\n[ERROR] Configuration error:")
        print(f"  {e}")
        return

    # Indexer les chunks
    try:
        indexer.index_chunks(chunks, batch_size=50)
    except Exception as e:
        print(f"\n[ERROR] Indexing failed: {e}")
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
