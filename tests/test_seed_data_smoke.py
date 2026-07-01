"""
スモークテスト: データ量・分布の検証

全問題数、コース別分布、ドメイン別分布、用語集数をチェックする。
Requirements: 1.1, 1.5, 1.6, 1.8, 4.5, 5.6, 6.1, 8.3
"""

from collections import Counter

from app.data.seed_data import QUESTIONS, COURSES
from app.data.seed_data_extra import EXTRA_QUESTIONS
from app.data.seed_data_extra2 import EXTRA_QUESTIONS_3
from app.data.glossary_seed import GLOSSARY_SEED_DATA

ALL_QUESTIONS = QUESTIONS + EXTRA_QUESTIONS + EXTRA_QUESTIONS_3

# Valid course IDs: nanyo-stage-01~31, chuyo-stage-01~20, toyo-stage-01~20
VALID_COURSE_IDS = (
    [f"nanyo-stage-{i:02d}" for i in range(1, 32)]
    + [f"chuyo-stage-{i:02d}" for i in range(1, 21)]
    + [f"toyo-stage-{i:02d}" for i in range(1, 21)]
)


def test_total_question_count():
    """全問題数が300以上であることを確認する。"""
    assert len(ALL_QUESTIONS) >= 300, (
        f"Expected >= 300 questions, got {len(ALL_QUESTIONS)}"
    )


def test_all_courses_have_questions():
    """71コース全てに少なくとも1問が存在することを確認する。"""
    course_ids_with_questions = {q["course_id"] for q in ALL_QUESTIONS}
    for course_id in VALID_COURSE_IDS:
        assert course_id in course_ids_with_questions, (
            f"Course '{course_id}' has no questions"
        )


def test_questions_per_course_range():
    """各コースの問題数が3〜7の範囲であることを確認する。"""
    counter = Counter(q["course_id"] for q in ALL_QUESTIONS)
    for course_id in VALID_COURSE_IDS:
        count = counter.get(course_id, 0)
        assert 3 <= count <= 7, (
            f"Course '{course_id}' has {count} questions (expected 3-7)"
        )


def test_clf_cloud_concepts_count():
    """CLF-C02 Cloud Conceptsドメインの問題数が47以上であることを確認する。"""
    count = sum(1 for q in ALL_QUESTIONS if q["exam_domain"] == "Cloud Concepts")
    assert count >= 47, (
        f"Cloud Concepts: expected >= 47, got {count}"
    )


def test_clf_security_count():
    """CLF-C02 Security and Complianceドメインの問題数が61以上であることを確認する。"""
    count = sum(1 for q in ALL_QUESTIONS if q["exam_domain"] == "Security and Compliance")
    assert count >= 61, (
        f"Security and Compliance: expected >= 61, got {count}"
    )


def test_clf_technology_count():
    """CLF-C02 Cloud Technology and Servicesドメインの問題数が70以上であることを確認する。"""
    count = sum(1 for q in ALL_QUESTIONS if q["exam_domain"] == "Cloud Technology and Services")
    assert count >= 70, (
        f"Cloud Technology and Services: expected >= 70, got {count}"
    )


def test_clf_billing_count():
    """CLF-C02 Billing Pricing and Supportドメインの問題数が24以上であることを確認する。"""
    count = sum(1 for q in ALL_QUESTIONS if q["exam_domain"] == "Billing Pricing and Support")
    assert count >= 24, (
        f"Billing Pricing and Support: expected >= 24, got {count}"
    )


def test_aif_ai_ml_count():
    """AIF-C01 AI and ML Fundamentalsドメインの問題数が25以上であることを確認する。"""
    count = sum(1 for q in ALL_QUESTIONS if q["exam_domain"] == "AI and ML Fundamentals")
    assert count >= 25, (
        f"AI and ML Fundamentals: expected >= 25, got {count}"
    )


def test_aif_genai_count():
    """AIF-C01 Generative AI Conceptsドメインの問題数が30以上であることを確認する。"""
    count = sum(1 for q in ALL_QUESTIONS if q["exam_domain"] == "Generative AI Concepts")
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
        if q["exam_domain"] == "Security Compliance and Governance"
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
    """COURSESが71件で、全て有効なIDであることを確認する。"""
    assert len(COURSES) == 71, (
        f"Expected 71 courses, got {len(COURSES)}"
    )
    course_ids = [c["id"] for c in COURSES]
    for valid_id in VALID_COURSE_IDS:
        assert valid_id in course_ids, (
            f"Expected course '{valid_id}' not found in COURSES"
        )
