"""
愛媛探索AIクイズ - AI練習問題ルーター

学習結果に基づいてAIが自動生成した問題で練習するエンドポイント。
弱点ドメインを分析し、Gemini APIで問題を生成する。
"""

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.data.database import get_db
from app.data.question_repository import QuestionRepository
from app.data.user_record_repository import UserRecordRepository
from app.domain.gemini_question_generator import GeminiQuestionGenerator
from app.domain.models import AnswerRecord, Question, WeakArea
from app.domain.scoring import identify_weak_areas
from app.presentation.dependencies import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-practice", tags=["ai-practice"])
templates = Jinja2Templates(directory="app/templates")

MIN_ANSWERS_FOR_AI = 5  # AI生成に必要な最低回答数

# シングルトンインスタンス
_generator: GeminiQuestionGenerator | None = None


def _get_generator() -> GeminiQuestionGenerator:
    global _generator
    if _generator is None:
        _generator = GeminiQuestionGenerator()
    return _generator


@router.get("/start", response_class=HTMLResponse)
async def start_ai_practice(
    request: Request,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """AI練習問題を開始する。

    弱点分析→問題生成→最初の問題表示の流れ。
    """
    user_record_repo = UserRecordRepository(db)
    question_repo = QuestionRepository(db)
    generator = _get_generator()

    # ユーザーの回答記録を取得
    records = user_record_repo.get_records_by_user(user_id)

    if len(records) < MIN_ANSWERS_FOR_AI:
        return templates.TemplateResponse(
            request,
            "ai_practice_unavailable.html",
            context={
                "reason": "not_enough_data",
                "current_count": len(records),
                "required_count": MIN_ANSWERS_FOR_AI,
            },
        )

    # 弱点領域を特定
    question_domains: dict[str, str] = {}
    for record in records:
        if record.question_id not in question_domains:
            q = question_repo.get_question_by_id(record.question_id)
            if q and q.exam_domain:
                question_domains[record.question_id] = q.exam_domain

    weak_areas = identify_weak_areas(records, question_domains, threshold=0.6)

    if not weak_areas:
        return templates.TemplateResponse(
            request,
            "ai_practice_unavailable.html",
            context={
                "reason": "no_weak_areas",
                "current_count": len(records),
                "required_count": MIN_ANSWERS_FOR_AI,
            },
        )

    # API利用可能チェック
    if not generator.is_available:
        return templates.TemplateResponse(
            request,
            "ai_practice_unavailable.html",
            context={
                "reason": "api_unavailable",
                "current_count": len(records),
                "required_count": MIN_ANSWERS_FOR_AI,
                "weak_areas": weak_areas,
            },
        )

    # 問題を生成（全弱点領域をまとめて1回のAPIコールで10問生成）
    try:
        questions = generator.generate_questions_batch(weak_areas[:3], total_count=10)
    except Exception as e:
        logger.error("AI問題生成エラー: %s", str(e))
        return templates.TemplateResponse(
            request,
            "ai_practice_unavailable.html",
            context={
                "reason": "generation_failed",
                "current_count": len(records),
                "required_count": MIN_ANSWERS_FOR_AI,
            },
        )

    if not questions:
        return templates.TemplateResponse(
            request,
            "ai_practice_unavailable.html",
            context={
                "reason": "generation_failed",
                "current_count": len(records),
                "required_count": MIN_ANSWERS_FOR_AI,
            },
        )

    # セッションにAI生成問題を保存（インメモリ）
    session_id = str(uuid.uuid4())
    _ai_sessions[session_id] = {
        "questions": questions,
        "current_index": 0,
        "correct_count": 0,
        "total_count": len(questions),
        "weak_areas": weak_areas[:3],
    }

    return RedirectResponse(
        url=f"/ai-practice/{session_id}/question",
        status_code=303,
    )


# インメモリセッション管理（簡易実装）
_ai_sessions: dict[str, dict] = {}


@router.get("/{session_id}/question", response_class=HTMLResponse)
async def show_ai_question(
    session_id: str,
    request: Request,
):
    """AI生成問題を表示する。"""
    session = _ai_sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")

    idx = session["current_index"]
    questions = session["questions"]

    if idx >= len(questions):
        return RedirectResponse(
            url=f"/ai-practice/{session_id}/result",
            status_code=303,
        )

    question = questions[idx]
    choices = [question.choice_1, question.choice_2,
               question.choice_3, question.choice_4]

    return templates.TemplateResponse(
        request,
        "ai_practice_quiz.html",
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
async def submit_ai_answer(
    session_id: str,
    request: Request,
    choice_index: int = Form(...),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """AI練習問題の回答を送信し、DBに記録する。"""
    session = _ai_sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")

    idx = session["current_index"]
    question = session["questions"][idx]
    is_correct = choice_index == question.correct_choice_index

    if is_correct:
        session["correct_count"] += 1

    # DBに回答記録を保存
    import uuid as _uuid
    from datetime import datetime as _dt
    from app.data.models import AnswerRecordModel
    try:
        record = AnswerRecordModel(
            id=str(_uuid.uuid4()),
            user_id=user_id,
            question_id=question.id,
            course_id="ai-generated",
            selected_choice_index=choice_index,
            is_correct=is_correct,
            answered_at=_dt.now(),
        )
        db.add(record)
        db.commit()
    except Exception:
        db.rollback()  # 保存失敗しても問題表示は継続

    # 次の問題へ
    session["current_index"] += 1

    choices = [question.choice_1, question.choice_2,
               question.choice_3, question.choice_4]

    return templates.TemplateResponse(
        request,
        "ai_practice_explanation.html",
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
async def show_ai_result(
    session_id: str,
    request: Request,
):
    """AI練習問題の結果を表示する。"""
    session = _ai_sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")

    correct = session["correct_count"]
    total = session["total_count"]
    accuracy = round((correct / total * 100), 1) if total > 0 else 0

    weak_areas = session.get("weak_areas", [])

    # セッションクリーンアップ
    del _ai_sessions[session_id]

    return templates.TemplateResponse(
        request,
        "ai_practice_result.html",
        context={
            "correct_count": correct,
            "total_count": total,
            "accuracy": accuracy,
            "weak_areas": weak_areas,
        },
    )
