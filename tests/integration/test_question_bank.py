"""
問題バンクの初期データ要件を検証する統合テスト

シードデータ（COURSES, QUESTIONS）が要件を満たしていることを直接検証し、
さらにインメモリDBを使ってデータの永続化・取得が正しく行われることを確認する。

Requirements: 9.2, 7.1, 7.2, 7.3
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.data.database import Base
from app.data.models import CourseModel, QuestionModel
from app.data.seed_data import COURSES, QUESTIONS, seed_database


# =============================================================================
# CCP / AI ドメイン定義
# =============================================================================

CCP_DOMAINS = [
    "Cloud Concepts",
    "Security and Compliance",
    "Cloud Technology and Services",
    "Billing Pricing and Support",
]

AI_DOMAINS = [
    "AI and ML Fundamentals",
    "Generative AI",
    "Responsible AI",
]

ALL_DOMAINS = CCP_DOMAINS + AI_DOMAINS

VALID_REGIONS = {"中予", "南予", "東予"}


# =============================================================================
# Part 1: シードデータリスト（COURSES, QUESTIONS）の直接検証
# =============================================================================


class TestSeedDataDirectValidation:
    """シードデータのリスト定義を直接検証するテスト群"""

    def test_total_questions_at_least_102(self):
        """問題数が102問以上であること（Req 10.1）"""
        assert len(QUESTIONS) >= 102, (
            f"問題数が不足: {len(QUESTIONS)}問 (最低102問必要)"
        )

    def test_total_courses_at_least_9(self):
        """コース数が9以上であること（Req 8.1）"""
        assert len(COURSES) >= 9, (
            f"コース数が不足: {len(COURSES)}コース (最低9コース必要)"
        )

    def test_at_least_one_course_per_region(self):
        """各地域（中予・南予・東予）に最低1コースあること（Req 9.2）"""
        regions = {course["region"] for course in COURSES}
        for region in VALID_REGIONS:
            assert region in regions, (
                f"地域「{region}」にコースがありません"
            )

    def test_each_ccp_domain_has_at_least_3_questions(self):
        """各CCPドメインに3問以上あること（Req 7.1）"""
        for domain in CCP_DOMAINS:
            count = sum(
                1 for q in QUESTIONS if q["exam_domain"] == domain
            )
            assert count >= 3, (
                f"CCPドメイン「{domain}」の問題数が不足: {count}問 (最低3問必要)"
            )

    def test_each_ai_domain_has_at_least_3_questions(self):
        """各AIドメインに3問以上あること（Req 7.2）"""
        for domain in AI_DOMAINS:
            count = sum(
                1 for q in QUESTIONS if q["exam_domain"] == domain
            )
            assert count >= 3, (
                f"AIドメイン「{domain}」の問題数が不足: {count}問 (最低3問必要)"
            )

    def test_every_question_has_non_empty_exam_domain(self):
        """全問題にexam_domainラベルが付与されていること（Req 7.3）"""
        for q in QUESTIONS:
            assert q.get("exam_domain"), (
                f"問題 {q['id']} に exam_domain が設定されていません"
            )
            assert q["exam_domain"].strip() != "", (
                f"問題 {q['id']} の exam_domain が空文字です"
            )

    def test_every_question_has_valid_course_id(self):
        """全問題のcourse_idが既存コースを参照していること"""
        valid_course_ids = {course["id"] for course in COURSES}
        for q in QUESTIONS:
            assert q["course_id"] in valid_course_ids, (
                f"問題 {q['id']} の course_id「{q['course_id']}」は"
                f"存在しないコースを参照しています"
            )

    def test_every_question_has_exactly_4_non_empty_choices(self):
        """全問題が4つの非空選択肢を持つこと"""
        for q in QUESTIONS:
            choices = [
                q.get("choice_1", ""),
                q.get("choice_2", ""),
                q.get("choice_3", ""),
                q.get("choice_4", ""),
            ]
            assert len(choices) == 4, (
                f"問題 {q['id']} の選択肢数が4ではありません"
            )
            for i, choice in enumerate(choices, 1):
                assert choice.strip() != "", (
                    f"問題 {q['id']} の choice_{i} が空です"
                )

    def test_every_question_has_valid_correct_choice_index(self):
        """全問題のcorrect_choice_indexが0〜3の範囲内であること"""
        for q in QUESTIONS:
            idx = q["correct_choice_index"]
            assert 0 <= idx <= 3, (
                f"問題 {q['id']} の correct_choice_index が範囲外: {idx}"
            )

    def test_every_question_has_non_empty_ehime_trivia_and_explanation(self):
        """全問題にehime_triviaとaws_ai_explanationがあること"""
        for q in QUESTIONS:
            assert q.get("ehime_trivia", "").strip() != "", (
                f"問題 {q['id']} の ehime_trivia が空です"
            )
            assert q.get("aws_ai_explanation", "").strip() != "", (
                f"問題 {q['id']} の aws_ai_explanation が空です"
            )

    def test_all_question_ids_are_unique(self):
        """全問題IDが一意であること（Req 9.5）"""
        ids = [q["id"] for q in QUESTIONS]
        assert len(ids) == len(set(ids)), (
            f"重複する問題IDがあります: "
            f"{[qid for qid in ids if ids.count(qid) > 1]}"
        )


# =============================================================================
# Part 2: インメモリDB経由での統合検証
# =============================================================================


@pytest.fixture
def db_session():
    """インメモリSQLiteデータベースのセッションを提供するフィクスチャ"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


