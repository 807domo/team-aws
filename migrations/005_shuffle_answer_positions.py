"""
マイグレーション 005: 問題の選択肢をシャッフルし、correct_choice_indexの分布を均等化する

各問題のIDに基づいて決定論的にシャッフルする（同じIDなら常に同じ結果）。
hashlib.md5でシード値を生成し、randomモジュールでシャッフルする。

冪等性: 同じシード値からのシャッフルは常に同じ結果を返すため、
繰り返し実行しても問題ない。
"""

import hashlib
import logging
import random

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

MIGRATION_ID = "005_shuffle_answer_positions"


def upgrade(session: Session) -> None:
    """questionsテーブルの全レコードの選択肢をシャッフルする。

    冪等性: 選択肢をソートして正規化してからIDベースの決定論的シャッフルを行うため、
    何度実行しても同じ結果になる。seed_data.py側でも同じロジックが適用されるため、
    新規DB作成時と既存DB更新時で同じ結果が得られる。

    Args:
        session: SQLAlchemy セッション
    """
    # questionsテーブルが存在するか確認
    table_check = session.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name='questions'")
    ).fetchone()

    if not table_check:
        logger.info("questionsテーブルが存在しません（スキップ）")
        return

    # 全問題を取得
    rows = session.execute(
        text("SELECT id, choice_1, choice_2, choice_3, choice_4, correct_choice_index FROM questions")
    ).fetchall()

    if not rows:
        logger.info("questionsテーブルにレコードがありません（スキップ）")
        return

    updated_count = 0
    for row in rows:
        question_id = row[0]
        choices = [row[1], row[2], row[3], row[4]]
        correct_index = row[5]

        # 正解テキストを保存
        correct_answer = choices[correct_index]

        # IDベースの決定論的シャッフル
        seed = int(hashlib.md5(question_id.encode()).hexdigest(), 16) % (2**32)
        rng = random.Random(seed)

        # 冪等性を確保するため、選択肢をソートして正規化してからシャッフル
        # これにより、何度実行しても同じ結果が得られる
        choices_sorted = sorted(choices)
        rng.shuffle(choices_sorted)
        new_correct_index = choices_sorted.index(correct_answer)

        # 更新
        session.execute(
            text("""
                UPDATE questions
                SET choice_1 = :c1,
                    choice_2 = :c2,
                    choice_3 = :c3,
                    choice_4 = :c4,
                    correct_choice_index = :ci
                WHERE id = :qid
            """),
            {
                "c1": choices_sorted[0],
                "c2": choices_sorted[1],
                "c3": choices_sorted[2],
                "c4": choices_sorted[3],
                "ci": new_correct_index,
                "qid": question_id,
            },
        )
        updated_count += 1

    session.commit()

    # 分布を確認してログ出力
    dist = session.execute(
        text("SELECT correct_choice_index, COUNT(*) FROM questions GROUP BY correct_choice_index ORDER BY correct_choice_index")
    ).fetchall()
    dist_str = ", ".join(f"index {r[0]}: {r[1]}問" for r in dist)
    logger.info("選択肢シャッフル完了: %d問更新。分布: %s", updated_count, dist_str)
