"""
愛媛探索AIクイズ - Results Service

結果画面と成長可視化に必要なデータを集約するサービスクラス。
ダッシュボードデータ、レーダーチャートデータ、探索率、学習履歴を提供する。
"""

from __future__ import annotations

from app.data.course_repository import CourseRepository
from app.data.question_repository import QuestionRepository
from app.data.user_record_repository import UserRecordRepository
from app.domain.models import (
    AttemptRecord,
    DashboardData,
    ExamType,
    ExplorationRate,
    Grade,
    RadarChartData,
    Region,
    SessionStatus,
)
from app.domain.scoring import (
    calculate_accuracy_rate,
    calculate_domain_accuracy,
    calculate_grade,
)


# AWS認定試験のドメイン定義
CLOUD_PRACTITIONER_DOMAINS = [
    "Cloud Concepts",
    "Security and Compliance",
    "Cloud Technology and Services",
    "Billing Pricing and Support",
]

AI_PRACTITIONER_DOMAINS = [
    "AI and ML Fundamentals",
    "Generative AI",
    "Responsible AI",
]


class ResultsService:
    """結果画面と成長可視化のためのサービスクラス。

    リポジトリ群を利用してダッシュボードに必要な集約データを提供する。
    """

    def __init__(
        self,
        user_record_repository: UserRecordRepository,
        course_repository: CourseRepository,
        question_repository: QuestionRepository,
    ) -> None:
        """
        Args:
            user_record_repository: 回答記録リポジトリ
            course_repository: コースリポジトリ
            question_repository: 問題リポジトリ
        """
        self._user_record_repo = user_record_repository
        self._course_repo = course_repository
        self._question_repo = question_repository

    def get_dashboard_data(self, user_id: str) -> DashboardData:
        """ダッシュボードに必要な全データを集約して返す。

        スコア、グレード、レーダーチャートデータ、探索率、学習履歴を含む。
        学習履歴がない場合は has_history=False を設定する。

        Args:
            user_id: ユーザーID

        Returns:
            DashboardData: ダッシュボード集約データ
        """
        # 全体正答率を取得
        cumulative_accuracy = self._user_record_repo.get_cumulative_accuracy(user_id)

        # グレード判定
        grade = calculate_grade(cumulative_accuracy)

        # レーダーチャートデータ（デフォルトは Cloud Practitioner）
        radar_chart = self.get_radar_chart_data(user_id, ExamType.CLOUD_PRACTITIONER)

        # 探索率
        exploration_rate = self.get_exploration_rate(user_id)

        # 学習履歴
        attempt_history = self.get_attempt_history(user_id)

        # 学習履歴の有無判定
        has_history = len(attempt_history) > 0

        return DashboardData(
            cumulative_accuracy=cumulative_accuracy,
            grade=grade,
            radar_chart=radar_chart,
            exploration_rate=exploration_rate,
            attempt_history=attempt_history,
            has_history=has_history,
        )

    def get_radar_chart_data(self, user_id: str, exam_type: ExamType) -> RadarChartData:
        """レーダーチャート用のドメイン別正答率を計算する。

        指定された試験タイプのドメインに対応する問題の正答率を計算する。
        回答がないドメインは 0.0% として返す。

        Args:
            user_id: ユーザーID
            exam_type: 試験タイプ（Cloud Practitioner / AI Practitioner）

        Returns:
            RadarChartData: ドメイン別正答率データ
        """
        # ユーザーの全回答記録を取得
        answer_records = self._user_record_repo.get_records_by_user(user_id)

        if not answer_records:
            # 回答なしの場合、全ドメイン 0.0% で返す
            domains = self._get_domains_for_exam_type(exam_type)
            return RadarChartData(domain_accuracy={domain: 0.0 for domain in domains})

        # 問題IDからドメインへのマッピングを構築
        question_domains = self._build_question_domain_map(answer_records)

        # ドメイン別正答率を計算
        domain_accuracy = calculate_domain_accuracy(answer_records, question_domains)

        # 指定試験タイプのドメインのみ抽出し、未回答ドメインは0.0%
        target_domains = self._get_domains_for_exam_type(exam_type)
        filtered_accuracy: dict[str, float] = {}
        for domain in target_domains:
            filtered_accuracy[domain] = domain_accuracy.get(domain, 0.0)

        return RadarChartData(domain_accuracy=filtered_accuracy)

    def get_exploration_rate(self, user_id: str) -> ExplorationRate:
        """愛媛探索率を計算する。

        完了コース数/全コース数のパーセンテージと、
        少なくとも1コース完了した難易度の数を返す。

        Args:
            user_id: ユーザーID

        Returns:
            ExplorationRate: 探索率データ
        """
        # 全コースを取得
        all_courses = self._course_repo.get_all_courses()
        total_courses = len(all_courses)

        if total_courses == 0:
            return ExplorationRate(
                completed_courses=0,
                total_courses=0,
                exploration_percentage=0.0,
                completed_region_count=0,
            )

        # ユーザーの回答記録からコース別に回答の有無を確認
        answer_records = self._user_record_repo.get_records_by_user(user_id)

        # 回答があるコースIDを収集（=完了とみなす）
        completed_course_ids: set[str] = set()
        for record in answer_records:
            completed_course_ids.add(record.course_id)

        # 実際に存在するコースのみカウント
        valid_completed_ids = completed_course_ids.intersection(
            {course.id for course in all_courses}
        )
        completed_courses = len(valid_completed_ids)

        # 探索率計算
        exploration_percentage = calculate_accuracy_rate(completed_courses, total_courses)

        # 完了した地域数を計算
        completed_regions: set[Region] = set()
        course_map = {course.id: course for course in all_courses}
        for course_id in valid_completed_ids:
            course = course_map.get(course_id)
            if course:
                completed_regions.add(course.region)

        return ExplorationRate(
            completed_courses=completed_courses,
            total_courses=total_courses,
            exploration_percentage=exploration_percentage,
            completed_region_count=len(completed_regions),
        )

    def get_attempt_history(self, user_id: str) -> list[AttemptRecord]:
        """ユーザーの試験・クイズ試行履歴を時系列順で返す。

        各コースでの回答をグルーピングし、コース別の正答率とグレードを
        時系列順（古い順）で返す。

        Args:
            user_id: ユーザーID

        Returns:
            時系列順（昇順）の AttemptRecord リスト
        """
        # ユーザーの全回答記録を取得
        answer_records = self._user_record_repo.get_records_by_user(user_id)

        if not answer_records:
            return []

        # コース別に回答をグルーピング
        course_records: dict[str, list] = {}
        for record in answer_records:
            if record.course_id not in course_records:
                course_records[record.course_id] = []
            course_records[record.course_id].append(record)

        # 全コース情報を取得してマッピング
        all_courses = self._course_repo.get_all_courses()
        course_name_map = {course.id: course.name for course in all_courses}

        # コース別の AttemptRecord を作成
        attempts: list[AttemptRecord] = []
        for course_id, records in course_records.items():
            # コース名を取得（見つからない場合はIDを使用）
            course_name = course_name_map.get(course_id, course_id)

            # 正答率を計算
            total = len(records)
            correct = sum(1 for r in records if r.is_correct)
            accuracy_rate = calculate_accuracy_rate(correct, total)

            # グレードを判定
            grade = calculate_grade(accuracy_rate)

            # 最終回答日時をセッション完了日時として使用
            latest_answer = max(records, key=lambda r: r.answered_at)

            attempts.append(
                AttemptRecord(
                    session_id=course_id,  # コースIDをセッションIDとして使用
                    course_name=course_name,
                    accuracy_rate=accuracy_rate,
                    grade=grade,
                    completed_at=latest_answer.answered_at,
                )
            )

        # 時系列順（昇順）でソート
        attempts.sort(key=lambda a: a.completed_at)

        return attempts

    def _build_question_domain_map(self, answer_records: list) -> dict[str, str]:
        """回答記録に含まれる問題IDからドメインへのマッピングを構築する。

        Args:
            answer_records: 回答記録リスト

        Returns:
            {question_id: exam_domain} のマッピング辞書
        """
        question_ids = {record.question_id for record in answer_records}
        question_domains: dict[str, str] = {}

        for qid in question_ids:
            question = self._question_repo.get_question_by_id(qid)
            if question and question.exam_domain:
                question_domains[qid] = question.exam_domain

        return question_domains

    @staticmethod
    def _get_domains_for_exam_type(exam_type: ExamType) -> list[str]:
        """試験タイプに応じたドメインリストを返す。

        Args:
            exam_type: 試験タイプ

        Returns:
            ドメイン名のリスト
        """
        if exam_type == ExamType.CLOUD_PRACTITIONER:
            return CLOUD_PRACTITIONER_DOMAINS
        elif exam_type == ExamType.AI_PRACTITIONER:
            return AI_PRACTITIONER_DOMAINS
        else:
            return CLOUD_PRACTITIONER_DOMAINS
