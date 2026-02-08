"""
Script pour indexer le nouveau chunk sur les passoires énergétiques
"""

import os
from supabase import create_client
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Lire le nouveau fichier
file_path = "../Corpus/02_fiches_ia_ready/location/Fiche_IA_READY_Passoires_Energetiques_Interdiction_Location.md"
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Fichier lu: {len(content)} caracteres")

# Generer l'embedding
print("Generation de l'embedding avec OpenAI...")
response = openai_client.embeddings.create(
    model="text-embedding-3-small",
    input=content,
    dimensions=768
)
embedding = response.data[0].embedding

print(f"Embedding genere: {len(embedding)} dimensions")

# Preparer les donnees
chunk_data = {
    "chunk_id": "passoire_energ",
    "text": content,
    "layer": "fiches_ia_ready",
    "type": "fiche",
    "domaine": "location",
    "source_file": "Fiche_IA_READY_Passoires_Energetiques_Interdiction_Location.md",
    "articles": ["L173-1-1", "L126-26", "L126-33", "Loi 1989 Art 6", "Loi 1989 Art 17", "Loi 1989 Art 17-2"],
    "sous_themes": ["passoire énergétique", "DPE", "classe G", "classe F", "interdiction location", "gel loyer", "rénovation énergétique"],
    "keywords": ["passoire énergétique", "logement G", "logement F", "interdiction", "location", "DPE", "gel loyer", "2025", "loi climat", "rénovation"],
    "word_count": len(content.split()),
    "embedding": embedding
}

# Inserer dans Supabase
print("Insertion dans Supabase...")
result = supabase.table('legal_chunks').insert(chunk_data).execute()

print(f"\nSUCCES ! Chunk insere avec l'ID: {result.data[0]['id']}")
print(f"Source: {result.data[0]['source_file']}")
print(f"Domaine: {result.data[0]['domaine']}")
