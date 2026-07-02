"""
愛媛探索AIクイズ - Glossary Repository

用語集データへのアクセスを提供するリポジトリクラス。
"""

from sqlalchemy.orm import Session

from app.data.models import GlossaryTermModel


class GlossaryRepository:
    """用語集データへのアクセスを提供するリポジトリ"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_all_grouped_by_category(self) -> dict[str, list[dict]]:
        """全用語をカテゴリ別にグルーピングして返す。"""
        terms = (
            self._session.query(GlossaryTermModel)
            .order_by(GlossaryTermModel.category, GlossaryTermModel.sort_order)
            .all()
        )

        result: dict[str, list[dict]] = {}
        for t in terms:
            result.setdefault(t.category, []).append(
                {"term": t.term, "description": t.description}
            )
        return result