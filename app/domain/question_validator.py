"""
愛媛探索AIクイズ - 問題バリデーター

問題データ（dict）の妥当性を検証する純粋関数を提供する。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.models import Difficulty


@dataclass
class ValidationResult:
    """バリデーション結果を保持するデータクラス"""

    is_valid: bool
    errors: list[str] = field(default_factory=list)


# 有効な難易度の値セット
_VALID_DIFFICULTIES = {d.value for d in Difficulty}

# 有効な exam_domain 値セット
VALID_EXAM_DOMAINS = {
    "Cloud Concepts",
    "Security and Compliance",
    "Cloud Technology and Services",
    "Billing Pricing and Support",
    "AI and ML Fundamentals",
    "Generative AI",
    "Responsible AI",
}

# 選択肢フィールド名
_CHOICE_FIELDS = ["choice_1", "choice_2", "choice_3", "choice_4"]


def validate_question(question_data: dict) -> ValidationResult:
    """
    問題データの妥当性を検証する。

    検証条件:
    - 非空のテキスト（text）
    - 正確に4つの非空選択肢（choice_1, choice_2, choice_3, choice_4）
    - correct_choice_index が 0-3 の範囲の整数
    - 非空の ehime_trivia
    - 非空の aws_ai_explanation
    - 有効な course_id（非空文字列）
    - 有効な difficulty（"基礎", "中級", "上級" のいずれか）

    Args:
        question_data: 検証対象の問題データ辞書

    Returns:
        ValidationResult: is_valid と errors を持つバリデーション結果
    """
    errors: list[str] = []

    # id の検証
    question_id = question_data.get("id")
    if not question_id or not isinstance(question_id, str) or not question_id.strip():
        errors.append("id: 問題IDは空にできません")
    elif len(question_id) > 50:
        errors.append("id: 問題IDは50文字以内である必要があります")

    # テキストの検証
    text = question_data.get("text")
    if not text or not isinstance(text, str) or not text.strip():
        errors.append("text: 問題テキストは空にできません")

    # 4つの選択肢の検証
    for field_name in _CHOICE_FIELDS:
        value = question_data.get(field_name)
        if not value or not isinstance(value, str) or not value.strip():
            errors.append(f"{field_name}: 選択肢は空にできません")
        elif len(value) > 200:
            errors.append(f"{field_name}: 選択肢は200文字以内である必要があります")

    # correct_choice_index の検証
    correct_choice_index = question_data.get("correct_choice_index")
    if correct_choice_index is None:
        errors.append("correct_choice_index: 正解インデックスは必須です")
    elif not isinstance(correct_choice_index, int):
        errors.append("correct_choice_index: 正解インデックスは整数である必要があります")
    elif correct_choice_index < 0 or correct_choice_index > 3:
        errors.append("correct_choice_index: 正解インデックスは0-3の範囲である必要があります")

    # ehime_trivia の検証
    ehime_trivia = question_data.get("ehime_trivia")
    if not ehime_trivia or not isinstance(ehime_trivia, str) or not ehime_trivia.strip():
        errors.append("ehime_trivia: 愛媛トリビアは空にできません")
    elif len(ehime_trivia) > 200:
        errors.append("ehime_trivia: 愛媛トリビアは200文字以内である必要があります")

    # aws_ai_explanation の検証
    aws_ai_explanation = question_data.get("aws_ai_explanation")
    if not aws_ai_explanation or not isinstance(aws_ai_explanation, str) or not aws_ai_explanation.strip():
        errors.append("aws_ai_explanation: AWS/AI解説は空にできません")

    # course_id の検証
    course_id = question_data.get("course_id")
    if not course_id or not isinstance(course_id, str) or not course_id.strip():
        errors.append("course_id: コースIDは空にできません")

    # difficulty の検証
    difficulty = question_data.get("difficulty")
    if not difficulty or not isinstance(difficulty, str):
        errors.append("difficulty: 難易度は必須です")
    elif difficulty not in _VALID_DIFFICULTIES:
        errors.append(
            f"difficulty: 難易度は {', '.join(sorted(_VALID_DIFFICULTIES))} のいずれかである必要があります"
        )

    # exam_domain の検証
    exam_domain = question_data.get("exam_domain")
    if not exam_domain or not isinstance(exam_domain, str):
        errors.append("exam_domain: 試験ドメインは必須です")
    elif exam_domain not in VALID_EXAM_DOMAINS:
        errors.append(f"exam_domain: 試験ドメインは {VALID_EXAM_DOMAINS} のいずれかである必要があります")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors)
