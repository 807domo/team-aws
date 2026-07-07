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
    delete_item,
    get_item,
    get_table,
    is_dynamodb_enabled,
    put_item,
    query_by_index,
    scan_table,
)
from app.domain.models import (
    AnswerRecord,
    Course,
    Difficulty,
    Question,
    QuizSession,
    Region,
    SessionStatus,
)
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
        courses = [self._to_domain(item) for item in items]
        return sorted(courses, key=lambda x: x.id)

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

        courses = [self._to_domain(item) for item in items]
        return sorted(courses, key=lambda x: x.id)

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

    def get_all_domains(self) -> list[str]:
        """全問題のexam_domainの重複なしリストを返す。"""
        items = scan_table("questions")
        domains = set()
        for item in items:
            domain = item.get("exam_domain", "")
            if domain:
                domains.add(domain)
        return sorted(domains)

    def get_questions_filtered(
        self, domains: list[str], difficulty: str = "all"
    ) -> list[Question]:
        """ドメインリストと難易度でフィルタリングした問題一覧を返す。

        Args:
            domains: 対象ドメインリスト
            difficulty: 難易度フィルタ ("all" で全件)

        Returns:
            条件に合致するQuestionリスト
        """
        items = scan_table("questions")
        filtered = []
        for item in items:
            if item.get("exam_domain", "") not in domains:
                continue
            if difficulty != "all" and item.get("difficulty", "") != difficulty:
                continue
            filtered.append(self._to_domain(item))
        return filtered

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


# =============================================================================
# DynamoDBUserRepository
# =============================================================================


class DynamoDBUserRepository:
    """DynamoDB を使用したユーザーリポジトリ"""

    def create(self, user_id: str, display_name: str, password_hash: str) -> None:
        """ユーザーを作成する。

        Args:
            user_id: ユーザーID
            display_name: 表示名
            password_hash: ハッシュ化済みパスワード
        """
        item = {
            "id": user_id,
            "display_name": display_name,
            "password_hash": password_hash,
            "created_at": datetime.now().isoformat(),
            "total_xp": 0,
            "level": 1,
        }
        put_item("users", item)

    def get_by_id(self, user_id: str) -> Optional[dict]:
        """IDを指定してユーザーを取得する。存在しない場合は None を返す。

        Args:
            user_id: ユーザーID

        Returns:
            ユーザー情報辞書 or None
        """
        item = get_item("users", {"id": user_id})
        if item is None:
            return None
        return self._to_dict(item)

    def get_by_display_name(self, display_name: str) -> Optional[dict]:
        """表示名を指定してユーザーを取得する。存在しない場合は None を返す。

        テーブルスキャン＋フィルタで検索する（ユーザー数少量のため許容）。

        Args:
            display_name: 表示名

        Returns:
            ユーザー情報辞書 or None
        """
        items = scan_table("users")
        for item in items:
            if item.get("display_name") == display_name:
                return self._to_dict(item)
        return None

    def get_gemini_api_key(self, user_id: str) -> Optional[str]:
        """ユーザーのGemini APIキーを取得する。

        Args:
            user_id: ユーザーID

        Returns:
            APIキー文字列 or None
        """
        item = get_item("users", {"id": user_id})
        if item is None:
            return None
        return item.get("gemini_api_key")

    def set_gemini_api_key(self, user_id: str, api_key: Optional[str]) -> None:
        """ユーザーのGemini APIキーを設定する。

        Args:
            user_id: ユーザーID
            api_key: APIキー文字列（Noneで削除）
        """
        table = get_table("users")
        if api_key:
            table.update_item(
                Key={"id": user_id},
                UpdateExpression="SET gemini_api_key = :key",
                ExpressionAttributeValues={":key": api_key},
            )
        else:
            table.update_item(
                Key={"id": user_id},
                UpdateExpression="REMOVE gemini_api_key",
            )

    @staticmethod
    def _to_dict(item: dict) -> dict:
        """DynamoDB アイテムを標準辞書形式に変換する。"""
        return {
            "id": item["id"],
            "display_name": item["display_name"],
            "password_hash": item["password_hash"],
            "created_at": item.get("created_at", ""),
            "total_xp": int(item.get("total_xp", 0)),
            "level": int(item.get("level", 1)),
            "gemini_api_key": item.get("gemini_api_key"),
        }


