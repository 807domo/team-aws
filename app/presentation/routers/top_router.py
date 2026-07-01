"""
愛媛探索AIクイズ - RPGトップ画面ルーター

GET / でRPG風トップ画面を表示する。
GET /courses/{region} でHTMX用コースパネルHTMLフラグメントを返す。
GET /api/region-summary/{region} でツールチップ用地域サマリーJSONを返す。
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.data.course_repository import CourseRepository
from app.data.database import get_db
from app.data.question_repository import QuestionRepository
from app.data.user_record_repository import UserRecordRepository
from app.domain.level_calculator import calculate_level, calculate_xp_gauge
from app.domain.models import CourseInfo, Region, RegionMapData, UserStatus
from app.domain.progress_calculator import ProgressStatus, calculate_region_progress
from app.domain.title_master import get_title
from app.presentation.dependencies import get_current_user_id

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# 進捗ステータスに応じた塗り色マッピング
PROGRESS_FILL_COLORS: dict[ProgressStatus, str] = {
    ProgressStatus.NOT_STARTED: "#D1D5DB",  # light gray
    ProgressStatus.IN_PROGRESS: "#FED7AA",  # light orange
    ProgressStatus.COMPLETE: "#F97316",  # vivid mikan orange
}


def _safe_get_user_status(user_id: str, db: Session) -> UserStatus:
    """ユーザーステータスを安全に取得する。DB異常時はデフォルト値を返す。"""
    try:
        user_record_repo = UserRecordRepository(db)
        user_xp_data = user_record_repo.get_user_xp(user_id)
        total_xp = user_xp_data["total_xp"]
        level = calculate_level(total_xp)
        title = get_title(level)
        gauge = calculate_xp_gauge(total_xp, level)

        # display_name取得
        from app.data.models import UserModel

        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        display_name = "ゲスト"
        if user and user.display_name:
            display_name = (
                user.display_name[:20] + "…"
                if len(user.display_name) > 20
                else user.display_name
            )

        return UserStatus(
            display_name=display_name,
            level=level,
            title=title,
            total_xp=total_xp,
            xp_gauge_percentage=gauge["percentage"],
            current_level_xp=gauge["current_level_xp"],
            required_xp=gauge["required_xp"],
        )
    except Exception:
        return UserStatus(
            display_name="ゲスト",
            level=1,
            title="伊予の迷い人",
            total_xp=0,
            xp_gauge_percentage=0.0,
            current_level_xp=0,
            required_xp=100,
        )


def _get_region_map_data(
    region: Region,
    course_repo: CourseRepository,
    question_repo: QuestionRepository,
    user_record_repo: UserRecordRepository,
    user_id: str,
) -> RegionMapData:
    """指定地域のマップ描画用データを構築する。"""
    from app.domain.models import Course

    # 地域のコースを取得
    courses = course_repo.get_courses_by_region(region)
    course_ids = [c.id for c in courses]

    # コースごとの問題IDリストを構築
    course_questions: dict[str, list[str]] = {}
    for course in courses:
        questions = question_repo.get_questions_by_course(course.id)
        course_questions[course.id] = [q.id for q in questions]

    # ユーザーの回答記録を取得
    user_records = user_record_repo.get_records_by_user(user_id)

    # 進捗ステータスを算出
    progress_status = calculate_region_progress(
        region.name, course_ids, user_records, course_questions
    )

    # 塗り色を決定
    fill_color = PROGRESS_FILL_COLORS[progress_status]

    # CourseInfoリストを構築
    course_infos = []
    for course in courses:
        questions = question_repo.get_questions_by_course(course.id)
        course_infos.append(
            CourseInfo(
                id=course.id,
                name=course.name,
                region=course.region,
                difficulty=course.difficulty,
                description=course.description,
                question_count=len(questions),
            )
        )

    return RegionMapData(
        region=region,
        progress_status=progress_status.value,
        fill_color=fill_color,
        courses=course_infos,
    )


@router.get("/", response_class=HTMLResponse)
async def rpg_top_screen(
    request: Request,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """RPG風トップ画面を表示する。

    ステータス表示、SVGマップ、コースパネルを統合して返す。
    デフォルト選択地域は中予。
    """
    # ユーザーステータスを安全に取得
    user_status = _safe_get_user_status(user_id, db)

    # 各地域のマップデータを構築
    course_repo = CourseRepository(db)
    question_repo = QuestionRepository(db)
    user_record_repo = UserRecordRepository(db)

    regions = []
    for region in Region:
        region_data = _get_region_map_data(
            region, course_repo, question_repo, user_record_repo, user_id
        )
        regions.append(region_data)

    # デフォルト選択地域
    selected_region = Region.CHUYO.name

    return templates.TemplateResponse(
        request,
        "rpg_top.html",
        context={
            "user_status": user_status,
            "regions": regions,
            "selected_region": selected_region,
        },
    )


@router.get("/courses/{region}", response_class=HTMLResponse)
async def get_region_courses(
    request: Request,
    region: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """HTMX用: 指定地域のコースパネルHTMLフラグメントを返す。

    マップクリック時にHTMXがこのエンドポイントを呼び出し、
    コースパネル部分のみを差し替える。

    Args:
        region: 地域名（"CHUYO", "NANYO", "TOYO"）
    """
    # Region enumに変換（不正な値の場合はデフォルトで中予を使用）
    try:
        region_enum = Region[region]
    except KeyError:
        region_enum = Region.CHUYO

    # 地域のマップデータを構築
    course_repo = CourseRepository(db)
    question_repo = QuestionRepository(db)
    user_record_repo = UserRecordRepository(db)

    region_data = _get_region_map_data(
        region_enum, course_repo, question_repo, user_record_repo, user_id
    )

    # 部分HTMLテンプレートをレンダリングして返す
    return templates.TemplateResponse(
        request,
        "partials/course_panel.html",
        context={
            "region_data": region_data,
        },
    )


@router.get("/api/region-summary/{region}")
async def get_region_summary(
    region: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """ツールチップ用: 地域のコース数と完了数をJSON形式で返す。

    Args:
        region: 地域名（"CHUYO", "NANYO", "TOYO"）。
                不正な値の場合はデフォルトで中予にフォールバック。

    Returns:
        {"region_name": "中予", "total_count": N, "completed_count": M}
    """
    # Region enumに変換（不正な値の場合はデフォルトで中予を使用）
    try:
        region_enum = Region[region]
    except KeyError:
        region_enum = Region.CHUYO

    # リポジトリの準備
    course_repo = CourseRepository(db)
    question_repo = QuestionRepository(db)
    user_record_repo = UserRecordRepository(db)

    # 地域のコースを取得
    courses = course_repo.get_courses_by_region(region_enum)
    total_count = len(courses)

    # 完了コース数を算出
    completed_count = 0

    if total_count > 0:
        # ユーザーの回答記録を取得
        user_records = user_record_repo.get_records_by_user(user_id)

        for course in courses:
            questions = question_repo.get_questions_by_course(course.id)
            question_ids = [q.id for q in questions]

            # 問題がないコースは完了とみなす
            if not question_ids:
                completed_count += 1
                continue

            # このコースで正解した問題IDを収集
            correct_question_ids = {
                r.question_id
                for r in user_records
                if r.course_id == course.id and r.is_correct
            }

            # 全問題に少なくとも1回正解しているか確認
            if all(q_id in correct_question_ids for q_id in question_ids):
                completed_count += 1

    return {
        "region_name": region_enum.value,
        "total_count": total_count,
        "completed_count": completed_count,
    }


@router.get("/licenses", response_class=HTMLResponse)
async def licenses_page(request: Request):
    """ライセンス・クレジット表記ページを表示する。"""
    return templates.TemplateResponse(request, "licenses.html")
