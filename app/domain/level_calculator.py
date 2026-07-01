"""
愛媛探索AIクイズ - レベル算出モジュール

累計XPからレベルを算出し、XPゲージ表示用データを計算する純粋関数群。
すべての関数は副作用を持たない。
"""

import math

MAX_LEVEL: int = 10
MAX_XP: int = 10_000  # 10² × 100


def calculate_level(total_xp: int) -> int:
    """累計XPからレベルを算出する。

    Level N の境界: Level N は累計XP (N-1)² × 100 以上で到達する。
    Level 1: 0 XP, Level 2: 100 XP, Level 3: 400 XP, ...

    Args:
        total_xp: 累計XP（0以上の整数）

    Returns:
        レベル（1〜99）

    Raises:
        ValueError: total_xpが負の場合、または整数でない場合
    """
    if not isinstance(total_xp, int):
        raise ValueError(
            f"total_xp must be an integer, got {type(total_xp).__name__}"
        )
    if total_xp < 0:
        raise ValueError(
            f"total_xp must be non-negative, got {total_xp}"
        )

    level = int(math.isqrt(total_xp // 100)) + 1
    return min(level, MAX_LEVEL)


def xp_threshold_for_level(level: int) -> int:
    """指定レベルの上限XPしきい値（次レベルに到達するための累計XP）を返す。

    Level N のしきい値 = N² × 100
    これは Level N+1 に到達するために必要な累計XPである。

    Args:
        level: レベル（1以上の整数）

    Returns:
        累計XPしきい値（level² × 100）

    Raises:
        ValueError: levelが1未満または整数でない場合
    """
    if not isinstance(level, int):
        raise ValueError(
            f"level must be an integer, got {type(level).__name__}"
        )
    if level < 1:
        raise ValueError(f"level must be at least 1, got {level}")

    return level * level * 100


def calculate_xp_gauge(total_xp: int, level: int) -> dict:
    """XPゲージ表示用データを算出する。

    現在のレベル開始XPから次レベル到達XPまでの進捗を計算する。

    Args:
        total_xp: 現在の累計XP（0以上の整数）
        level: 現在のレベル（1以上の整数）

    Returns:
        {"current_level_xp": int, "required_xp": int, "percentage": float}
        - current_level_xp: 現レベル開始からの累計XP
        - required_xp: 現レベル開始から次レベルまでの必要XP
        - percentage: 進捗パーセンテージ（0.0〜100.0）

    Raises:
        ValueError: total_xpが負の場合、levelが1未満の場合、
                    または整数でない場合
    """
    if not isinstance(total_xp, int):
        raise ValueError(
            f"total_xp must be an integer, got {type(total_xp).__name__}"
        )
    if not isinstance(level, int):
        raise ValueError(
            f"level must be an integer, got {type(level).__name__}"
        )
    if total_xp < 0:
        raise ValueError(
            f"total_xp must be non-negative, got {total_xp}"
        )
    if level < 1:
        raise ValueError(f"level must be at least 1, got {level}")

    if level >= MAX_LEVEL:
        return {
            "current_level_xp": 0,
            "required_xp": 0,
            "percentage": 100.0,
        }

    # 現レベル開始XP = (level - 1)² × 100
    level_start_xp = (level - 1) * (level - 1) * 100
    # 次レベル開始XP = level² × 100
    next_level_xp = xp_threshold_for_level(level)

    current_level_xp = total_xp - level_start_xp
    required_xp = next_level_xp - level_start_xp

    if required_xp == 0:
        percentage = 100.0
    else:
        percentage = round(current_level_xp / required_xp * 100, 1)

    return {
        "current_level_xp": current_level_xp,
        "required_xp": required_xp,
        "percentage": percentage,
    }
