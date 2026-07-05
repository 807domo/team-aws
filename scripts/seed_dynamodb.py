"""
Seed DynamoDB tables with initial data from seed_data files.

Usage:
    python scripts/seed_dynamodb.py

DynamoDB テーブルにシードデータ（コース・問題・用語集）を投入するスクリプト。
既存の seed_data モジュールからデータを読み込み、DynamoDB に書き込む。

改善点:
  - 25件バッチ制限の明示的処理
  - UnprocessedItems のリトライ（指数バックオフ付き最大3回）
  - テーブルアクセスエラー (ResourceNotFoundException等) で早期終了
  - 冪等性: put_item の上書きセマンティクス（条件なし put）
  - 完了時に各テーブルの投入件数を stdout に出力
"""

import sys
import time
import uuid

sys.path.insert(0, ".")

import os

os.environ["USE_DYNAMODB"] = "1"

from botocore.exceptions import ClientError, EndpointConnectionError  # noqa: E402

from app.data.dynamodb import get_table_name, get_dynamodb_resource  # noqa: E402
from app.data.glossary_seed import GLOSSARY_SEED_DATA  # noqa: E402
from app.data.seed_data import COURSES, QUESTIONS  # noqa: E402
from app.data.seed_data_extra import EXTRA_QUESTIONS  # noqa: E402
from app.data.seed_data_extra2 import EXTRA_QUESTIONS_2  # noqa: E402


MAX_BATCH_SIZE = 25
MAX_RETRIES = 3


def _check_table_accessible(table_key: str) -> str:
    """テーブルが存在しアクセス可能であることを確認する。

    Args:
        table_key: テーブルキー (例: "courses", "questions")

    Returns:
        完全修飾テーブル名

    Raises:
        SystemExit: テーブルが存在しないかアクセスできない場合
    """
    table_name = get_table_name(table_key)
    try:
        resource = get_dynamodb_resource()
        table = resource.Table(table_name)
        # describe_table を呼んでテーブルの存在を確認する
        table.load()
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        print(
            f"Error: Cannot access table '{table_name}': {error_code} - {e.response['Error']['Message']}",
            file=sys.stderr,
        )
        sys.exit(1)
    except EndpointConnectionError as e:
        print(
            f"Error: Cannot connect to DynamoDB endpoint for table '{table_name}': {e}",
            file=sys.stderr,
        )
        sys.exit(1)
    return table_name


def batch_write_with_retry(
    table_name: str, items: list[dict], max_retries: int = MAX_RETRIES
) -> int:
    """バッチ書き込み（25件ずつ、リトライ付き）。

    DynamoDB の batch_write_item API を使用し、25件以下のバッチに分割して書き込む。
    UnprocessedItems がある場合は指数バックオフで最大 max_retries 回リトライする。
    put_item の上書きセマンティクス（条件なし put）により冪等性を確保する。

    Args:
        table_name: 完全修飾テーブル名 (例: "EhimeAI2026-courses")
        items: 書き込むアイテムのリスト (Python dict 形式)
        max_retries: UnprocessedItems のリトライ最大回数

    Returns:
        書き込みに成功したアイテム数

    Raises:
        SystemExit: リトライ超過またはAPI エラーで書き込み失敗した場合
    """
    resource = get_dynamodb_resource()
    client = resource.meta.client
    total_written = 0

    for i in range(0, len(items), MAX_BATCH_SIZE):
        batch = items[i : i + MAX_BATCH_SIZE]
        batch_size = len(batch)

        # resource.meta.client は Python dict を自動的に DynamoDB 形式に変換する
        request_items = {
            table_name: [
                {"PutRequest": {"Item": item}} for item in batch
            ]
        }

        retries = 0
        while request_items:
            try:
                response = client.batch_write_item(RequestItems=request_items)
            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                print(
                    f"Error: batch_write_item failed for '{table_name}': "
                    f"{error_code} - {e.response['Error']['Message']}",
                    file=sys.stderr,
                )
                sys.exit(1)
            except EndpointConnectionError as e:
                print(
                    f"Error: Cannot connect to DynamoDB endpoint: {e}",
                    file=sys.stderr,
                )
                sys.exit(1)

            unprocessed = response.get("UnprocessedItems", {})
            if not unprocessed:
                total_written += batch_size
                break

            # UnprocessedItems がある場合リトライ
            unprocessed_count = len(unprocessed.get(table_name, []))
            processed_in_this_call = batch_size - unprocessed_count
            total_written += processed_in_this_call

            retries += 1
            if retries > max_retries:
                print(
                    f"Error: Failed to write {unprocessed_count} items to "
                    f"'{table_name}' after {max_retries} retries",
                    file=sys.stderr,
                )
                sys.exit(1)

            # 指数バックオフ
            backoff_time = 2**retries
            time.sleep(backoff_time)

            # 残りのアイテムでリトライ
            request_items = unprocessed
            batch_size = unprocessed_count

    return total_written


def seed_courses() -> int:
    """コースデータを DynamoDB に投入する。

    Returns:
        投入したアイテム数
    """
    table_name = _check_table_accessible("courses")
    count = batch_write_with_retry(table_name, COURSES)
    return count


def seed_questions() -> int:
    """問題データを DynamoDB に投入する。

    QUESTIONS, EXTRA_QUESTIONS, EXTRA_QUESTIONS_2 を統合し、
    重複IDを除外して投入する。

    Returns:
        投入したアイテム数
    """
    table_name = _check_table_accessible("questions")

    all_q = list(QUESTIONS) + list(EXTRA_QUESTIONS) + list(EXTRA_QUESTIONS_2)

    # 重複ID除外
    seen_ids: set[str] = set()
    unique_questions: list[dict] = []
    for q in all_q:
        qid = q["id"]
        if qid not in seen_ids:
            seen_ids.add(qid)
            unique_questions.append(q)

    count = batch_write_with_retry(table_name, unique_questions)
    return count


def seed_glossary() -> int:
    """用語集データを DynamoDB に投入する。

    各エントリに決定的な UUID (uuid5) を付与して投入する。
    term + category から決定的な ID を生成することで、
    put_item の上書きセマンティクスにより冪等性を確保する。

    Returns:
        投入したアイテム数
    """
    table_name = _check_table_accessible("glossary_terms")

    items = []
    for entry in GLOSSARY_SEED_DATA:
        # term + category から決定的な UUID を生成して冪等性を確保
        deterministic_id = str(
            uuid.uuid5(uuid.NAMESPACE_DNS, f"{entry['term']}:{entry['category']}")
        )
        items.append({"id": deterministic_id, **entry})

    count = batch_write_with_retry(table_name, items)
    return count


def main():
    """メインエントリポイント。全テーブルにシードデータを投入する。"""
    results: list[tuple[str, int]] = []

    courses_count = seed_courses()
    table_name = get_table_name("courses")
    results.append((table_name, courses_count))

    questions_count = seed_questions()
    table_name = get_table_name("questions")
    results.append((table_name, questions_count))

    glossary_count = seed_glossary()
    table_name = get_table_name("glossary_terms")
    results.append((table_name, glossary_count))

    # 完了時に各テーブルの投入件数を出力
    for tbl_name, count in results:
        print(f"{tbl_name}: {count} items inserted")


if __name__ == "__main__":
    main()
