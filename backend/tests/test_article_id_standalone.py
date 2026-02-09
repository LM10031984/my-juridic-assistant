"""
Tests standalone pour article_id.py (sans pytest)
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from api.utils.article_id import (
    normalize_article_id,
    is_ambiguous_numeric,
    extract_article_ids,
    extract_article_ids_from_base_juridique
)


def test_normalize_article_id():
    """Test de normalize_article_id()"""
    print("\n=== Test normalize_article_id() ===")

    tests = [
        ("Article L. 213-2", "L213-2"),
        ("L. 213-2", "L213-2"),
        ("L213-2", "L213-2"),
        ("R. 123-4", "R123-4"),
        ("D. 1-1", "D1-1"),
        ("Article 25-8", "25-8"),
        ("Art. 3", "3"),
        ("Article 3-2", "3-2"),
    ]

    passed = 0
    for input_val, expected in tests:
        result = normalize_article_id(input_val)
        status = "PASS" if result == expected else "FAIL"
        print(f"  [{status}] normalize_article_id({input_val!r}) = {result!r} (expected {expected!r})")
        if result == expected:
            passed += 1

    print(f"\nPassed: {passed}/{len(tests)}")
    return passed == len(tests)


def test_is_ambiguous_numeric():
    """Test de is_ambiguous_numeric()"""
    print("\n=== Test is_ambiguous_numeric() ===")

    tests = [
        # (input, should_be_ambiguous)
        ("1", True),
        ("2", True),
        ("17", True),
        ("123", True),
        ("L213-2", False),
        ("R123-4", False),
        ("25-8", False),
        ("3-2", False),
        ("1234", False),
    ]

    passed = 0
    for input_val, expected_ambiguous in tests:
        result = is_ambiguous_numeric(input_val)
        status = "PASS" if result == expected_ambiguous else "FAIL"
        print(f"  [{status}] is_ambiguous_numeric({input_val!r}) = {result} (expected {expected_ambiguous})")
        if result == expected_ambiguous:
            passed += 1

    print(f"\nPassed: {passed}/{len(tests)}")
    return passed == len(tests)


def test_extract_article_ids():
    """Test de extract_article_ids()"""
    print("\n=== Test extract_article_ids() ===")

    text1 = """
    ### Article L. 213-2
    Texte de l'article...

    ### Article R. 123-4
    Conformément à l'article 25-8...
    """

    result1 = extract_article_ids(text1)
    print(f"  Text with headers and inline refs:")
    print(f"    Extracted: {result1}")
    print(f"    Expected: ['L213-2', 'R123-4', '25-8']")

    # Check if all expected articles are present
    expected1 = ["L213-2", "R123-4", "25-8"]
    all_present = all(art in result1 for art in expected1)
    status1 = "PASS" if all_present else "FAIL"
    print(f"  [{status1}] All expected articles found")

    # Test dedupe
    text2 = """
    Article L. 213-2 est important.
    L'article L. 213-2 dispose que...
    L. 213-2 est clair.
    """

    result2 = extract_article_ids(text2)
    count_l213_2 = result2.count("L213-2")
    status2 = "PASS" if count_l213_2 == 1 else "FAIL"
    print(f"\n  [{status2}] Deduplication: 'L213-2' appears {count_l213_2} time(s) (expected 1)")

    return all_present and count_l213_2 == 1


def test_extract_from_base_juridique():
    """Test de extract_article_ids_from_base_juridique()"""
    print("\n=== Test extract_article_ids_from_base_juridique() ===")

    response = """
    ## RÉPONSE

    L'article L. 999-9 dit que... (cet article NE doit PAS être extrait)

    ## BASE JURIDIQUE

    - Article L. 213-2 (Loi 1989)
    - Article R. 123-4 (Décret 1987)
    - Article 25-8

    ## SOURCES

    - Loi 1989
    """

    result = extract_article_ids_from_base_juridique(response)
    print(f"  Extracted from BASE JURIDIQUE: {result}")

    expected_present = ["L213-2", "R123-4", "25-8"]
    expected_absent = ["L999-9"]

    all_present = all(art in result for art in expected_present)
    none_absent = all(art not in result for art in expected_absent)

    status_present = "PASS" if all_present else "FAIL"
    status_absent = "PASS" if none_absent else "FAIL"

    print(f"  [{status_present}] Expected articles found: {expected_present}")
    print(f"  [{status_absent}] Articles outside BASE JURIDIQUE ignored: {expected_absent}")

    return all_present and none_absent


def main():
    """Run all tests"""
    print("=" * 80)
    print("ARTICLE ID NORMALIZATION - UNIT TESTS")
    print("=" * 80)

    results = []

    results.append(("normalize_article_id", test_normalize_article_id()))
    results.append(("is_ambiguous_numeric", test_is_ambiguous_numeric()))
    results.append(("extract_article_ids", test_extract_article_ids()))
    results.append(("extract_from_base_juridique", test_extract_from_base_juridique()))

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  [{status}]: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n[PASS] ALL TESTS PASSED")
        return 0
    else:
        print(f"\n[FAIL] {total - passed} TEST(S) FAILED")
        return 1


if __name__ == '__main__':
    exit(main())
