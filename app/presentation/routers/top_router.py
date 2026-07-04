"""
愛媛探索AIクイズ - RPGトップ画面ルーター

GET / でRPG風トップ画面を表示する。
GET /courses/{region} でHTMX用コースパネルHTMLフラグメントを返す。
GET /api/region-summary/{region} でツールチップ用難易度サマリーJSONを返す。
GET /badges でバッジ一覧ページを表示する。
GET /bookmarks でブックマーク一覧ページを表示する。
POST /bookmark/{question_id} でブックマーク追加/削除を行う。
"""

import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.data.database import get_db
from app.data.models import AnswerRecordModel, BookmarkModel, QuestionModel
from app.data.repository_factory import get_course_repository, get_question_repository, get_user_record_repository
from app.domain.badge_service import check_badges
from app.domain.level_calculator import calculate_level, calculate_xp_gauge
from app.domain.models import CourseInfo, Region, RegionMapData, UserStatus
from app.domain.progress_calculator import ProgressStatus, calculate_region_progress
from app.domain.quiz_service import QuizService
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


def _calculate_streak(user_id: str, db: Session) -> int:
    """今日から遡って連続で回答した日数を計算する。"""
    records = (
        db.query(func.date(AnswerRecordModel.answered_at))
        .filter(AnswerRecordModel.user_id == user_id)
        .distinct()
        .all()
    )
    if not records:
        return 0

    answered_dates = sorted(
        {date.fromisoformat(str(r[0])) for r in records}, reverse=True
    )
    today = date.today()

    if not answered_dates or (
        answered_dates[0] != today and answered_dates[0] != today - timedelta(days=1)
    ):
        return 0

    streak = 0
    check_date = answered_dates[0]
    for d in answered_dates:
        if d == check_date:
            streak += 1
            check_date -= timedelta(days=1)
        elif d < check_date:
            break

    return streak


