"""
Enrichisseur de métadonnées pour les chunks juridiques

Ce script enrichit les chunks générés avec des métadonnées supplémentaires :
- sous-thème (détecté automatiquement)
- version_date (extrait du contenu)
- section_title (titre de section contextuel)
- keywords (mots-clés juridiques)
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set


class MetadataEnricher:
    """Enrichit les métadonnées des chunks juridiques"""

    def __init__(self):
        # Mapping de mots-clés vers sous-thèmes par domaine
        self.sous_themes = {
            'copropriete': {
                'assemblée générale': ['assemblée', 'ag', 'convocation', 'vote', 'majorité', 'procès-verbal'],
                'syndic': ['syndic', 'gestion', 'administration', 'mandat'],
                'charges': ['charges', 'appel de fonds', 'répartition', 'tantièmes'],
                'travaux': ['travaux', 'entretien', 'réparation', 'amélioration'],
                'règlement': ['règlement de copropriété', 'parties communes', 'parties privatives'],
                'contestation': ['contestation', 'tribunal', 'recours', 'délai'],
            },
            'location': {
                'bail': ['bail', 'contrat', 'location', 'durée', 'résidence principale'],
                'loyer': ['loyer', 'révision', 'augmentation', 'encadrement'],
                'charges': ['charges', 'récupérable', 'régularisation', 'provisions'],
                'décence': ['décence', 'habitabilité', 'salubrité', 'surface'],
                'dpe': ['dpe', 'performance énergétique', 'classe énergétique', 'passoire'],
                'congé': ['congé', 'préavis', 'résiliation', 'renouvellement'],
                'dépôt': ['dépôt de garantie', 'caution', 'restitution'],
                'réparations': ['réparations', 'entretien', 'travaux', 'locataire'],
            },
            'pro_immo': {
                'carte professionnelle': ['carte', 'professionnel', 'titre', 'délivrance'],
                'mandat': ['mandat', 'contrat', 'écrit', 'durée', 'exclusivité'],
                'honoraires': ['honoraires', 'rémunération', 'commission', 'affichage'],
                'garantie': ['garantie financière', 'rcp', 'assurance'],
                'maniement fonds': ['fonds', 'dépôt', 'compte', 'registre'],
                'obligations': ['information', 'publicité', 'transparence', 'affichage'],
            },
            'transaction': {
                'vente': ['vente', 'prix', 'compromis', 'promesse', 'acte authentique'],
                'vice caché': ['vice', 'caché', 'défaut', 'conformité'],
                'dpe': ['dpe', 'diagnostic', 'performance', 'annonce'],
                'responsabilité': ['responsabilité', 'faute', 'dommage', 'préjudice'],
                'crédit': ['crédit', 'prêt', 'financement', 'condition suspensive'],
                'clause': ['clause', 'condition', 'délai', 'pénale'],
            }
        }

        # Pattern pour extraire les dates de version
        self.date_patterns = [
            re.compile(r'Version\s+en\s+vigueur\s+(?:au|depuis\s+le)\s+(\d{1,2}\s+\w+\s+\d{4})', re.IGNORECASE),
            re.compile(r'Consolidé\s+(\d{4})', re.IGNORECASE),
            re.compile(r'Texte\s+Consolidé\s+(\d{4})', re.IGNORECASE),
            re.compile(r'(\d{1,2}/\d{1,2}/\d{4})'),
        ]

    def detect_sous_theme(self, text: str, domaine: str) -> List[str]:
        """Détecte les sous-thèmes présents dans le texte"""
        text_lower = text.lower()
        detected = []

        if domaine not in self.sous_themes:
            return []

        for sous_theme, keywords in self.sous_themes[domaine].items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    detected.append(sous_theme)
                    break  # Un seul match par sous-thème suffit

        return detected

    def extract_version_date(self, text: str) -> str:
        """Extrait la date de version du texte"""
        for pattern in self.date_patterns:
            match = pattern.search(text)
            if match:
                return match.group(1)
        return None

    def extract_section_title(self, text: str) -> str:
        """Extrait le titre de section principal"""
        lines = text.split('\n')

        for line in lines[:10]:  # Chercher dans les 10 premières lignes
            line = line.strip()
            # Chercher les titres markdown (# ou ##)
            if line.startswith('# '):
                return line.lstrip('#').strip()
            elif line.startswith('## '):
                return line.lstrip('#').strip()

        return None

    def extract_keywords(self, text: str) -> List[str]:
        """Extrait les mots-clés juridiques importants"""
        keywords = []

        # Pattern pour les articles
        article_pattern = re.compile(r'(?:Article|Art\.?)\s+([\d\-]+)', re.IGNORECASE)
        articles = article_pattern.findall(text)
        keywords.extend([f"Article {art}" for art in articles[:5]])  # Max 5 articles

        # Termes juridiques fréquents
        legal_terms = [
            'obligation', 'responsabilité', 'garantie', 'charge', 'délai',
            'sanction', 'interdiction', 'droit', 'devoir', 'condition'
        ]

        text_lower = text.lower()
        for term in legal_terms:
            if term in text_lower and term not in keywords:
                keywords.append(term)

        return keywords[:10]  # Limiter à 10 mots-clés

    def enrich_chunk(self, chunk: Dict) -> Dict:
        """Enrichit un chunk avec des métadonnées supplémentaires"""
        text = chunk['text']
        metadata = chunk['metadata']

        # Détecter sous-thèmes
        sous_themes = self.detect_sous_theme(text, metadata['domaine'])
        metadata['sous_themes'] = sous_themes

        # Extraire date de version
        version_date = self.extract_version_date(text)
        if version_date:
            metadata['version_date'] = version_date

        # Extraire titre de section
        section_title = self.extract_section_title(text)
        if section_title:
            metadata['section_title'] = section_title

        # Extraire mots-clés
        keywords = self.extract_keywords(text)
        metadata['keywords'] = keywords

        # Ajouter un ID unique
        import hashlib
        chunk_id = hashlib.md5(text.encode('utf-8')).hexdigest()[:16]
        metadata['chunk_id'] = chunk_id

        return chunk

    def enrich_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Enrichit tous les chunks"""
        enriched = []

        for i, chunk in enumerate(chunks):
            print(f"Enriching chunk {i + 1}/{len(chunks)}", end='\r')
            enriched_chunk = self.enrich_chunk(chunk)
            enriched.append(enriched_chunk)

        print(f"\n[OK] Enriched {len(enriched)} chunks")
        return enriched


