"""
Chunker intelligent pour le corpus juridique My Juridic Assistant

Ce script découpe les textes juridiques en chunks de 300-1200 mots tout en:
- Respectant les frontières sémantiques (articles, sections)
- Préservant le contexte (titre, numéro d'article)
- Générant des chunks stables et réutilisables
"""

import re
import os
from pathlib import Path
from typing import List, Dict, Tuple
import json


class LegalChunker:
    """Chunker spécialisé pour les textes juridiques français"""

    def __init__(self, min_words=300, max_words=1200):
        self.min_words = min_words
        self.max_words = max_words

        # Patterns pour identifier les structures juridiques
        self.article_pattern = re.compile(r'^###?\s*(Article|Art\.?)\s+[\d\-]+', re.IGNORECASE | re.MULTILINE)
        self.section_pattern = re.compile(r'^##\s+(.+)$', re.MULTILINE)
        self.title_pattern = re.compile(r'^#\s+(.+)$', re.MULTILINE)

    def count_words(self, text: str) -> int:
        """Compte le nombre de mots dans un texte"""
        return len(text.split())

    def extract_metadata_from_path(self, file_path: Path) -> Dict[str, str]:
        """Extrait les métadonnées basées sur le chemin du fichier"""
        parts = file_path.parts

        # Déterminer la couche (Layer 1, 2, ou 3)
        if '01_sources_text' in parts:
            layer = 'sources_juridiques'
            type_doc = self._determine_type_from_filename(file_path.name)
        elif '02_fiches_ia_ready' in parts:
            layer = 'fiches_ia_ready'
            type_doc = 'fiche'
        elif '03_regles_liaison' in parts:
            layer = 'regles_liaison'
            type_doc = 'regle_liaison'
        else:
            layer = 'unknown'
            type_doc = 'unknown'

        # Déterminer le domaine
        domaine = None
        for part in parts:
            if part in ['copropriete', 'location', 'pro_immo', 'transaction']:
                domaine = part
                break

        return {
            'layer': layer,
            'type': type_doc,
            'domaine': domaine or 'unknown',
            'source_file': file_path.name
        }

    def _determine_type_from_filename(self, filename: str) -> str:
        """Détermine le type de document juridique à partir du nom de fichier"""
        filename_lower = filename.lower()

        if 'loi' in filename_lower:
            return 'loi'
        elif 'decret' in filename_lower or 'décret' in filename_lower:
            return 'decret'
        elif 'code_civil' in filename_lower:
            return 'code_civil'
        elif 'cch' in filename_lower:
            return 'code_construction_habitation'
        elif 'code_conso' in filename_lower:
            return 'code_consommation'
        else:
            return 'texte_juridique'

    def extract_article_number(self, text: str) -> List[str]:
        """Extrait les numéros d'articles présents dans le texte"""
        articles = []

        # Pattern pour capturer "Article X" ou "Art. X"
        pattern = re.compile(r'(?:Article|Art\.?)\s+([\d\-]+(?:\s*à\s*[\d\-]+)?)', re.IGNORECASE)
        matches = pattern.findall(text)

        for match in matches:
            articles.append(match.strip())

        return articles

    def split_by_articles(self, content: str) -> List[Dict[str, str]]:
        """Découpe le contenu en segments basés sur les articles"""
        segments = []

        # Trouver tous les articles
        article_matches = list(self.article_pattern.finditer(content))

        if not article_matches:
            # Pas d'articles détectés, traiter comme un seul segment
            return [{'text': content, 'context': ''}]

        # Extraire le contexte avant le premier article (titres, sections)
        preamble = content[:article_matches[0].start()]
        context = self._extract_context(preamble)

        # Découper par articles
        for i, match in enumerate(article_matches):
            start = match.start()
            end = article_matches[i + 1].start() if i + 1 < len(article_matches) else len(content)

            article_text = content[start:end].strip()
            segments.append({
                'text': article_text,
                'context': context
            })

        return segments

    def _extract_context(self, preamble: str) -> str:
        """Extrait le contexte (titres, sections) du préambule"""
        lines = preamble.strip().split('\n')
        context_lines = []

        for line in lines:
            line = line.strip()
            # Garder les titres et sections
            if line.startswith('#'):
                context_lines.append(line)

        return '\n'.join(context_lines[-3:])  # Garder les 3 derniers niveaux de contexte

    def chunk_text(self, content: str, metadata: Dict[str, str]) -> List[Dict]:
        """Découpe le texte en chunks intelligents"""
        chunks = []

        # Étape 1: Diviser par articles
        article_segments = self.split_by_articles(content)

        # Étape 2: Regrouper les articles en chunks de taille appropriée
        current_chunk = {'text': '', 'context': '', 'articles': []}

        for segment in article_segments:
            segment_words = self.count_words(segment['text'])
            current_words = self.count_words(current_chunk['text'])

            # Si le segment seul dépasse max_words, le découper
            if segment_words > self.max_words:
                # Sauvegarder le chunk actuel s'il existe
                if current_chunk['text']:
                    chunks.append(self._finalize_chunk(current_chunk, metadata))
                    current_chunk = {'text': '', 'context': '', 'articles': []}

                # Découper le segment long en sous-chunks
                sub_chunks = self._split_long_segment(segment, metadata)
                chunks.extend(sub_chunks)
                continue

            # Si l'ajout du segment dépasse max_words, finaliser le chunk actuel
            if current_words + segment_words > self.max_words and current_words >= self.min_words:
                chunks.append(self._finalize_chunk(current_chunk, metadata))
                current_chunk = {'text': '', 'context': segment['context'], 'articles': []}

            # Ajouter le segment au chunk actuel
            if not current_chunk['text']:
                current_chunk['context'] = segment['context']

            current_chunk['text'] += '\n\n' + segment['text'] if current_chunk['text'] else segment['text']

            # Extraire les numéros d'articles
            articles = self.extract_article_number(segment['text'])
            current_chunk['articles'].extend(articles)

        # Finaliser le dernier chunk
        if current_chunk['text']:
            chunks.append(self._finalize_chunk(current_chunk, metadata))

        return chunks

    def _split_long_segment(self, segment: Dict[str, str], metadata: Dict[str, str]) -> List[Dict]:
        """Découpe un segment trop long en sous-chunks"""
        text = segment['text']
        paragraphs = text.split('\n\n')

        chunks = []
        current_chunk = {'text': '', 'context': segment['context'], 'articles': []}

        for para in paragraphs:
            para_words = self.count_words(para)
            current_words = self.count_words(current_chunk['text'])

            if current_words + para_words > self.max_words and current_words >= self.min_words:
                chunks.append(self._finalize_chunk(current_chunk, metadata))
                current_chunk = {'text': '', 'context': segment['context'], 'articles': []}

            current_chunk['text'] += '\n\n' + para if current_chunk['text'] else para
            articles = self.extract_article_number(para)
            current_chunk['articles'].extend(articles)

        if current_chunk['text']:
            chunks.append(self._finalize_chunk(current_chunk, metadata))

        return chunks

    def _finalize_chunk(self, chunk_data: Dict, metadata: Dict[str, str]) -> Dict:
        """Finalise un chunk avec toutes ses métadonnées"""
        full_text = chunk_data['context'] + '\n\n' + chunk_data['text'] if chunk_data['context'] else chunk_data['text']

        return {
            'text': full_text.strip(),
            'metadata': {
                **metadata,
                'articles': list(set(chunk_data['articles'])),  # Dédupliquer
                'word_count': self.count_words(full_text),
                'has_context': bool(chunk_data['context'])
            }
        }

    def process_file(self, file_path: Path) -> List[Dict]:
        """Traite un fichier et retourne ses chunks"""
        print(f"Processing: {file_path}")

        # Lire le contenu
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extraire métadonnées du chemin
        metadata = self.extract_metadata_from_path(file_path)

        # Générer les chunks
        chunks = self.chunk_text(content, metadata)

        print(f"  -> Generated {len(chunks)} chunks")
        return chunks

    def process_corpus(self, corpus_dir: Path) -> List[Dict]:
        """Traite tout le corpus et retourne tous les chunks"""
        all_chunks = []

        # Trouver tous les fichiers .md dans le corpus
        md_files = list(corpus_dir.glob('**/*.md'))

        print(f"Found {len(md_files)} markdown files in corpus")
        print("-" * 80)

        for md_file in md_files:
            chunks = self.process_file(md_file)
            all_chunks.extend(chunks)

        print("-" * 80)
        print(f"Total chunks generated: {len(all_chunks)}")

        return all_chunks


