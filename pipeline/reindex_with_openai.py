"""
Script de re-indexation avec OpenAI Embeddings
Remplace les embeddings sentence-transformers par des embeddings OpenAI
"""

import os
import json
from supabase import create_client
from openai import OpenAI
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Initialize clients
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
openai_key = os.getenv('OPENAI_API_KEY')

if not all([supabase_url, supabase_key, openai_key]):
    raise ValueError("Missing environment variables")

supabase = create_client(supabase_url, supabase_key)
openai_client = OpenAI(api_key=openai_key)

print("Demarrage de la re-indexation avec OpenAI Embeddings")
print(f"Supabase: {supabase_url}")
print(f"OpenAI: Utilisation de text-embedding-3-small (768d)")
print()

# Recuperer tous les chunks
print("Recuperation des chunks depuis Supabase...")
response = supabase.table('legal_chunks').select('*').execute()
chunks = response.data

print(f"OK - {len(chunks)} chunks recuperes")
print()

# Re-indexer chaque chunk
success_count = 0
error_count = 0

for i, chunk in enumerate(chunks, 1):
    try:
        chunk_id = chunk['id']
        content = chunk['text']  # Fixed: field is 'text', not 'content'

        print(f"[{i}/{len(chunks)}] Processing chunk {chunk_id}...")

        # Generer embedding avec OpenAI
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=content,
            dimensions=768  # Compatible avec la base
        )

        new_embedding = response.data[0].embedding

        # Mettre a jour dans Supabase
        supabase.table('legal_chunks').update({
            'embedding': new_embedding
        }).eq('id', chunk_id).execute()

        success_count += 1
        print(f"   OK - Updated successfully")

        # Rate limiting (eviter de depasser les limites OpenAI)
        if i % 10 == 0:
            print(f"   Pause (rate limiting)...")
            time.sleep(1)

    except Exception as e:
        error_count += 1
        print(f"   ERROR: {e}")
        continue

print()
print("=" * 60)
print("Re-indexation terminee!")
print(f"Succes: {success_count}/{len(chunks)}")
print(f"Erreurs: {error_count}/{len(chunks)}")
print("=" * 60)
