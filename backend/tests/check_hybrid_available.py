"""
Test simple pour vérifier si hybrid_search_rrf existe
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

supabase = create_client(supabase_url, supabase_key)

print("Test 1: Vérification de la fonction hybrid_search_rrf...")

try:
    # Tester avec des paramètres minimaux
    test_embedding = [0.1] * 768

    result = supabase.rpc(
        'hybrid_search_rrf',
        {
            'query_text': 'test',
            'query_embedding': test_embedding,
            'match_count': 1
        }
    ).execute()

    print(f"✅ Fonction hybrid_search_rrf existe !")
    print(f"   Résultats: {len(result.data)} chunks")

except Exception as e:
    print(f"❌ Erreur: {str(e)}")
    print(f"   Type: {type(e).__name__}")

    if 'does not exist' in str(e).lower() or 'function' in str(e).lower():
        print("   → La fonction n'existe pas en base")
    else:
        print("   → Autre erreur")

print("\nTest 2: Vérification de la colonne search_vector...")

try:
    result = supabase.table('legal_chunks').select('search_vector').limit(1).execute()

    if result.data and result.data[0].get('search_vector'):
        print(f"✅ Colonne search_vector existe et est peuplée !")
    else:
        print(f"⚠️  Colonne existe mais vide")

except Exception as e:
    print(f"❌ Erreur: {str(e)}")
