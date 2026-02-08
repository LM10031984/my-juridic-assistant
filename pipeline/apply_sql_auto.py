"""
Script automatique pour appliquer setup_hybrid_search.sql
"""
import os
import sys
from pathlib import Path

# Fix encodage Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Construire la connection string
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
host = SUPABASE_URL.replace('https://', '').replace('.supabase.co', '')

# Demander le mot de passe
print("Pour appliquer le SQL, j'ai besoin de la connection string PostgreSQL.")
print(f"\nTrouvez-la dans : Supabase Dashboard > Settings > Database > Connection string > URI")
print(f"\nFormat attendu : postgresql://postgres:[PASSWORD]@{host}.supabase.co:5432/postgres")

conn_string = input("\nCollez la connection string PostgreSQL ici : ").strip()

if not conn_string:
    print("❌ Connection string vide, annulation.")
    sys.exit(1)

# Lire le fichier SQL
sql_file = Path(__file__).parent / "setup_hybrid_search.sql"
with open(sql_file, 'r', encoding='utf-8') as f:
    sql_content = f.read()

print(f"\n🔄 Connexion à PostgreSQL...")

try:
    conn = psycopg2.connect(conn_string)
    conn.autocommit = True
    cursor = conn.cursor()

    print("✅ Connecté !")
    print("\n🔄 Exécution du SQL (cela peut prendre 10-20 secondes)...")

    cursor.execute(sql_content)

    print("\n✅ SQL exécuté avec succès !")

    # Vérification
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(search_vector) as with_sv
        FROM legal_chunks
    """)

    total, with_sv = cursor.fetchone()
    print(f"\n📊 Vérification :")
    print(f"   Total chunks : {total}")
    print(f"   Avec search_vector : {with_sv}")

    if total == with_sv:
        print("\n🎉 SUCCÈS : Hybrid search configuré !")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"\n❌ Erreur : {str(e)}")
    sys.exit(1)