# =============================================================================
# DynamoDBBookmarkRepository
# =============================================================================


class DynamoDBBookmarkRepository:
    """DynamoDB を使用したブックマークリポジトリ"""

    def add(self, user_id: str, question_id: str) -> str:
        """ブックマークを追加する。

        UUIDを生成してブックマークを永続化する。

        Args:
            user_id: ユーザーID
            question_id: 問題ID

        Returns:
            生成されたブックマークID
        """
        bookmark_id = str(uuid.uuid4())
        item = {
            "id": bookmark_id,
            "user_id": user_id,
            "question_id": question_id,
            "created_at": datetime.now().isoformat(),
        }
        put_item("bookmarks", item)
        return bookmark_id

    def remove(self, user_id: str, question_id: str) -> bool:
        """ブックマークを削除する。

        GSI user_id-index でクエリし、question_id に一致するアイテムを削除する。

        Args:
            user_id: ユーザーID
            question_id: 問題ID

        Returns:
            削除できた場合True、対象が存在しなかった場合False
        """
        items = query_by_index(
            "bookmarks",
            "user_id-index",
            Key("user_id").eq(user_id),
        )
        target = next(
            (item for item in items if item.get("question_id") == question_id),
            None,
        )
        if target is None:
            return False
        delete_item("bookmarks", {"id": target["id"]})
        return True

    def toggle(self, user_id: str, question_id: str) -> bool:
        """ブックマークをトグルする。

        既にブックマークが存在する場合は削除し、存在しない場合は追加する。

        Args:
            user_id: ユーザーID
            question_id: 問題ID

        Returns:
            追加した場合True、削除した場合False
        """
        if self.exists(user_id, question_id):
            self.remove(user_id, question_id)
            return False
        else:
            self.add(user_id, question_id)
            return True

    def get_by_user(self, user_id: str) -> list[dict]:
        """ユーザーのブックマーク一覧を取得する。

        GSI user_id-index でクエリし、created_at 降順（新しい順）でソートして返す。

        Args:
            user_id: ユーザーID

        Returns:
            ブックマーク情報のリスト。各要素は {id, user_id, question_id, created_at} の辞書。
        """
        items = query_by_index(
            "bookmarks",
            "user_id-index",
            Key("user_id").eq(user_id),
        )
        # created_at 降順でソート
        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return [
            {
                "id": item["id"],
                "user_id": item["user_id"],
                "question_id": item["question_id"],
                "created_at": item.get("created_at", ""),
            }
            for item in items
        ]

    def exists(self, user_id: str, question_id: str) -> bool:
        """ブックマークが存在するか確認する。

        GSI user_id-index でクエリし、question_id に一致するアイテムがあるか確認する。

        Args:
            user_id: ユーザーID
            question_id: 問題ID

        Returns:
            存在する場合True、しない場合False
        """
        items = query_by_index(
            "bookmarks",
            "user_id-index",
            Key("user_id").eq(user_id),
        )
        return any(item.get("question_id") == question_id for item in items)


# =============================================================================
# DynamoDBSessionRepository
# =============================================================================


