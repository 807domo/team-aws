"""
愛媛探索AIクイズ - QuizService ユニットテスト

QuizService のコース取得、セッション開始、回答判定、コース完了をテストする。
SQLite インメモリDBを使用してテスト実行する。
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.data.database import Base
from app.data.models import CourseModel, QuestionModel, UserModel
from app.domain.models import (
    Difficulty,
    Grade,
    Region,
    SessionStatus,
)
from app.domain.quiz_service import QuizService


@pytest.fixture
def db_session():
    """テスト用のインメモリSQLiteセッション"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def seed_data(db_session: Session):
    """テスト用の初期データ投入"""
    # ユーザー作成
    user = UserModel(id="user-1", display_name="テストユーザー")
    db_session.add(user)

    # コース作成（3地域）
    courses = [
        CourseModel(
            id="course-chuyo-1",
            name="松山城コース（基礎）",
            region="中級",
            difficulty="基礎",
            description="松山城周辺の観光とクラウド基礎",
        ),
        CourseModel(
            id="course-nanyo-1",
            name="宇和島コース（基礎）",
            region="初級",
            difficulty="基礎",
            description="宇和島の郷土料理とAI基礎",
        ),
        CourseModel(
            id="course-toyo-1",
            name="しまなみ海道コース（中級）",
            region="上級",
            difficulty="中級",
            description="しまなみ海道とネットワーク",
        ),
    ]
    db_session.add_all(courses)

    # 問題作成
    questions = [
        QuestionModel(
            id="q1",
            course_id="course-chuyo-1",
            text="松山城の築城者は？",
            choice_1="加藤嘉明",
            choice_2="豊臣秀吉",
            choice_3="徳川家康",
            choice_4="伊達政宗",
            correct_choice_index=0,
            ehime_trivia="松山城は加藤嘉明が1602年に築城を開始した。",
            aws_ai_explanation="AWS CloudFormationのように、計画に基づいてインフラを構築する。",
            difficulty="基礎",
            exam_domain="Cloud Concepts",
        ),
        QuestionModel(
            id="q2",
            course_id="course-chuyo-1",
            text="道後温泉の歴史は何年？",
            choice_1="約1000年",
            choice_2="約2000年",
            choice_3="約3000年",
            choice_4="約500年",
            correct_choice_index=2,
            ehime_trivia="道後温泉は約3000年の歴史を持つ日本最古の温泉。",
            aws_ai_explanation="Amazon S3のように、長期間にわたってデータを安全に保存する。",
            difficulty="基礎",
            exam_domain="Cloud Concepts",
        ),
        QuestionModel(
            id="q3",
            course_id="course-nanyo-1",
            text="宇和島の郷土料理は？",
            choice_1="鯛めし",
            choice_2="お好み焼き",
            choice_3="たこ焼き",
            choice_4="もんじゃ焼き",
            correct_choice_index=0,
            ehime_trivia="宇和島鯛めしは生の鯛の刺身を使う独特の料理。",
            aws_ai_explanation="Amazon Personalizeのように、地域の特性に合わせたカスタマイズ。",
            difficulty="基礎",
            exam_domain="AI and ML Fundamentals",
        ),
    ]
    db_session.add_all(questions)
    db_session.commit()


class TestGetCourses:
    """get_courses メソッドのテスト"""

    def test_returns_all_regions(self, db_session, seed_data):
        """全地域がキーとして含まれる"""
        service = QuizService(db_session)
        result = service.get_courses()

        assert Region.CHUYO in result
        assert Region.NANYO in result
        assert Region.TOYO in result

    def test_courses_grouped_by_region(self, db_session, seed_data):
        """コースが正しい地域にグルーピングされる"""
        service = QuizService(db_session)
        result = service.get_courses()

        assert len(result[Region.CHUYO]) == 1
        assert result[Region.CHUYO][0].name == "松山城コース（基礎）"
        assert len(result[Region.NANYO]) == 1
        assert result[Region.NANYO][0].name == "宇和島コース（基礎）"
        assert len(result[Region.TOYO]) == 1
        assert result[Region.TOYO][0].name == "しまなみ海道コース（中級）"

    def test_filter_by_region(self, db_session, seed_data):
        """特定地域のみフィルタリング"""
        service = QuizService(db_session)
        result = service.get_courses(region=Region.CHUYO)

        assert len(result[Region.CHUYO]) == 1
        assert len(result[Region.NANYO]) == 0
        assert len(result[Region.TOYO]) == 0

    def test_empty_region_returns_empty_list(self, db_session):
        """コースがない地域は空リスト（「準備中」状態）"""
        service = QuizService(db_session)
        result = service.get_courses()

        # コースが登録されていないので全て空
        for region in Region:
            assert result[region] == []

    def test_course_info_includes_question_count(self, db_session, seed_data):
        """CourseInfo に問題数が含まれる"""
        service = QuizService(db_session)
        result = service.get_courses()

        chuyo_course = result[Region.CHUYO][0]
        assert chuyo_course.question_count == 2  # q1, q2


class TestIsRegionAvailable:
    """is_region_available メソッドのテスト"""

    def test_available_when_courses_exist(self, db_session, seed_data):
        """コースがある地域は True"""
        service = QuizService(db_session)
        assert service.is_region_available(Region.CHUYO) is True

    def test_unavailable_when_no_courses(self, db_session):
        """コースがない地域は False（準備中）"""
        service = QuizService(db_session)
        assert service.is_region_available(Region.CHUYO) is False


