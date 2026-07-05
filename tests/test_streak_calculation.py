"""
ストリーク計算のプロパティベーステスト

Property 5: 連続回答日数計算の正確性
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock

from hypothesis import given, settings
from hypothesis import strategies as st

from app.presentation.routers.top_router import _calculate_streak


# Feature: dynamodb-migration-completion, Property 5: 連続回答日数計算の正確性


@dataclass
class MockAnswerRecord:
    """テスト用のモック回答記録"""

    id: str
    user_id: str
    question_id: str
    course_id: str
    selected_choice_index: int
    is_correct: bool
    answered_at: datetime


def _reference_streak(dates: list[date]) -> int:
    """リファレンス実装: 連続回答日数を計算する。

    - 最新の回答日が今日でも昨日でもない場合 → 0
    - そうでなければ最新日から遡って連続している日数を返す
    """
    if not dates:
        return 0

    unique_dates = sorted(set(dates), reverse=True)
    today = date.today()

    if unique_dates[0] != today and unique_dates[0] != today - timedelta(days=1):
        return 0

    streak = 0
    check_date = unique_dates[0]
    for d in unique_dates:
        if d == check_date:
            streak += 1
            check_date -= timedelta(days=1)
        elif d < check_date:
            break

    return streak


# 過去30日以内の日付を生成するストラテジー
date_strategy = st.dates(
    min_value=date.today() - timedelta(days=30),
    max_value=date.today(),
)


@settings(max_examples=100)
@given(answer_dates=st.lists(date_strategy, min_size=0, max_size=20))
def test_streak_calculation_matches_reference(answer_dates: list[date]):
    """
    Feature: dynamodb-migration-completion, Property 5: 連続回答日数計算の正確性

    任意の回答日付リストに対して、_calculate_streak関数はリファレンス実装と
    同じ結果を返す。

    **Validates: Requirements 3.1**
    """
    user_id = "test-user-001"

    # モックAnswerRecordオブジェクトを作成
    mock_records = [
        MockAnswerRecord(
            id=f"record-{i}",
            user_id=user_id,
            question_id=f"question-{i}",
            course_id=f"course-{i % 3}",
            selected_choice_index=0,
            is_correct=True,
            answered_at=datetime.combine(d, datetime.min.time()),
        )
        for i, d in enumerate(answer_dates)
    ]

    # モックリポジトリを作成
    mock_repo = MagicMock()
    mock_repo.get_records_by_user.return_value = mock_records

    # 実装を呼び出し
    result = _calculate_streak(user_id, mock_repo)

    # リファレンス実装と比較
    expected = _reference_streak(answer_dates)

    assert result == expected, (
        f"streak mismatch: got {result}, expected {expected}, "
        f"dates={sorted(set(answer_dates), reverse=True)}"
    )
