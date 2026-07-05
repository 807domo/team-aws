"""
愛媛探索AIクイズ - Quiz Service

クイズの出題フロー全体を管理するコアサービス。
コース選択、セッション管理、回答判定、コース完了を統括する。
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.data.repository_factory import (
    get_course_repository,
    get_question_repository,
    get_session_repository,
    get_user_record_repository,
)
from app.domain.models import (
    AnswerRecord,
    AnswerResult,
    Course,
    CourseInfo,
    CourseSummary,
    Question,
    QuizSession,
    Region,
    SessionStatus,
)
from app.domain.scoring import calculate_accuracy_rate, calculate_grade
from app.domain.xp_calculator import add_xp, calculate_xp_award
from app.domain.level_calculator import calculate_level

logger = logging.getLogger(__name__)


class QuizService:
    """クイズ出題フロー全体を管理するコアサービス。

    コース選択、セッション管理、回答の正誤判定、コース完了処理を提供する。
    リポジトリ経由でデータアクセスし、scoring モジュールで採点ロジックを呼び出す。
    """

    def __init__(self, db_session: Session) -> None:
        """
        Args:
            db_session: SQLAlchemy データベースセッション
        """
        self._db = db_session
        self._course_repo = get_course_repository(db_session)
        self._question_repo = get_question_repository(db_session)
        self._user_record_repo = get_user_record_repository(db_session)
        self._session_repo = get_session_repository(db_session)

    # =========================================================================
    # コース一覧取得
    # =========================================================================

    def get_courses(
        self, region: Optional[Region] = None
    ) -> dict[Region, list[CourseInfo]]:
        """地域別コース一覧を取得する。

        各地域にコースがグルーピングされた辞書を返す。
        地域にコースがない場合は空リストとなり、呼び出し側で「準備中」表示に利用する。

        Args:
            region: 特定の地域を指定する場合。None の場合は全地域を返す。

        Returns:
            地域をキー、CourseInfo リストを値とする辞書。
            全地域（中予・南予・東予）が必ずキーとして含まれる。
        """
        if region is not None:
            courses = self._course_repo.get_courses_by_region(region)
            # 指定地域のみ返すが、全地域キーを含める
            grouped: dict[Region, list[CourseInfo]] = {r: [] for r in Region}
            grouped[region] = [self._to_course_info(c) for c in courses]
            return grouped

        # 全地域のコースを取得
        all_grouped = self._course_repo.get_courses_grouped_by_region()
        result: dict[Region, list[CourseInfo]] = {}
        for r in Region:
            courses_in_region = all_grouped.get(r, [])
            result[r] = [self._to_course_info(c) for c in courses_in_region]
        return result

    def is_region_available(self, region: Region) -> bool:
        """指定地域にコースが存在するか確認する。

        Args:
            region: 確認対象の地域

        Returns:
            True ならコースあり、False なら「準備中」状態
        """
        courses = self._course_repo.get_courses_by_region(region)
        return len(courses) > 0

    # =========================================================================
    # コース開始
    # =========================================================================

    def start_course(self, user_id: str, course_id: str) -> tuple[QuizSession, list[Question]]:
        """コースを開始または再開し、クイズセッションと問題リストを返す。

        同じコースに中断（SUSPENDED）または進行中（IN_PROGRESS）のセッションがある場合は
        そのセッションを再開する。ない場合は新しいセッションを作成する。
        他のコースの未完了セッションは中断扱いにする。

        Args:
            user_id: ユーザーID
            course_id: 開始するコースID

        Returns:
            (QuizSession, 問題リスト) のタプル

        Raises:
            ValueError: 指定コースが存在しない場合
        """
        # コースの存在確認
        course = self._course_repo.get_course_by_id(course_id)
        if course is None:
            raise ValueError(f"コースが見つかりません: {course_id}")

        # 他のコースの未完了セッションを中断扱いにする
        self._suspend_other_sessions(user_id, course_id)

        # 同じコースで再開可能なセッションを探す
        resumable_sessions = self._session_repo.get_by_user_course_status(
            user_id, course_id, [SessionStatus.IN_PROGRESS, SessionStatus.SUSPENDED]
        )
        resumable_session = resumable_sessions[0] if resumable_sessions else None

        if resumable_session:
            # セッションを再開（IN_PROGRESSに戻す）
            self._session_repo.update_status(resumable_session.id, SessionStatus.IN_PROGRESS)

            quiz_session = QuizSession(
                id=resumable_session.id,
                user_id=resumable_session.user_id,
                course_id=resumable_session.course_id,
                started_at=resumable_session.started_at,
                completed_at=None,
                status=SessionStatus.IN_PROGRESS,
            )
        else:
            # 新しいセッションを作成
            session_id = str(uuid.uuid4())
            now = datetime.now()

            quiz_session = QuizSession(
                id=session_id,
                user_id=user_id,
                course_id=course_id,
                started_at=now,
                completed_at=None,
                status=SessionStatus.IN_PROGRESS,
            )
            self._session_repo.create(quiz_session)

        # コースの問題一覧を取得
        questions = self._question_repo.get_questions_by_course(course_id)

        return quiz_session, questions

    def get_answered_count(self, session_id: str) -> int:
        """セッション内の回答済み問題数を返す。

        Args:
            session_id: クイズセッションID

        Returns:
            回答済み問題数
        """
        session = self._session_repo.get_by_id(session_id)
        if session is None:
            return 0

        records = self._user_record_repo.get_records_by_user_and_course(
            session.user_id, session.course_id
        )

        # このセッション開始後の回答のみカウント
        session_started_at = session.started_at
        session_records = [
            r for r in records if r.answered_at >= session_started_at
        ]
        return len(session_records)

    # =========================================================================
    # 回答送信・正誤判定
    # =========================================================================

    def submit_answer(
        self, session_id: str, question_id: str, choice_index: int
    ) -> AnswerResult:
        """回答を送信し、正誤判定を行う。

        正誤判定後に AnswerRecord を保存し、コース別正答率を再計算する。

        Args:
            session_id: クイズセッションID
            question_id: 問題ID
            choice_index: 選択した選択肢のインデックス (0-3)

        Returns:
            AnswerResult（正誤フィードバック）

        Raises:
            ValueError: セッションまたは問題が見つからない場合、
                       セッションが進行中でない場合
        """
        # セッション取得と検証
        session = self._session_repo.get_by_id(session_id)
        if session is None:
            raise ValueError(f"セッションが見つかりません: {session_id}")

        if session.status != SessionStatus.IN_PROGRESS:
            raise ValueError(f"セッションは既に終了しています: {session_id}")

        # 問題取得
        question = self._question_repo.get_question_by_id(question_id)
        if question is None:
            raise ValueError(f"問題が見つかりません: {question_id}")

        # 正誤判定
        is_correct = choice_index == question.correct_choice_index

        # AnswerRecord を保存
        record = AnswerRecord(
            id=str(uuid.uuid4()),
            user_id=session.user_id,
            question_id=question_id,
            course_id=session.course_id,
            selected_choice_index=choice_index,
            is_correct=is_correct,
            answered_at=datetime.now(),
        )
        self._user_record_repo.save_answer_record(record)

        return AnswerResult(
            question_id=question_id,
            selected_choice_index=choice_index,
            correct_choice_index=question.correct_choice_index,
            is_correct=is_correct,
        )

    # =========================================================================
    # コース完了
    # =========================================================================

    def complete_course(self, session_id: str) -> CourseSummary:
        """コースを完了し、結果サマリーを返す。

        セッションのステータスを COMPLETED に更新し、正解数/総問題数を集計する。

        Args:
            session_id: クイズセッションID

        Returns:
            CourseSummary（コース名、正解数、総問題数、正答率、グレード）

        Raises:
            ValueError: セッションが見つからない場合、
                       セッションが進行中でない場合
        """
        # セッション取得
        session = self._session_repo.get_by_id(session_id)
        if session is None:
            raise ValueError(f"セッションが見つかりません: {session_id}")

        if session.status != SessionStatus.IN_PROGRESS:
            raise ValueError(f"セッションは既に終了しています: {session_id}")

        # セッション完了に更新
        self._session_repo.update_status(session_id, SessionStatus.COMPLETED, completed_at=datetime.now())

        # コース名取得
        course = self._course_repo.get_course_by_id(session.course_id)
        course_name = course.name if course else "不明なコース"

        # セッション中の回答記録を取得（ユーザー＋コース別）
        records = self._user_record_repo.get_records_by_user_and_course(
            session.user_id, session.course_id
        )

        # セッション開始後の回答のみをフィルタ
        session_started_at = session.started_at
        session_records = [
            r for r in records if r.answered_at >= session_started_at
        ]

        # 正解数・総問題数を集計
        total_count = len(session_records)
        correct_count = sum(1 for r in session_records if r.is_correct)

        # 正答率とグレード計算
        accuracy_rate = calculate_accuracy_rate(correct_count, total_count)
        grade = calculate_grade(accuracy_rate)

        # XP付与ロジック
        self._award_xp(session.user_id, correct_count, total_count)

        return CourseSummary(
            course_id=session.course_id,
            course_name=course_name,
            correct_count=correct_count,
            total_count=total_count,
            accuracy_rate=accuracy_rate,
            grade=grade,
        )

    def abort_course(self, session_id: str) -> CourseSummary:
        """コースを途中中断し、それまでの回答を元にサマリーを返す。

        セッションのステータスを SUSPENDED に更新する。
        再開可能な状態を維持する。

        Args:
            session_id: クイズセッションID

        Returns:
            CourseSummary（コース名、正解数、回答済み問題数、正答率、グレード）

        Raises:
            ValueError: セッションが見つからない場合、
                       セッションが進行中でない場合
        """
        # セッション取得
        session = self._session_repo.get_by_id(session_id)
        if session is None:
            raise ValueError(f"セッションが見つかりません: {session_id}")

        if session.status != SessionStatus.IN_PROGRESS:
            raise ValueError(f"セッションは既に終了しています: {session_id}")

        # セッションを中断状態に更新（再開可能）
        self._session_repo.update_status(session_id, SessionStatus.SUSPENDED)

        # コース名取得
        course = self._course_repo.get_course_by_id(session.course_id)
        course_name = course.name if course else "不明なコース"

        # セッション中の回答記録を取得
        records = self._user_record_repo.get_records_by_user_and_course(
            session.user_id, session.course_id
        )

        # セッション開始後の回答のみをフィルタ
        session_started_at = session.started_at
        session_records = [
            r for r in records if r.answered_at >= session_started_at
        ]

        # 正解数・回答済み問題数を集計
        total_count = len(session_records)
        correct_count = sum(1 for r in session_records if r.is_correct)

        # 正答率とグレード計算
        accuracy_rate = calculate_accuracy_rate(correct_count, total_count)
        grade = calculate_grade(accuracy_rate)

        return CourseSummary(
            course_id=session.course_id,
            course_name=course_name,
            correct_count=correct_count,
            total_count=total_count,
            accuracy_rate=accuracy_rate,
            grade=grade,
        )

    def complete_in_progress_sessions(self, user_id: str) -> None:
        """ユーザーの未完了セッションをすべて中断状態にする。

        Args:
            user_id: ユーザーID
        """
        in_progress_sessions = self._session_repo.get_by_user_and_status(user_id, SessionStatus.IN_PROGRESS)
        for session in in_progress_sessions:
            self._session_repo.update_status(session.id, SessionStatus.SUSPENDED)

    def _suspend_other_sessions(self, user_id: str, current_course_id: str) -> None:
        """指定コース以外の未完了セッションを中断状態にする。

        別のコースを開始する際に、他コースのIN_PROGRESSセッションを中断する。

        Args:
            user_id: ユーザーID
            current_course_id: 現在開始するコースID（これは中断しない）
        """
        other_sessions = self._session_repo.get_in_progress_by_user_except_course(user_id, current_course_id)
        for session in other_sessions:
            self._session_repo.update_status(session.id, SessionStatus.SUSPENDED)

    # =========================================================================
    # セッション取得
    # =========================================================================

    def get_session(self, session_id: str) -> Optional[QuizSession]:
        """セッションIDからQuizSessionを取得する。

        Args:
            session_id: クイズセッションID

        Returns:
            QuizSession ドメインオブジェクト。存在しない場合は None。
        """
        return self._session_repo.get_by_id(session_id)

    # =========================================================================
    # ヘルパーメソッド
    # =========================================================================

    def _award_xp(self, user_id: str, correct_count: int, total_count: int) -> None:
        """コース完了時にXPを付与し、レベルを更新する。

        XP算出→加算→レベル計算→永続化の一連のフローを実行する。
        永続化失敗時はエラーをログに記録するが、例外は送出しない。

        Args:
            user_id: ユーザーID
            correct_count: 正解数
            total_count: 総問題数
        """
        try:
            # 1. XP獲得量を算出
            xp_award = calculate_xp_award(correct_count, total_count)

            # 2. 現在のXPを取得
            user_xp_data = self._user_record_repo.get_user_xp(user_id)
            current_xp = user_xp_data["total_xp"]

            # 3. 累計XPを計算
            new_total_xp = add_xp(current_xp, xp_award)

            # 4. 新レベルを算出
            new_level = calculate_level(new_total_xp)

            # 5. 永続化
            self._user_record_repo.update_user_xp_and_level(
                user_id, new_total_xp, new_level
            )
        except Exception as e:
            # XP永続化失敗時はエラーメッセージを記録するがアプリはクラッシュさせない
            logger.error(
                "経験値の保存に失敗しました (user_id=%s): %s", user_id, str(e)
            )

    def _to_course_info(self, course: Course) -> CourseInfo:
        """Course ドメインモデルを CourseInfo レスポンスモデルに変換する。"""
        questions = self._question_repo.get_questions_by_course(course.id)
        return CourseInfo(
            id=course.id,
            name=course.name,
            region=course.region,
            difficulty=course.difficulty,
            description=course.description,
            question_count=len(questions),
        )
