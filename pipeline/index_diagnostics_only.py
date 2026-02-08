"""
Indexation UNIQUEMENT des fiches du dossier diagnostics/
"""

import os, sys
from pathlib import Path
from openai import OpenAI
from supabase import create_client
from dotenv import load_dotenv
import time

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

load_dotenv()

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

DIAGNOSTICS_DIR = Path(__file__).parent.parent / "Corpus" / "02_fiches_ia_ready" / "diagnostics"

print("\n" + "="*70)
print("INDEXATION FICHES DIAGNOSTICS UNIQUEMENT")
print("="*70)

fiches = list(DIAGNOSTICS_DIR.glob("Fiche_IA_READY_*.md"))
print(f"\n[INFO] {len(fiches)} fiches trouvées dans diagnostics/\n")

results = []
for i, fiche_path in enumerate(fiches, 1):
    print(f"[{i}/{len(fiches)}] {fiche_path.name[:50]}...")

    try:
        with open(fiche_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Générer embedding
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=content,
            dimensions=768
        )
        embedding = response.data[0].embedding

        # Préparer données (chunk_id court : DIAG_001, DIAG_002, etc.)
        chunk_id = f"DIAG_{i:03d}"  # Format: DIAG_001, DIAG_002, ..., DIAG_025

        chunk_data = {
            "chunk_id": chunk_id,
            "text": content,
            "layer": "fiches_ia_ready",
            "type": "fiche",
            "domaine": "diagnostics",
            "source_file": fiche_path.name,
            "word_count": len(content.split()),
            "embedding": embedding
        }

        # Insérer
        result = supabase.table('legal_chunks').insert(chunk_data).execute()
        chunk_db_id = result.data[0]['id']

        print(f"    [OK] ID: {chunk_db_id}")
        results.append({'success': True, 'id': chunk_db_id})

    except Exception as e:
        error_msg = str(e)
        if 'duplicate key' in error_msg:
            print(f"    [SKIP] Déjà indexé")
            results.append({'success': False, 'error': 'duplicate'})
        else:
            print(f"    [ERROR] {error_msg[:100]}")
            results.append({'success': False, 'error': error_msg})

    if i % 10 == 0 and i < len(fiches):
        time.sleep(1)

print("\n" + "="*70)
successes = [r for r in results if r.get('success')]
duplicates = [r for r in results if r.get('error') == 'duplicate']
errors = [r for r in results if r.get('error') and r.get('error') != 'duplicate']

print(f"[OK] Nouvelles fiches indexées : {len(successes)}")
print(f"[SKIP] Déjà en base : {len(duplicates)}")
print(f"[ERROR] Erreurs : {len(errors)}")
print("="*70)
