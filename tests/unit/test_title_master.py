"""
称号マスタモジュールのユニットテスト

Requirements: 4.1, 4.3, 4.4
"""

import pytest

from app.domain.title_master import get_title


class TestGetTitle:
    """get_title のユニットテスト"""

    def test_get_title_level_1(self):
        """Level 1 → 伊予の迷い人"""
        assert get_title(1) == "伊予の迷い人"

    def test_get_title_level_2(self):
        """Level 2 → 伊予の迷い人（範囲上限）"""
        assert get_title(2) == "伊予の迷い人"

    def test_get_title_level_3(self):
        """Level 3 → 愛媛の駆け出しAI研究者（範囲下限）"""
        assert get_title(3) == "愛媛の駆け出しAI研究者"

    def test_get_title_level_5(self):
        """Level 5 → 愛媛の駆け出しAI研究者（範囲上限）"""
        assert get_title(5) == "愛媛の駆け出しAI研究者"

    def test_get_title_level_6(self):
        """Level 6 → 道後を極めしAIエンジニア（範囲下限）"""
        assert get_title(6) == "道後を極めしAIエンジニア"

    def test_get_title_level_9(self):
        """Level 9 → 道後を極めしAIエンジニア（範囲上限）"""
        assert get_title(9) == "道後を極めしAIエンジニア"

    def test_get_title_level_10(self):
        """Level 10 → 伝説の愛媛AIマスター（最高称号下限）"""
        assert get_title(10) == "伝説の愛媛AIマスター"

    def test_get_title_level_99(self):
        """Level 99 → 伝説の愛媛AIマスター（最高レベル）"""
        assert get_title(99) == "伝説の愛媛AIマスター"


class TestGetTitleInvalidInput:
    """get_title の不正入力テスト"""

    def test_get_title_zero_raises(self):
        """Level 0 → ValueError"""
        with pytest.raises(ValueError):
            get_title(0)

    def test_get_title_negative_raises(self):
        """Level -1 → ValueError"""
        with pytest.raises(ValueError):
            get_title(-1)

    def test_get_title_float_raises(self):
        """浮動小数点 → ValueError"""
        with pytest.raises(ValueError):
            get_title(3.5)
