"""
愛媛探索AIクイズ - 採点モジュール

正答率計算、グレード判定、ドメイン別正答率、弱点特定を行う純粋関数群。
すべての関数は副作用を持たない。
"""

from app.domain.models import AnswerRecord, Grade, WeakArea


def calculate_accuracy_rate(correct_count: int, total_count: int) -> float:
    """正答率を計算する（パーセンテージ、小数第1位まで）。

    Args:
        correct_count: 正解数
        total_count: 総回答数

    Returns:
        正答率（0.0〜100.0）。total_count=0の場合は0.0を返す。
    """
    if total_count == 0:
        return 0.0
    return round(correct_count / total_count * 100, 1)


def calculate_grade(score_percentage: float) -> Grade:
    """スコアからグレードを判定する。

    Args:
        score_percentage: スコア（0.0〜100.0のパーセンテージ）

    Returns:
        Grade enum (A: 90-100, B: 80-89, C: 70-79, D: 60-69, E: 0-59)
    """
    if score_percentage >= 90:
        return Grade.A
    elif score_percentage >= 80:
        return Grade.B
    elif score_percentage >= 70:
        return Grade.C
    elif score_percentage >= 60:
        return Grade.D
    else:
        return Grade.E


def calculate_domain_accuracy(
    answer_records: list[AnswerRecord],
    question_domains: dict[str, str],
) -> dict[str, float]:
    """ドメイン別の正答率を計算する。

    Args:
        answer_records: 回答記録リスト
        question_domains: 問題IDからドメインへのマッピング {question_id: exam_domain}

    Returns:
        ドメイン別正答率の辞書 {domain: accuracy_rate}。
        各値は0.0〜100.0のパーセンテージ（小数第1位まで）。
    """
    domain_correct: dict[str, int] = {}
    domain_total: dict[str, int] = {}

    for record in answer_records:
        domain = question_domains.get(record.question_id)
        if domain is None:
            continue

        domain_total[domain] = domain_total.get(domain, 0) + 1
        if record.is_correct:
            domain_correct[domain] = domain_correct.get(domain, 0) + 1

    result: dict[str, float] = {}
    for domain, total in domain_total.items():
        correct = domain_correct.get(domain, 0)
        result[domain] = round(correct / total * 100, 1)

    return result


def identify_weak_areas(
    answer_records: list[AnswerRecord],
    question_domains: dict[str, str],
    threshold: float = 0.5,
) -> list[WeakArea]:
    """誤答率がthreshold以上のドメインを弱点として特定する。

    Args:
        answer_records: 回答記録リスト
        question_domains: 問題IDからドメインへのマッピング {question_id: exam_domain}
        threshold: 弱点判定の閾値（デフォルト0.5 = 50%）

    Returns:
        弱点領域のリスト。各WeakAreaには domain と incorrect_rate を含む。
        incorrect_rate は0.0〜100.0のパーセンテージ（小数第1位まで）。
    """
    domain_correct: dict[str, int] = {}
    domain_total: dict[str, int] = {}

    for record in answer_records:
        domain = question_domains.get(record.question_id)
        if domain is None:
            continue

        domain_total[domain] = domain_total.get(domain, 0) + 1
        if record.is_correct:
            domain_correct[domain] = domain_correct.get(domain, 0) + 1

    weak_areas: list[WeakArea] = []
    for domain, total in domain_total.items():
        correct = domain_correct.get(domain, 0)
        incorrect = total - correct
        incorrect_rate = incorrect / total

        if incorrect_rate >= threshold:
            weak_areas.append(
                WeakArea(
                    domain=domain,
                    incorrect_rate=round(incorrect_rate * 100, 1),
                )
            )

    return weak_areas
