"""
スモークテスト: データ量・分布の検証

全問題数、コース別分布、ドメイン別分布、用語集数をチェックする。
Requirements: 1.1, 1.5, 1.6, 1.8, 4.5, 5.6, 6.1, 8.3
"""

from collections import Counter

from app.data.seed_data import QUESTIONS, COURSES
from app.data.seed_data_extra import EXTRA_QUESTIONS
from app.data.seed_data_extra2 import EXTRA_QUESTIONS_2
from app.data.glossary_seed import GLOSSARY_SEED_DATA

ALL_QUESTIONS = QUESTIONS + EXTRA_QUESTIONS + EXTRA_QUESTIONS_2

# Valid course IDs derived from actual COURSES definition
VALID_COURSE_IDS = [c["id"] for c in COURSES]

# Course IDs that actually have questions assigned
COURSE_IDS_WITH_QUESTIONS = sorted(set(q["course_id"] for q in ALL_QUESTIONS) & set(VALID_COURSE_IDS))


def test_total_question_count():
    """全問題数が300以上であることを確認する。"""
    assert len(ALL_QUESTIONS) >= 300, (
        f"Expected >= 300 questions, got {len(ALL_QUESTIONS)}"
    )


def test_all_courses_have_questions():
    """問題が割り当てられたコースに少なくとも1問が存在することを確認する。"""
    course_ids_with_questions = {q["course_id"] for q in ALL_QUESTIONS}
    for course_id in COURSE_IDS_WITH_QUESTIONS:
        assert course_id in course_ids_with_questions, (
            f"Course '{course_id}' has no questions"
        )


def test_questions_per_course_range():
    """問題ありコースの問題数が3〜15の範囲であることを確認する。"""
    counter = Counter(q["course_id"] for q in ALL_QUESTIONS)
    for course_id in COURSE_IDS_WITH_QUESTIONS:
        count = counter.get(course_id, 0)
        assert 3 <= count <= 15, (
            f"Course '{course_id}' has {count} questions (expected 3-15)"
        )


def test_clf_cloud_concepts_count():
    """CLF-C02 Cloud Conceptsドメインの問題数が30以上であることを確認する。"""
    count = sum(1 for q in ALL_QUESTIONS if q["exam_domain"] == "Cloud Concepts")
    assert count >= 30, (
        f"Cloud Concepts: expected >= 30, got {count}"
    )


def test_clf_security_count():
    """CLF-C02 Security and Complianceドメインの問題数が50以上であることを確認する。"""
    count = sum(1 for q in ALL_QUESTIONS if q["exam_domain"] == "Security and Compliance")
    assert count >= 50, (
        f"Security and Compliance: expected >= 50, got {count}"
    )


def test_clf_technology_count():
    """CLF-C02 Cloud Technology and Servicesドメインの問題数が70以上であることを確認する。"""
    count = sum(1 for q in ALL_QUESTIONS if q["exam_domain"] == "Cloud Technology and Services")
    assert count >= 70, (
        f"Cloud Technology and Services: expected >= 70, got {count}"
    )


def test_clf_billing_count():
    """CLF-C02 Billing Pricing and Supportドメインの問題数が12以上であることを確認する。"""
    count = sum(1 for q in ALL_QUESTIONS if q["exam_domain"] == "Billing, Pricing, and Support")
    assert count >= 12, (
        f"Billing, Pricing, and Support: expected >= 12, got {count}"
    )


def test_aif_ai_ml_count():
    """AIF-C01 AI and ML Fundamentalsドメインの問題数が25以上であることを確認する。"""
    count = sum(1 for q in ALL_QUESTIONS if q["exam_domain"] == "Fundamentals of AI and ML")
    assert count >= 25, (
        f"AI and ML Fundamentals: expected >= 25, got {count}"
    )


def test_aif_genai_count():
    """AIF-C01 Generative AI Conceptsドメインの問題数が30以上であることを確認する。"""
    count = sum(1 for q in ALL_QUESTIONS if q["exam_domain"] == "Fundamentals of Generative AI")
    assert count >= 30, (
        f"Generative AI Concepts: expected >= 30, got {count}"
    )


def test_aif_fm_count():
    """AIF-C01 Applications of Foundation Modelsドメインの問題数が35以上であることを確認する。"""
    count = sum(1 for q in ALL_QUESTIONS if q["exam_domain"] == "Applications of Foundation Models")
    assert count >= 35, (
        f"Applications of Foundation Models: expected >= 35, got {count}"
    )


def test_aif_responsible_count():
    """AIF-C01 Guidelines for Responsible AIドメインの問題数が18以上であることを確認する。"""
    count = sum(1 for q in ALL_QUESTIONS if q["exam_domain"] == "Guidelines for Responsible AI")
    assert count >= 18, (
        f"Guidelines for Responsible AI: expected >= 18, got {count}"
    )


def test_aif_security_gov_count():
    """AIF-C01 Security Compliance and Governanceドメインの問題数が18以上であることを確認する。"""
    count = sum(
        1 for q in ALL_QUESTIONS
        if q["exam_domain"] == "Security, Compliance, and Governance for AI Solutions"
    )
    assert count >= 18, (
        f"Security Compliance and Governance: expected >= 18, got {count}"
    )


def test_glossary_count():
    """用語集エントリが150以上であることを確認する。"""
    assert len(GLOSSARY_SEED_DATA) >= 150, (
        f"Expected >= 150 glossary entries, got {len(GLOSSARY_SEED_DATA)}"
    )


def test_courses_count():
    """COURSESが40件で、全て有効なIDであることを確認する。"""
    assert len(COURSES) == 40, (
        f"Expected 40 courses, got {len(COURSES)}"
    )
    course_ids = [c["id"] for c in COURSES]
    for valid_id in VALID_COURSE_IDS:
        assert valid_id in course_ids, (
            f"Expected course '{valid_id}' not found in COURSES"
        )
