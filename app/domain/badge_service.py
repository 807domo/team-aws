"""
愛媛探索AIクイズ - バッジ（実績）サービス

ユーザーの学習実績に基づいてバッジの獲得判定を行う。
"""

from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.data.models import AnswerRecordModel, QuestionModel, CourseModel


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
]


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

    answered_dates = sorted({date.fromisoformat(str(r[0])) for r in records}, reverse=True)
    today = date.today()

    # 今日か昨日に回答がなければストリーク0
    if not answered_dates or (answered_dates[0] != today and answered_dates[0] != today - timedelta(days=1)):
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


def _check_region_complete(user_id: str, region: str, db: Session) -> bool:
    """指定リージョンの全コースが完了しているか確認する。"""
    courses = db.query(CourseModel).filter(CourseModel.region == region).all()
    if not courses:
        return False

    for course in courses:
        questions = db.query(QuestionModel).filter(QuestionModel.course_id == course.id).all()
        if not questions:
            continue
        question_ids = {q.id for q in questions}
        correct_ids = set(
            r[0] for r in db.query(AnswerRecordModel.question_id)
            .filter(
                AnswerRecordModel.user_id == user_id,
                AnswerRecordModel.course_id == course.id,
                AnswerRecordModel.is_correct == True,
            )
            .all()
        )
        if not question_ids.issubset(correct_ids):
            return False

    return True


def check_badges(user_id: str, db: Session) -> list[dict]:
    """ユーザーが獲得済みのバッジリストを返す。"""
    earned = []

    # 回答数
    total_answers = (
        db.query(func.count(AnswerRecordModel.id))
        .filter(AnswerRecordModel.user_id == user_id)
        .scalar()
    ) or 0

    # 正解数
    correct_count = (
        db.query(func.count(AnswerRecordModel.id))
        .filter(
            AnswerRecordModel.user_id == user_id,
            AnswerRecordModel.is_correct == True,
        )
        .scalar()
    ) or 0

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
    from sqlalchemy import and_
    courses_with_answers = (
        db.query(AnswerRecordModel.course_id)
        .filter(AnswerRecordModel.user_id == user_id)
        .distinct()
        .all()
    )
    for (course_id,) in courses_with_answers:
        if course_id == "custom-stage":
            continue
        questions = db.query(QuestionModel).filter(QuestionModel.course_id == course_id).all()
        if not questions:
            continue
        question_ids = {q.id for q in questions}
        # このコースの全問正解記録を確認
        correct_ids = set(
            r[0] for r in db.query(AnswerRecordModel.question_id)
            .filter(
                AnswerRecordModel.user_id == user_id,
                AnswerRecordModel.course_id == course_id,
                AnswerRecordModel.is_correct == True,
            )
            .all()
        )
        if question_ids.issubset(correct_ids):
            # 不正解が1つもないか確認
            incorrect_exists = (
                db.query(func.count(AnswerRecordModel.id))
                .filter(
                    AnswerRecordModel.user_id == user_id,
                    AnswerRecordModel.course_id == course_id,
                    AnswerRecordModel.is_correct == False,
                )
                .scalar()
            )
            if not incorrect_exists:
                earned.append("perfect_stage")
                break

    # all_nanyo, all_chuyo, all_toyo
    if _check_region_complete(user_id, "南予", db):
        earned.append("all_nanyo")
    if _check_region_complete(user_id, "中予", db):
        earned.append("all_chuyo")
    if _check_region_complete(user_id, "東予", db):
        earned.append("all_toyo")

    # streak
    streak = _calculate_streak(user_id, db)
    if streak >= 3:
        earned.append("streak_3")
    if streak >= 7:
        earned.append("streak_7")

    # ai_practice: AI弱点練習を1回でも完了したか
    ai_records = (
        db.query(func.count(AnswerRecordModel.id))
        .filter(
            AnswerRecordModel.user_id == user_id,
            AnswerRecordModel.course_id == "ai-practice",
        )
        .scalar()
    ) or 0
    if ai_records > 0:
        earned.append("ai_practice")

    # バッジ定義と照合して返す
    result = []
    for badge_def in BADGE_DEFINITIONS:
        result.append({
            **badge_def,
            "earned": badge_def["id"] in earned,
        })

    return result
