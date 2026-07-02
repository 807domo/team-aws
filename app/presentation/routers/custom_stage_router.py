"""
愛媛探索AIクイズ - カスタムステージルーター

ユーザーが既存問題を組み合わせてオリジナルステージを作成・プレイする機能。
"""

import uuid
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.data.database import get_db
from app.data.models import AnswerRecordModel
from app.data.question_repository import QuestionRepository
from app.domain.models import Question
from app.presentation.dependencies import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/custom-stage", tags=["custom-stage"])
templates = Jinja2Templates(directory="app/templates")

# インメモリでカスタムステージセッションを管理
_custom_sessions: dict[str, dict] = {}


@router.get("/create", response_class=HTMLResponse)
async def create_stage_page(
    request: Request,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """カスタムステージ作成画面を表示。全問題一覧から選択できる。"""
    question_repo = QuestionRepository(db)

    # 全問題を取得（ドメイン別にグループ化）
    from app.data.seed_data import QUESTIONS
    domains = {}
    for q in QUESTIONS:
        domain = q.get("exam_domain", "その他")
        if domain not in domains:
            domains[domain] = []
        domains[domain].append({
            "id": q["id"],
            "text": q["text"][:60] + "..." if len(q["text"]) > 60 else q["text"],
            "domain": domain,
        })

    return templates.TemplateResponse(
        request,
        "custom_stage_create.html",
        context={"domains": domains},
    )


@router.post("/start", response_class=HTMLResponse)
async def start_custom_stage(
    request: Request,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """選択された問題でカスタムステージを開始する。"""
    form = await request.form()
    selected_ids = form.getlist("question_ids")

    if not selected_ids or len(selected_ids) < 1:
        return RedirectResponse(url="/custom-stage/create", status_code=303)

    # 問題を取得
    question_repo = QuestionRepository(db)
    questions = []
    for qid in selected_ids:
        q = question_repo.get_question_by_id(qid)
        if q:
            questions.append(q)

    if not questions:
        return RedirectResponse(url="/custom-stage/create", status_code=303)

    # セッション作成
    session_id = str(uuid.uuid4())
    _custom_sessions[session_id] = {
        "questions": questions,
        "current_index": 0,
        "correct_count": 0,
        "total_count": len(questions),
        "user_id": user_id,
    }

    return RedirectResponse(
        url=f"/custom-stage/{session_id}/question",
        status_code=303,
    )


@router.get("/{session_id}/question", response_class=HTMLResponse)
async def show_custom_question(
    session_id: str,
    request: Request,
):
    """カスタムステージの問題を表示する。"""
    session = _custom_sessions.get(session_id)
    if session is None:
        return RedirectResponse(url="/custom-stage/create", status_code=303)

    idx = session["current_index"]
    questions = session["questions"]

    if idx >= len(questions):
        return RedirectResponse(
            url=f"/custom-stage/{session_id}/result", status_code=303
        )

    question = questions[idx]
    choices = [question.choice_1, question.choice_2,
               question.choice_3, question.choice_4]

    return templates.TemplateResponse(
        request,
        "custom_stage_quiz.html",
        context={
            "session_id": session_id,
            "question": question,
            "choices": choices,
            "question_index": idx,
            "total_questions": len(questions),
            "progress_percent": int((idx / len(questions)) * 100),
        },
    )


@router.post("/{session_id}/answer", response_class=HTMLResponse)
async def submit_custom_answer(
    session_id: str,
    request: Request,
    choice_index: int = Form(...),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """カスタムステージの回答を送信し記録する。"""
    session = _custom_sessions.get(session_id)
    if session is None:
        return RedirectResponse(url="/custom-stage/create", status_code=303)

    idx = session["current_index"]
    question = session["questions"][idx]
    is_correct = choice_index == question.correct_choice_index

    if is_correct:
        session["correct_count"] += 1

    # DB記録
    try:
        record = AnswerRecordModel(
            id=str(uuid.uuid4()),
            user_id=user_id,
            question_id=question.id,
            course_id="custom-stage",
            selected_choice_index=choice_index,
            is_correct=is_correct,
            answered_at=datetime.now(),
        )
        db.add(record)
        db.commit()
    except Exception:
        db.rollback()

    session["current_index"] += 1

    choices = [question.choice_1, question.choice_2,
               question.choice_3, question.choice_4]

    return templates.TemplateResponse(
        request,
        "custom_stage_explanation.html",
        context={
            "session_id": session_id,
            "question": question,
            "choices": choices,
            "is_correct": is_correct,
            "selected_index": choice_index,
            "correct_index": question.correct_choice_index,
            "question_index": idx,
            "total_questions": session["total_count"],
            "is_last": session["current_index"] >= session["total_count"],
            "explanation": question.aws_ai_explanation,
        },
    )


@router.get("/{session_id}/result", response_class=HTMLResponse)
async def show_custom_result(
    session_id: str,
    request: Request,
):
    """カスタムステージの結果を表示する。"""
    session = _custom_sessions.get(session_id)
    if session is None:
        return RedirectResponse(url="/custom-stage/create", status_code=303)

    correct = session["correct_count"]
    total = session["total_count"]
    accuracy = round((correct / total * 100), 1) if total > 0 else 0

    # セッション削除
    del _custom_sessions[session_id]

    return templates.TemplateResponse(
        request,
        "custom_stage_result.html",
        context={
            "correct_count": correct,
            "total_count": total,
            "accuracy": accuracy,
        },
    )
