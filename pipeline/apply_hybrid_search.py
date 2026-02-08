"""
Script pour appliquer le setup hybrid search à Supabase
========================================================

Ce script applique automatiquement le fichier setup_hybrid_search.sql
à votre base de données Supabase.

Usage :
    python apply_hybrid_search.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Fix pour l'encodage Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Charger les variables d'environnement
load_dotenv()


def apply_hybrid_search_setup():
    """Applique le setup hybrid search à Supabase"""

    # Récupérer les credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ ERREUR : Variables SUPABASE_URL et SUPABASE_KEY manquantes")
        print("   Vérifiez votre fichier .env")
        sys.exit(1)

    print("="*70)
    print("APPLICATION DU HYBRID SEARCH SETUP")
    print("="*70)
    print(f"\nConnexion à Supabase : {supabase_url}")

    # Créer le client Supabase
    supabase: Client = create_client(supabase_url, supabase_key)

    # Lire le fichier SQL
    sql_file = Path(__file__).parent / "setup_hybrid_search.sql"

    if not sql_file.exists():
        print(f"❌ ERREUR : Fichier {sql_file} introuvable")
        sys.exit(1)

    print(f"📄 Lecture de : {sql_file}")

    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    print(f"   Taille du script : {len(sql_content)} caractères")

    # Exécuter le SQL via RPC
    print("\n🔄 Exécution du script SQL...")
    print("   (cela peut prendre quelques secondes)")

    try:
        # Note: Supabase Python client ne supporte pas directement l'exécution de SQL
        # Il faut soit :
        # 1. Utiliser psycopg2 directement avec la connection string
        # 2. Exécuter manuellement dans Supabase SQL Editor
        # 3. Utiliser Supabase CLI

        print("\n⚠️  IMPORTANT :")
        print("   Le client Python Supabase ne supporte pas l'exécution de SQL brut.")
        print("\n📋 Veuillez suivre ces étapes :")
        print("\n1. Ouvrez Supabase SQL Editor :")
        print(f"   {supabase_url.replace('https://', 'https://app.')}/sql")
        print("\n2. Copiez tout le contenu de ce fichier :")
        print(f"   {sql_file}")
        print("\n3. Collez et exécutez dans l'éditeur SQL")
        print("\n4. Vérifiez que vous voyez le message de confirmation")
        print("\nOU utilisez psycopg2 pour une application automatique.")

        # Alternative : Proposer d'utiliser psycopg2
        print("\n" + "="*70)
        print("ALTERNATIVE : Installation automatique avec psycopg2")
        print("="*70)

        try:
            import psycopg2
            use_psycopg2 = input("\nUtiliser psycopg2 pour appliquer automatiquement ? (y/n) : ").lower()

            if use_psycopg2 == 'y':
                # Demander la connection string
                print("\nVous devez fournir la connection string PostgreSQL.")
                print("Format : postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres")
                print("\nTrouvez-la dans : Supabase Dashboard > Settings > Database > Connection string > URI")

                conn_string = input("\nConnection string : ").strip()

                if conn_string:
                    apply_with_psycopg2(conn_string, sql_content)
                else:
                    print("❌ Connection string vide, annulation")

        except ImportError:
            print("\n💡 Pour une installation automatique, installez psycopg2 :")
            print("   pip install psycopg2-binary")

    except Exception as e:
        print(f"\n❌ Erreur : {str(e)}")
        import traceback
        traceback.print_exc()


def apply_with_psycopg2(conn_string: str, sql_content: str):
    """Applique le SQL via psycopg2"""
    import psycopg2

    print("\n🔄 Connexion à PostgreSQL...")

    try:
        conn = psycopg2.connect(conn_string)
        conn.autocommit = True
        cursor = conn.cursor()

        print("✓ Connecté")
        print("\n🔄 Exécution du script SQL...")

        # Exécuter le script SQL
        cursor.execute(sql_content)

        print("✓ Script exécuté avec succès !")

        # Vérifier les résultats
        print("\n📊 Vérification :")
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(search_vector) as with_search_vector
            FROM legal_chunks
        """)

        row = cursor.fetchone()
        total, with_sv = row

        print(f"   • Total chunks : {total}")
        print(f"   • Chunks avec search_vector : {with_sv}")

        if total == with_sv:
            print("\n✅ SUCCÈS : Hybrid search configuré correctement !")
        else:
            print(f"\n⚠️  ATTENTION : {total - with_sv} chunks sans search_vector")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"\n❌ Erreur lors de l'exécution : {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    apply_hybrid_search_setup()
