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
    """
    dashboard_data = results_service.get_dashboard_data(user_id)

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