def _safe_get_user_status(user_id: str, db: Session) -> UserStatus:
    """ユーザーステータスを安全に取得する。DB異常時はデフォルト値を返す。"""
    try:
        user_record_repo = get_user_record_repository(db)
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
    course_repo,
    question_repo,
    user_record_repo,
    user_id: str,
    suspended_sessions: dict[str, int] | None = None,
) -> RegionMapData:
    """指定地域のマップ描画用データを構築する。

    Args:
        suspended_sessions: {course_id: answered_count} 中断中セッションの回答済み数
    """
    from app.domain.models import Course

    if suspended_sessions is None:
        suspended_sessions = {}

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
        question_ids = [q.id for q in questions]
        is_suspended = course.id in suspended_sessions
        answered_count = suspended_sessions.get(course.id, 0)

        # ピンの状態を判定
        pin_status = "not_started"
        if question_ids:
            # このコースの回答記録を抽出
            course_records = [r for r in user_records if r.course_id == course.id]
            if course_records:
                correct_ids = {r.question_id for r in course_records if r.is_correct}
                if correct_ids >= set(question_ids):
                    # 全問正解の記録があるか確認
                    all_correct = all(
                        any(r.question_id == qid and r.is_correct for r in course_records)
                        for qid in question_ids
                    )
                    # 不正解が1つもないか（=満点）
                    incorrect_exists = any(
                        r.course_id == course.id and not r.is_correct
                        for r in course_records
                    )
                    if all_correct and not incorrect_exists:
                        pin_status = "perfect"
                    elif all_correct:
                        pin_status = "completed"
                    else:
                        pin_status = "in_progress"
                else:
                    pin_status = "in_progress"
        elif is_suspended:
            pin_status = "in_progress"

        course_infos.append(
            CourseInfo(
                id=course.id,
                name=course.name,
                region=course.region,
                difficulty=course.difficulty,
                description=course.description,
                question_count=len(questions),
                is_suspended=is_suspended,
                answered_count=answered_count,
                pin_status=pin_status,
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
    # クイズ画面から離脱した場合、進行中セッションを中断扱いにする
    quiz_service = QuizService(db)
    quiz_service.complete_in_progress_sessions(user_id)

    # ユーザーステータスを安全に取得
    user_status = _safe_get_user_status(user_id, db)

    # ストリーク日数を計算
    streak_days = _calculate_streak(user_id, db)

    # バッジ獲得数を計算
    badges = check_badges(user_id, db)
    earned_badge_count = sum(1 for b in badges if b["earned"])

    # 中断中セッションの情報を取得
    from app.data.models import QuizSessionModel
    from app.domain.models import SessionStatus

    suspended_sessions_raw = (
        db.query(QuizSessionModel)
        .filter(
            QuizSessionModel.user_id == user_id,
            QuizSessionModel.status == SessionStatus.SUSPENDED.value,
        )
        .all()
    )
    # {course_id: answered_count} を構築
    suspended_sessions: dict[str, int] = {}
    for sess in suspended_sessions_raw:
        from app.data.models import AnswerRecordModel
        answered = (
            db.query(AnswerRecordModel)
            .filter(
                AnswerRecordModel.user_id == user_id,
                AnswerRecordModel.course_id == sess.course_id,
                AnswerRecordModel.answered_at >= sess.started_at,
            )
            .count()
        )
        suspended_sessions[sess.course_id] = answered

    # 各地域のマップデータを構築
    course_repo = get_course_repository(db)
    question_repo = get_question_repository(db)
    user_record_repo = get_user_record_repository(db)

    regions = []
    for region in Region:
        region_data = _get_region_map_data(
            region, course_repo, question_repo, user_record_repo, user_id,
            suspended_sessions=suspended_sessions,
        )
        regions.append(region_data)

    # 全地域コンプリート判定
    all_complete = all(r.progress_status == "コンプリート" for r in regions)

    # デフォルト選択地域
    selected_region = Region.NANYO.name

    return templates.TemplateResponse(
        request,
        "rpg_top.html",
        context={
            "user_status": user_status,
            "regions": regions,
            "selected_region": selected_region,
            "all_complete": all_complete,
            "streak_days": streak_days,
            "earned_badge_count": earned_badge_count,
        },
    )


@router.get("/courses/{region}", response_class=HTMLResponse)
async def get_region_courses(
    request: Request,
    region: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """HTMX用: 指定難易度のコースパネルHTMLフラグメントを返す。

    マップクリック時にHTMXがこのエンドポイントを呼び出し、
    コースパネル部分のみを差し替える。

    Args:
        region: 難易度名（"CHUYO", "NANYO", "TOYO"）
    """
    # Region enumに変換（不正な値の場合はデフォルトで初級を使用）
    try:
        region_enum = Region[region]
    except KeyError:
        region_enum = Region.NANYO

    # 地域のマップデータを構築
    course_repo = get_course_repository(db)
    question_repo = get_question_repository(db)
    user_record_repo = get_user_record_repository(db)

    # 中断中セッション情報を取得
    from app.data.models import AnswerRecordModel, QuizSessionModel
    from app.domain.models import SessionStatus

    suspended_sessions_raw = (
        db.query(QuizSessionModel)
        .filter(
            QuizSessionModel.user_id == user_id,
            QuizSessionModel.status == SessionStatus.SUSPENDED.value,
        )
        .all()
    )
    suspended_sessions: dict[str, int] = {}
    for sess in suspended_sessions_raw:
        answered = (
            db.query(AnswerRecordModel)
            .filter(
                AnswerRecordModel.user_id == user_id,
                AnswerRecordModel.course_id == sess.course_id,
                AnswerRecordModel.answered_at >= sess.started_at,
            )
            .count()
        )
        suspended_sessions[sess.course_id] = answered

    region_data = _get_region_map_data(
        region_enum, course_repo, question_repo, user_record_repo, user_id,
        suspended_sessions=suspended_sessions,
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
    request: Request,
    region: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """ツールチップ用: 難易度のコース数と完了数をJSON形式で返す。

    Args:
        region: 難易度名（"CHUYO", "NANYO", "TOYO"）。
                不正な値の場合はデフォルトで初級にフォールバック。

    Returns:
        {"region_name": "初級", "total_count": N, "completed_count": M}
    """
    # Region enumに変換（不正な値の場合はデフォルトで初級を使用）
    try:
        region_enum = Region[region]
    except KeyError:
        region_enum = Region.NANYO

    # リポジトリの準備
    course_repo = get_course_repository(db)
    question_repo = get_question_repository(db)
    user_record_repo = get_user_record_repository(db)

    # 地域のコースを取得
    courses = course_repo.get_courses_by_region(region_enum)
    total_count = len(courses)

    # 完了コース数を算出
    # コースが完了 = コース内の全問題について少なくとも1回正解した記録が存在
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


@router.get("/tutorial", response_class=HTMLResponse)
async def tutorial_page(request: Request):
    """初回ログイン時のチュートリアルページを表示する。"""
    return templates.TemplateResponse(request, "tutorial.html")


@router.get("/badges", response_class=HTMLResponse)
async def badges_page(
    request: Request,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """バッジ一覧ページを表示する。"""
    badges = check_badges(user_id, db)
    earned_count = sum(1 for b in badges if b["earned"])
    total_count = len(badges)

    return templates.TemplateResponse(
        request,
        "badges.html",
        context={
            "badges": badges,
            "earned_count": earned_count,
            "total_count": total_count,
        },
    )


@router.post("/bookmark/{question_id}")
async def toggle_bookmark(
    question_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """ブックマークの追加/削除をトグルする。"""
    existing = (
        db.query(BookmarkModel)
        .filter(
            BookmarkModel.user_id == user_id,
            BookmarkModel.question_id == question_id,
        )
        .first()
    )

    if existing:
        db.delete(existing)
        db.commit()
    else:
        bookmark = BookmarkModel(
            id=str(uuid.uuid4()),
            user_id=user_id,
            question_id=question_id,
        )
        db.add(bookmark)
        db.commit()

    # リファラーがあればそこに戻る、なければブックマーク一覧へ
    referer = request.headers.get("referer")
    if referer:
        return RedirectResponse(url=referer, status_code=303)
    return RedirectResponse(url="/bookmarks", status_code=303)


@router.get("/bookmarks", response_class=HTMLResponse)
async def bookmarks_page(
    request: Request,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """ブックマーク一覧ページを表示する。"""
    bookmark_records = (
        db.query(BookmarkModel)
        .filter(BookmarkModel.user_id == user_id)
        .order_by(BookmarkModel.created_at.desc())
        .all()
    )

    bookmarks = []
    for bm in bookmark_records:
        question = db.query(QuestionModel).filter(QuestionModel.id == bm.question_id).first()
        if question:
            bookmarks.append({
                "question_id": bm.question_id,
                "text": question.text,
                "domain": question.exam_domain or "その他",
                "created_at": bm.created_at.strftime("%Y/%m/%d") if bm.created_at else "",
            })

    return templates.TemplateResponse(
        request,
        "bookmarks.html",
        context={"bookmarks": bookmarks},
    )