def main():
    """Point d'entrée principal"""
    # Définir les chemins
    base_dir = Path(__file__).parent.parent
    corpus_dir = base_dir / 'Corpus'
    output_dir = base_dir / 'pipeline' / 'output'

    # Créer le dossier de sortie
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialiser le chunker
    chunker = LegalChunker(min_words=300, max_words=1200)

    # Traiter le corpus
    print("=" * 80)
    print("MY JURIDIC ASSISTANT - LEGAL CORPUS CHUNKER")
    print("=" * 80)
    print()

    all_chunks = chunker.process_corpus(corpus_dir)

    # Sauvegarder les chunks
    output_file = output_dir / 'chunks.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print()
    print(f"[OK] Chunks saved to: {output_file}")

    # Statistiques
    print()
    print("=" * 80)
    print("STATISTICS")
    print("=" * 80)

    word_counts = [chunk['metadata']['word_count'] for chunk in all_chunks]
    print(f"Total chunks: {len(all_chunks)}")
    print(f"Average words per chunk: {sum(word_counts) / len(word_counts):.1f}")
    print(f"Min words: {min(word_counts)}")
    print(f"Max words: {max(word_counts)}")

    # Statistiques par domaine
    domains = {}
    for chunk in all_chunks:
        domain = chunk['metadata']['domaine']
        domains[domain] = domains.get(domain, 0) + 1

    print()
    print("Chunks by domain:")
    for domain, count in sorted(domains.items()):
        print(f"  {domain}: {count}")

    # Statistiques par type
    types = {}
    for chunk in all_chunks:
        doc_type = chunk['metadata']['type']
        types[doc_type] = types.get(doc_type, 0) + 1

    print()
    print("Chunks by type:")
    for doc_type, count in sorted(types.items()):
        print(f"  {doc_type}: {count}")


if __name__ == '__main__':
    main()
