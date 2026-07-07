"""
愛媛探索AIクイズ - カスタムステージルーター

ユーザーが既存問題を組み合わせてオリジナルステージを作成・プレイする機能。
"""

import os
import uuid
import logging
import random
from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.data.repository_factory import (
    get_question_repository,
    get_user_record_repository,
)
from app.domain.models import AnswerRecord, Question
from app.presentation.dependencies import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/custom-stage", tags=["custom-stage"])
templates = Jinja2Templates(directory="app/templates")

# インメモリでカスタムステージセッションを管理
_custom_sessions: dict[str, dict] = {}


def _get_db_session():
    """SQLiteモード時のみDBセッションを返す。DynamoDBモードではNone。"""
    if os.environ.get("USE_DYNAMODB", "0") == "1":
        return None
    from app.data.database import SessionLocal
    return SessionLocal()


@router.get("/create", response_class=HTMLResponse)
async def create_stage_page(
    request: Request,
    user_id: str = Depends(get_current_user_id),
):
    """カスタムステージ作成画面を表示。分野・問題数・難易度を設定できる。"""
    use_dynamodb = os.environ.get("USE_DYNAMODB", "0") == "1"

    if use_dynamodb:
        question_repo = get_question_repository()
        domains = question_repo.get_all_domains()
    else:
        from sqlalchemy.orm import Session
        from app.data.database import get_db, SessionLocal
        from app.data.models import QuestionModel as QM

        db = SessionLocal()
        try:
            domain_rows = (
                db.query(QM.exam_domain)
                .filter(QM.exam_domain != None, QM.exam_domain != "")
                .distinct()
                .all()
            )
            domains = sorted(r[0] for r in domain_rows)
        finally:
            db.close()

    return templates.TemplateResponse(
        request,
        "custom_stage_create.html",
        context={"domains": domains},
    )


@router.post("/start", response_class=HTMLResponse)
async def start_custom_stage(
    request: Request,
    user_id: str = Depends(get_current_user_id),
):
    """設定に基づいて問題をランダム選択しカスタムステージを開始する。"""
    use_dynamodb = os.environ.get("USE_DYNAMODB", "0") == "1"

    form = await request.form()
    selected_domains = form.getlist("domains")
    count = int(form.get("count", "5"))
    difficulty = form.get("difficulty", "all")

    if not selected_domains:
        return RedirectResponse(url="/custom-stage/create", status_code=303)

    if use_dynamodb:
        question_repo = get_question_repository()
        candidates = question_repo.get_questions_filtered(selected_domains, difficulty)
    else:
        from app.data.database import SessionLocal
        from app.data.models import QuestionModel as QM

        db = SessionLocal()
        try:
            query = db.query(QM).filter(QM.exam_domain.in_(selected_domains))
            if difficulty != "all":
                query = query.filter(QM.difficulty == difficulty)
            candidate_models = query.all()

            question_repo = get_question_repository(db)
            candidates = []
            for model in candidate_models:
                q = question_repo.get_question_by_id(model.id)
                if q:
                    candidates.append(q)
        finally:
            db.close()

    if not candidates:
        return RedirectResponse(url="/custom-stage/create", status_code=303)

    # ランダムに指定数を選択
    count = min(count, len(candidates))
    questions = random.sample(candidates, count)

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

    # 回答記録を保存
    try:
        use_dynamodb = os.environ.get("USE_DYNAMODB", "0") == "1"
        if use_dynamodb:
            record_repo = get_user_record_repository()
        else:
            from app.data.database import SessionLocal
            db = SessionLocal()
            record_repo = get_user_record_repository(db)

        record = AnswerRecord(
            id=str(uuid.uuid4()),
            user_id=user_id,
            question_id=question.id,
            course_id="custom-stage",
            selected_choice_index=choice_index,
            is_correct=is_correct,
            answered_at=datetime.now(),
        )
        record_repo.save_answer_record(record)

        if not use_dynamodb:
            db.commit()
            db.close()
    except Exception as e:
        logger.warning(f"回答記録の保存に失敗: {e}")
        if not use_dynamodb and 'db' in locals():
            db.rollback()
            db.close()

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
