"""
愛媛探索AIクイズ - ドメインモデル定義

Enum定義とデータモデル（dataclass）を提供する。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


# =============================================================================
# Enum 定義
# =============================================================================


class Region(str, Enum):
    """難易度による区分（マップ上の地域に対応）"""

    NANYO = "初級"
    TOYO = "中級"
    CHUYO = "上級"


class Difficulty(str, Enum):
    """問題の難易度"""

    BASIC = "基礎"
    INTERMEDIATE = "中級"
    ADVANCED = "上級"


class ExamType(str, Enum):
    """AWS認定資格の試験タイプ"""

    CLOUD_PRACTITIONER = "AWS Certified Cloud Practitioner"
    AI_PRACTITIONER = "AWS AI Practitioner"


class Grade(str, Enum):
    """成績グレード（A: 90-100%, B: 80-89%, C: 70-79%, D: 60-69%, E: 0-59%）"""

    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


class SessionStatus(str, Enum):
    """セッションの状態"""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SUSPENDED = "suspended"
    EXPIRED = "expired"


# =============================================================================
# ドメインモデル（エンティティ）
# =============================================================================


@dataclass
class Course:
    """クイズコース"""

    id: str
    name: str
    region: Region
    difficulty: Difficulty
    description: str


@dataclass
class Question:
    """クイズ問題"""

    id: str
    course_id: str
    text: str
    choice_1: str
    choice_2: str
    choice_3: str
    choice_4: str
    correct_choice_index: int  # 0-3
    ehime_trivia: str
    aws_ai_explanation: str
    difficulty: Difficulty
    exam_domain: str


@dataclass
class User:
    """ユーザー"""

    id: str
    display_name: str
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AnswerRecord:
    """回答記録"""

    id: str
    user_id: str
    question_id: str
    course_id: str
    selected_choice_index: int
    is_correct: bool
    answered_at: datetime = field(default_factory=datetime.now)


@dataclass
class QuizSession:
    """クイズセッション"""

    id: str
    user_id: str
    course_id: str
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    status: SessionStatus = SessionStatus.IN_PROGRESS


@dataclass
class MockExamSession:
    """模擬試験セッション"""

    id: str
    user_id: str
    exam_type: ExamType
    started_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: SessionStatus = SessionStatus.IN_PROGRESS


# =============================================================================
# レスポンスモデル
# =============================================================================


@dataclass
class CourseInfo:
    """コース表示用データ"""

    id: str
    name: str
    region: Region
    difficulty: Difficulty
    description: str
    question_count: int = 0
    is_suspended: bool = False
    answered_count: int = 0


@dataclass
class AnswerResult:
    """回答結果（正誤フィードバック）"""

    question_id: str
    selected_choice_index: int
    correct_choice_index: int
    is_correct: bool


@dataclass
class Explanation:
    """解説データ（愛媛トリビア + AWS/AI概念説明）"""

    ehime_trivia: str
    aws_ai_explanation: str


@dataclass
class CourseSummary:
    """コース完了サマリー"""

    course_id: str
    course_name: str
    correct_count: int
    total_count: int
    accuracy_rate: float  # パーセンテージ（小数第1位まで）
    grade: Grade


@dataclass
class WeakArea:
    """弱点領域"""

    domain: str
    incorrect_rate: float  # パーセンテージ（小数第1位まで）


@dataclass
class RadarChartData:
    """レーダーチャート用データ（ドメイン別正答率）"""

    domain_accuracy: dict[str, float] = field(default_factory=dict)
    # key: ドメイン名, value: 正答率（0-100%）


@dataclass
class ExplorationRate:
    """愛媛探索率"""

    completed_courses: int
    total_courses: int
    exploration_percentage: float  # パーセンテージ（小数第1位まで）
    completed_region_count: int  # 完了した地域数（0-3）


@dataclass
class DashboardData:
    """ダッシュボード集約データ"""

    cumulative_accuracy: float  # 全体正答率
    grade: Grade
    radar_chart: RadarChartData
    exploration_rate: ExplorationRate
    attempt_history: list[AttemptRecord] = field(default_factory=list)
    has_history: bool = False


@dataclass
class AttemptRecord:
    """試験/クイズ試行記録（時系列表示用）"""

    session_id: str
    course_name: str
    accuracy_rate: float
    grade: Grade
    completed_at: datetime


# =============================================================================
# RPGトップ画面モデル
# =============================================================================


@dataclass
class UserStatus:
    """RPGステータス表示用データ"""

    display_name: str
    level: int
    title: str
    total_xp: int
    xp_gauge_percentage: float  # 0.0〜100.0
    current_level_xp: int  # 現レベルから貯めたXP
    required_xp: int  # 次レベルまでの必要XP


@dataclass
class RegionMapData:
    """マップ描画用地域データ"""

    region: Region
    progress_status: str  # "未着手" | "進行中" | "コンプリート"
    fill_color: str  # CSS色コード
    courses: list[CourseInfo]
