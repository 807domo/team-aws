"""
愛媛探索AIクイズ - 設定ルーター

ユーザー設定（APIキーなど）の表示・更新を行う。
"""

import os

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Depends

from app.data.repository_factory import get_user_repository
from app.presentation.dependencies import get_current_user_id

router = APIRouter(prefix="/settings", tags=["settings"])
templates = Jinja2Templates(directory="app/templates")


def _get_user_repo_and_db():
    """環境に応じたユーザーリポジトリとDBセッションを返す。

    Returns:
        (user_repo, db_session or None)
    """
    use_dynamodb = os.environ.get("USE_DYNAMODB", "0") == "1"
    if use_dynamodb:
        return get_user_repository(), None
    else:
        from app.data.database import SessionLocal
        db = SessionLocal()
        return get_user_repository(db), db


@router.get("", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
):
    """設定画面を表示する。"""
    use_dynamodb = os.environ.get("USE_DYNAMODB", "0") == "1"

    if use_dynamodb:
        user_repo = get_user_repository()
        api_key = user_repo.get_gemini_api_key(user_id)
    else:
        from app.data.database import SessionLocal
        from app.data.models import UserModel
        db = SessionLocal()
        try:
            user = db.query(UserModel).filter(UserModel.id == user_id).first()
            api_key = getattr(user, "gemini_api_key", None) if user else None
        finally:
            db.close()

    has_key = bool(api_key)

    return templates.TemplateResponse(
        request,
        "settings.html",
        context={
            "current_key_masked": "",
            "has_key": has_key,
            "message": None,
            "message_type": None,
        },
    )


@router.post("/api-key", response_class=HTMLResponse)
async def save_api_key(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    api_key: str = Form(default=""),
    action: str = Form(default="save"),
):
    """APIキーを保存または削除する。"""
    use_dynamodb = os.environ.get("USE_DYNAMODB", "0") == "1"

    if action == "delete":
        if use_dynamodb:
            user_repo = get_user_repository()
            user_repo.set_gemini_api_key(user_id, None)
        else:
            from app.data.database import SessionLocal
            from app.data.models import UserModel
            db = SessionLocal()
            try:
                user = db.query(UserModel).filter(UserModel.id == user_id).first()
                if user:
                    user.gemini_api_key = None
                    db.commit()
            finally:
                db.close()

        return templates.TemplateResponse(
            request,
            "settings.html",
            context={
                "current_key_masked": "",
                "has_key": False,
                "message": "APIキーを削除しました",
                "message_type": "success",
            },
        )

    # キーを保存
    api_key = api_key.strip()
    if not api_key:
        # 現在のキー有無を確認
        if use_dynamodb:
            user_repo = get_user_repository()
            existing_key = user_repo.get_gemini_api_key(user_id)
        else:
            from app.data.database import SessionLocal
            from app.data.models import UserModel
            db = SessionLocal()
            try:
                user = db.query(UserModel).filter(UserModel.id == user_id).first()
                existing_key = getattr(user, "gemini_api_key", None) if user else None
            finally:
                db.close()

        return templates.TemplateResponse(
            request,
            "settings.html",
            context={
                "current_key_masked": "",
                "has_key": bool(existing_key),
                "message": "APIキーを入力してください",
                "message_type": "error",
            },
        )

    # キーを保存
    if use_dynamodb:
        user_repo = get_user_repository()
        user_repo.set_gemini_api_key(user_id, api_key)
    else:
        from app.data.database import SessionLocal
        from app.data.models import UserModel
        db = SessionLocal()
        try:
            user = db.query(UserModel).filter(UserModel.id == user_id).first()
            if user:
                user.gemini_api_key = api_key
                db.commit()
        finally:
            db.close()

    return templates.TemplateResponse(
        request,
        "settings.html",
        context={
            "current_key_masked": "",
            "has_key": True,
            "message": "APIキーを保存しました",
            "message_type": "success",
        },
    )
