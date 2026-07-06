"""
愛媛探索AIクイズ - FastAPI アプリケーション

メインエントリーポイント。FastAPI アプリケーションの作成、
Jinja2Templates 設定、静的ファイルマウント、ルーター登録を行う。
グローバルエラーハンドラーの登録も含む。
"""

import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()  # .envファイルから環境変数を読み込む

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.data.database import DatabaseConnectionError, SessionLocal, create_tables
from app.data.seed_data import seed_database
from migrations.runner import run_migrations

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーション起動時・終了時の処理。

    起動時にデータベーステーブルを作成し、初期データを投入する。
    """
    # 起動時: テーブル作成
    create_tables()

    # 起動時: マイグレーション実行（既存テーブルへのカラム追加等）
    db = SessionLocal()
    try:
        run_migrations(db)
    finally:
        db.close()

    # 起動時: シードデータ投入（データが空の場合のみ）
    db = SessionLocal()
    try:
        seeded = seed_database(db)
        if seeded:
            logger.info("シードデータを投入しました")
    finally:
        db.close()

    # 起動時: 用語集データ投入
    db = SessionLocal()
    try:
        from app.data.glossary_seed import seed_glossary
        seeded = seed_glossary(db)
        if seeded:
            logger.info("用語集データを投入しました")
    finally:
        db.close()

    yield
    # 終了時: クリーンアップ（必要に応じて追加）


# FastAPI アプリケーション作成
app = FastAPI(
    title="愛媛探索AIクイズ",
    description="愛媛県の大学生・高専生向けAI学習プラットフォーム",
    version="0.1.0",
    lifespan=lifespan,
)

# Jinja2 テンプレート設定
templates = Jinja2Templates(directory="app/templates")

# 静的ファイル（CSS/JS）のマウント
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# =============================================================================
# 認証コンテキストミドルウェア
# =============================================================================

from starlette.middleware.base import BaseHTTPMiddleware

from app.domain.auth_service import AuthService


class AuthContextMiddleware(BaseHTTPMiddleware):
    """リクエストスコープでログインユーザー名をrequest.stateに設定するミドルウェア。"""

    async def dispatch(self, request, call_next):
        token = request.cookies.get("session_token")
        user_id = AuthService.get_user_id_from_session(token)

        request.state.current_user_name = None

        if user_id:
            try:
                from app.data.database import SessionLocal
                from app.data.models import UserModel

                db = SessionLocal()
                user = db.query(UserModel).filter(UserModel.id == user_id).first()
                if user:
                    request.state.current_user_name = user.display_name
                db.close()
            except Exception:
                pass

        response = await call_next(request)
        return response


app.add_middleware(AuthContextMiddleware)


# =============================================================================
# グローバルエラーハンドラー
# =============================================================================


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> HTMLResponse:
    """HTTPException をキャッチしてユーザーフレンドリーなエラーページを返す。"""
    # ステータスコードに応じた日本語メッセージ
    error_messages = {
        400: "リクエストが正しくありません。",
        404: "お探しのページが見つかりません。",
        500: "サーバー内部でエラーが発生しました。しばらくしてからお試しください。",
    }
    error_message = exc.detail or error_messages.get(
        exc.status_code, "エラーが発生しました。"
    )

    return templates.TemplateResponse(
        request,
        "error.html",
        context={
            "error_title": f"エラー ({exc.status_code})",
            "error_message": error_message,
            "retry_url": None,
        },
        status_code=exc.status_code,
    )


@app.exception_handler(DatabaseConnectionError)
async def database_connection_error_handler(
    request: Request, exc: DatabaseConnectionError
) -> HTMLResponse:
    """データベース接続エラーをキャッチしてエラーページを返す。"""
    logger.error("データベース接続エラー: %s", str(exc))
    return templates.TemplateResponse(
        request,
        "error.html",
        context={
            "error_title": "接続エラー",
            "error_message": "接続エラーが発生しました。しばらくしてからお試しください。",
            "retry_url": str(request.url),
        },
        status_code=503,
    )


from app.presentation.dependencies import RequiresLoginException


@app.exception_handler(RequiresLoginException)
async def requires_login_handler(request: Request, exc: RequiresLoginException):
    """未ログイン時にログイン画面へリダイレクトする。"""
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/auth/login", status_code=303)


# 注意: 汎用Exceptionハンドラーはデバッグ中は無効化
# @app.exception_handler(Exception)
# async def unhandled_exception_handler(
#     request: Request, exc: Exception
# ) -> HTMLResponse:
#     """未処理の例外をキャッチしてユーザーフレンドリーなエラーページを返す。"""
#     logger.error("未処理の例外: %s: %s", type(exc).__name__, str(exc))
#     return HTMLResponse(
#         content=f"<html><body><h1>Error</h1><pre>{type(exc).__name__}: {exc}</pre></body></html>",
#         status_code=500,
#     )


# =============================================================================
# ルーター登録
# =============================================================================

from app.presentation.routers.top_router import router as top_router

app.include_router(top_router)

from app.presentation.routers.auth_router import router as auth_router

app.include_router(auth_router)

from app.presentation.routers.course_router import router as course_router
from app.presentation.routers.results_router import router as results_router

app.include_router(course_router)
app.include_router(results_router)

from app.presentation.routers.quiz_router import router as quiz_router

app.include_router(quiz_router)

from app.presentation.routers.mock_exam_router import router as mock_exam_router

app.include_router(mock_exam_router)

from app.presentation.routers.ai_practice_router import router as ai_practice_router

app.include_router(ai_practice_router)

from app.presentation.routers.custom_stage_router import router as custom_stage_router

app.include_router(custom_stage_router)

from app.presentation.routers.study_router import router as study_router

app.include_router(study_router)

from app.presentation.routers.review_router import router as review_router

app.include_router(review_router)

from app.presentation.routers.settings_router import router as settings_router

app.include_router(settings_router)


# =============================================================================
# Lambda handler (Mangum adapter)
# =============================================================================

try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    handler = None  # Local development without mangum
