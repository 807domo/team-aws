"""
QuestionRepository のユニットテスト

SQLite インメモリ DB を使用してリポジトリ操作を検証する。
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.data.database import Base
from app.data.models import CourseModel, QuestionModel
from app.data.question_repository import QuestionRepository
from app.domain.models import Difficulty, Question


@pytest.fixture
def db_session():
    """テスト用インメモリ SQLite セッションを作成する"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()

    # テスト用コースを作成
    course = CourseModel(
        id="course-chuyo-basic",
        name="松山城コース（基礎）",
        region="中予",
        difficulty="基礎",
        description="中予地域の基礎コース",
    )
    session.add(course)
    session.commit()

    yield session
    session.close()


def _valid_question_data() -> dict:
    """有効な問題データのベースを返す"""
    return {
        "text": "松山城の別名は何でしょう？",
        "choice_1": "金亀城",
        "choice_2": "白鷺城",
        "choice_3": "烏城",
        "choice_4": "鶴ヶ城",
        "correct_choice_index": 0,
        "ehime_trivia": "松山城は加藤嘉明が築城した日本の現存12天守の一つです。",
        "aws_ai_explanation": "Amazon S3のバケット命名は城の別名のようにユニークである必要があります。",
        "course_id": "course-chuyo-basic",
        "difficulty": "基礎",
        "exam_domain": "Cloud Concepts",
    }


class TestCreateQuestion:
    """create_question メソッドのテスト"""

    def test_creates_question_with_valid_data(self, db_session: Session):
        """有効なデータで問題を作成できる"""
        repo = QuestionRepository(db_session)
        data = _valid_question_data()

        question = repo.create_question(data)

        assert isinstance(question, Question)
        assert question.text == data["text"]
        assert question.choice_1 == data["choice_1"]
        assert question.choice_2 == data["choice_2"]
        assert question.choice_3 == data["choice_3"]
        assert question.choice_4 == data["choice_4"]
        assert question.correct_choice_index == data["correct_choice_index"]
        assert question.ehime_trivia == data["ehime_trivia"]
        assert question.aws_ai_explanation == data["aws_ai_explanation"]
        assert question.course_id == data["course_id"]
        assert question.difficulty == Difficulty.BASIC
        assert question.exam_domain == data["exam_domain"]

    def test_generates_uuid_when_id_not_provided(self, db_session: Session):
        """ID が未指定の場合は UUID を自動生成する"""
        repo = QuestionRepository(db_session)
        data = _valid_question_data()

        question = repo.create_question(data)

        assert question.id is not None
        assert len(question.id) > 0

    def test_uses_provided_id(self, db_session: Session):
        """ID が指定されている場合はそれを使用する"""
        repo = QuestionRepository(db_session)
        data = _valid_question_data()
        data["id"] = "custom-id-123"

        question = repo.create_question(data)

        assert question.id == "custom-id-123"

    def test_rejects_invalid_data(self, db_session: Session):
        """不正なデータは ValueError でリジェクトする"""
        repo = QuestionRepository(db_session)
        data = _valid_question_data()
        data["text"] = ""  # 空テキストは不正

        with pytest.raises(ValueError) as exc_info:
            repo.create_question(data)

        assert "問題データが不正です" in str(exc_info.value)

    def test_rejects_missing_choices(self, db_session: Session):
        """選択肢が不足するデータはリジェクトする"""
        repo = QuestionRepository(db_session)
        data = _valid_question_data()
        del data["choice_3"]

        with pytest.raises(ValueError):
            repo.create_question(data)

    def test_rejects_invalid_difficulty(self, db_session: Session):
        """無効な難易度はリジェクトする"""
        repo = QuestionRepository(db_session)
        data = _valid_question_data()
        data["difficulty"] = "超上級"

        with pytest.raises(ValueError):
            repo.create_question(data)


class TestGetQuestionById:
    """get_question_by_id メソッドのテスト"""

    def test_retrieves_existing_question(self, db_session: Session):
        """保存済みの問題を ID で取得できる"""
        repo = QuestionRepository(db_session)
        data = _valid_question_data()
        data["id"] = "test-question-1"
        repo.create_question(data)

        result = repo.get_question_by_id("test-question-1")

        assert result is not None
        assert result.id == "test-question-1"
        assert result.text == data["text"]

    def test_returns_none_for_nonexistent_id(self, db_session: Session):
        """存在しない ID は None を返す"""
        repo = QuestionRepository(db_session)

        result = repo.get_question_by_id("nonexistent-id")

        assert result is None


class TestGetQuestionsByCourse:
    """get_questions_by_course メソッドのテスト"""

    def test_retrieves_questions_for_course(self, db_session: Session):
        """コース ID で問題を取得できる"""
        repo = QuestionRepository(db_session)

        for i in range(3):
            data = _valid_question_data()
            data["id"] = f"q-{i}"
            data["text"] = f"問題{i}"
            repo.create_question(data)

        results = repo.get_questions_by_course("course-chuyo-basic")

        assert len(results) == 3

    def test_returns_empty_for_nonexistent_course(self, db_session: Session):
        """存在しないコースの場合は空リストを返す"""
        repo = QuestionRepository(db_session)

        results = repo.get_questions_by_course("nonexistent-course")

        assert results == []


class TestGetQuestionsByDomain:
    """get_questions_by_domain メソッドのテスト"""

    def test_retrieves_questions_for_domain(self, db_session: Session):
        """ドメインで問題をフィルタリングして取得できる"""
        repo = QuestionRepository(db_session)

        data1 = _valid_question_data()
        data1["id"] = "q-cloud-1"
        data1["exam_domain"] = "Cloud Concepts"
        repo.create_question(data1)

        data2 = _valid_question_data()
        data2["id"] = "q-security-1"
        data2["exam_domain"] = "Security"
        repo.create_question(data2)

        results = repo.get_questions_by_domain("Cloud Concepts")

        assert len(results) == 1
        assert results[0].exam_domain == "Cloud Concepts"

    def test_returns_empty_for_nonexistent_domain(self, db_session: Session):
        """存在しないドメインの場合は空リストを返す"""
        repo = QuestionRepository(db_session)

        results = repo.get_questions_by_domain("Nonexistent Domain")

        assert results == []


class TestRoundTrip:
    """データの保存と取得のラウンドトリップテスト"""

    def test_all_fields_preserved(self, db_session: Session):
        """保存した問題の全フィールドが取得時に保持される"""
        repo = QuestionRepository(db_session)
        data = _valid_question_data()
        data["id"] = "roundtrip-test"

        created = repo.create_question(data)
        retrieved = repo.get_question_by_id("roundtrip-test")

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.text == created.text
        assert retrieved.choice_1 == created.choice_1
        assert retrieved.choice_2 == created.choice_2
        assert retrieved.choice_3 == created.choice_3
        assert retrieved.choice_4 == created.choice_4
        assert retrieved.correct_choice_index == created.correct_choice_index
        assert retrieved.ehime_trivia == created.ehime_trivia
        assert retrieved.aws_ai_explanation == created.aws_ai_explanation
        assert retrieved.course_id == created.course_id
        assert retrieved.difficulty == created.difficulty
        assert retrieved.exam_domain == created.exam_domain
