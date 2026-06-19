"""
Course Repository のユニットテスト

インメモリ SQLite を使用してリポジトリ操作を検証する。
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.data.course_repository import CourseRepository
from app.data.database import Base
from app.data.models import CourseModel
from app.domain.models import Course, Difficulty, Region


def _create_test_session() -> Session:
    """テスト用のインメモリDBセッションを作成する"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    return TestSession()


def _seed_courses(session: Session) -> None:
    """テスト用のコースデータをDBに投入する"""
    courses = [
        CourseModel(
            id="course-chuyo-basic",
            name="松山城コース（基礎）",
            region="中予",
            difficulty="基礎",
            description="松山城を題材にしたAWS基礎コース",
        ),
        CourseModel(
            id="course-chuyo-intermediate",
            name="道後温泉コース（中級）",
            region="中予",
            difficulty="中級",
            description="道後温泉を題材にしたAWS中級コース",
        ),
        CourseModel(
            id="course-nanyo-basic",
            name="宇和島コース（基礎）",
            region="南予",
            difficulty="基礎",
            description="宇和島を題材にしたAI基礎コース",
        ),
        CourseModel(
            id="course-toyo-advanced",
            name="しまなみ海道コース（上級）",
            region="東予",
            difficulty="上級",
            description="しまなみ海道を題材にしたAWS上級コース",
        ),
    ]
    session.add_all(courses)
    session.commit()


class TestGetAllCourses:
    """get_all_courses のテスト"""

    def test_empty_database_returns_empty_list(self):
        session = _create_test_session()
        repo = CourseRepository(session)
        result = repo.get_all_courses()
        assert result == []

    def test_returns_all_courses(self):
        session = _create_test_session()
        _seed_courses(session)
        repo = CourseRepository(session)
        result = repo.get_all_courses()
        assert len(result) == 4

    def test_returns_domain_models(self):
        session = _create_test_session()
        _seed_courses(session)
        repo = CourseRepository(session)
        result = repo.get_all_courses()
        for course in result:
            assert isinstance(course, Course)
            assert isinstance(course.region, Region)
            assert isinstance(course.difficulty, Difficulty)


class TestGetCoursesByRegion:
    """get_courses_by_region のテスト"""

    def test_chuyo_returns_two_courses(self):
        session = _create_test_session()
        _seed_courses(session)
        repo = CourseRepository(session)
        result = repo.get_courses_by_region(Region.CHUYO)
        assert len(result) == 2
        assert all(c.region == Region.CHUYO for c in result)

    def test_nanyo_returns_one_course(self):
        session = _create_test_session()
        _seed_courses(session)
        repo = CourseRepository(session)
        result = repo.get_courses_by_region(Region.NANYO)
        assert len(result) == 1
        assert result[0].name == "宇和島コース（基礎）"

    def test_toyo_returns_one_course(self):
        session = _create_test_session()
        _seed_courses(session)
        repo = CourseRepository(session)
        result = repo.get_courses_by_region(Region.TOYO)
        assert len(result) == 1
        assert result[0].region == Region.TOYO

    def test_region_with_no_courses_returns_empty(self):
        session = _create_test_session()
        # 中予のコースのみ追加
        session.add(
            CourseModel(
                id="course-1",
                name="テストコース",
                region="中予",
                difficulty="基礎",
                description="テスト",
            )
        )
        session.commit()
        repo = CourseRepository(session)
        result = repo.get_courses_by_region(Region.NANYO)
        assert result == []


class TestGetCourseById:
    """get_course_by_id のテスト"""

    def test_existing_course_returns_course(self):
        session = _create_test_session()
        _seed_courses(session)
        repo = CourseRepository(session)
        result = repo.get_course_by_id("course-chuyo-basic")
        assert result is not None
        assert result.id == "course-chuyo-basic"
        assert result.name == "松山城コース（基礎）"
        assert result.region == Region.CHUYO
        assert result.difficulty == Difficulty.BASIC

    def test_nonexistent_course_returns_none(self):
        session = _create_test_session()
        _seed_courses(session)
        repo = CourseRepository(session)
        result = repo.get_course_by_id("nonexistent-id")
        assert result is None

    def test_empty_database_returns_none(self):
        session = _create_test_session()
        repo = CourseRepository(session)
        result = repo.get_course_by_id("any-id")
        assert result is None


class TestGetCoursesGroupedByRegion:
    """get_courses_grouped_by_region のテスト"""

    def test_all_regions_present_in_result(self):
        session = _create_test_session()
        _seed_courses(session)
        repo = CourseRepository(session)
        result = repo.get_courses_grouped_by_region()
        # 全地域がキーとして存在する
        assert Region.CHUYO in result
        assert Region.NANYO in result
        assert Region.TOYO in result

    def test_courses_grouped_correctly(self):
        session = _create_test_session()
        _seed_courses(session)
        repo = CourseRepository(session)
        result = repo.get_courses_grouped_by_region()
        assert len(result[Region.CHUYO]) == 2
        assert len(result[Region.NANYO]) == 1
        assert len(result[Region.TOYO]) == 1

    def test_empty_database_returns_empty_lists_for_all_regions(self):
        session = _create_test_session()
        repo = CourseRepository(session)
        result = repo.get_courses_grouped_by_region()
        assert result[Region.CHUYO] == []
        assert result[Region.NANYO] == []
        assert result[Region.TOYO] == []

    def test_each_course_appears_in_exactly_one_region(self):
        session = _create_test_session()
        _seed_courses(session)
        repo = CourseRepository(session)
        result = repo.get_courses_grouped_by_region()
        all_course_ids = []
        for courses in result.values():
            all_course_ids.extend(c.id for c in courses)
        # 重複なし
        assert len(all_course_ids) == len(set(all_course_ids))
        # 全コースが含まれる
        assert len(all_course_ids) == 4
