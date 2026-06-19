"""
愛媛探索AIクイズ - Results Service ユニットテスト

ResultsService のメソッドをテストする。
SQLite インメモリDBを使用して各メソッドの正しさを検証する。
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.data.course_repository import CourseRepository
from app.data.database import Base
from app.data.models import (
    AnswerRecordModel,
    CourseModel,
    QuestionModel,
    UserModel,
)
from app.data.question_repository import QuestionRepository
from app.data.user_record_repository import UserRecordRepository
from app.domain.models import (
    DashboardData,
    ExamType,
    ExplorationRate,
    Grade,
    RadarChartData,
)
from app.domain.results_service import ResultsService


@pytest.fixture
def db_session():
    """テスト用のインメモリDB セッションを提供する"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    yield session
    session.close()


@pytest.fixture
def repos(db_session):
    """リポジトリインスタンスを提供する"""
    return {
        "user_record": UserRecordRepository(db_session),
        "course": CourseRepository(db_session),
        "question": QuestionRepository(db_session),
    }


@pytest.fixture
def results_service(repos):
    """ResultsService インスタンスを提供する"""
    return ResultsService(
        user_record_repository=repos["user_record"],
        course_repository=repos["course"],
        question_repository=repos["question"],
    )


@pytest.fixture
def setup_data(db_session):
    """テスト用の基本データをセットアップする"""
    # ユーザー作成
    user = UserModel(id="user-1", display_name="テストユーザー")
    db_session.add(user)

    # コース作成（3地域）
    courses = [
        CourseModel(
            id="course-chuyo",
            name="松山城コース",
            region="中予",
            difficulty="基礎",
            description="中予の基礎コース",
        ),
        CourseModel(
            id="course-nanyo",
            name="宇和島コース",
            region="南予",
            difficulty="中級",
            description="南予の中級コース",
        ),
        CourseModel(
            id="course-toyo",
            name="しまなみ海道コース",
            region="東予",
            difficulty="上級",
            description="東予の上級コース",
        ),
    ]
    for c in courses:
        db_session.add(c)

    # 問題作成（各コースに問題）
    questions = [
        QuestionModel(
            id="q1",
            course_id="course-chuyo",
            text="松山城に関する問題",
            choice_1="A",
            choice_2="B",
            choice_3="C",
            choice_4="D",
            correct_choice_index=0,
            ehime_trivia="松山城は日本三大平山城の一つ",
            aws_ai_explanation="EC2はクラウド上の仮想サーバーです",
            difficulty="基礎",
            exam_domain="Cloud Concepts",
        ),
        QuestionModel(
            id="q2",
            course_id="course-chuyo",
            text="道後温泉に関する問題",
            choice_1="A",
            choice_2="B",
            choice_3="C",
            choice_4="D",
            correct_choice_index=1,
            ehime_trivia="道後温泉は日本最古の温泉",
            aws_ai_explanation="S3はオブジェクトストレージです",
            difficulty="基礎",
            exam_domain="Security and Compliance",
        ),
        QuestionModel(
            id="q3",
            course_id="course-nanyo",
            text="宇和島に関する問題",
            choice_1="A",
            choice_2="B",
            choice_3="C",
            choice_4="D",
            correct_choice_index=2,
            ehime_trivia="宇和島の鯛めし",
            aws_ai_explanation="Lambdaはサーバーレスです",
            difficulty="中級",
            exam_domain="Cloud Technology and Services",
        ),
        QuestionModel(
            id="q4",
            course_id="course-toyo",
            text="しまなみ海道に関する問題",
            choice_1="A",
            choice_2="B",
            choice_3="C",
            choice_4="D",
            correct_choice_index=3,
            ehime_trivia="しまなみ海道は全長約60km",
            aws_ai_explanation="VPCはネットワーク分離です",
            difficulty="上級",
            exam_domain="Billing Pricing and Support",
        ),
    ]
    for q in questions:
        db_session.add(q)

    db_session.commit()
    return {"user_id": "user-1", "courses": courses, "questions": questions}


