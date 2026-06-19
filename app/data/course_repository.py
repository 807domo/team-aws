"""
愛媛探索AIクイズ - Course Repository

コースデータへのアクセスを提供するリポジトリクラス。
SQLAlchemy Session をコンストラクタインジェクションで受け取り、テスト容易性を確保する。
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.data.models import CourseModel
from app.domain.models import Course, Difficulty, Region


class CourseRepository:
    """コースデータへのアクセスを提供するリポジトリ"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_all_courses(self) -> list[Course]:
        """全コースを取得する"""
        course_models = self._session.query(CourseModel).all()
        return [self._to_domain(model) for model in course_models]

    def get_courses_by_region(self, region: Region) -> list[Course]:
        """指定された地域のコースを取得する"""
        course_models = (
            self._session.query(CourseModel)
            .filter(CourseModel.region == region.value)
            .all()
        )
        return [self._to_domain(model) for model in course_models]

    def get_course_by_id(self, course_id: str) -> Optional[Course]:
        """IDを指定してコースを取得する。存在しない場合は None を返す"""
        model = self._session.query(CourseModel).filter(CourseModel.id == course_id).first()
        if model is None:
            return None
        return self._to_domain(model)

    def get_courses_grouped_by_region(self) -> dict[Region, list[Course]]:
        """全コースを地域別にグルーピングして返す"""
        # 全地域を初期化（コースがない地域も空リストで含める）
        grouped: dict[Region, list[Course]] = {region: [] for region in Region}

        all_courses = self.get_all_courses()
        for course in all_courses:
            grouped[course.region].append(course)

        return grouped

    @staticmethod
    def _to_domain(model: CourseModel) -> Course:
        """SQLAlchemy ORM モデルをドメインモデルに変換する"""
        return Course(
            id=model.id,
            name=model.name,
            region=Region(model.region),
            difficulty=Difficulty(model.difficulty),
            description=model.description,
        )