class TestStartCourse:
    """start_course メソッドのテスト"""

    def test_creates_session_and_returns_questions(self, db_session, seed_data):
        """セッション作成と問題リスト取得"""
        service = QuizService(db_session)
        session, questions = service.start_course("user-1", "course-chuyo-1")

        assert session.user_id == "user-1"
        assert session.course_id == "course-chuyo-1"
        assert session.status == SessionStatus.IN_PROGRESS
        assert len(questions) == 2

    def test_raises_error_for_invalid_course(self, db_session, seed_data):
        """存在しないコースID"""
        service = QuizService(db_session)
        with pytest.raises(ValueError, match="コースが見つかりません"):
            service.start_course("user-1", "nonexistent-course")


class TestSubmitAnswer:
    """submit_answer メソッドのテスト"""

    def test_correct_answer(self, db_session, seed_data):
        """正解時のフィードバック"""
        service = QuizService(db_session)
        session, _ = service.start_course("user-1", "course-chuyo-1")

        result = service.submit_answer(session.id, "q1", 0)

        assert result.is_correct is True
        assert result.correct_choice_index == 0
        assert result.selected_choice_index == 0

    def test_incorrect_answer(self, db_session, seed_data):
        """不正解時のフィードバック"""
        service = QuizService(db_session)
        session, _ = service.start_course("user-1", "course-chuyo-1")

        result = service.submit_answer(session.id, "q1", 2)

        assert result.is_correct is False
        assert result.correct_choice_index == 0
        assert result.selected_choice_index == 2

    def test_answer_record_saved(self, db_session, seed_data):
        """回答記録が保存される"""
        service = QuizService(db_session)
        session, _ = service.start_course("user-1", "course-chuyo-1")

        service.submit_answer(session.id, "q1", 0)

        records = service._user_record_repo.get_records_by_user("user-1")
        assert len(records) == 1
        assert records[0].is_correct is True
        assert records[0].question_id == "q1"

    def test_raises_error_for_invalid_session(self, db_session, seed_data):
        """存在しないセッションID"""
        service = QuizService(db_session)
        with pytest.raises(ValueError, match="セッションが見つかりません"):
            service.submit_answer("invalid-session", "q1", 0)

    def test_raises_error_for_completed_session(self, db_session, seed_data):
        """完了済みセッションへの回答"""
        service = QuizService(db_session)
        session, _ = service.start_course("user-1", "course-chuyo-1")
        service.submit_answer(session.id, "q1", 0)
        service.complete_course(session.id)

        with pytest.raises(ValueError, match="セッションは既に終了しています"):
            service.submit_answer(session.id, "q2", 1)

    def test_raises_error_for_invalid_question(self, db_session, seed_data):
        """存在しない問題ID"""
        service = QuizService(db_session)
        session, _ = service.start_course("user-1", "course-chuyo-1")

        with pytest.raises(ValueError, match="問題が見つかりません"):
            service.submit_answer(session.id, "nonexistent-q", 0)


class TestCompleteCourse:
    """complete_course メソッドのテスト"""

    def test_returns_summary_with_correct_counts(self, db_session, seed_data):
        """正解数・総問題数の正しい集計"""
        service = QuizService(db_session)
        session, _ = service.start_course("user-1", "course-chuyo-1")

        # 1問正解、1問不正解
        service.submit_answer(session.id, "q1", 0)  # 正解
        service.submit_answer(session.id, "q2", 0)  # 不正解（正解は2）

        summary = service.complete_course(session.id)

        assert summary.course_id == "course-chuyo-1"
        assert summary.course_name == "松山城コース（基礎）"
        assert summary.correct_count == 1
        assert summary.total_count == 2
        assert summary.accuracy_rate == 50.0
        assert summary.grade == Grade.E

    def test_perfect_score(self, db_session, seed_data):
        """全問正解時のグレード"""
        service = QuizService(db_session)
        session, _ = service.start_course("user-1", "course-chuyo-1")

        service.submit_answer(session.id, "q1", 0)  # 正解
        service.submit_answer(session.id, "q2", 2)  # 正解

        summary = service.complete_course(session.id)

        assert summary.correct_count == 2
        assert summary.total_count == 2
        assert summary.accuracy_rate == 100.0
        assert summary.grade == Grade.A

    def test_session_marked_completed(self, db_session, seed_data):
        """セッションが COMPLETED に更新される"""
        service = QuizService(db_session)
        session, _ = service.start_course("user-1", "course-chuyo-1")
        service.submit_answer(session.id, "q1", 0)

        service.complete_course(session.id)

        updated = service.get_session(session.id)
        assert updated.status == SessionStatus.COMPLETED
        assert updated.completed_at is not None

    def test_raises_error_for_already_completed(self, db_session, seed_data):
        """既に完了済みのセッション"""
        service = QuizService(db_session)
        session, _ = service.start_course("user-1", "course-chuyo-1")
        service.submit_answer(session.id, "q1", 0)
        service.complete_course(session.id)

        with pytest.raises(ValueError, match="セッションは既に終了しています"):
            service.complete_course(session.id)
