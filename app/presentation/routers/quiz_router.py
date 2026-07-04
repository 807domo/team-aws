"""
愛媛探索AIクイズ - クイズ出題・回答ルーター

クイズセッションの開始、問題表示、回答送信、解説表示、コース完了を提供する。
HTMX による部分更新に対応し、1問ずつの4択クイズUIを実現する。
成績記録保存失敗時のエラーハンドリングとリトライ機構を含む。
"""

import hashlib
import logging
import random

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.domain.models import Question
from app.domain.quiz_service import QuizService
from app.presentation.dependencies import get_current_user_id, get_question_repository, get_quiz_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quiz", tags=["quiz"])
templates = Jinja2Templates(directory="app/templates")


def _shuffle_questions(questions: list[Question], session_id: str) -> list[Question]:
    """セッションIDをシードとして問題をシャッフルする。

    同じセッションIDでは常に同じ順番になるため、再開時も一貫した順序を維持する。
    """
    seed = int(hashlib.md5(session_id.encode()).hexdigest(), 16) % (2**32)
    shuffled = list(questions)
    random.Random(seed).shuffle(shuffled)
    return shuffled


@router.post("/start/{course_id}", response_class=HTMLResponse)
async def start_quiz(
    course_id: str,
    request: Request,
    quiz_service: QuizService = Depends(get_quiz_service),
    user_id: str = Depends(get_current_user_id),
):
    """コースのクイズを開始または再開する。

    中断されたセッションがある場合は、中断した問題から再開する。
    新規の場合は最初の問題から開始する。

    Args:
        course_id: 開始するコースのID
    """
    try:
        session, questions = quiz_service.start_course(user_id, course_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if not questions:
        raise HTTPException(status_code=404, detail="このコースには問題がありません")

    # 回答済み問題数を取得して、再開位置を決定
    answered_count = quiz_service.get_answered_count(session.id)
    start_index = min(answered_count, len(questions) - 1)

    # 全問回答済みなら完了画面へ
    if answered_count >= len(questions):
        return RedirectResponse(
            url=f"/quiz/{session.id}/complete",
            status_code=303,
        )

    return RedirectResponse(
        url=f"/quiz/{session.id}/question?index={start_index}",
        status_code=303,
    )


@router.get("/{session_id}/question", response_class=HTMLResponse)
async def show_question(
    session_id: str,
    request: Request,
    index: int = 0,
    quiz_service: QuizService = Depends(get_quiz_service),
    question_repo=Depends(get_question_repository),
):
    """現在の問題を表示する。

    セッションに紐づくコースの問題一覧から、index 番目の問題を表示する。
    全問回答済みの場合はコース完了画面にリダイレクトする。

    Args:
        session_id: クイズセッションID
        index: 問題のインデックス（0始まり）
    """
    # セッション検証
    session = quiz_service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")

    # コースの問題一覧を取得（セッションIDベースでシャッフル）
    questions = question_repo.get_questions_by_course(session.course_id)
    if not questions:
        raise HTTPException(status_code=404, detail="問題が見つかりません")
    questions = _shuffle_questions(questions, session_id)

    # インデックスが範囲外の場合はコース完了へ
    if index >= len(questions):
        return RedirectResponse(
            url=f"/quiz/{session_id}/complete",
            status_code=303,
        )

    question = questions[index]
    choices = [
        question.choice_1,
        question.choice_2,
        question.choice_3,
        question.choice_4,
    ]

    return templates.TemplateResponse(
        request,
        "quiz.html",
        context={
            "session_id": session_id,
            "question": question,
            "choices": choices,
            "question_index": index,
            "total_questions": len(questions),
            "progress_percent": int((index / len(questions)) * 100),
        },
    )


@router.post("/{session_id}/answer", response_class=HTMLResponse)
async def submit_answer(
    session_id: str,
    request: Request,
    question_id: str = Form(...),
    choice_index: int = Form(...),
    question_index: int = Form(...),
    quiz_service: QuizService = Depends(get_quiz_service),
    question_repo=Depends(get_question_repository),
):
    """回答を送信し、正誤フィードバックを表示する。

    正誤判定後、解説画面にリダイレクトする。
    成績記録保存に失敗した場合でも正誤フィードバックは必ず表示し、
    保存失敗のエラーメッセージとリトライオプションを提供する（Requirement 4.5）。

    Args:
        session_id: クイズセッションID
        question_id: 回答した問題のID
        choice_index: 選択した選択肢のインデックス (0-3)
        question_index: 現在の問題インデックス
    """
    # 問題データを事前に取得（正誤表示に必要）
    question = question_repo.get_question_by_id(question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="問題が見つかりません")

    # 正誤判定（選択肢とcorrect_choice_indexの比較は常に可能）
    is_correct = choice_index == question.correct_choice_index
    save_failed = False

    try:
        result = quiz_service.submit_answer(session_id, question_id, choice_index)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 成績記録保存失敗: 正誤フィードバックは表示し、保存失敗を通知する
        logger.error("成績記録保存失敗: %s", str(e))
        save_failed = True

    # セッション情報から総問題数を取得
    session = quiz_service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")

    # 保存失敗時: エラーメッセージ付きでリトライオプションを含む解説画面へ遷移
    # 正誤フィードバックは必ず表示する（Requirement 2.3: 技術的問題に関係なく常に表示）
    redirect_url = (
        f"/quiz/{session_id}/explanation/{question_id}"
        f"?is_correct={is_correct}"
        f"&selected={choice_index}"
        f"&correct={question.correct_choice_index}"
        f"&question_index={question_index}"
    )

    if save_failed:
        redirect_url += "&save_failed=true"

    return RedirectResponse(url=redirect_url, status_code=303)


@router.get("/{session_id}/explanation/{question_id}", response_class=HTMLResponse)
async def show_explanation(
    session_id: str,
    question_id: str,
    request: Request,
    is_correct: bool = False,
    selected: int = 0,
    correct: int = 0,
    question_index: int = 0,
    save_failed: bool = False,
    quiz_service: QuizService = Depends(get_quiz_service),
    question_repo=Depends(get_question_repository),
):
    """解説画面を表示する。

    愛媛トリビアとAWS/AI概念の解説を表示し、「次へ」ボタンで次の問題に進む。
    成績記録保存に失敗した場合はエラーメッセージとリトライボタンを表示する。

    Args:
        session_id: クイズセッションID
        question_id: 問題ID
        is_correct: 正解だったかどうか
        selected: ユーザーが選択した選択肢インデックス
        correct: 正解の選択肢インデックス
        question_index: 現在の問題インデックス
        save_failed: 成績記録保存が失敗したかどうか
    """
    # セッション検証
    session = quiz_service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")

    # 問題データ取得
    question = question_repo.get_question_by_id(question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="問題が見つかりません")

    # コース全体の問題数を取得
    questions = question_repo.get_questions_by_course(session.course_id)
    total_questions = len(questions)

    # 次の問題のインデックス
    next_index = question_index + 1
    is_last_question = next_index >= total_questions

    choices = [
        question.choice_1,
        question.choice_2,
        question.choice_3,
        question.choice_4,
    ]

    return templates.TemplateResponse(
        request,
        "explanation.html",
        context={
            "session_id": session_id,
            "question": question,
            "choices": choices,
            "is_correct": is_correct,
            "selected_index": selected,
            "correct_index": correct,
            "question_index": question_index,
            "total_questions": total_questions,
            "next_index": next_index,
            "is_last_question": is_last_question,
            "save_failed": save_failed,
        },
    )


@router.get("/{session_id}/complete", response_class=HTMLResponse)
async def course_complete(
    session_id: str,
    request: Request,
    quiz_service: QuizService = Depends(get_quiz_service),
):
    """コース完了サマリー画面を表示する。

    正解数、総問題数、正答率、グレードを表示する。

    Args:
        session_id: クイズセッションID
    """
    try:
        summary = quiz_service.complete_course(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return templates.TemplateResponse(
        request,
        "course_complete.html",
        context={
            "summary": summary,
            "session_id": session_id,
            "aborted": False,
        },
    )


@router.post("/{session_id}/abort", response_class=HTMLResponse)
async def abort_quiz(
    session_id: str,
    request: Request,
    quiz_service: QuizService = Depends(get_quiz_service),
):
    """クイズを途中中断し、それまでの結果をサマリー表示する。

    セッションを完了状態にし、回答済みの問題のみでスコアを計算する。

    Args:
        session_id: クイズセッションID
    """
    try:
        summary = quiz_service.abort_course(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return templates.TemplateResponse(
        request,
        "course_complete.html",
        context={
            "summary": summary,
            "session_id": session_id,
            "aborted": True,
        },
    )
