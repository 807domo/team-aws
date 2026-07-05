"""
愛媛探索AIクイズ - Bookmark Repository

ブックマークデータへのアクセスを提供するリポジトリクラス。
SQLAlchemy Session をコンストラクタインジェクションで受け取り、テスト容易性を確保する。
"""

import uuid

from sqlalchemy.orm import Session

from app.data.models import BookmarkModel


class BookmarkRepository:
    """ブックマークデータへのアクセスを提供するリポジトリ"""

    def __init__(self, session: Session) -> None:
        self._db = session

    def add(self, user_id: str, question_id: str) -> str:
        """ブックマークを追加する。

        UUIDを生成してブックマークを永続化する。

        Args:
            user_id: ユーザーID
            question_id: 問題ID

        Returns:
            生成されたブックマークID
        """
        bookmark_id = str(uuid.uuid4())
        bookmark = BookmarkModel(
            id=bookmark_id,
            user_id=user_id,
            question_id=question_id,
        )
        self._db.add(bookmark)
        self._db.commit()
        return bookmark_id

    def remove(self, user_id: str, question_id: str) -> bool:
        """ブックマークを削除する。

        Args:
            user_id: ユーザーID
            question_id: 問題ID

        Returns:
            削除できた場合True、対象が存在しなかった場合False
        """
        bookmark = (
            self._db.query(BookmarkModel)
            .filter(
                BookmarkModel.user_id == user_id,
                BookmarkModel.question_id == question_id,
            )
            .first()
        )
        if bookmark is None:
            return False
        self._db.delete(bookmark)
        self._db.commit()
        return True

    def toggle(self, user_id: str, question_id: str) -> bool:
        """ブックマークをトグルする。

        既にブックマークが存在する場合は削除し、存在しない場合は追加する。

        Args:
            user_id: ユーザーID
            question_id: 問題ID

        Returns:
            追加した場合True、削除した場合False
        """
        if self.exists(user_id, question_id):
            self.remove(user_id, question_id)
            return False
        else:
            self.add(user_id, question_id)
            return True

    def get_by_user(self, user_id: str) -> list[dict]:
        """ユーザーのブックマーク一覧を取得する。

        作成日時の降順（新しい順）でソートして返す。

        Args:
            user_id: ユーザーID

        Returns:
            ブックマーク情報のリスト。各要素は {id, user_id, question_id, created_at} の辞書。
        """
        bookmarks = (
            self._db.query(BookmarkModel)
            .filter(BookmarkModel.user_id == user_id)
            .order_by(BookmarkModel.created_at.desc())
            .all()
        )
        return [
            {
                "id": bookmark.id,
                "user_id": bookmark.user_id,
                "question_id": bookmark.question_id,
                "created_at": bookmark.created_at,
            }
            for bookmark in bookmarks
        ]

    def exists(self, user_id: str, question_id: str) -> bool:
        """ブックマークが存在するか確認する。

        Args:
            user_id: ユーザーID
            question_id: 問題ID

        Returns:
            存在する場合True、しない場合False
        """
        bookmark = (
            self._db.query(BookmarkModel)
            .filter(
                BookmarkModel.user_id == user_id,
                BookmarkModel.question_id == question_id,
            )
            .first()
        )
        return bookmark is not None
