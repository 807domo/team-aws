"""
Repository factory - returns SQLAlchemy or DynamoDB repositories based on environment.

USE_DYNAMODB=1 の場合は DynamoDB リポジトリを返し、
それ以外の場合は SQLAlchemy リポジトリを返す。
"""

import os
from typing import Optional

from sqlalchemy.orm import Session


def get_course_repository(session: Optional[Session] = None):
    """コースリポジトリを取得する。"""
    if os.environ.get("USE_DYNAMODB", "0") == "1":
        from app.data.dynamodb_repositories import DynamoDBCourseRepository

        return DynamoDBCourseRepository()
    else:
        from app.data.course_repository import CourseRepository

        return CourseRepository(session)


def get_question_repository(session: Optional[Session] = None):
    """問題リポジトリを取得する。"""
    if os.environ.get("USE_DYNAMODB", "0") == "1":
        from app.data.dynamodb_repositories import DynamoDBQuestionRepository

        return DynamoDBQuestionRepository()
    else:
        from app.data.question_repository import QuestionRepository

        return QuestionRepository(session)


def get_user_record_repository(session: Optional[Session] = None):
    """ユーザー回答記録リポジトリを取得する。"""
    if os.environ.get("USE_DYNAMODB", "0") == "1":
        from app.data.dynamodb_repositories import DynamoDBUserRecordRepository

        return DynamoDBUserRecordRepository()
    else:
        from app.data.user_record_repository import UserRecordRepository

        return UserRecordRepository(session)


def get_glossary_repository(session: Optional[Session] = None):
    """用語集リポジトリを取得する。"""
    if os.environ.get("USE_DYNAMODB", "0") == "1":
        from app.data.dynamodb_repositories import DynamoDBGlossaryRepository

        return DynamoDBGlossaryRepository()
    else:
        from app.data.glossary_repository import GlossaryRepository

        return GlossaryRepository(session)
