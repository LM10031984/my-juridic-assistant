"""
Tests unitaires pour article_id.py
Vérifie la normalisation et l'extraction d'identifiants d'articles
"""

import pytest
from api.utils.article_id import (
    normalize_article_id,
    is_ambiguous_numeric,
    extract_article_ids,
    extract_article_ids_from_base_juridique
)


class TestNormalizeArticleId:
    """Tests pour normalize_article_id()"""

    def test_normalize_with_spaces_and_dots(self):
        """Article L. 213-2 avec espaces et points"""
        assert normalize_article_id("Article L. 213-2") == "L213-2"
        assert normalize_article_id("L. 213-2") == "L213-2"
        assert normalize_article_id("L . 213 - 2") == "L213-2"

    def test_normalize_without_spaces(self):
        """Articles déjà compacts"""
        assert normalize_article_id("L213-2") == "L213-2"
        assert normalize_article_id("R123-4") == "R123-4"

    def test_normalize_d_and_c_codes(self):
        """Codes D et C"""
        assert normalize_article_id("D. 1-1") == "D1-1"
        assert normalize_article_id("D.1-1") == "D1-1"
        assert normalize_article_id("C. 456") == "C456"

    def test_normalize_numeric_only(self):
        """Articles purement numériques"""
        assert normalize_article_id("Article 25-8") == "25-8"
        assert normalize_article_id("Art. 3") == "3"
        assert normalize_article_id("Article 3-2") == "3-2"

    def test_normalize_case_insensitive(self):
        """Majuscules/minuscules"""
        assert normalize_article_id("article l. 213-2") == "L213-2"
        assert normalize_article_id("ARTICLE L. 213-2") == "L213-2"
        assert normalize_article_id("Art. L. 213-2") == "L213-2"

    def test_normalize_empty(self):
        """Cas limites"""
        assert normalize_article_id("") == ""
        assert normalize_article_id("   ") == ""


class TestIsAmbiguousNumeric:
    """Tests pour is_ambiguous_numeric()"""

    def test_ambiguous_short_numeric(self):
        """Articles courts et numériques = ambigus"""
        assert is_ambiguous_numeric("1") is True
        assert is_ambiguous_numeric("2") is True
        assert is_ambiguous_numeric("17") is True
        assert is_ambiguous_numeric("123") is True

    def test_not_ambiguous_with_letter_code(self):
        """Articles avec code lettre = non ambigus"""
        assert is_ambiguous_numeric("L213-2") is False
        assert is_ambiguous_numeric("R123-4") is False
        assert is_ambiguous_numeric("D1-1") is False

    def test_not_ambiguous_with_hyphen(self):
        """Articles avec trait d'union = non ambigus"""
        assert is_ambiguous_numeric("25-8") is False
        assert is_ambiguous_numeric("3-2") is False

    def test_not_ambiguous_long_numeric(self):
        """Articles longs (>3 chiffres) = non ambigus"""
        assert is_ambiguous_numeric("1234") is False
        assert is_ambiguous_numeric("12345") is False

    def test_empty(self):
        """Cas limites"""
        assert is_ambiguous_numeric("") is True
        assert is_ambiguous_numeric(None) is True


class TestExtractArticleIds:
    """Tests pour extract_article_ids()"""

    def test_extract_header_level_with_letter_codes(self):
        """Headers avec codes L/R/D"""
        text = """
        ### Article L. 213-2
        Texte de l'article...

        ### Article R. 123-4
        Autre texte...
        """
        result = extract_article_ids(text)
        assert "L213-2" in result
        assert "R123-4" in result

    def test_extract_header_level_numeric(self):
        """Headers numériques"""
        text = """
        ### Article 25-8
        Texte...

        ## Article 3
        Autre texte...
        """
        result = extract_article_ids(text)
        assert "25-8" in result
        assert "3" in result

    def test_extract_inline_references(self):
        """Références inline"""
        text = """
        Conformément à l'article L. 213-2, le locataire doit...
        Selon l'article 25-8, il est interdit...
        """
        result = extract_article_ids(text)
        assert "L213-2" in result
        assert "25-8" in result

    def test_extract_mixed_formats(self):
        """Mélange de formats"""
        text = """
        ### Article L. 213-2
        Selon l'article R. 123-4 et l'article 25-8...
        L. 456-1 s'applique également.
        """
        result = extract_article_ids(text)
        assert "L213-2" in result
        assert "R123-4" in result
        assert "25-8" in result
        assert "L456-1" in result

    def test_no_duplicates(self):
        """Pas de doublons"""
        text = """
        Article L. 213-2 est important.
        L'article L. 213-2 dispose que...
        L. 213-2 est clair.
        """
        result = extract_article_ids(text)
        # Tous normalisés vers "L213-2", donc une seule occurrence
        assert result.count("L213-2") == 1

    def test_empty_text(self):
        """Texte vide"""
        assert extract_article_ids("") == []
        assert extract_article_ids("   ") == []
        assert extract_article_ids("Pas d'articles ici.") == []


class TestExtractArticleIdsFromBaseJuridique:
    """Tests pour extract_article_ids_from_base_juridique()"""

    def test_extract_from_base_juridique_section(self):
        """Extraction depuis section BASE JURIDIQUE"""
        response = """
        ## RÉPONSE

        Le locataire doit payer son loyer...

        ## BASE JURIDIQUE

        - Article L. 213-2 (Loi 1989)
        - Article R. 123-4 (Décret 1987)
        - Article 25-8

        ## SOURCES

        - Loi 1989
        """
        result = extract_article_ids_from_base_juridique(response)
        assert "L213-2" in result
        assert "R123-4" in result
        assert "25-8" in result

    def test_ignore_articles_outside_base_juridique(self):
        """Ignorer articles hors section BASE JURIDIQUE"""
        response = """
        ## RÉPONSE

        L'article L. 999-9 dit que... (cet article NE doit PAS être extrait)

        ## BASE JURIDIQUE

        - Article L. 213-2 (seul cet article doit être extrait)
        """
        result = extract_article_ids_from_base_juridique(response)
        assert "L213-2" in result
        assert "L999-9" not in result

    def test_no_base_juridique_section(self):
        """Pas de section BASE JURIDIQUE"""
        response = """
        ## RÉPONSE

        Texte sans base juridique...
        """
        result = extract_article_ids_from_base_juridique(response)
        assert result == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
