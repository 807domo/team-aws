"""
愛媛探索AIクイズ - 模擬試験ルーター

模擬試験モード（AWS CCP / AI Practitioner）のエンドポイントを提供する。
タイマー付き65問・90分の試験セッション管理、問題ナビゲーション、
回答記録（即時フィードバックなし）、試験終了・結果表示を行う。

Requirements: 5.1, 5.2, 5.3, 5.5, 5.6
"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.data.database import get_db
from app.data.models import MockExamResultModel
from app.domain.mock_exam_engine import MockExamEngine
from app.domain.models import ExamType
from app.presentation.dependencies import get_current_user_id, get_mock_exam_engine

router = APIRouter(prefix="/mock-exam", tags=["mock-exam"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/select", response_class=HTMLResponse)
async def mock_exam_select(request: Request):
    """模擬試験タイプ選択画面を表示する。

    CCP（Cloud Practitioner）と AI Practitioner の2つの試験タイプを表示する。
    Requirements: 5.1
    """
    exam_types = [
        {
            "value": ExamType.CLOUD_PRACTITIONER.value,
            "label": "AWS Certified Cloud Practitioner",
            "short_label": "CCP",
            "description": "クラウドの基礎概念、セキュリティ、テクノロジー、料金を網羅",
            "questions": 65,
            "duration": 90,
        },
        {
            "value": ExamType.AI_PRACTITIONER.value,
            "label": "AWS AI Practitioner",
            "short_label": "AIF",
            "description": "AI/MLの基礎、生成AI、責任あるAIを網羅",
            "questions": 65,
            "duration": 90,
        },
    ]

    return templates.TemplateResponse(
        request,
        "mock_exam_select.html",
        context={
            "exam_types": exam_types,
        },
    )


@router.post("/start")
async def mock_exam_start(
    request: Request,
    exam_type: str = Form(...),
    engine: MockExamEngine = Depends(get_mock_exam_engine),
    user_id: str = Depends(get_current_user_id),
):
    """模擬試験を開始する。

    選択された試験タイプでセッションを作成し、最初の問題にリダイレクトする。
    Requirements: 5.1
    """
    # exam_type 文字列を ExamType enum に変換
    selected_type = ExamType(exam_type)

    session = engine.start_exam(user_id=user_id, exam_type=selected_type)

    return RedirectResponse(
        url=f"/mock-exam/{session.id}/question/0",
        status_code=303,
    )


@router.get("/{session_id}/question/{index}", response_class=HTMLResponse)
async def mock_exam_question(
    request: Request,
    session_id: str,
    index: int,
    engine: MockExamEngine = Depends(get_mock_exam_engine),
):
    """指定インデックスの問題を表示する。

    カウントダウンタイマー、問題ナビゲーション、ページ離脱確認を含む。
    Requirements: 5.2, 5.6
    """
    try:
        question_view = engine.navigate_to_question(session_id, index)
    except ValueError as e:
        # タイマー切れまたはセッション無効の場合は結果画面へ
        if "試験時間が終了しました" in str(e):
            return RedirectResponse(
                url=f"/mock-exam/{session_id}/finish",
                status_code=303,
            )
        return templates.TemplateResponse(
            request,
            "mock_exam_select.html",
            context={"exam_types": [], "error": str(e)},
            status_code=404,
        )

    remaining = engine.get_remaining_time(session_id)
    answer_status = engine.get_answer_status(session_id)
    session = engine.get_session(session_id)

    # 残り時間を秒数に変換
    remaining_seconds = int(remaining.total_seconds())

    # 選択肢リスト作成
    choices = [
        question_view.question.choice_1,
        question_view.question.choice_2,
        question_view.question.choice_3,
        question_view.question.choice_4,
    ]

    return templates.TemplateResponse(
        request,
        "mock_exam.html",
        context={
            "session_id": session_id,
            "question_view": question_view,
            "choices": choices,
            "remaining_seconds": remaining_seconds,
            "answer_status": answer_status,
            "total_questions": question_view.total_questions,
            "current_index": question_view.question_index,
            "exam_type_label": session.exam_type.value if session else "",
        },
    )


@router.get("/{session_id}", response_class=HTMLResponse)
async def mock_exam_current(
    request: Request,
    session_id: str,
    engine: MockExamEngine = Depends(get_mock_exam_engine),
):
    """現在の問題を表示する（最初の問題にリダイレクト）。

    Requirements: 5.6
    """
    return RedirectResponse(
        url=f"/mock-exam/{session_id}/question/0",
        status_code=303,
    )


@router.post("/{session_id}/answer")
async def mock_exam_answer(
    request: Request,
    session_id: str,
    question_id: str = Form(...),
    question_index: int = Form(...),
    choice_index: int = Form(...),
    engine: MockExamEngine = Depends(get_mock_exam_engine),
):
    """回答を記録する（即時フィードバックなし）。

    回答を記録した後、同じ問題ページにリダイレクトする。
    Requirements: 5.3（即時フィードバックなし）
    """
    try:
        engine.submit_answer(session_id, question_id, choice_index)
    except ValueError as e:
        if "試験時間が終了しました" in str(e):
            return RedirectResponse(
                url=f"/mock-exam/{session_id}/finish",
                status_code=303,
            )

    # 次の問題に移動（最後の問題なら同じ問題に留まる）
    return RedirectResponse(
        url=f"/mock-exam/{session_id}/question/{question_index}",
        status_code=303,
    )


@router.post("/{session_id}/finish")
async def mock_exam_finish_post(
    request: Request,
    session_id: str,
    engine: MockExamEngine = Depends(get_mock_exam_engine),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """試験を終了し、結果画面にリダイレクトする。"""
    try:
        result = engine.finish_exam(session_id)
    except ValueError:
        return RedirectResponse(url="/mock-exam/select", status_code=303)

    # 結果をDBに保存
    import uuid
    db_result = MockExamResultModel(
        id=str(uuid.uuid4()),
        user_id=user_id,
        exam_type=result.exam_type.value,
        total_questions=result.total_questions,
        correct_count=result.correct_count,
        score_percentage=result.score_percentage,
        grade=result.grade.value,
        completed_at=result.completed_at,
    )
    db.add(db_result)
    db.commit()

    return templates.TemplateResponse(
        request, "mock_exam_result.html", context={"result": result}
    )


@router.get("/{session_id}/finish", response_class=HTMLResponse)
async def mock_exam_finish_get(
    request: Request,
    session_id: str,
    engine: MockExamEngine = Depends(get_mock_exam_engine),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """試験を終了し結果画面を表示する（GET: タイマー切れリダイレクト用）。"""
    try:
        result = engine.finish_exam(session_id)
    except ValueError:
        return RedirectResponse(url="/mock-exam/select", status_code=303)

    # 結果をDBに保存
    import uuid
    db_result = MockExamResultModel(
        id=str(uuid.uuid4()),
        user_id=user_id,
        exam_type=result.exam_type.value,
        total_questions=result.total_questions,
        correct_count=result.correct_count,
        score_percentage=result.score_percentage,
        grade=result.grade.value,
        completed_at=result.completed_at,
    )
    db.add(db_result)
    db.commit()

    return templates.TemplateResponse(
        request, "mock_exam_result.html", context={"result": result}
    )


@router.get("/{session_id}/status", response_class=HTMLResponse)
async def mock_exam_status(
    request: Request,
    session_id: str,
    engine: MockExamEngine = Depends(get_mock_exam_engine),
):
    """残り時間を返す（HTMX ポーリング用）。

    Requirements: 5.2
    """
    remaining = engine.get_remaining_time(session_id)
    remaining_seconds = int(remaining.total_seconds())

    if remaining_seconds <= 0:
        # タイマー切れ: クライアントにリダイレクト指示
        return HTMLResponse(
            content='<div id="timer" hx-get="/mock-exam/'
            + session_id
            + '/status" hx-trigger="load" hx-swap="outerHTML">'
            '<script>window.location.href="/mock-exam/'
            + session_id
            + '/finish";</script></div>',
        )

    minutes = remaining_seconds // 60
    seconds = remaining_seconds % 60

    return HTMLResponse(
        content=f'<span id="timer-display">{minutes:02d}:{seconds:02d}</span>',
    )