class TestSeedDataDatabaseIntegration:
    """インメモリDBにシードデータを投入し、リポジトリ経由で検証するテスト群"""

    def test_seed_database_inserts_all_courses(self, db_session: Session):
        """seed_databaseがすべてのコースを正しく投入すること"""
        result = seed_database(db_session)
        assert result is True

        courses = db_session.query(CourseModel).all()
        assert len(courses) == len(COURSES)

    def test_seed_database_inserts_all_questions(self, db_session: Session):
        """seed_databaseがすべての問題を正しく投入すること"""
        seed_database(db_session)

        questions = db_session.query(QuestionModel).all()
        assert len(questions) == len(QUESTIONS)
        assert len(questions) >= 102

    def test_seed_database_is_idempotent(self, db_session: Session):
        """seed_databaseが冪等であること（2回目はスキップ）"""
        first_result = seed_database(db_session)
        assert first_result is True

        second_result = seed_database(db_session)
        assert second_result is False

        # データ数が変わらないこと
        courses = db_session.query(CourseModel).all()
        assert len(courses) == len(COURSES)

    def test_questions_have_valid_course_foreign_key(self, db_session: Session):
        """DB上で全問題のcourse_idが正しい外部キーを参照していること"""
        seed_database(db_session)

        questions = db_session.query(QuestionModel).all()
        course_ids = {c.id for c in db_session.query(CourseModel).all()}

        for q in questions:
            assert q.course_id in course_ids, (
                f"問題 {q.id} の course_id「{q.course_id}」がDBに存在しません"
            )

    def test_all_domains_present_in_db(self, db_session: Session):
        """DB上で全ドメインが問題に割り当てられていること"""
        seed_database(db_session)

        questions = db_session.query(QuestionModel).all()
        domains_in_db = {q.exam_domain for q in questions}

        for domain in ALL_DOMAINS:
            assert domain in domains_in_db, (
                f"ドメイン「{domain}」がDB内の問題に存在しません"
            )

    def test_each_domain_has_minimum_questions_in_db(self, db_session: Session):
        """DB上で各ドメインに3問以上あること"""
        seed_database(db_session)

        for domain in ALL_DOMAINS:
            count = (
                db_session.query(QuestionModel)
                .filter(QuestionModel.exam_domain == domain)
                .count()
            )
            assert count >= 3, (
                f"ドメイン「{domain}」のDB問題数が不足: {count}問"
            )

    def test_regions_covered_in_db(self, db_session: Session):
        """DB上で全地域にコースがあること"""
        seed_database(db_session)

        courses = db_session.query(CourseModel).all()
        regions_in_db = {c.region for c in courses}

        for region in VALID_REGIONS:
            assert region in regions_in_db, (
                f"地域「{region}」がDB内のコースに存在しません"
            )
