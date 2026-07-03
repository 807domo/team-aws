"""
愛媛探索AIクイズ - 結果ダッシュボードルーター

GET /results/dashboard でダッシュボード画面を表示する。
GET /results/radar-chart でレーダーチャートデータをJSON形式で返す。
"""

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.data.database import get_db
from app.domain.models import ExamType
from app.domain.quiz_service import QuizService
from app.domain.results_service import ResultsService
from app.presentation.dependencies import get_current_user_id, get_results_service

from app.data.user_record_repository import UserRecordRepository
from app.domain.level_calculator import (
    calculate_level,
    calculate_xp_gauge,
    xp_threshold_for_level,
)
from app.domain.title_master import (
    get_all_titles_with_requirements,
    get_next_title,
    get_title,
)

router = APIRouter(prefix="/results", tags=["results"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    results_service: ResultsService = Depends(get_results_service),
    user_id: str = Depends(get_current_user_id),
):
    """結果ダッシュボード画面を表示する。

    スコア・グレード、レーダーチャート（ドメイン別正答率）、
    愛媛探索率、学習履歴を表示する。
    学習履歴がない場合は「まだ学習履歴がありません」メッセージを表示する。
    日別学習量グラフ（過去30日）も表示する。
    """
    from datetime import date, timedelta
    from sqlalchemy import func as sa_func
    from app.data.models import AnswerRecordModel

    # クイズ画面から離脱した場合、進行中セッションを中断扱いにする
    quiz_service = QuizService(db)
    quiz_service.complete_in_progress_sessions(user_id)

    dashboard_data = results_service.get_dashboard_data(user_id)

    # ユーザーのXP/レベル情報を取得
    user_record_repo = UserRecordRepository(db)
    user_xp_data = user_record_repo.get_user_xp(user_id)
    total_xp = user_xp_data["total_xp"]

    level = calculate_level(total_xp)
    title = get_title(level)
    gauge = calculate_xp_gauge(total_xp, level)
    next_level_xp = xp_threshold_for_level(level)
    xp_to_next_level = next_level_xp - total_xp
    next_title = get_next_title(level)
    all_titles = get_all_titles_with_requirements()

    xp_info = {
        "total_xp": total_xp,
        "level": level,
        "title": title,
        "xp_gauge_percentage": gauge["percentage"],
        "current_level_xp": gauge["current_level_xp"],
        "required_xp": gauge["required_xp"],
        "xp_to_next_level": max(xp_to_next_level, 0),
        "next_title": next_title,
        "all_titles": all_titles,
    }

    # レーダーチャート用データをテンプレートに渡せる形式に変換
    radar_labels = list(dashboard_data.radar_chart.domain_accuracy.keys())
    radar_values = list(dashboard_data.radar_chart.domain_accuracy.values())

    # 学習履歴をテンプレート用に変換
    attempt_history = [
        {
            "session_id": attempt.session_id,
            "course_name": attempt.course_name,
            "accuracy_rate": attempt.accuracy_rate,
            "grade": attempt.grade.value,
            "completed_at": attempt.completed_at.strftime("%Y/%m/%d %H:%M"),
        }
        for attempt in dashboard_data.attempt_history
    ]

    # 過去30日の日別回答数を集計
    today = date.today()
    thirty_days_ago = today - timedelta(days=29)
    daily_counts_raw = (
        db.query(
            sa_func.date(AnswerRecordModel.answered_at).label("day"),
            sa_func.count(AnswerRecordModel.id).label("count"),
        )
        .filter(
            AnswerRecordModel.user_id == user_id,
            sa_func.date(AnswerRecordModel.answered_at) >= thirty_days_ago,
        )
        .group_by(sa_func.date(AnswerRecordModel.answered_at))
        .all()
    )

    # 30日分の全日付を生成し、回答数がない日は0にする
    daily_counts_map = {str(r[0]): r[1] for r in daily_counts_raw}
    daily_labels = []
    daily_values = []
    for i in range(30):
        d = thirty_days_ago + timedelta(days=i)
        label = d.strftime("%m/%d")
        daily_labels.append(label)
        daily_values.append(daily_counts_map.get(str(d), 0))


    return templates.TemplateResponse(
        request,
        "dashboard.html",
        context={
            "cumulative_accuracy": dashboard_data.cumulative_accuracy,
            "grade": dashboard_data.grade.value,
            "radar_labels": radar_labels,
            "radar_values": radar_values,
            "exploration_rate": dashboard_data.exploration_rate,
            "attempt_history": attempt_history,
            "has_history": dashboard_data.has_history,
            "daily_labels": daily_labels,
            "daily_values": daily_values,
            "xp_info": xp_info,
        },
    )


@router.get("/radar-chart")
async def radar_chart_data(
    request: Request,
    exam_type: str = Query(
        default=ExamType.CLOUD_PRACTITIONER.value,
        description="試験タイプ（Cloud Practitioner / AI Practitioner）",
    ),
    results_service: ResultsService = Depends(get_results_service),
    user_id: str = Depends(get_current_user_id),
) -> JSONResponse:
    """レーダーチャート用のドメイン別正答率をJSON形式で返す。

    HTMX/AJAX から呼び出され、試験タイプに応じたレーダーチャートデータを返す。
    """
    # exam_type 文字列から ExamType enum に変換
    if exam_type == ExamType.AI_PRACTITIONER.value:
        selected_exam_type = ExamType.AI_PRACTITIONER
    else:
        selected_exam_type = ExamType.CLOUD_PRACTITIONER

    radar_data = results_service.get_radar_chart_data(user_id, selected_exam_type)

    return JSONResponse(
        content={
            "labels": list(radar_data.domain_accuracy.keys()),
            "values": list(radar_data.domain_accuracy.values()),
        }
    )


@router.get("/mock-exams", response_class=HTMLResponse)
async def mock_exam_history(
    request: Request,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """模擬試験の受験履歴を表示する。"""
    from app.data.models import MockExamResultModel

    results = (
        db.query(MockExamResultModel)
        .filter(MockExamResultModel.user_id == user_id)
        .order_by(MockExamResultModel.completed_at.desc())
        .all()
    )

    history = [
        {
            "exam_type": r.exam_type,
            "total_questions": r.total_questions,
            "correct_count": r.correct_count,
            "score_percentage": r.score_percentage,
            "grade": r.grade,
            "completed_at": r.completed_at.strftime("%Y/%m/%d %H:%M"),
        }
        for r in results
    ]

    return templates.TemplateResponse(
        request,
        "mock_exam_history.html",
        context={"history": history},
    )