def _add_answer(db_session, record_id, user_id, question_id, course_id, is_correct, answered_at=None):
    """回答記録を追加するヘルパー"""
    if answered_at is None:
        answered_at = datetime.now()
    record = AnswerRecordModel(
        id=record_id,
        user_id=user_id,
        question_id=question_id,
        course_id=course_id,
        selected_choice_index=0 if is_correct else 1,
        is_correct=is_correct,
        answered_at=answered_at,
    )
    db_session.add(record)
    db_session.commit()


class TestGetDashboardData:
    """get_dashboard_data のテスト"""

    def test_no_history(self, results_service, setup_data, db_session):
        """学習履歴なしの場合は has_history=False"""
        data = results_service.get_dashboard_data("user-1")

        assert data.has_history is False
        assert data.cumulative_accuracy == 0.0
        assert data.grade == Grade.E
        assert data.attempt_history == []

    def test_with_history(self, results_service, setup_data, db_session):
        """学習履歴ありの場合はデータが集約される"""
        # 回答を追加（2問正解、1問不正解）
        _add_answer(db_session, "r1", "user-1", "q1", "course-chuyo", True)
        _add_answer(db_session, "r2", "user-1", "q2", "course-chuyo", True)
        _add_answer(db_session, "r3", "user-1", "q3", "course-nanyo", False)

        data = results_service.get_dashboard_data("user-1")

        assert data.has_history is True
        # 2/3 = 66.7%
        assert data.cumulative_accuracy == 66.7
        assert data.grade == Grade.D
        assert len(data.attempt_history) == 2  # 2コースに回答

    def test_perfect_score(self, results_service, setup_data, db_session):
        """全問正解の場合はグレードA"""
        _add_answer(db_session, "r1", "user-1", "q1", "course-chuyo", True)
        _add_answer(db_session, "r2", "user-1", "q2", "course-chuyo", True)

        data = results_service.get_dashboard_data("user-1")

        assert data.cumulative_accuracy == 100.0
        assert data.grade == Grade.A


class TestGetRadarChartData:
    """get_radar_chart_data のテスト"""

    def test_no_answers(self, results_service, setup_data):
        """回答なしの場合、全ドメイン0%"""
        result = results_service.get_radar_chart_data("user-1", ExamType.CLOUD_PRACTITIONER)

        assert isinstance(result, RadarChartData)
        for domain, accuracy in result.domain_accuracy.items():
            assert accuracy == 0.0
        # Cloud Practitioner は 4ドメイン
        assert len(result.domain_accuracy) == 4

    def test_cloud_practitioner_domains(self, results_service, setup_data, db_session):
        """Cloud Practitionerのドメイン別正答率が計算される"""
        _add_answer(db_session, "r1", "user-1", "q1", "course-chuyo", True)  # Cloud Concepts
        _add_answer(db_session, "r2", "user-1", "q2", "course-chuyo", False)  # Security

        result = results_service.get_radar_chart_data("user-1", ExamType.CLOUD_PRACTITIONER)

        assert result.domain_accuracy["Cloud Concepts"] == 100.0
        assert result.domain_accuracy["Security and Compliance"] == 0.0
        assert result.domain_accuracy["Cloud Technology and Services"] == 0.0
        assert result.domain_accuracy["Billing Pricing and Support"] == 0.0

    def test_ai_practitioner_domains(self, results_service, setup_data, db_session):
        """AI Practitionerのドメインリストが返される"""
        result = results_service.get_radar_chart_data("user-1", ExamType.AI_PRACTITIONER)

        assert len(result.domain_accuracy) == 3
        assert "AI and ML Fundamentals" in result.domain_accuracy
        assert "Generative AI" in result.domain_accuracy
        assert "Responsible AI" in result.domain_accuracy