class DynamoDBSessionRepository:
    """DynamoDB を使用したクイズセッションリポジトリ"""

    def create(self, quiz_session: QuizSession) -> QuizSession:
        """新しいクイズセッションを作成する。

        Args:
            quiz_session: 作成するクイズセッションのドメインオブジェクト

        Returns:
            作成されたクイズセッションのドメインオブジェクト
        """
        item = {
            "id": quiz_session.id,
            "user_id": quiz_session.user_id,
            "course_id": quiz_session.course_id,
            "started_at": quiz_session.started_at.isoformat(),
            "completed_at": (
                quiz_session.completed_at.isoformat()
                if quiz_session.completed_at
                else None
            ),
            "status": quiz_session.status.value,
        }
        put_item("quiz_sessions", item)
        return quiz_session

    def get_by_id(self, session_id: str) -> Optional[QuizSession]:
        """セッションIDを指定してクイズセッションを取得する。

        Args:
            session_id: クイズセッションID

        Returns:
            該当するQuizSessionオブジェクト。存在しない場合はNone。
        """
        item = get_item("quiz_sessions", {"id": session_id})
        if item is None:
            return None
        return self._to_domain(item)

    def get_by_user_and_status(
        self, user_id: str, status: SessionStatus
    ) -> list[QuizSession]:
        """ユーザーIDとステータスを指定してセッション一覧を取得する。

        GSI `user_id-index` でuser_idをクエリし、statusでPythonフィルタする。

        Args:
            user_id: ユーザーID
            status: セッションステータス

        Returns:
            条件に合致するQuizSessionオブジェクトのリスト
        """
        items = query_by_index(
            "quiz_sessions",
            "user_id-index",
            Key("user_id").eq(user_id),
        )
        return [
            self._to_domain(item)
            for item in items
            if item.get("status") == status.value
        ]

    def get_by_user_course_status(
        self, user_id: str, course_id: str, statuses: list[SessionStatus]
    ) -> list[QuizSession]:
        """ユーザーID、コースID、ステータスリストを指定してセッション一覧を取得する。

        GSI `user_id-index` でuser_idをクエリし、course_idとstatusesでPythonフィルタする。

        Args:
            user_id: ユーザーID
            course_id: コースID
            statuses: 検索対象のセッションステータスリスト

        Returns:
            条件に合致するQuizSessionオブジェクトのリスト（started_at降順）
        """
        status_values = [s.value for s in statuses]
        items = query_by_index(
            "quiz_sessions",
            "user_id-index",
            Key("user_id").eq(user_id),
        )
        filtered = [
            self._to_domain(item)
            for item in items
            if item.get("course_id") == course_id
            and item.get("status") in status_values
        ]
        # started_at降順でソート（SQLAlchemy版と同じ動作）
        filtered.sort(key=lambda s: s.started_at, reverse=True)
        return filtered

    def update_status(
        self,
        session_id: str,
        status: SessionStatus,
        completed_at: Optional[datetime] = None,
    ) -> None:
        """セッションのステータスを更新する。

        Args:
            session_id: クイズセッションID
            status: 更新先のセッションステータス
            completed_at: 完了日時（COMPLETED時に設定）
        """
        table = get_table("quiz_sessions")
        update_expr = "SET #st = :status"
        expr_names = {"#st": "status"}
        expr_values: dict = {":status": status.value}

        if completed_at is not None:
            update_expr += ", completed_at = :completed_at"
            expr_values[":completed_at"] = completed_at.isoformat()

        table.update_item(
            Key={"id": session_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
        )

    def get_in_progress_by_user_except_course(
        self, user_id: str, exclude_course_id: str
    ) -> list[QuizSession]:
        """指定コース以外のユーザーのIN_PROGRESSセッションを取得する。

        GSI `user_id-index` でuser_idをクエリし、
        status==IN_PROGRESS かつ course_id != exclude_course_id でPythonフィルタする。

        Args:
            user_id: ユーザーID
            exclude_course_id: 除外するコースID

        Returns:
            条件に合致するQuizSessionオブジェクトのリスト
        """
        items = query_by_index(
            "quiz_sessions",
            "user_id-index",
            Key("user_id").eq(user_id),
        )
        return [
            self._to_domain(item)
            for item in items
            if item.get("status") == SessionStatus.IN_PROGRESS.value
            and item.get("course_id") != exclude_course_id
        ]

    @staticmethod
    def _to_domain(item: dict) -> QuizSession:
        """DynamoDB アイテムをドメイン QuizSession に変換する。"""
        started_at = item.get("started_at")
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)
        elif started_at is None:
            started_at = datetime.now()

        completed_at = item.get("completed_at")
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)
        else:
            completed_at = None

        return QuizSession(
            id=item["id"],
            user_id=item["user_id"],
            course_id=item["course_id"],
            started_at=started_at,
            completed_at=completed_at,
            status=SessionStatus(item["status"]),
        )
