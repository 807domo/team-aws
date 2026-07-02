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


def get_next_title(level: int) -> str | None:
    """現在のレベルの次の称号を返す。最高称号の場合はNone。

    Args:
        level: 現在のレベル（1以上の整数）

    Returns:
        次の称号文字列。最高称号の場合はNone。
    """
    current_title = get_title(level)
    if current_title == MAX_TITLE:
        return None

    for i, (level_range, title) in enumerate(TITLE_MAPPING):
        if level in level_range:
            if i + 1 < len(TITLE_MAPPING):
                return TITLE_MAPPING[i + 1][1]
            else:
                return MAX_TITLE
    return None


def get_all_titles_with_requirements() -> list[dict]:
    """全称号と解放条件（必要レベル・XP）のリストを返す。

    Returns:
        [{"title": str, "min_level": int, "min_xp": int}, ...]
        min_xp は (min_level - 1)² × 100 で算出。
    """
    result = []
    for level_range, title in TITLE_MAPPING:
        min_level = level_range.start
        min_xp = (min_level - 1) * (min_level - 1) * 100
        result.append({
            "title": title,
            "min_level": min_level,
            "min_xp": min_xp,
        })
    # MAX_TITLE (Level 10+)
    min_level = TITLE_MAPPING[-1][0].stop  # 10
    min_xp = (min_level - 1) * (min_level - 1) * 100
    result.append({
        "title": MAX_TITLE,
        "min_level": min_level,
        "min_xp": min_xp,
    })
    return result
