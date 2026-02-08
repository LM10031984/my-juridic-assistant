"""
Indexation massive des 110 nouvelles fiches dans Supabase
- Génération des embeddings OpenAI
- Insertion dans legal_chunks
- Mise à jour des search_vectors pour hybrid search
"""

import os
import sys
from pathlib import Path
from openai import OpenAI
from supabase import create_client
from dotenv import load_dotenv
import time

# Encodage UTF-8 pour Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

load_dotenv()

# Clients
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Chemins
CORPUS_DIR = Path(__file__).parent.parent / "Corpus" / "02_fiches_ia_ready"

def get_all_fiches():
    """Récupère toutes les fiches à indexer"""
    fiches = []
    for domaine in ['location', 'copropriete', 'transaction', 'pro_immo']:
        domaine_path = CORPUS_DIR / domaine
        if domaine_path.exists():
            for fiche_path in domaine_path.glob("Fiche_IA_READY_*.md"):
                fiches.append({
                    'path': fiche_path,
                    'domaine': domaine,
                    'filename': fiche_path.name
                })
    return fiches

def extract_metadata(content):
    """Extrait les métadonnées du front matter YAML"""
    import re

    # Extraire le front matter
    match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}

    yaml_content = match.group(1)
    metadata = {}

    # Parser simple (pas besoin de PyYAML pour ce cas)
    for line in yaml_content.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().strip('"')

            # Parser les listes (tags, etc.)
            if value.startswith('[') and value.endswith(']'):
                value = [v.strip().strip('"') for v in value[1:-1].split(',')]

            metadata[key] = value

    return metadata

def index_fiche(fiche_info, index):
    """Indexe une fiche dans Supabase"""
    print(f"\n[{index}] {fiche_info['filename'][:50]}...")

    try:
        # Lire le contenu
        with open(fiche_info['path'], 'r', encoding='utf-8') as f:
            content = f.read()

        print(f"    [OK] Fichier lu ({len(content)} caracteres)")

        # Extraire métadonnées
        metadata = extract_metadata(content)

        # Générer l'embedding
        print(f"    [*] Generation embedding...")
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=content,
            dimensions=768
        )
        embedding = response.data[0].embedding
        print(f"    [OK] Embedding genere (768d)")

        # Préparer les données
        chunk_id = fiche_info['filename'].replace('Fiche_IA_READY_', '').replace('.md', '')[:16]

        chunk_data = {
            "chunk_id": chunk_id,
            "text": content,
            "layer": "fiches_ia_ready",
            "type": "fiche",
            "domaine": fiche_info['domaine'],
            "source_file": fiche_info['filename'],
            "articles": metadata.get('tags', [])[:3] if isinstance(metadata.get('tags'), list) else [],
            "sous_themes": metadata.get('tags', []) if isinstance(metadata.get('tags'), list) else [],
            "keywords": metadata.get('tags', []) if isinstance(metadata.get('tags'), list) else [],
            "word_count": len(content.split()),
            "embedding": embedding
        }

        # Insérer dans Supabase
        print(f"    [*] Insertion Supabase...")
        result = supabase.table('legal_chunks').insert(chunk_data).execute()

        chunk_db_id = result.data[0]['id']
        print(f"    [OK] Insere (ID: {chunk_db_id})")

        return {
            'success': True,
            'id': chunk_db_id,
            'filename': fiche_info['filename']
        }

    except Exception as e:
        print(f"    [ERROR] {str(e)}")
        return {
            'success': False,
            'filename': fiche_info['filename'],
            'error': str(e)
        }

def main():
    """Indexation principale"""
    print("\n" + "="*70)
    print("INDEXATION MASSIVE DES NOUVELLES FICHES")
    print("="*70)

    # Récupérer toutes les fiches
    print("\n[1/3] Recensement des fiches...")
    fiches = get_all_fiches()
    print(f"[OK] {len(fiches)} fiches trouvees")

    by_domaine = {}
    for f in fiches:
        by_domaine[f['domaine']] = by_domaine.get(f['domaine'], 0) + 1

    for domaine, count in by_domaine.items():
        print(f"    - {domaine}: {count} fiches")

    # Indexation
    print(f"\n[2/3] Indexation des {len(fiches)} fiches...")
    print("(Durée estimée: ~{} minutes)".format(len(fiches) * 3 // 60))

    results = []
    start_time = time.time()

    for i, fiche in enumerate(fiches, 1):
        result = index_fiche(fiche, i)
        results.append(result)

        # Pause toutes les 10 fiches pour éviter rate limit
        if i % 10 == 0:
            print(f"\n    [PAUSE] {i}/{len(fiches)} fiches indexees, pause 2s...")
            time.sleep(2)

    elapsed = time.time() - start_time

    # Statistiques
    print("\n" + "="*70)
    print("STATISTIQUES D'INDEXATION")
    print("="*70)

    successes = [r for r in results if r['success']]
    failures = [r for r in results if not r['success']]

    print(f"\n[OK] Succes: {len(successes)}/{len(fiches)}")
    print(f"[ERROR] Echecs: {len(failures)}/{len(fiches)}")
    print(f"[TIME] Duree totale: {elapsed:.1f}s ({elapsed/60:.1f} min)")
    print(f"[TIME] Moyenne: {elapsed/len(fiches):.1f}s par fiche")

    if failures:
        print(f"\n[WARNING] {len(failures)} fiches en echec:")
        for fail in failures[:10]:  # Afficher max 10 erreurs
            print(f"    - {fail['filename']}: {fail.get('error', 'Unknown')}")

    # IDs des chunks insérés
    inserted_ids = [r['id'] for r in successes]
    print(f"\n[INFO] IDs inseres: {min(inserted_ids)} à {max(inserted_ids)}")

    # Sauvegarder les IDs pour mise à jour search_vector
    ids_file = Path(__file__).parent / "inserted_chunk_ids.txt"
    with open(ids_file, 'w') as f:
        f.write('\n'.join(map(str, inserted_ids)))
    print(f"[INFO] IDs sauvegardes dans: {ids_file}")

    print("\n" + "="*70)
    if len(successes) == len(fiches):
        print("[SUCCESS] TOUTES LES FICHES ONT ETE INDEXEES !")
    else:
        print(f"[WARNING] {len(failures)} fiches non indexees")
    print("="*70)

if __name__ == "__main__":
    main()
