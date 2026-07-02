"""
愛媛探索AIクイズ - XP算出モジュール

コース完了時のXP獲得量算出とXP加算を行う純粋関数群。
すべての関数は副作用を持たない。
"""

XP_PER_CORRECT_ANSWER: int = 24
PERFECT_COURSE_BONUS: int = 50


def calculate_xp_award(correct_count: int, total_count: int) -> int:
    """コース完了時のXP獲得量を算出する。

    正解数×10 XP を基本獲得量とし、全問正解（パーフェクト）時に
    追加で100 XP ボーナスを付与する。

    Args:
        correct_count: 正解数（0以上の整数）
        total_count: 総問題数（0以上の整数）

    Returns:
        獲得XP（正解数×10 + パーフェクト時100ボーナス）
    """
    base_xp = correct_count * XP_PER_CORRECT_ANSWER

    if total_count > 0 and correct_count == total_count:
        return base_xp + PERFECT_COURSE_BONUS

    return base_xp


def add_xp(current_xp: int, award: int) -> int:
    """現在のXPに獲得XPを加算する。

    Args:
        current_xp: 現在の累計XP（0以上の整数）
        award: 獲得XP（0以上の整数）

    Returns:
        新しい累計XP

    Raises:
        ValueError: current_xpまたはawardが負の場合
    """
    if current_xp < 0:
        raise ValueError(
            f"current_xp must be non-negative, got {current_xp}"
        )
    if award < 0:
        raise ValueError(f"award must be non-negative, got {award}")

    return current_xp + award
