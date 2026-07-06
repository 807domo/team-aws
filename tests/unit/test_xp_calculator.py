"""
XP算出モジュールのユニットテスト

Requirements: 2.1, 2.2, 2.3, 2.6
"""

import pytest

from app.domain.xp_calculator import (
    XP_PER_CORRECT_ANSWER,
    PERFECT_COURSE_BONUS,
    add_xp,
    calculate_xp_award,
)


class TestCalculateXpAward:
    """calculate_xp_award のユニットテスト"""

    def test_calculate_xp_award_zero_correct(self):
        """0問正解 → 0 XP"""
        assert calculate_xp_award(0, 5) == 0

    def test_calculate_xp_award_one_correct(self):
        """1問正解/5問 → 24 XP"""
        assert calculate_xp_award(1, 5) == XP_PER_CORRECT_ANSWER

    def test_calculate_xp_award_perfect_5(self):
        """5問全正解/5問 → 5*24 + 50 = 170 XP"""
        assert calculate_xp_award(5, 5) == 5 * XP_PER_CORRECT_ANSWER + PERFECT_COURSE_BONUS

    def test_calculate_xp_award_perfect_10(self):
        """10問全正解/10問 → 10*24 + 50 = 290 XP"""
        assert calculate_xp_award(10, 10) == 10 * XP_PER_CORRECT_ANSWER + PERFECT_COURSE_BONUS


class TestAddXp:
    """add_xp のユニットテスト"""

    def test_add_xp_normal(self):
        """100 + 50 = 150"""
        assert add_xp(100, 50) == 150

    def test_add_xp_zero(self):
        """0 + 0 = 0"""
        assert add_xp(0, 0) == 0

    def test_add_xp_negative_current_raises(self):
        """current_xp=-1 raises ValueError"""
        with pytest.raises(ValueError):
            add_xp(-1, 10)

    def test_add_xp_negative_award_raises(self):
        """award=-1 raises ValueError"""
        with pytest.raises(ValueError):
            add_xp(100, -1)
