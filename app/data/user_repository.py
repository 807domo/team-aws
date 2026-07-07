"""
愛媛探索AIクイズ - User Repository

ユーザーの作成・ID検索・表示名検索を行うリポジトリ。
SQLAlchemy Session をコンストラクタインジェクションで受け取る。
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.data.models import UserModel


class UserRepository:
    """ユーザーリポジトリ（SQLAlchemy版）"""

    def __init__(self, session: Session) -> None:
        self._db = session

    def create(self, user_id: str, display_name: str, password_hash: str) -> None:
        """新規ユーザーを作成する。

        Args:
            user_id: ユーザーID
            display_name: 表示名
            password_hash: パスワードハッシュ
        """
        user = UserModel(
            id=user_id,
            display_name=display_name,
            password_hash=password_hash,
        )
        self._db.add(user)
        self._db.commit()

    def get_by_id(self, user_id: str) -> Optional[dict]:
        """ユーザーIDで検索する。

        Args:
            user_id: ユーザーID

        Returns:
            ユーザー情報の辞書。存在しない場合はNone。
        """
        user = (
            self._db.query(UserModel)
            .filter(UserModel.id == user_id)
            .first()
        )
        if user is None:
            return None
        return self._to_dict(user)

    def get_by_display_name(self, display_name: str) -> Optional[dict]:
        """表示名で検索する。

        Args:
            display_name: 表示名

        Returns:
            ユーザー情報の辞書。存在しない場合はNone。
        """
        user = (
            self._db.query(UserModel)
            .filter(UserModel.display_name == display_name)
            .first()
        )
        if user is None:
            return None
        return self._to_dict(user)

    def get_gemini_api_key(self, user_id: str) -> Optional[str]:
        """ユーザーのGemini APIキーを取得する。

        Args:
            user_id: ユーザーID

        Returns:
            APIキー文字列 or None
        """
        user = (
            self._db.query(UserModel)
            .filter(UserModel.id == user_id)
            .first()
        )
        if user is None:
            return None
        return getattr(user, "gemini_api_key", None)

    def set_gemini_api_key(self, user_id: str, api_key: Optional[str]) -> None:
        """ユーザーのGemini APIキーを設定する。

        Args:
            user_id: ユーザーID
            api_key: APIキー文字列（Noneで削除）
        """
        user = (
            self._db.query(UserModel)
            .filter(UserModel.id == user_id)
            .first()
        )
        if user:
            user.gemini_api_key = api_key
            self._db.commit()

    @staticmethod
    def _to_dict(user: UserModel) -> dict:
        """UserModelからユーザー情報辞書に変換する。"""
        return {
            "id": user.id,
            "display_name": user.display_name,
            "password_hash": user.password_hash,
            "created_at": user.created_at,
            "total_xp": user.total_xp,
            "level": user.level,
            "gemini_api_key": getattr(user, "gemini_api_key", None),
        }
