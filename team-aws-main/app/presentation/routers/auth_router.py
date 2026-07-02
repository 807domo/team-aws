"""
愛媛探索AIクイズ - 認証ルーター

新規登録・ログイン・ログアウトのエンドポイントを提供する。
セッションはCookieベースで管理する。
"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.data.database import get_db
from app.domain.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="app/templates")

# Cookieの設定
SESSION_COOKIE_NAME = "session_token"


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """新規登録画面を表示する。"""
    return templates.TemplateResponse(
        request,
        "register.html",
        context={"error": None},
    )


@router.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    display_name: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    db: Session = Depends(get_db),
):
    """新規登録を処理する。

    成功時はトップページにリダイレクト。
    失敗時はエラーメッセージ付きで登録画面を再表示。
    """
    # パスワード確認チェック
    if password != password_confirm:
        return templates.TemplateResponse(
            request,
            "register.html",
            context={"error": "パスワードが一致しません", "display_name": display_name},
        )

    auth_service = AuthService(db)

    try:
        user_id, token = auth_service.register(display_name, password)
    except ValueError as e:
        return templates.TemplateResponse(
            request,
            "register.html",
            context={"error": str(e), "display_name": display_name},
        )

    # ログイン成功 → Cookie設定してトップへリダイレクト
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7日間
    )
    return response


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """ログイン画面を表示する。"""
    return templates.TemplateResponse(
        request,
        "login.html",
        context={"error": None},
    )


@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    display_name: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """ログインを処理する。

    成功時はトップページにリダイレクト。
    失敗時はエラーメッセージ付きでログイン画面を再表示。
    """
    auth_service = AuthService(db)

    try:
        user_id, token = auth_service.login(display_name, password)
    except ValueError as e:
        return templates.TemplateResponse(
            request,
            "login.html",
            context={"error": str(e), "display_name": display_name},
        )

    # ログイン成功 → Cookie設定してトップへリダイレクト
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7日間
    )
    return response


@router.get("/logout")
async def logout(request: Request):
    """ログアウトしてログイン画面にリダイレクトする。"""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        from app.domain.auth_service import _active_sessions
        _active_sessions.pop(token, None)

    response = RedirectResponse(url="/auth/login", status_code=303)
    response.delete_cookie(key=SESSION_COOKIE_NAME)
    return response
