"""
愛媛探索AIクイズ - 称号マスタモジュール

レベルに応じた称号マッピングを管理する純粋関数群。
すべての関数は副作用を持たない。
"""

TITLE_MAPPING: list[tuple[range, str]] = [
    (range(1, 3), "伊予の迷い人"),             # Level 1-2
    (range(3, 6), "愛媛の駆け出しAI研究者"),    # Level 3-5
    (range(6, 10), "道後を極めしAIエンジニア"),  # Level 6-9
]

MAX_TITLE: str = "伝説の愛媛AIマスター"


def get_title(level: int) -> str:
    """レベルに対応する称号を返す。

    Args:
        level: 現在のレベル（1以上の整数）

    Returns:
        称号文字列

    Raises:
        ValueError: levelが1未満または整数でない場合
    """
    if not isinstance(level, int) or isinstance(level, bool):
        raise ValueError(f"levelは整数である必要があります: {level}")
    if level < 1:
        raise ValueError(f"levelは1以上である必要があります: {level}")

    for level_range, title in TITLE_MAPPING:
        if level in level_range:
            return title

    return MAX_TITLE
