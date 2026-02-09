"""
Mark Fiches as Needs Human - Hybrid Approach
Adds needs_human markers to fiches that require corpus enrichment.
"""

from pathlib import Path
import re


def mark_fiche_needs_human(file_path: Path, reason: str, missing_articles: list) -> bool:
    """Adds needs_human marker to a fiche"""

    content = file_path.read_text(encoding='utf-8')

    # Check if already marked
    if 'needs_human' in content.lower():
        print(f"  [SKIP] Already marked: {file_path.name}")
        return False

    # Find BASE JURIDIQUE section
    base_match = re.search(r'(##\s*BASE JURIDIQUE.*?)(\n---|\n##|\Z)', content, re.DOTALL | re.IGNORECASE)

    if not base_match:
        print(f"  [SKIP] No BASE JURIDIQUE section: {file_path.name}")
        return False

    base_section = base_match.group(1)
    after_base = base_match.group(2)

    # Add needs_human note to BASE JURIDIQUE section
    articles_str = ", ".join(missing_articles)
    needs_human_note = f"""

> **⚠️ NEEDS HUMAN REVIEW** : Articles manquants dans le corpus indexé: {articles_str}
>
> **Raison** : {reason}
>
> **Action requise** : Ajouter ces articles aux sources primaires puis ré-indexer.
> Voir: `backend/reports/missing_articles_report.md`
"""

    # Insert note before the separator
    updated_base = base_section + needs_human_note

    # Reconstruct content
    before_base = content[:base_match.start()]
    after_base_pos = base_match.end()
    rest_of_content = content[after_base_pos:]

    updated_content = before_base + updated_base + after_base + rest_of_content

    # Write updated content
    file_path.write_text(updated_content, encoding='utf-8')

    print(f"  [OK] Marked: {file_path.name}")
    return True


def main():
    """Main execution"""
    base_dir = Path(__file__).parent.parent.parent
    fiches_dir = base_dir / 'Corpus' / 'clean' / 'fiches_updated'

    # Define fiches that need human review
    needs_human_fiches = {
        'diagnostics/Fiche_IA_READY_DPE_04_Erreur_Recours.md': {
            'reason': 'Article L271-4 du CCH absent du corpus',
            'missing': ['L271-4']
        },
        'diagnostics/Fiche_IA_READY_DPE_05_Travaux_Renovation.md': {
            'reason': 'Articles L126-35-x du CCH (rénovation énergétique) absents',
            'missing': ['L126-35-4', 'L126-35-6', 'L126-35-7', 'L126-35-10', 'L126-35-11']
        },
        'location/Fiche_IA_READY_Passoires_Energetiques_Interdiction_2023.md': {
            'reason': 'Articles 149, 159 de la Loi Climat 2021 absents',
            'missing': ['149', '159']
        },
        'pro_immo/Fiche_IA_READY_Mandat_Exclusif_Vente_Directe.md': {
            'reason': 'Article 2 (référence ambiguë) non trouvé dans corpus',
            'missing': ['2']
        },
        'transaction/FICHE IA-READY — Décret 20 juillet 1972.md': {
            'reason': 'Template vide - articles existent dans corpus mais fiche non remplie',
            'missing': ['20', '25', '28', '33', '38']
        },
    }

    print("=" * 80)
    print("MARKING FICHES AS NEEDS_HUMAN - Hybrid Approach")
    print("=" * 80)
    print()

    marked_count = 0
    skipped_count = 0

    for fiche_path, info in needs_human_fiches.items():
        file_path = fiches_dir / fiche_path

        if not file_path.exists():
            # Try to find with glob pattern (for truncated names)
            domain = fiche_path.split('/')[0]
            pattern = fiche_path.split('/')[-1][:30] + '*'
            matches = list((fiches_dir / domain).glob(pattern))

            if matches:
                file_path = matches[0]
            else:
                print(f"  [NOT FOUND] {fiche_path}")
                skipped_count += 1
                continue

        if mark_fiche_needs_human(file_path, info['reason'], info['missing']):
            marked_count += 1
        else:
            skipped_count += 1

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Marked: {marked_count}")
    print(f"Skipped: {skipped_count}")
    print(f"Total: {len(needs_human_fiches)}")
    print()
    print("[OK] Re-run validation to see warnings instead of errors")


if __name__ == '__main__':
    main()
