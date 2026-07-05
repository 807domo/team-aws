"""
愛媛探索AIクイズ - 復習ルーター

間違えた問題の復習機能を提供する。
GET /review/mistakes — 不正解問題一覧を表示
POST /review/start — 復習クイズを開始
GET /review/{session_id}/question — 復習問題を表示
POST /review/{session_id}/answer — 復習回答を送信
GET /review/{session_id}/result — 復習結果を表示
"""

import uuid
import random
from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.data.database import get_db
from app.data.repository_factory import get_user_record_repository, get_question_repository
from app.domain.models import AnswerRecord
from app.presentation.dependencies import get_current_user_id

router = APIRouter(prefix="/review", tags=["review"])
templates = Jinja2Templates(directory="app/templates")

# インメモリで復習セッションを管理
_review_sessions: dict[str, dict] = {}


@router.get("/mistakes", response_class=HTMLResponse)
async def review_mistakes(
    request: Request,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """不正解問題の一覧を表示する。"""
    user_record_repo = get_user_record_repository(db)
    question_repo = get_question_repository(db)

    # 不正解だった問題IDを取得（重複排除）
    all_records = user_record_repo.get_records_by_user(user_id)
    incorrect_question_ids = list({r.question_id for r in all_records if not r.is_correct})

    # 問題詳細を取得
    questions_by_domain: dict[str, list] = {}
    for qid in incorrect_question_ids:
        question = question_repo.get_question_by_id(qid)
        if question:
            domain = question.exam_domain or "その他"
            if domain not in questions_by_domain:
                questions_by_domain[domain] = []
            questions_by_domain[domain].append({
                "id": question.id,
                "text": question.text,
                "domain": domain,
            })

    total_count = sum(len(qs) for qs in questions_by_domain.values())

    return templates.TemplateResponse(
        request,
        "review_mistakes.html",
        context={
            "questions_by_domain": questions_by_domain,
            "total_count": total_count,
        },
    )


@router.post("/start", response_class=HTMLResponse)
async def start_review(
    request: Request,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """復習クイズを開始する。"""
    user_record_repo = get_user_record_repository(db)
    question_repo = get_question_repository(db)

    form = await request.form()
    mode = form.get("mode", "all")  # "all" or "random5"

    # 不正解問題を取得
    all_records = user_record_repo.get_records_by_user(user_id)
    incorrect_question_ids = list({r.question_id for r in all_records if not r.is_correct})

    if not incorrect_question_ids:
        return RedirectResponse(url="/review/mistakes", status_code=303)

    # 問題を取得
    questions = []
    for qid in incorrect_question_ids:
        q = question_repo.get_question_by_id(qid)
        if q:
            questions.append(q)

    if not questions:
        return RedirectResponse(url="/review/mistakes", status_code=303)

    # ランダム5問モード
    if mode == "random5":
        questions = random.sample(questions, min(5, len(questions)))
    else:
        random.shuffle(questions)

    # セッション作成
    session_id = str(uuid.uuid4())
    _review_sessions[session_id] = {
        "questions": questions,
        "current_index": 0,
        "correct_count": 0,
        "total_count": len(questions),
        "user_id": user_id,
    }

    return RedirectResponse(
        url=f"/review/{session_id}/question",
        status_code=303,
    )


@router.get("/{session_id}/question", response_class=HTMLResponse)
async def show_review_question(
    session_id: str,
    request: Request,
):
    """復習問題を表示する。"""
    session = _review_sessions.get(session_id)
    if session is None:
        return RedirectResponse(url="/review/mistakes", status_code=303)

    idx = session["current_index"]
    questions = session["questions"]

    if idx >= len(questions):
        return RedirectResponse(
            url=f"/review/{session_id}/result", status_code=303
        )

    question = questions[idx]
    choices = [question.choice_1, question.choice_2,
               question.choice_3, question.choice_4]

    return templates.TemplateResponse(
        request,
        "review_quiz.html",
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
async def submit_review_answer(
    session_id: str,
    request: Request,
    choice_index: int = Form(...),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """復習回答を送信し記録する。"""
    session = _review_sessions.get(session_id)
    if session is None:
        return RedirectResponse(url="/review/mistakes", status_code=303)

    idx = session["current_index"]
    question = session["questions"][idx]
    is_correct = choice_index == question.correct_choice_index

    if is_correct:
        session["correct_count"] += 1

    # DB記録
    try:
        user_record_repo = get_user_record_repository(db)
        record = AnswerRecord(
            id=str(uuid.uuid4()),
            user_id=user_id,
            question_id=question.id,
            course_id=question.course_id if question.course_id else "review",
            selected_choice_index=choice_index,
            is_correct=is_correct,
            answered_at=datetime.now(),
        )
        user_record_repo.save_answer_record(record)
    except Exception:
        pass

    session["current_index"] += 1

    choices = [question.choice_1, question.choice_2,
               question.choice_3, question.choice_4]

    return templates.TemplateResponse(
        request,
        "review_explanation.html",
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
async def show_review_result(
    session_id: str,
    request: Request,
):
    """復習クイズの結果を表示する。"""
    session = _review_sessions.get(session_id)
    if session is None:
        return RedirectResponse(url="/review/mistakes", status_code=303)

    correct = session["correct_count"]
    total = session["total_count"]
    accuracy = round((correct / total * 100), 1) if total > 0 else 0

    # セッション削除
    del _review_sessions[session_id]

    return templates.TemplateResponse(
        request,
        "review_result.html",
        context={
            "correct_count": correct,
            "total_count": total,
            "accuracy": accuracy,
        },
    )
