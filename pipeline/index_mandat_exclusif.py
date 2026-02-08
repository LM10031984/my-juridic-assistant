"""
Script pour indexer le nouveau chunk sur le mandat exclusif et vente directe
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
file_path = "../Corpus/02_fiches_ia_ready/pro_immo/Fiche_IA_READY_Mandat_Exclusif_Vente_Directe.md"
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
    "chunk_id": "mandat_excl_full",
    "text": content,
    "layer": "fiches_ia_ready",
    "type": "fiche",
    "domaine": "pro_immo",
    "source_file": "Fiche_IA_READY_Mandat_Exclusif_Vente_Directe.md",
    "articles": ["L70-9 Art 6", "L70-9 Art 7", "D72-678 Art 6", "1984", "1991-2010", "1217", "1231-5", "2224"],
    "sous_themes": ["mandat", "exclusif", "vente directe", "commission", "agent immobilier", "recours", "loi Hoguet"],
    "keywords": ["mandat exclusif", "vente directe", "commission", "agent immobilier", "loi Hoguet", "recours", "clause penale", "indemnite"],
    "word_count": len(content.split()),
    "embedding": embedding
}

# Inserer dans Supabase
print("Insertion dans Supabase...")
result = supabase.table('legal_chunks').insert(chunk_data).execute()

print(f"\nSUCCES ! Chunk insere avec l'ID: {result.data[0]['id']}")
print(f"Source: {result.data[0]['source_file']}")
print(f"Domaine: {result.data[0]['domaine']}")
