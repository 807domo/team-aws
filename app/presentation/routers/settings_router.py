"""
愛媛探索AIクイズ - 設定ルーター

ユーザー設定（APIキーなど）の表示・更新を行う。
"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.data.database import get_db
from app.data.models import UserModel
from app.presentation.dependencies import get_current_user_id

router = APIRouter(prefix="/settings", tags=["settings"])
templates = Jinja2Templates(directory="app/templates")


def _mask_key(key: str) -> str:
    """APIキーをマスクして表示用にする。"""
    if not key:
        return ""
    if len(key) <= 8:
        return "****"
    return key[:4] + "..." + key[-4:]


@router.get("", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """設定画面を表示する。"""
    user = db.query(UserModel).filter(UserModel.id == user_id).first()

    current_key = getattr(user, "gemini_api_key", None) or ""
    has_key = bool(current_key)

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
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    api_key: str = Form(default=""),
    action: str = Form(default="save"),
):
    """APIキーを保存または削除する。"""
    user = db.query(UserModel).filter(UserModel.id == user_id).first()

    if action == "delete":
        # キーを削除
        user.gemini_api_key = None
        db.commit()
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
        return templates.TemplateResponse(
            request,
            "settings.html",
            context={
                "current_key_masked": "",
                "has_key": bool(getattr(user, "gemini_api_key", None)),
                "message": "APIキーを入力してください",
                "message_type": "error",
            },
        )

    user.gemini_api_key = api_key
    db.commit()

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
