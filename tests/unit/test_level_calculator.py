"""
レベル算出モジュールのユニットテスト

Requirements: 3.1, 3.2, 3.3, 3.4, 1.2, 1.3, 1.5
"""

import pytest

from app.domain.level_calculator import (
    calculate_level,
    calculate_xp_gauge,
    xp_threshold_for_level,
)


class TestCalculateLevel:
    """calculate_level のユニットテスト（境界値テスト）"""

    def test_calculate_level_zero_xp(self):
        """XP=0 → Level 1"""
        assert calculate_level(0) == 1

    def test_calculate_level_99_xp(self):
        """XP=99 → Level 1（100未満なのでLevel 1のまま）"""
        assert calculate_level(99) == 1

    def test_calculate_level_100_xp(self):
        """XP=100 → Level 2（1²×100 = 100でLevel 2到達）"""
        assert calculate_level(100) == 2

    def test_calculate_level_400_xp(self):
        """XP=400 → Level 3（2²×100 = 400でLevel 3到達）"""
        assert calculate_level(400) == 3

    def test_calculate_level_max_xp(self):
        """XP=MAX_XP以上 → MAX_LEVEL"""
        from app.domain.level_calculator import MAX_LEVEL, MAX_XP
        assert calculate_level(MAX_XP) == MAX_LEVEL


class TestXpThresholdForLevel:
    """xp_threshold_for_level のユニットテスト"""

    def test_xp_threshold_for_level_1(self):
        """Level 1のしきい値は 1²×100 = 100"""
        assert xp_threshold_for_level(1) == 100

    def test_xp_threshold_for_level_2(self):
        """Level 2のしきい値は 2²×100 = 400"""
        assert xp_threshold_for_level(2) == 400


class TestCalculateXpGauge:
    """calculate_xp_gauge のユニットテスト（ゲージ計算）"""

    def test_calculate_xp_gauge_level1_50xp(self):
        """Level 1で50XP → 50% progress (50/100)"""
        result = calculate_xp_gauge(50, 1)
        assert result["current_level_xp"] == 50
        assert result["required_xp"] == 100
        assert result["percentage"] == 50.0

    def test_calculate_xp_gauge_level2_200xp(self):
        """Level 2で200XP → 33.3% progress ((200-100)/(400-100))"""
        result = calculate_xp_gauge(200, 2)
        assert result["current_level_xp"] == 100
        assert result["required_xp"] == 300
        assert result["percentage"] == 33.3


class TestCalculateLevelInvalidInput:
    """calculate_level の不正入力テスト"""

    def test_calculate_level_negative_raises(self):
        """負値入力 → ValueError"""
        with pytest.raises(ValueError):
            calculate_level(-1)

    def test_calculate_level_float_raises(self):
        """浮動小数点入力 → ValueError"""
        with pytest.raises(ValueError):
            calculate_level(3.5)

    def test_calculate_level_none_raises(self):
        """None入力 → ValueError"""
        with pytest.raises(ValueError):
            calculate_level(None)
