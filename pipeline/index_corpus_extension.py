"""
Script pour indexer les 5 nouveaux fichiers du corpus (extension Phase 1)
- 2 fiches DPE/passoires énergétiques (location)
- 2 fiches vices cachés (transaction)
- 1 fiche charges copropriété (copropriete)
"""

import os
import sys
from pathlib import Path
from supabase import create_client
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Définir les fichiers à indexer
FILES_TO_INDEX = [
    {
        "path": "../Corpus/02_fiches_ia_ready/location/Fiche_IA_READY_Passoires_Energetiques_Interdiction_2023.md",
        "chunk_id": "passoires_2023",
        "layer": "fiches_ia_ready",
        "type": "fiche",
        "domaine": "location",
        "source_file": "Fiche_IA_READY_Passoires_Energetiques_Interdiction_2023.md",
        "articles": ["L173-1-1", "Article 160 Loi Climat"],
        "sous_themes": ["DPE", "passoires énergétiques", "interdiction", "location", "décence", "G", "F", "E"],
        "keywords": ["passoire énergétique", "DPE", "interdiction", "louer", "G", "F", "classe énergétique", "2025", "2028", "2034"]
    },
    {
        "path": "../Corpus/02_fiches_ia_ready/location/Fiche_IA_READY_Decence_Energetique.md",
        "chunk_id": "decence_energ",
        "layer": "fiches_ia_ready",
        "type": "fiche",
        "domaine": "location",
        "source_file": "Fiche_IA_READY_Decence_Energetique.md",
        "articles": ["Article 6 Loi 1989", "L173-1-1"],
        "sous_themes": ["décence", "DPE", "énergie", "indécence", "450 kWh"],
        "keywords": ["décence", "indécent", "DPE", "énergie", "performance énergétique", "450 kWh", "commission conciliation"]
    },
    {
        "path": "../Corpus/02_fiches_ia_ready/transaction/Fiche_IA_READY_Vices_Caches_Delais.md",
        "chunk_id": "vice_delais",
        "layer": "fiches_ia_ready",
        "type": "fiche",
        "domaine": "transaction",
        "source_file": "Fiche_IA_READY_Vices_Caches_Delais.md",
        "articles": ["1648", "1641", "1644"],
        "sous_themes": ["vices cachés", "délai", "prescription", "2 ans", "découverte"],
        "keywords": ["vice caché", "délai", "2 ans", "prescription", "découverte", "action rédhibitoire", "action estimatoire"]
    },
    {
        "path": "../Corpus/02_fiches_ia_ready/transaction/Fiche_IA_READY_Vices_Caches_Types.md",
        "chunk_id": "vice_types",
        "layer": "fiches_ia_ready",
        "type": "fiche",
        "domaine": "transaction",
        "source_file": "Fiche_IA_READY_Vices_Caches_Types.md",
        "articles": ["1641", "1642", "1643", "1644"],
        "sous_themes": ["vices cachés", "types", "infiltrations", "mérule", "termites", "amiante", "plomb", "fissures"],
        "keywords": ["vice caché", "infiltration", "mérule", "termites", "amiante", "plomb", "fissures", "malfaçons", "assainissement"]
    },
    {
        "path": "../Corpus/02_fiches_ia_ready/copropriete/Fiche_IA_READY_Charges_Repartition.md",
        "chunk_id": "charges_repart",
        "layer": "fiches_ia_ready",
        "type": "fiche",
        "domaine": "copropriete",
        "source_file": "Fiche_IA_READY_Charges_Repartition.md",
        "articles": ["10", "10-1", "24", "25", "26", "19-1"],
        "sous_themes": ["charges", "répartition", "tantièmes", "copropriété", "assemblée générale"],
        "keywords": ["charges", "répartition", "tantièmes", "copropriété", "ravalement", "façade", "ascenseur", "chauffage collectif", "impayés"]
    }
]

def index_file(file_info):
    """Indexe un fichier dans Supabase"""
    print(f"\n{'='*70}")
    print(f"[*] Indexation : {file_info['source_file']}")
    print(f"{'='*70}")

    # Lire le fichier
    try:
        with open(file_info['path'], 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"[OK] Fichier lu : {len(content)} caracteres")
    except FileNotFoundError:
        print(f"[ERROR] Fichier introuvable : {file_info['path']}")
        return False

    # Générer l'embedding
    print("[*] Generation de l'embedding avec OpenAI...")
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=content,
            dimensions=768
        )
        embedding = response.data[0].embedding
        print(f"[OK] Embedding genere : {len(embedding)} dimensions")
    except Exception as e:
        print(f"[ERROR] Erreur lors de la generation de l'embedding : {e}")
        return False

    # Préparer les données
    chunk_data = {
        "chunk_id": file_info['chunk_id'],
        "text": content,
        "layer": file_info['layer'],
        "type": file_info['type'],
        "domaine": file_info['domaine'],
        "source_file": file_info['source_file'],
        "articles": file_info['articles'],
        "sous_themes": file_info['sous_themes'],
        "keywords": file_info['keywords'],
        "word_count": len(content.split()),
        "embedding": embedding
    }

    # Insérer dans Supabase
    print("[*] Insertion dans Supabase...")
    try:
        result = supabase.table('legal_chunks').insert(chunk_data).execute()
        print(f"[OK] SUCCES ! Chunk insere avec l'ID : {result.data[0]['id']}")
        print(f"    Domaine : {result.data[0]['domaine']}")
        print(f"    Mots : {result.data[0]['word_count']}")
        return True
    except Exception as e:
        print(f"[ERROR] Erreur lors de l'insertion : {e}")
        return False


def main():
    """Indexe tous les nouveaux fichiers"""
    print("\n" + "="*70)
    print("INDEXATION DES NOUVEAUX FICHIERS DU CORPUS")
    print("="*70)
    print(f"\nNombre de fichiers a indexer : {len(FILES_TO_INDEX)}")

    successes = 0
    failures = 0

    for file_info in FILES_TO_INDEX:
        success = index_file(file_info)
        if success:
            successes += 1
        else:
            failures += 1

    # Résumé
    print("\n" + "="*70)
    print("RESUME DE L'INDEXATION")
    print("="*70)
    print(f"[OK] Succes : {successes}/{len(FILES_TO_INDEX)}")
    print(f"[ERROR] Echecs : {failures}/{len(FILES_TO_INDEX)}")

    if failures == 0:
        print("\n[SUCCESS] TOUS LES FICHIERS ONT ETE INDEXES AVEC SUCCES !")
    else:
        print(f"\n[WARNING] {failures} fichier(s) n'ont pas pu etre indexes.")
        sys.exit(1)


if __name__ == "__main__":
    main()
