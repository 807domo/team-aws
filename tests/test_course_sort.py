"""
コースソート順序のプロパティベーステスト

DynamoDBCourseRepository の get_all_courses() および get_courses_by_region() が
常に course_id 昇順でソートされた結果を返すことを検証する。

# Feature: dynamodb-migration-completion, Property 11: コースソート順序の不変条件
"""

import os

import pytest
import boto3
from moto import mock_aws
from hypothesis import given, settings
from hypothesis import strategies as st

from app.data.dynamodb import TABLE_PREFIX
import app.data.dynamodb as dynamodb_module
from app.data.dynamodb_repositories import DynamoDBCourseRepository
from app.domain.models import Region


@pytest.fixture(autouse=True)
def _set_dynamodb_env(monkeypatch):
    """テスト用環境変数をスコープ内で設定し、テスト終了後に自動クリーンアップする。"""
    monkeypatch.setenv("USE_DYNAMODB", "1")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-northeast-1")


# =============================================================================
# Strategies
# =============================================================================

REGIONS = [r.value for r in Region]
DIFFICULTIES = ["基礎", "中級", "上級"]

course_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "Pd")),
    min_size=1,
    max_size=20,
)

course_list_strategy = st.lists(
    st.fixed_dictionaries(
        {
            "id": course_id_strategy,
            "name": st.text(min_size=1, max_size=30),
            "region": st.sampled_from(REGIONS),
            "difficulty": st.sampled_from(DIFFICULTIES),
            "description": st.text(min_size=1, max_size=50),
        }
    ),
    min_size=1,
    max_size=15,
    unique_by=lambda x: x["id"],
)


# =============================================================================
# Helpers
# =============================================================================


def _create_courses_table():
    """moto モック内で courses テーブルを作成する。"""
    client = boto3.client("dynamodb", region_name="ap-northeast-1")
    client.create_table(
        TableName=f"{TABLE_PREFIX}courses",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )


def _reset_dynamodb_singletons():
    """DynamoDB モジュールのシングルトンをリセットして moto モックが適用されるようにする。"""
    dynamodb_module._dynamodb_resource = None
    dynamodb_module._dynamodb_client = None


# =============================================================================
# Property 11: コースソート順序の不変条件
# =============================================================================


@settings(max_examples=20, deadline=None)
@given(courses=course_list_strategy)
@mock_aws
def test_get_all_courses_sorted_by_id(courses):
    """
    Feature: dynamodb-migration-completion, Property 11: コースソート順序の不変条件

    任意のコース集合に対して、get_all_courses() は常に course_id 昇順で
    ソートされた結果を返す。

    **Validates: Requirements 7.1, 7.3**
    """
    _reset_dynamodb_singletons()
    _create_courses_table()

    # ランダムな順序でコースを DynamoDB に投入
    table = boto3.resource("dynamodb", region_name="ap-northeast-1").Table(
        f"{TABLE_PREFIX}courses"
    )
    for course in courses:
        table.put_item(Item=course)

    # リポジトリ経由で全コースを取得
    repo = DynamoDBCourseRepository()
    result = repo.get_all_courses()

    # 結果が id 昇順でソートされていることを検証
    result_ids = [c.id for c in result]
    assert result_ids == sorted(result_ids), (
        f"get_all_courses() の結果が id 昇順でソートされていない: {result_ids}"
    )


@settings(max_examples=20, deadline=None)
@given(courses=course_list_strategy)
@mock_aws
def test_get_courses_by_region_sorted_by_id(courses):
    """
    Feature: dynamodb-migration-completion, Property 11: コースソート順序の不変条件

    任意のコース集合に対して、get_courses_by_region() は常に course_id 昇順で
    ソートされた結果を返す。

    **Validates: Requirements 7.2, 7.3**
    """
    _reset_dynamodb_singletons()
    _create_courses_table()

    # ランダムな順序でコースを DynamoDB に投入
    table = boto3.resource("dynamodb", region_name="ap-northeast-1").Table(
        f"{TABLE_PREFIX}courses"
    )
    for course in courses:
        table.put_item(Item=course)

    repo = DynamoDBCourseRepository()

    # 各地域について検証
    for region in Region:
        result = repo.get_courses_by_region(region)

        # 結果が id 昇順でソートされていることを検証
        result_ids = [c.id for c in result]
        assert result_ids == sorted(result_ids), (
            f"get_courses_by_region({region}) の結果が id 昇順でソートされていない: "
            f"{result_ids}"
        )

        # 全結果が指定地域に属することを検証
        for c in result:
            assert c.region == region, (
                f"get_courses_by_region({region}) に別地域のコースが含まれている: "
                f"course {c.id} has region {c.region}"
            )
