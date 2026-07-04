"""
愛媛探索AIクイズ - DynamoDB Repository Implementations

DynamoDB をバックエンドとするリポジトリ実装。
SQLAlchemy 版と同じ公開インターフェースを提供する。
Lambda 環境で USE_DYNAMODB=1 の場合に使用される。
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from boto3.dynamodb.conditions import Attr, Key

from app.data.dynamodb import (
    batch_write_items,
    get_item,
    get_table,
    is_dynamodb_enabled,
    put_item,
    query_by_index,
    scan_table,
)
from app.domain.models import AnswerRecord, Course, Difficulty, Question, Region
from app.domain.question_validator import validate_question
from app.domain.scoring import calculate_accuracy_rate


# =============================================================================
# DynamoDBCourseRepository
# =============================================================================


class DynamoDBCourseRepository:
    """DynamoDB を使用したコースリポジトリ"""

    def get_all_courses(self) -> list[Course]:
        """全コースを取得する"""
        items = scan_table("courses")
        return [self._to_domain(item) for item in items]

    def get_courses_by_region(self, region: Region) -> list[Course]:
        """指定された地域のコースを取得する"""
        table = get_table("courses")
        response = table.scan(
            FilterExpression=Attr("region").eq(region.value)
        )
        items = response.get("Items", [])

        # ページネーション対応
        while "LastEvaluatedKey" in response:
            response = table.scan(
                FilterExpression=Attr("region").eq(region.value),
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(response.get("Items", []))

        return [self._to_domain(item) for item in items]

    def get_course_by_id(self, course_id: str) -> Optional[Course]:
        """IDを指定してコースを取得する。存在しない場合は None を返す"""
        item = get_item("courses", {"id": course_id})
        if item is None:
            return None
        return self._to_domain(item)

    def get_courses_grouped_by_region(self) -> dict[Region, list[Course]]:
        """全コースを地域別にグルーピングして返す"""
        grouped: dict[Region, list[Course]] = {region: [] for region in Region}

        all_courses = self.get_all_courses()
        for course in all_courses:
            grouped[course.region].append(course)

        return grouped

    @staticmethod
    def _to_domain(item: dict) -> Course:
        """DynamoDB アイテムをドメインモデルに変換する"""
        return Course(
            id=item["id"],
            name=item["name"],
            region=Region(item["region"]),
            difficulty=Difficulty(item["difficulty"]),
            description=item["description"],
        )


# =============================================================================
# DynamoDBQuestionRepository
# =============================================================================


class DynamoDBQuestionRepository:
    """DynamoDB を使用した問題リポジトリ"""

    def create_question(self, question_data: dict) -> Question:
        """問題を作成して永続化する。

        バリデーションを実行し、不正データはリジェクトする。
        question_data に id が含まれない場合は UUID を自動生成する。

        Args:
            question_data: 問題データ辞書

        Returns:
            作成された Question ドメインオブジェクト

        Raises:
            ValueError: バリデーション失敗時
        """
        # ID が未指定の場合は UUID を生成
        if not question_data.get("id"):
            question_data = {**question_data, "id": str(uuid.uuid4())}

        # バリデーション実行
        result = validate_question(question_data)
        if not result.is_valid:
            raise ValueError(f"問題データが不正です: {result.errors}")

        # DynamoDB に保存
        item = {
            "id": question_data["id"],
            "course_id": question_data["course_id"],
            "text": question_data["text"],
            "choice_1": question_data["choice_1"],
            "choice_2": question_data["choice_2"],
            "choice_3": question_data["choice_3"],
            "choice_4": question_data["choice_4"],
            "correct_choice_index": question_data["correct_choice_index"],
            "ehime_trivia": question_data["ehime_trivia"],
            "aws_ai_explanation": question_data["aws_ai_explanation"],
            "difficulty": question_data["difficulty"],
            "exam_domain": question_data.get("exam_domain", ""),
        }
        put_item("questions", item)

        return self._to_domain(item)

    def get_question_by_id(self, question_id: str) -> Optional[Question]:
        """ID を指定して問題を取得する。"""
        item = get_item("questions", {"id": question_id})
        if item is None:
            return None
        return self._to_domain(item)

    def get_questions_by_course(self, course_id: str) -> list[Question]:
        """コース ID を指定して問題一覧を取得する。"""
        items = query_by_index(
            "questions",
            "course_id-index",
            Key("course_id").eq(course_id),
        )
        return [self._to_domain(item) for item in items]

    def get_questions_by_domain(self, domain: str) -> list[Question]:
        """試験ドメインを指定して問題一覧を取得する。"""
        table = get_table("questions")
        response = table.scan(
            FilterExpression=Attr("exam_domain").eq(domain)
        )
        items = response.get("Items", [])

        # ページネーション対応
        while "LastEvaluatedKey" in response:
            response = table.scan(
                FilterExpression=Attr("exam_domain").eq(domain),
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(response.get("Items", []))

        return [self._to_domain(item) for item in items]

    @staticmethod
    def _to_domain(item: dict) -> Question:
        """DynamoDB アイテムをドメイン Question に変換する"""
        return Question(
            id=item["id"],
            course_id=item["course_id"],
            text=item["text"],
            choice_1=item["choice_1"],
            choice_2=item["choice_2"],
            choice_3=item["choice_3"],
            choice_4=item["choice_4"],
            correct_choice_index=int(item["correct_choice_index"]),
            ehime_trivia=item["ehime_trivia"],
            aws_ai_explanation=item["aws_ai_explanation"],
            difficulty=Difficulty(item["difficulty"]),
            exam_domain=item["exam_domain"],
        )


# =============================================================================
# DynamoDBUserRecordRepository
# =============================================================================


class DynamoDBUserRecordRepository:
    """DynamoDB を使用したユーザー回答記録リポジトリ"""

    def save_answer_record(self, record: AnswerRecord) -> AnswerRecord:
        """回答記録を保存する。

        Args:
            record: 保存する回答記録（ドメインモデル）

        Returns:
            保存された回答記録（ドメインモデル）
        """
        item = {
            "id": record.id,
            "user_id": record.user_id,
            "question_id": record.question_id,
            "course_id": record.course_id,
            "selected_choice_index": record.selected_choice_index,
            "is_correct": record.is_correct,
            "answered_at": record.answered_at.isoformat(),
        }
        put_item("answer_records", item)
        return record

    def get_records_by_user(self, user_id: str) -> list[AnswerRecord]:
        """ユーザーの全回答記録を取得する。"""
        items = query_by_index(
            "answer_records",
            "user_id-index",
            Key("user_id").eq(user_id),
        )
        return [self._to_domain(item) for item in items]

    def get_records_by_user_and_course(
        self, user_id: str, course_id: str
    ) -> list[AnswerRecord]:
        """ユーザー＋コース別の回答記録を取得する。"""
        items = query_by_index(
            "answer_records",
            "user_course-index",
            Key("user_id").eq(user_id) & Key("course_id").eq(course_id),
        )
        return [self._to_domain(item) for item in items]

    def get_accuracy_by_course(self, user_id: str, course_id: str) -> float:
        """コース別正答率を返す。"""
        records = self.get_records_by_user_and_course(user_id, course_id)
        total_count = len(records)
        correct_count = sum(1 for r in records if r.is_correct)
        return calculate_accuracy_rate(correct_count, total_count)

    def get_cumulative_accuracy(self, user_id: str) -> float:
        """全体正答率を返す。"""
        records = self.get_records_by_user(user_id)
        total_count = len(records)
        correct_count = sum(1 for r in records if r.is_correct)
        return calculate_accuracy_rate(correct_count, total_count)

    def get_user_xp(self, user_id: str) -> dict:
        """ユーザーのXPとレベルを取得する。

        Returns:
            {"total_xp": int, "level": int}
        """
        item = get_item("users", {"id": user_id})
        if item is None:
            return {"total_xp": 0, "level": 1}

        total_xp = item.get("total_xp")
        level = item.get("level")

        # null または不正データ時のフォールバック
        if total_xp is None:
            total_xp = 0
        else:
            total_xp = int(total_xp)
            if total_xp < 0:
                total_xp = 0

        if level is None:
            level = 1
        else:
            level = int(level)
            if level < 1:
                level = 1

        return {"total_xp": total_xp, "level": level}

    def update_user_xp_and_level(
        self, user_id: str, total_xp: int, level: int
    ) -> None:
        """ユーザーのXPとレベルを永続化する。

        Args:
            user_id: ユーザーID
            total_xp: 新しい累計XP（0以上）
            level: 新しいレベル（1以上）

        Raises:
            ValueError: total_xp が負、または level が1未満の場合
        """
        if total_xp < 0:
            raise ValueError(f"total_xp must be non-negative, got {total_xp}")
        if level < 1:
            raise ValueError(f"level must be at least 1, got {level}")

        table = get_table("users")
        table.update_item(
            Key={"id": user_id},
            UpdateExpression="SET total_xp = :xp, #lvl = :lvl",
            ExpressionAttributeNames={"#lvl": "level"},
            ExpressionAttributeValues={":xp": total_xp, ":lvl": level},
        )

    @staticmethod
    def _to_domain(item: dict) -> AnswerRecord:
        """DynamoDB アイテムをドメイン AnswerRecord に変換する"""
        answered_at = item.get("answered_at")
        if isinstance(answered_at, str):
            answered_at = datetime.fromisoformat(answered_at)
        elif answered_at is None:
            answered_at = datetime.now()

        return AnswerRecord(
            id=item["id"],
            user_id=item["user_id"],
            question_id=item["question_id"],
            course_id=item["course_id"],
            selected_choice_index=int(item["selected_choice_index"]),
            is_correct=item["is_correct"],
            answered_at=answered_at,
        )


# =============================================================================
# DynamoDBGlossaryRepository
# =============================================================================


class DynamoDBGlossaryRepository:
    """DynamoDB を使用した用語集リポジトリ"""

    def get_all_grouped_by_category(self) -> dict[str, list[dict]]:
        """全用語をカテゴリ別にグルーピングして返す。"""
        items = scan_table("glossary_terms")

        # sort_order でソート
        items.sort(key=lambda x: (x.get("category", ""), int(x.get("sort_order", 0))))

        result: dict[str, list[dict]] = {}
        for item in items:
            category = item.get("category", "")
            result.setdefault(category, []).append(
                {"term": item["term"], "description": item["description"]}
            )
        return result
