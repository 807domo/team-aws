"""
愛媛探索AIクイズ - バッジ（実績）サービス

ユーザーの学習実績に基づいてバッジの獲得判定を行う。
"""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.data.repository_factory import (
    get_course_repository,
    get_question_repository,
    get_user_record_repository,
    get_user_repository,
)
from app.domain.level_calculator import calculate_level
from app.domain.models import Region


# バッジ定義
BADGE_DEFINITIONS = [
    {
        "id": "first_correct",
        "name": "初めての正解",
        "description": "初めて問題に正解した",
        "icon": "🎯",
    },
    {
        "id": "perfect_stage",
        "name": "パーフェクト",
        "description": "ステージを満点でクリアした",
        "icon": "💯",
    },
    {
        "id": "all_nanyo",
        "name": "南予マスター",
        "description": "南予の全ステージを完了した",
        "icon": "🏝️",
    },
    {
        "id": "all_chuyo",
        "name": "中予マスター",
        "description": "中予の全ステージを完了した",
        "icon": "🏯",
    },
    {
        "id": "all_toyo",
        "name": "東予マスター",
        "description": "東予の全ステージを完了した",
        "icon": "⛰️",
    },
    {
        "id": "streak_3",
        "name": "3日連続学習",
        "description": "3日連続で学習した",
        "icon": "🔥",
    },
    {
        "id": "streak_7",
        "name": "7日連続学習",
        "description": "7日連続で学習した",
        "icon": "🔥🔥",
    },
    {
        "id": "questions_50",
        "name": "50問達成",
        "description": "合計50問に回答した",
        "icon": "📚",
    },
    {
        "id": "questions_100",
        "name": "100問達成",
        "description": "合計100問に回答した",
        "icon": "📖",
    },
    {
        "id": "ai_practice",
        "name": "AI練習完了",
        "description": "AI弱点練習を完了した",
        "icon": "🤖",
    },
    # 称号バッジ
    {
        "id": "title_researcher",
        "name": "愛媛の駆け出しAI研究者",
        "description": "Lv.3に到達し称号を獲得した",
        "icon": "🔬",
    },
    {
        "id": "title_engineer",
        "name": "道後を極めしAIエンジニア",
        "description": "Lv.6に到達し称号を獲得した",
        "icon": "⚙️",
    },
    {
        "id": "title_master",
        "name": "伝説の愛媛AIマスター",
        "description": "Lv.10に到達し最高称号を獲得した",
        "icon": "👑",
    },
]


def _calculate_streak(user_id: str, db: Session) -> int:
    """今日から遡って連続で回答した日数を計算する。"""
    user_record_repo = get_user_record_repository(db)
    records = user_record_repo.get_records_by_user(user_id)

    if not records:
        return 0

    answered_dates = sorted(
        {r.answered_at.date() for r in records}, reverse=True
    )
    today = date.today()

    # 今日か昨日に回答がなければストリーク0
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


def _check_region_complete(user_id: str, region: Region, db: Session) -> bool:
    """指定リージョンの全コースが完了しているか確認する。"""
    course_repo = get_course_repository(db)
    question_repo = get_question_repository(db)
    user_record_repo = get_user_record_repository(db)

    courses = course_repo.get_courses_by_region(region)
    if not courses:
        return False

    for course in courses:
        questions = question_repo.get_questions_by_course(course.id)
        if not questions:
            continue
        question_ids = {q.id for q in questions}
        course_records = user_record_repo.get_records_by_user_and_course(
            user_id, course.id
        )
        correct_ids = {r.question_id for r in course_records if r.is_correct}
        if not question_ids.issubset(correct_ids):
            return False

    return True


def check_badges(user_id: str, db: Session) -> list[dict]:
    """ユーザーが獲得済みのバッジリストを返す。"""
    earned = []

    user_record_repo = get_user_record_repository(db)
    question_repo = get_question_repository(db)

    # 全回答記録を取得
    all_records = user_record_repo.get_records_by_user(user_id)

    # 回答数
    total_answers = len(all_records)

    # 正解数
    correct_count = sum(1 for r in all_records if r.is_correct)

    # first_correct
    if correct_count >= 1:
        earned.append("first_correct")

    # questions_50
    if total_answers >= 50:
        earned.append("questions_50")

    # questions_100
    if total_answers >= 100:
        earned.append("questions_100")

    # perfect_stage: コースの全問正解（不正解なし）
    courses_with_answers = {r.course_id for r in all_records}
    for course_id in courses_with_answers:
        if course_id == "custom-stage":
            continue
        questions = question_repo.get_questions_by_course(course_id)
        if not questions:
            continue
        question_ids = {q.id for q in questions}
        # このコースの回答記録をフィルタ
        course_records = [r for r in all_records if r.course_id == course_id]
        correct_ids = {r.question_id for r in course_records if r.is_correct}
        if question_ids.issubset(correct_ids):
            # 不正解が1つもないか確認
            incorrect_exists = any(
                not r.is_correct for r in course_records
            )
            if not incorrect_exists:
                earned.append("perfect_stage")
                break

    # all_nanyo, all_chuyo, all_toyo
    if _check_region_complete(user_id, Region.NANYO, db):
        earned.append("all_nanyo")
    if _check_region_complete(user_id, Region.CHUYO, db):
        earned.append("all_chuyo")
    if _check_region_complete(user_id, Region.TOYO, db):
        earned.append("all_toyo")

    # streak
    streak = _calculate_streak(user_id, db)
    if streak >= 3:
        earned.append("streak_3")
    if streak >= 7:
        earned.append("streak_7")

    # ai_practice: AI弱点練習を1回でも完了したか
    ai_records = [r for r in all_records if r.course_id == "ai-practice"]
    if len(ai_records) > 0:
        earned.append("ai_practice")

    # 称号バッジ: レベルに基づく
    user_repo = get_user_repository(db)
    user_data = user_repo.get_by_id(user_id)
    if user_data:
        user_level = calculate_level(user_data.get("total_xp") or 0)
        if user_level >= 3:
            earned.append("title_researcher")
        if user_level >= 6:
            earned.append("title_engineer")
        if user_level >= 10:
            earned.append("title_master")

    # バッジ定義と照合して返す
    result = []
    for badge_def in BADGE_DEFINITIONS:
        result.append({
            **badge_def,
            "earned": badge_def["id"] in earned,
        })

    return result