def main():
    """Point d'entrée principal"""
    base_dir = Path(__file__).parent
    input_file = base_dir / 'output' / 'chunks.json'
    output_file = base_dir / 'output' / 'chunks_enriched.json'

    print("=" * 80)
    print("MY JURIDIC ASSISTANT - METADATA ENRICHER")
    print("=" * 80)
    print()

    # Charger les chunks
    print(f"Loading chunks from: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    print(f"Loaded {len(chunks)} chunks")
    print()

    # Enrichir
    enricher = MetadataEnricher()
    enriched_chunks = enricher.enrich_chunks(chunks)

    # Sauvegarder
    print()
    print(f"Saving enriched chunks to: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(enriched_chunks, f, ensure_ascii=False, indent=2)

    print()
    print("=" * 80)
    print("ENRICHMENT STATISTICS")
    print("=" * 80)

    # Statistiques sur les sous-thèmes
    sous_themes_count = {}
    for chunk in enriched_chunks:
        for st in chunk['metadata'].get('sous_themes', []):
            sous_themes_count[st] = sous_themes_count.get(st, 0) + 1

    print()
    print("Top 10 sous-themes:")
    for st, count in sorted(sous_themes_count.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {st}: {count}")

    # Statistiques sur les dates
    with_dates = sum(1 for c in enriched_chunks if 'version_date' in c['metadata'])
    print()
    print(f"Chunks with version_date: {with_dates}/{len(enriched_chunks)}")

    # Statistiques sur les titres
    with_titles = sum(1 for c in enriched_chunks if 'section_title' in c['metadata'])
    print(f"Chunks with section_title: {with_titles}/{len(enriched_chunks)}")

    print()
    print("[OK] Enrichment complete!")


if __name__ == '__main__':
    main()
