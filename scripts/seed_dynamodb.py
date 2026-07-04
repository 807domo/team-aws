"""
Seed DynamoDB tables with initial data from seed_data files.

Usage:
    python scripts/seed_dynamodb.py

DynamoDB テーブルにシードデータ（コース・問題・用語集）を投入するスクリプト。
既存の seed_data モジュールからデータを読み込み、DynamoDB に書き込む。
"""

import sys
import uuid

sys.path.insert(0, ".")

import os

os.environ["USE_DYNAMODB"] = "1"

from app.data.dynamodb import batch_write_items  # noqa: E402
from app.data.glossary_seed import GLOSSARY_SEED_DATA  # noqa: E402
from app.data.seed_data import COURSES, QUESTIONS  # noqa: E402
from app.data.seed_data_extra import EXTRA_QUESTIONS  # noqa: E402
from app.data.seed_data_extra2 import EXTRA_QUESTIONS_2  # noqa: E402


def seed_courses():
    """コースデータを DynamoDB に投入する。"""
    print(f"Seeding {len(COURSES)} courses...")
    batch_write_items("courses", COURSES)
    print("Done.")


def seed_questions():
    """問題データを DynamoDB に投入する。

    QUESTIONS には既に BUNKAZAI_QUESTIONS と extra_questions が含まれているため、
    EXTRA_QUESTIONS (seed_data_extra) と EXTRA_QUESTIONS_2 (seed_data_extra2) を追加する。
    重複IDは除外する。
    """
    all_q = list(QUESTIONS) + list(EXTRA_QUESTIONS) + list(EXTRA_QUESTIONS_2)

    # 重複ID除外
    seen_ids: set[str] = set()
    unique_questions: list[dict] = []
    for q in all_q:
        qid = q["id"]
        if qid not in seen_ids:
            seen_ids.add(qid)
            unique_questions.append(q)

    print(f"Seeding {len(unique_questions)} questions...")
    batch_write_items("questions", unique_questions)
    print("Done.")


def seed_glossary():
    """用語集データを DynamoDB に投入する。"""
    items = []
    for entry in GLOSSARY_SEED_DATA:
        items.append({"id": str(uuid.uuid4()), **entry})
    print(f"Seeding {len(items)} glossary terms...")
    batch_write_items("glossary_terms", items)
    print("Done.")


if __name__ == "__main__":
    seed_courses()
    seed_questions()
    seed_glossary()
    print("All seeding complete!")
