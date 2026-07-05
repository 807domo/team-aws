"""
DynamoDB アクセスレイヤー

環境変数 USE_DYNAMODB=1 の場合に DynamoDB を使用する。
Lambda 環境では自動的に DynamoDB を使用し、ローカル開発では SQLite を使用する。

テーブル定義:
  - EhimeAI2026-users (PK: id)
  - EhimeAI2026-courses (PK: id)
  - EhimeAI2026-questions (PK: id, GSI: course_id-index)
  - EhimeAI2026-answer_records (PK: id, GSI: user_id-index, GSI: user_course-index)
  - EhimeAI2026-quiz_sessions (PK: id, GSI: user_id-index)
  - EhimeAI2026-mock_exam_sessions (PK: id, GSI: user_id-index)
  - EhimeAI2026-mock_exam_results (PK: id, GSI: user_id-index)
  - EhimeAI2026-bookmarks (PK: id, GSI: user_id-index)
  - EhimeAI2026-glossary_terms (PK: id, GSI: category-index)
  - EhimeAI2026-sessions (PK: id)
"""

import os
import logging
from typing import Optional

import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

TABLE_PREFIX = "EhimeAI2026-"

# Toggle: set USE_DYNAMODB=1 in Lambda environment
USE_DYNAMODB = os.environ.get("USE_DYNAMODB", "0") == "1"

# Optional: DynamoDB Local endpoint for local testing
DYNAMODB_ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT", None)

# AWS region (default: ap-northeast-1 for Japan)
AWS_REGION = os.environ.get("AWS_REGION", "ap-northeast-1")


# --------------------------------------------------------------------------
# Table name helpers
# --------------------------------------------------------------------------

TABLE_NAMES = {
    "users": f"{TABLE_PREFIX}users",
    "courses": f"{TABLE_PREFIX}courses",
    "questions": f"{TABLE_PREFIX}questions",
    "answer_records": f"{TABLE_PREFIX}answer_records",
    "quiz_sessions": f"{TABLE_PREFIX}quiz_sessions",
    "mock_exam_sessions": f"{TABLE_PREFIX}mock_exam_sessions",
    "mock_exam_results": f"{TABLE_PREFIX}mock_exam_results",
    "bookmarks": f"{TABLE_PREFIX}bookmarks",
    "glossary_terms": f"{TABLE_PREFIX}glossary_terms",
    "sessions": f"{TABLE_PREFIX}sessions",
}


def get_table_name(table_key: str) -> str:
    """テーブルキーからプレフィックス付きテーブル名を取得する。"""
    if table_key not in TABLE_NAMES:
        raise ValueError(f"Unknown table key: {table_key}")
    return TABLE_NAMES[table_key]


# --------------------------------------------------------------------------
# DynamoDB Resource / Client
# --------------------------------------------------------------------------

_dynamodb_resource = None
_dynamodb_client = None


def get_dynamodb_resource():
    """boto3 DynamoDB resource をシングルトンとして取得する。"""
    global _dynamodb_resource
    if _dynamodb_resource is None:
        kwargs = {"region_name": AWS_REGION}
        if DYNAMODB_ENDPOINT:
            kwargs["endpoint_url"] = DYNAMODB_ENDPOINT
        _dynamodb_resource = boto3.resource("dynamodb", **kwargs)
    return _dynamodb_resource


def get_dynamodb_client():
    """boto3 DynamoDB client をシングルトンとして取得する。"""
    global _dynamodb_client
    if _dynamodb_client is None:
        kwargs = {"region_name": AWS_REGION}
        if DYNAMODB_ENDPOINT:
            kwargs["endpoint_url"] = DYNAMODB_ENDPOINT
        _dynamodb_client = boto3.client("dynamodb", **kwargs)
    return _dynamodb_client


def get_table(table_key: str):
    """指定されたテーブルキーに対応する DynamoDB Table オブジェクトを取得する。

    Args:
        table_key: テーブルキー (例: "users", "courses", "questions")

    Returns:
        boto3 DynamoDB Table リソース
    """
    resource = get_dynamodb_resource()
    table_name = get_table_name(table_key)
    return resource.Table(table_name)


# --------------------------------------------------------------------------
# Helper functions for common DynamoDB operations
# --------------------------------------------------------------------------


def put_item(table_key: str, item: dict) -> dict:
    """テーブルにアイテムを追加する。"""
    table = get_table(table_key)
    return table.put_item(Item=item)


def get_item(table_key: str, key: dict) -> Optional[dict]:
    """主キーでアイテムを取得する。"""
    table = get_table(table_key)
    response = table.get_item(Key=key)
    return response.get("Item")


def delete_item(table_key: str, key: dict) -> dict:
    """主キーでアイテムを削除する。"""
    table = get_table(table_key)
    return table.delete_item(Key=key)


def query_by_index(
    table_key: str,
    index_name: str,
    key_condition: Key,
    limit: Optional[int] = None,
) -> list[dict]:
    """GSI を使用してクエリを実行する。

    Args:
        table_key: テーブルキー
        index_name: GSI 名 (例: "course_id-index", "user_id-index")
        key_condition: boto3 Key condition expression
        limit: 取得件数上限

    Returns:
        アイテムのリスト
    """
    table = get_table(table_key)
    kwargs = {
        "IndexName": index_name,
        "KeyConditionExpression": key_condition,
    }
    if limit:
        kwargs["Limit"] = limit

    response = table.query(**kwargs)
    return response.get("Items", [])


def scan_table(table_key: str) -> list[dict]:
    """テーブル全体をスキャンする（小規模テーブル向け）。"""
    table = get_table(table_key)
    items = []
    response = table.scan()
    items.extend(response.get("Items", []))

    # ページネーション対応
    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))

    return items


def batch_write_items(table_key: str, items: list[dict]) -> None:
    """バッチでアイテムを書き込む（25件ずつ）。"""
    table = get_table(table_key)

    with table.batch_writer() as batch:
        for item in items:
            batch.put_item(Item=item)


# --------------------------------------------------------------------------
# Utility: Check if DynamoDB is enabled
# --------------------------------------------------------------------------


def is_dynamodb_enabled() -> bool:
    """DynamoDB が有効かどうかを返す。"""
    return USE_DYNAMODB
