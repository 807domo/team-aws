"""
愛媛探索AIクイズ - Mock Exam Engine（模擬試験エンジン）

AWS認定資格模擬試験モードを管理するドメインサービス。
タイマー付き65問・90分の試験セッションを提供し、
問題間ナビゲーション、回答記録（即時フィードバックなし）、
自動終了処理を実装する。

Requirements: 5.1, 5.2, 5.3, 5.4, 5.6
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from app.domain.models import (
    ExamType,
    Grade,
    MockExamSession,
    Question,
    SessionStatus,
)
from app.domain.scoring import calculate_accuracy_rate, calculate_grade


# =============================================================================
# Mock Exam 固有のデータモデル
# =============================================================================

MOCK_EXAM_QUESTION_COUNT = 65
MOCK_EXAM_DURATION_MINUTES = 90


@dataclass
class MockExamAnswer:
    """模擬試験の回答記録"""

    question_id: str
    choice_index: int
    answered_at: datetime = field(default_factory=datetime.now)


@dataclass
class QuestionView:
    """問題表示用データ（ナビゲーション結果）"""

    question: Question
    question_index: int
    total_questions: int
    is_answered: bool
    selected_choice_index: Optional[int] = None


@dataclass
class MockExamResult:
    """模擬試験結果"""

    session_id: str
    exam_type: ExamType
    total_questions: int
    answered_count: int
    correct_count: int
    score_percentage: float
    grade: Grade
    unanswered_count: int
    duration_minutes: float
    completed_at: datetime


# =============================================================================
# Mock Exam Engine
# =============================================================================


class MockExamEngine:
    """模擬試験エンジン

    タイマー付きの模擬試験セッションを管理し、
    問題間ナビゲーション、回答記録、自動終了処理を提供する。
    """

    def __init__(self, question_repository=None) -> None:
        """
        Args:
            question_repository: QuestionRepository インスタンス（問題取得用）
        """
        self._question_repository = question_repository
        # インメモリセッション管理（本番ではDB永続化に移行可能）
        self._sessions: dict[str, MockExamSession] = {}
        self._session_questions: dict[str, list[Question]] = {}
        self._session_answers: dict[str, dict[str, MockExamAnswer]] = {}

    def start_exam(self, user_id: str, exam_type: ExamType) -> MockExamSession:
        """模擬試験を開始する（65問, 90分）。

        セッションを作成し、タイマーを開始する。
        question_repository が設定されている場合は、対応する exam_type の
        問題を取得する。

        Args:
            user_id: ユーザーID
            exam_type: 試験タイプ（Cloud Practitioner / AI Practitioner）

        Returns:
            作成された MockExamSession

        Raises:
            ValueError: 問題が不足している場合
        """
        now = datetime.now()
        session_id = str(uuid.uuid4())
        expires_at = now + timedelta(minutes=MOCK_EXAM_DURATION_MINUTES)

        session = MockExamSession(
            id=session_id,
            user_id=user_id,
            exam_type=exam_type,
            started_at=now,
            expires_at=expires_at,
            status=SessionStatus.IN_PROGRESS,
        )

        # 問題を取得（リポジトリが設定されている場合）
        questions: list[Question] = []
        if self._question_repository is not None:
            questions = self._get_exam_questions(exam_type)

        self._sessions[session_id] = session
        self._session_questions[session_id] = questions
        self._session_answers[session_id] = {}

        return session

    def submit_answer(
        self, session_id: str, question_id: str, choice_index: int
    ) -> None:
        """模擬試験の回答を記録する（即時フィードバックなし）。

        本番の試験と同じく、回答提出時に正誤は通知しない。
        試験終了時にまとめて採点する。

        Args:
            session_id: セッションID
            question_id: 問題ID
            choice_index: 選択した選択肢インデックス（0-3）

        Raises:
            ValueError: セッションが見つからない/有効でない場合
            ValueError: choice_index が範囲外の場合
        """
        session = self._get_active_session(session_id)

        # タイマー期限切れチェック
        if self._is_expired(session):
            self._auto_finish(session_id)
            raise ValueError("試験時間が終了しました。自動採点されます。")

        if choice_index < 0 or choice_index > 3:
            raise ValueError(
                f"choice_index は 0〜3 の範囲で指定してください: {choice_index}"
            )

        # 回答を記録（同じ問題への再回答は上書き）
        self._session_answers[session_id][question_id] = MockExamAnswer(
            question_id=question_id,
            choice_index=choice_index,
            answered_at=datetime.now(),
        )

    def navigate_to_question(
        self, session_id: str, question_index: int
    ) -> QuestionView:
        """指定の問題に移動する。

        模擬試験では問題間を自由にナビゲートでき、
        未回答の問題をスキップすることも可能。

        Args:
            session_id: セッションID
            question_index: 問題インデックス（0-based）

        Returns:
            QuestionView（問題データ + 回答状態）

        Raises:
            ValueError: セッション無効、インデックス範囲外の場合
        """
        session = self._get_active_session(session_id)

        # タイマー期限切れチェック
        if self._is_expired(session):
            self._auto_finish(session_id)
            raise ValueError("試験時間が終了しました。自動採点されます。")

        questions = self._session_questions.get(session_id, [])
        total_questions = len(questions)

        if total_questions == 0:
            raise ValueError("このセッションには問題が登録されていません。")

        if question_index < 0 or question_index >= total_questions:
            raise ValueError(
                f"question_index は 0〜{total_questions - 1} の範囲で"
                f"指定してください: {question_index}"
            )

        question = questions[question_index]
        answers = self._session_answers.get(session_id, {})
        answer = answers.get(question.id)

        return QuestionView(
            question=question,
            question_index=question_index,
            total_questions=total_questions,
            is_answered=answer is not None,
            selected_choice_index=answer.choice_index if answer else None,
        )

    def get_remaining_time(self, session_id: str) -> timedelta:
        """残り時間を返す。

        max(0, expires_at - now) で計算する。
        期限切れの場合は timedelta(0) を返し、自動終了処理を実行する。

        Args:
            session_id: セッションID

        Returns:
            残り時間（timedelta）

        Raises:
            ValueError: セッションが見つからない場合
        """
        session = self._get_session(session_id)

        if session.status != SessionStatus.IN_PROGRESS:
            return timedelta(0)

        if session.expires_at is None:
            return timedelta(0)

        now = datetime.now()
        remaining = session.expires_at - now

        if remaining.total_seconds() <= 0:
            # 期限切れ：自動終了
            self._auto_finish(session_id)
            return timedelta(0)

        return remaining

    def finish_exam(self, session_id: str) -> MockExamResult:
        """試験を終了し、結果を返す。

        未回答の問題は不正解として扱い、スコアとグレードを計算する。

        Args:
            session_id: セッションID

        Returns:
            MockExamResult（スコア、グレード、各種統計）

        Raises:
            ValueError: セッションが見つからない場合
        """
        session = self._get_session(session_id)

        if session.status != SessionStatus.IN_PROGRESS:
            raise ValueError(
                f"このセッションは既に終了しています: {session.status.value}"
            )

        return self._calculate_result(session_id)

    # =========================================================================
    # ヘルパーメソッド (public utility)
    # =========================================================================

    def get_session(self, session_id: str) -> Optional[MockExamSession]:
        """セッション情報を取得する（外部参照用）。

        Args:
            session_id: セッションID

        Returns:
            MockExamSession or None
        """
        return self._sessions.get(session_id)

    def get_answer_status(self, session_id: str) -> dict[int, bool]:
        """各問題の回答状態を取得する（ナビゲーション表示用）。

        Args:
            session_id: セッションID

        Returns:
            {question_index: is_answered} の辞書
        """
        questions = self._session_questions.get(session_id, [])
        answers = self._session_answers.get(session_id, {})

        status: dict[int, bool] = {}
        for i, question in enumerate(questions):
            status[i] = question.id in answers

        return status

    # =========================================================================
    # プライベートメソッド
    # =========================================================================

    def _get_session(self, session_id: str) -> MockExamSession:
        """セッションを取得する（見つからない場合は例外）。"""
        session = self._sessions.get(session_id)
        if session is None:
            raise ValueError(f"セッションが見つかりません: {session_id}")
        return session

    def _get_active_session(self, session_id: str) -> MockExamSession:
        """アクティブ（進行中）のセッションを取得する。"""
        session = self._get_session(session_id)
        if session.status != SessionStatus.IN_PROGRESS:
            raise ValueError(
                f"このセッションは終了しています: {session.status.value}"
            )
        return session

    def _is_expired(self, session: MockExamSession) -> bool:
        """セッションが期限切れかどうかを判定する。"""
        if session.expires_at is None:
            return False
        return datetime.now() >= session.expires_at

    def _auto_finish(self, session_id: str) -> MockExamResult:
        """タイマー期限切れによる自動終了処理。

        セッションを EXPIRED 状態にし、結果を計算する。
        """
        session = self._sessions[session_id]
        if session.status != SessionStatus.IN_PROGRESS:
            # 既に終了済みの場合はスキップ
            return self._calculate_result_from_session(session_id, session)

        session.status = SessionStatus.EXPIRED
        session.completed_at = session.expires_at or datetime.now()
        return self._calculate_result_from_session(session_id, session)

    def _calculate_result(self, session_id: str) -> MockExamResult:
        """試験結果を計算し、セッションを完了状態にする。"""
        session = self._sessions[session_id]
        now = datetime.now()
        session.status = SessionStatus.COMPLETED
        session.completed_at = now
        return self._calculate_result_from_session(session_id, session)

    def _calculate_result_from_session(
        self, session_id: str, session: MockExamSession
    ) -> MockExamResult:
        """セッションから試験結果を計算する。

        未回答の問題は不正解として扱う。
        """
        questions = self._session_questions.get(session_id, [])
        answers = self._session_answers.get(session_id, {})

        total_questions = len(questions)
        answered_count = len(answers)
        unanswered_count = total_questions - answered_count

        # 正答数を計算（未回答は不正解）
        correct_count = 0
        for question in questions:
            answer = answers.get(question.id)
            if answer is not None and answer.choice_index == question.correct_choice_index:
                correct_count += 1

        # スコアとグレードを計算
        score_percentage = calculate_accuracy_rate(correct_count, total_questions)
        grade = calculate_grade(score_percentage)

        # 所要時間を計算
        completed_at = session.completed_at or datetime.now()
        duration = completed_at - session.started_at
        duration_minutes = round(duration.total_seconds() / 60, 1)

        return MockExamResult(
            session_id=session_id,
            exam_type=session.exam_type,
            total_questions=total_questions,
            answered_count=answered_count,
            correct_count=correct_count,
            score_percentage=score_percentage,
            grade=grade,
            unanswered_count=unanswered_count,
            duration_minutes=duration_minutes,
            completed_at=completed_at,
        )

    def _get_exam_questions(self, exam_type: ExamType) -> list[Question]:
        """試験タイプに応じた問題を取得する。

        exam_domain に基づいて問題をフィルタし、
        最大 MOCK_EXAM_QUESTION_COUNT 問を選択する。
        """
        if self._question_repository is None:
            return []

        # exam_type に対応するドメインを取得
        domains = self._get_domains_for_exam_type(exam_type)

        all_questions: list[Question] = []
        for domain in domains:
            domain_questions = self._question_repository.get_questions_by_domain(
                domain
            )
            all_questions.extend(domain_questions)

        # 最大65問に制限
        return all_questions[:MOCK_EXAM_QUESTION_COUNT]

    @staticmethod
    def _get_domains_for_exam_type(exam_type: ExamType) -> list[str]:
        """試験タイプに対応するドメイン名リストを返す。"""
        if exam_type == ExamType.CLOUD_PRACTITIONER:
            return [
                "Cloud Concepts",
                "Security and Compliance",
                "Cloud Technology and Services",
                "Billing Pricing and Support",
            ]
        elif exam_type == ExamType.AI_PRACTITIONER:
            return [
                "AI and ML Fundamentals",
                "Generative AI",
                "Responsible AI",
                "Fundamentals of AI and ML",
                "Fundamentals of Generative AI",
                "Applications of Foundation Models",
                "Guidelines for Responsible AI",
                "Security, Compliance, and Governance for AI Solutions",
            ]
        return []