class TestGetExplorationRate:
    """get_exploration_rate のテスト"""

    def test_no_courses_completed(self, results_service, setup_data):
        """コース未完了の場合"""
        rate = results_service.get_exploration_rate("user-1")

        assert isinstance(rate, ExplorationRate)
        assert rate.completed_courses == 0
        assert rate.total_courses == 3
        assert rate.exploration_percentage == 0.0
        assert rate.completed_region_count == 0

    def test_one_course_completed(self, results_service, setup_data, db_session):
        """1コース完了の場合"""
        _add_answer(db_session, "r1", "user-1", "q1", "course-chuyo", True)

        rate = results_service.get_exploration_rate("user-1")

        assert rate.completed_courses == 1
        assert rate.total_courses == 3
        assert rate.exploration_percentage == 33.3
        assert rate.completed_region_count == 1

    def test_all_regions_completed(self, results_service, setup_data, db_session):
        """全地域でコース完了の場合"""
        _add_answer(db_session, "r1", "user-1", "q1", "course-chuyo", True)
        _add_answer(db_session, "r2", "user-1", "q3", "course-nanyo", True)
        _add_answer(db_session, "r3", "user-1", "q4", "course-toyo", True)

        rate = results_service.get_exploration_rate("user-1")

        assert rate.completed_courses == 3
        assert rate.total_courses == 3
        assert rate.exploration_percentage == 100.0
        assert rate.completed_region_count == 3

    def test_no_courses_exist(self, db_session):
        """コースが存在しない場合"""
        repos = {
            "user_record": UserRecordRepository(db_session),
            "course": CourseRepository(db_session),
            "question": QuestionRepository(db_session),
        }
        service = ResultsService(
            user_record_repository=repos["user_record"],
            course_repository=repos["course"],
            question_repository=repos["question"],
        )
        # ユーザーだけ作成
        user = UserModel(id="user-2", display_name="テスト2")
        db_session.add(user)
        db_session.commit()

        rate = service.get_exploration_rate("user-2")

        assert rate.completed_courses == 0
        assert rate.total_courses == 0
        assert rate.exploration_percentage == 0.0
        assert rate.completed_region_count == 0


class TestGetAttemptHistory:
    """get_attempt_history のテスト"""

    def test_no_history(self, results_service, setup_data):
        """履歴なしの場合は空リスト"""
        history = results_service.get_attempt_history("user-1")
        assert history == []

    def test_chronological_order(self, results_service, setup_data, db_session):
        """時系列順（昇順）でソートされる"""
        base_time = datetime(2024, 1, 1, 10, 0, 0)

        # 南予コースを先に回答（時刻的に後）
        _add_answer(
            db_session, "r1", "user-1", "q3", "course-nanyo", True,
            answered_at=base_time + timedelta(hours=2),
        )
        # 中予コースを後で追加（時刻的に先）
        _add_answer(
            db_session, "r2", "user-1", "q1", "course-chuyo", True,
            answered_at=base_time + timedelta(hours=1),
        )

        history = results_service.get_attempt_history("user-1")

        assert len(history) == 2
        # 時系列順: 中予（1時間後）→ 南予（2時間後）
        assert history[0].course_name == "松山城コース"
        assert history[1].course_name == "宇和島コース"

    def test_accuracy_and_grade_calculation(self, results_service, setup_data, db_session):
        """コース別の正答率とグレードが正しく計算される"""
        _add_answer(db_session, "r1", "user-1", "q1", "course-chuyo", True)
        _add_answer(db_session, "r2", "user-1", "q2", "course-chuyo", False)

        history = results_service.get_attempt_history("user-1")

        assert len(history) == 1
        # 1/2 = 50.0%
        assert history[0].accuracy_rate == 50.0
        assert history[0].grade == Grade.E

    def test_no_learning_history_message(self, results_service, setup_data):
        """学習履歴なしの場合、DashboardData の has_history が False"""
        dashboard = results_service.get_dashboard_data("user-1")
        assert dashboard.has_history is False
