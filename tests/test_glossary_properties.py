"""
用語集データの構造的正当性を検証するプロパティベーステスト

Property 6: Glossary entry structural validity
Property 7: Glossary term uniqueness
"""

from hypothesis import given, settings
from hypothesis.strategies import sampled_from

from app.data.glossary_seed import GLOSSARY_SEED_DATA


# =============================================================================
# Property 6: Glossary entry structural validity
# =============================================================================

VALID_CATEGORIES = {
    "クラウド基礎",
    "AWSコンピューティング",
    "AWSストレージ・データベース",
    "AWSネットワーキング",
    "AWSセキュリティ",
    "AWS管理・ガバナンス",
    "AWS料金・サポート",
    "AI・ML基礎",
    "生成AI・基盤モデル",
    "AWS AIサービス",
    "責任あるAI",
}


@settings(max_examples=200)
@given(entry=sampled_from(GLOSSARY_SEED_DATA))
def test_glossary_entry_structural_validity(entry):
    """
    Feature: exam-ready-quiz-rebuild, Property 6: Glossary entry structural validity

    For any glossary entry in GLOSSARY_SEED_DATA, it must have a non-empty category
    from the set of 11 valid categories, a non-negative integer sort_order, a non-empty
    term string, and a description string of at least 20 characters.

    Validates: Requirements 6.2, 6.5, 6.6
    """
    # category is one of 11 valid categories
    category = entry["category"]
    assert category in VALID_CATEGORIES, (
        f"Glossary term '{entry.get('term', 'UNKNOWN')}': category '{category}' "
        f"is not valid. Must be one of: {sorted(VALID_CATEGORIES)}"
    )

    # sort_order is a non-negative integer
    sort_order = entry["sort_order"]
    assert isinstance(sort_order, int) and sort_order >= 0, (
        f"Glossary term '{entry.get('term', 'UNKNOWN')}': sort_order must be a "
        f"non-negative integer, got {sort_order}"
    )

    # term is a non-empty string
    term = entry["term"]
    assert isinstance(term, str) and len(term.strip()) > 0, (
        f"Glossary entry with category '{category}': term must be a non-empty string, "
        f"got '{term}'"
    )

    # description is at least 20 characters
    description = entry["description"]
    assert isinstance(description, str) and len(description) >= 20, (
        f"Glossary term '{term}': description must be at least 20 characters, "
        f"got {len(description)} characters: '{description}'"
    )


# =============================================================================
# Property 7: Glossary term uniqueness
# =============================================================================


def test_glossary_term_uniqueness():
    """
    Feature: exam-ready-quiz-rebuild, Property 7: Glossary term uniqueness

    All terms in GLOSSARY_SEED_DATA have unique term values (no duplicates
    across all categories).

    Validates: Requirements 6.7
    """
    all_terms = [entry["term"] for entry in GLOSSARY_SEED_DATA]
    duplicates = [term for term in all_terms if all_terms.count(term) > 1]
    assert len(all_terms) == len(set(all_terms)), (
        f"Duplicate glossary terms found: {set(duplicates)}"
    )
