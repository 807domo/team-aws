"""
愛媛探索AIクイズ - コース選択ルーター

GET / でコース選択画面を表示する。
地域別（中予・南予・東予）にグルーピングされたコース一覧を返す。
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.domain.models import Region
from app.domain.quiz_service import QuizService
from app.presentation.dependencies import get_quiz_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def course_select(
    request: Request,
    quiz_service: QuizService = Depends(get_quiz_service),
):
    """コース選択画面を表示する。

    全地域のコースを取得し、地域別タブでグルーピング表示する。
    コースがない地域は「準備中」バッジを表示する。
    """
    courses_by_region = quiz_service.get_courses()

    # テンプレートに渡すデータを構築
    regions = [
        {
            "key": region.name,
            "label": region.value,
            "courses": courses_by_region.get(region, []),
            "available": len(courses_by_region.get(region, [])) > 0,
        }
        for region in Region
    ]

    return templates.TemplateResponse(
        request,
        "course_select.html",
        context={
            "regions": regions,
            "active_region": Region.CHUYO.name,
        },
    )
