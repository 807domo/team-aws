"""
愛媛探索AIクイズ - 勉強ページルーター

AWS・AI用語集を表示する。
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.data.database import get_db
from app.data.glossary_repository import GlossaryRepository

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/study", response_class=HTMLResponse)
async def study_page(request: Request, db: Session = Depends(get_db)):
    """勉強ページ"""
    repo = GlossaryRepository(db)
    glossary = repo.get_all_grouped_by_category()

    return templates.TemplateResponse(
        request,
        "study.html",
        context={
            "glossary": glossary,
        },
    )