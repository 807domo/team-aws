"""
愛媛探索AIクイズ - 認証サービス

ユーザーの新規登録・ログイン・セッション管理を行うサービスクラス。
プロトタイプ用のシンプルなCookieセッション方式を採用。
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.data.models import UserModel


# セッション管理（インメモリ）
# key: session_token, value: user_id
_active_sessions: dict[str, str] = {}


def hash_password(password: str) -> str:
    """パスワードをSHA-256でハッシュ化する。

    プロトタイプ用の簡易実装。
    本番環境ではbcrypt等のより安全なハッシュ関数を使用すること。

    Args:
        password: 生パスワード

    Returns:
        ハッシュ化されたパスワード文字列
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """パスワードの検証を行う。

    Args:
        password: 入力された生パスワード
        hashed: 保存されたハッシュ値

    Returns:
        一致すればTrue
    """
    return hash_password(password) == hashed


class AuthService:
    """認証サービス。

    ユーザーの登録、ログイン、セッション管理を提供する。
    """

    def __init__(self, db_session: Session) -> None:
        self._db = db_session

    def register(self, display_name: str, password: str) -> tuple[str, str]:
        """新規ユーザーを登録する。

        Args:
            display_name: 表示名
            password: パスワード（4文字以上）

        Returns:
            (user_id, session_token) のタプル

        Raises:
            ValueError: 表示名が空、パスワードが短い、
                       または同名ユーザーが既に存在する場合
        """
        # バリデーション
        display_name = display_name.strip()
        if not display_name:
            raise ValueError("表示名を入力してください")
        if len(display_name) > 20:
            raise ValueError("表示名は20文字以内にしてください")
        if len(password) < 4:
            raise ValueError("パスワードは4文字以上にしてください")

        # 同名ユーザーの重複チェック
        existing = (
            self._db.query(UserModel)
            .filter(UserModel.display_name == display_name)
            .first()
        )
        if existing:
            raise ValueError("この表示名は既に使用されています")

        # ユーザー作成
        user_id = str(uuid.uuid4())
        hashed_pw = hash_password(password)

        user = UserModel(
            id=user_id,
            display_name=display_name,
            password_hash=hashed_pw,
        )
        self._db.add(user)
        self._db.commit()

        # セッション作成
        token = self._create_session(user_id)
        return user_id, token

    def login(self, display_name: str, password: str) -> tuple[str, str]:
        """ログインを行う。

        Args:
            display_name: 表示名
            password: パスワード

        Returns:
            (user_id, session_token) のタプル

        Raises:
            ValueError: 認証に失敗した場合
        """
        display_name = display_name.strip()
        if not display_name or not password:
            raise ValueError("表示名とパスワードを入力してください")

        user = (
            self._db.query(UserModel)
            .filter(UserModel.display_name == display_name)
            .first()
        )
        if user is None:
            raise ValueError("表示名またはパスワードが正しくありません")

        # パスワード未設定のユーザー（既存シードデータ等）
        if not user.password_hash:
            raise ValueError("表示名またはパスワードが正しくありません")

        if not verify_password(password, user.password_hash):
            raise ValueError("表示名またはパスワードが正しくありません")

        # セッション作成
        token = self._create_session(user.id)
        return user.id, token

    def logout(self, session_token: str) -> None:
        """ログアウト（セッション無効化）。

        Args:
            session_token: セッショントークン
        """
        _active_sessions.pop(session_token, None)

    @staticmethod
    def get_user_id_from_session(session_token: Optional[str]) -> Optional[str]:
        """セッショントークンからユーザーIDを取得する。

        Args:
            session_token: Cookieから取得したセッショントークン

        Returns:
            ユーザーID。無効なトークンの場合はNone。
        """
        if not session_token:
            return None
        return _active_sessions.get(session_token)

    @staticmethod
    def _create_session(user_id: str) -> str:
        """セッションを作成しトークンを返す。

        Args:
            user_id: ユーザーID

        Returns:
            セッショントークン
        """
        token = secrets.token_urlsafe(32)
        _active_sessions[token] = user_id
        return token
