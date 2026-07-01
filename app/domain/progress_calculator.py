"""
愛媛探索AIクイズ - 進捗ステータス算出モジュール

難易度ごとの進捗ステータスを算出する純粋関数群。
すべての関数は副作用を持たない。
"""

from enum import Enum

from app.domain.models import AnswerRecord


class ProgressStatus(str, Enum):
    """地域の進捗ステータス"""

    NOT_STARTED = "未着手"
    IN_PROGRESS = "進行中"
    COMPLETE = "コンプリート"


def calculate_region_progress(
    region: str,
    courses_in_region: list[str],
    user_answer_records: list[AnswerRecord],
    course_questions: dict[str, list[str]],
) -> ProgressStatus:
    """地域の進捗ステータスを算出する。

    判定ロジック:
    - ゼロコース地域 → コンプリート
    - エリア内コースに回答記録なし → 未着手
    - 全コースで全問正解記録が存在 → コンプリート
    - それ以外 → 進行中

    Args:
        region: 対象地域名（例: "CHUYO", "NANYO", "TOYO"）
        courses_in_region: その地域のコースIDリスト
        user_answer_records: ユーザーの回答記録リスト
        course_questions: コースごとの問題IDリスト {course_id: [question_ids]}

    Returns:
        ProgressStatus enum
    """
    # ゼロコース地域はコンプリートを返す
    if not courses_in_region:
        return ProgressStatus.COMPLETE

    # この地域のコースに該当する回答記録を抽出
    region_course_set = set(courses_in_region)
    region_records = [
        r for r in user_answer_records if r.course_id in region_course_set
    ]

    # 回答記録が一切ない場合は未着手
    if not region_records:
        return ProgressStatus.NOT_STARTED

    # 各コースについて全問正解が達成されているかチェック
    all_courses_complete = True
    for course_id in courses_in_region:
        if not _is_course_completed(course_id, region_records, course_questions):
            all_courses_complete = False
            break

    if all_courses_complete:
        return ProgressStatus.COMPLETE

    return ProgressStatus.IN_PROGRESS


def _is_course_completed(
    course_id: str,
    answer_records: list[AnswerRecord],
    course_questions: dict[str, list[str]],
) -> bool:
    """コースが完了しているか判定する。

    コース内の全問題について、少なくとも1回正解した記録が存在すれば完了とみなす。

    Args:
        course_id: 対象コースID
        answer_records: 回答記録リスト（地域でフィルタ済み）
        course_questions: コースごとの問題IDリスト

    Returns:
        全問正解が達成されている場合True
    """
    questions = course_questions.get(course_id, [])

    # 問題が定義されていないコースは完了とみなす
    if not questions:
        return True

    # このコースで正解した問題IDを収集
    correct_question_ids = {
        r.question_id
        for r in answer_records
        if r.course_id == course_id and r.is_correct
    }

    # 全問題に少なくとも1回正解しているか確認
    return all(q_id in correct_question_ids for q_id in questions)
