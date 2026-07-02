"""
AIQuestionGenerator のユニットテスト

弱点分析、問題生成、フォールバック、バリデーションの動作を検証する。
"""

from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.domain.ai_question_generator import (
    AI_GENERATION_TIMEOUT_SECONDS,
    AIQuestionGenerator,
    MIN_INCORRECT_ANSWERS_FOR_ANALYSIS,
)
from app.domain.models import AnswerRecord, Difficulty, Question, WeakArea


# =============================================================================
# テスト用ヘルパー
# =============================================================================


def _make_answer_record(
    question_id: str,
    is_correct: bool,
    user_id: str = "user-1",
    course_id: str = "course-1",
) -> AnswerRecord:
    """テスト用の AnswerRecord を生成する"""
    return AnswerRecord(
        id=f"rec-{question_id}-{is_correct}",
        user_id=user_id,
        question_id=question_id,
        course_id=course_id,
        selected_choice_index=0 if is_correct else 1,
        is_correct=is_correct,
        answered_at=datetime.now(),
    )


def _make_question(
    question_id: str, domain: str = "Cloud Concepts", course_id: str = "course-1"
) -> Question:
    """テスト用の Question を生成する"""
    return Question(
        id=question_id,
        course_id=course_id,
        text=f"問題 {question_id}",
        choice_1="選択肢A",
        choice_2="選択肢B",
        choice_3="選択肢C",
        choice_4="選択肢D",
        correct_choice_index=0,
        ehime_trivia="愛媛トリビア",
        aws_ai_explanation="AWS/AI解説",
        difficulty=Difficulty.INTERMEDIATE,
        exam_domain=domain,
    )


# =============================================================================
# analyze_weak_areas テスト
# =============================================================================


class TestAnalyzeWeakAreas:
    """analyze_weak_areas メソッドのテスト"""

    def test_returns_empty_when_no_records(self):
        """回答記録がない場合は空リストを返す"""
        mock_user_repo = MagicMock()
        mock_user_repo.get_records_by_user.return_value = []
        mock_question_repo = MagicMock()

        generator = AIQuestionGenerator(mock_user_repo, mock_question_repo)
        result = generator.analyze_weak_areas("user-1")

        assert result == []

    def test_returns_empty_when_insufficient_incorrect_answers(self):
        """誤答が10件未満の場合は空リストを返す"""
        # 9件の誤答 + 5件の正解 = 14件の回答（誤答9件 < 10件）
        records = []
        for i in range(9):
            records.append(_make_answer_record(f"q-{i}", is_correct=False))
        for i in range(5):
            records.append(_make_answer_record(f"q-correct-{i}", is_correct=True))

        mock_user_repo = MagicMock()
        mock_user_repo.get_records_by_user.return_value = records
        mock_question_repo = MagicMock()
        mock_question_repo.get_question_by_id.return_value = _make_question("q-0")

        generator = AIQuestionGenerator(mock_user_repo, mock_question_repo)
        result = generator.analyze_weak_areas("user-1")

        assert result == []

    def test_identifies_weak_areas_with_sufficient_incorrect_answers(self):
        """10件以上の誤答があり、50%以上の誤答率ドメインを弱点として特定する"""
        # Cloud Concepts: 8問中6問不正解（75%誤答率） → 弱点
        # Security: 8問中2問不正解（25%誤答率） → 弱点でない
        records = []
        for i in range(6):
            records.append(_make_answer_record(f"cloud-wrong-{i}", is_correct=False))
        for i in range(2):
            records.append(_make_answer_record(f"cloud-right-{i}", is_correct=True))
        for i in range(2):
            records.append(_make_answer_record(f"sec-wrong-{i}", is_correct=False))
        for i in range(6):
            records.append(_make_answer_record(f"sec-right-{i}", is_correct=True))

        # 合計誤答: 6 + 2 = 8件 → これだと10件に満たないので追加
        for i in range(4):
            records.append(_make_answer_record(f"cloud-extra-wrong-{i}", is_correct=False))

        mock_user_repo = MagicMock()
        mock_user_repo.get_records_by_user.return_value = records

        # 問題IDとドメインのマッピング
        def get_question_by_id(qid: str):
            if qid.startswith("cloud"):
                return _make_question(qid, domain="Cloud Concepts")
            elif qid.startswith("sec"):
                return _make_question(qid, domain="Security")
            return None

        mock_question_repo = MagicMock()
        mock_question_repo.get_question_by_id.side_effect = get_question_by_id

        generator = AIQuestionGenerator(mock_user_repo, mock_question_repo)
        result = generator.analyze_weak_areas("user-1")

        # Cloud Concepts のみ弱点として検出されるはず
        assert len(result) >= 1
        domains = [wa.domain for wa in result]
        assert "Cloud Concepts" in domains
        assert "Security" not in domains


# =============================================================================
# generate_questions テスト
# =============================================================================


class TestGenerateQuestions:
    """generate_questions メソッドのテスト"""

    def test_clamps_count_per_area_to_min(self):
        """count_per_area が 1 未満の場合は 1 にクランプされる"""
        mock_user_repo = MagicMock()
        mock_question_repo = MagicMock()
        mock_question_repo.get_questions_by_domain.return_value = [
            _make_question("q-1", domain="Cloud Concepts")
        ]

        generator = AIQuestionGenerator(mock_user_repo, mock_question_repo)
        weak_areas = [WeakArea(domain="Cloud Concepts", incorrect_rate=75.0)]

        result = generator.generate_questions(weak_areas, count_per_area=0)

        # フォールバックから1件取得
        mock_question_repo.get_questions_by_domain.assert_called_once_with("Cloud Concepts")
        assert len(result) <= 1

    def test_clamps_count_per_area_to_max(self):
        """count_per_area が 5 超の場合は 5 にクランプされる"""
        mock_user_repo = MagicMock()
        mock_question_repo = MagicMock()
        questions = [_make_question(f"q-{i}", domain="Security") for i in range(10)]
        mock_question_repo.get_questions_by_domain.return_value = questions

        generator = AIQuestionGenerator(mock_user_repo, mock_question_repo)
        weak_areas = [WeakArea(domain="Security", incorrect_rate=60.0)]

        result = generator.generate_questions(weak_areas, count_per_area=10)

        # 最大5件にクランプ
        assert len(result) <= 5

    def test_fallback_when_no_bedrock_client(self):
        """Bedrock クライアント未設定時はフォールバック問題を返す"""
        mock_user_repo = MagicMock()
        mock_question_repo = MagicMock()
        preset_questions = [
            _make_question("preset-1", domain="Cloud Concepts"),
            _make_question("preset-2", domain="Cloud Concepts"),
        ]
        mock_question_repo.get_questions_by_domain.return_value = preset_questions

        generator = AIQuestionGenerator(
            mock_user_repo, mock_question_repo, bedrock_client=None
        )
        weak_areas = [WeakArea(domain="Cloud Concepts", incorrect_rate=70.0)]

        result = generator.generate_questions(weak_areas, count_per_area=2)

        assert len(result) == 2
        assert result[0].id == "preset-1"
        assert result[1].id == "preset-2"

    def test_fallback_when_bedrock_raises_exception(self):
        """Bedrock 呼び出しが例外を投げた場合はフォールバック"""
        mock_user_repo = MagicMock()
        mock_question_repo = MagicMock()
        preset_questions = [_make_question("fallback-1", domain="AI Fundamentals")]
        mock_question_repo.get_questions_by_domain.return_value = preset_questions

        mock_bedrock = MagicMock()
        mock_bedrock.invoke_model.side_effect = Exception("Timeout or credentials error")

        generator = AIQuestionGenerator(
            mock_user_repo, mock_question_repo, bedrock_client=mock_bedrock
        )
        weak_areas = [WeakArea(domain="AI Fundamentals", incorrect_rate=80.0)]

        result = generator.generate_questions(weak_areas, count_per_area=1)

        assert len(result) == 1
        assert result[0].id == "fallback-1"

    def test_successful_bedrock_generation(self):
        """Bedrock が正常にレスポンスを返した場合、バリデーション済み問題を返す"""
        mock_user_repo = MagicMock()
        mock_question_repo = MagicMock()

        # Bedrock レスポンスをモック
        bedrock_response_data = [
            {
                "text": "松山城の天守閣とAWSリージョンの共通点は？",
                "choice_1": "可用性",
                "choice_2": "スケーラビリティ",
                "choice_3": "冗長性",
                "choice_4": "耐障害性",
                "correct_choice_index": 0,
                "ehime_trivia": "松山城は日本に12しかない現存天守の一つです。",
                "aws_ai_explanation": "AWSリージョンは高可用性を実現するために複数のAZで構成されています。",
                "difficulty": "基礎",
            }
        ]

        mock_body = MagicMock()
        mock_body.read.return_value = json.dumps({
            "content": [{"text": json.dumps(bedrock_response_data, ensure_ascii=False)}]
        }).encode()

        mock_bedrock = MagicMock()
        mock_bedrock.invoke_model.return_value = {"body": mock_body}

        generator = AIQuestionGenerator(
            mock_user_repo, mock_question_repo, bedrock_client=mock_bedrock
        )
        weak_areas = [WeakArea(domain="Cloud Concepts", incorrect_rate=75.0)]

        result = generator.generate_questions(weak_areas, count_per_area=1)

        assert len(result) == 1
        assert result[0].text == "松山城の天守閣とAWSリージョンの共通点は？"
        assert result[0].correct_choice_index == 0
        assert result[0].exam_domain == "Cloud Concepts"

    def test_fallback_when_bedrock_returns_invalid_format(self):
        """Bedrock が不正形式レスポンスを返した場合はフォールバック"""
        mock_user_repo = MagicMock()
        mock_question_repo = MagicMock()
        preset_questions = [_make_question("fallback-1", domain="Security")]
        mock_question_repo.get_questions_by_domain.return_value = preset_questions

        # 不正形式: correct_choice_index が範囲外
        invalid_response = [
            {
                "text": "問題テキスト",
                "choice_1": "A",
                "choice_2": "B",
                "choice_3": "C",
                "choice_4": "D",
                "correct_choice_index": 5,  # 不正
                "ehime_trivia": "トリビア",
                "aws_ai_explanation": "解説",
            }
        ]

        mock_body = MagicMock()
        mock_body.read.return_value = json.dumps({
            "content": [{"text": json.dumps(invalid_response, ensure_ascii=False)}]
        }).encode()

        mock_bedrock = MagicMock()
        mock_bedrock.invoke_model.return_value = {"body": mock_body}

        generator = AIQuestionGenerator(
            mock_user_repo, mock_question_repo, bedrock_client=mock_bedrock
        )
        weak_areas = [WeakArea(domain="Security", incorrect_rate=65.0)]

        result = generator.generate_questions(weak_areas, count_per_area=1)

        # バリデーション失敗 → フォールバック
        assert len(result) == 1
        assert result[0].id == "fallback-1"

    def test_multiple_weak_areas(self):
        """複数の弱点領域がある場合、各ドメインから問題を取得する"""
        mock_user_repo = MagicMock()
        mock_question_repo = MagicMock()

        def get_by_domain(domain: str):
            if domain == "Cloud Concepts":
                return [_make_question("cloud-1", domain="Cloud Concepts")]
            elif domain == "Security":
                return [_make_question("sec-1", domain="Security")]
            return []

        mock_question_repo.get_questions_by_domain.side_effect = get_by_domain

        generator = AIQuestionGenerator(mock_user_repo, mock_question_repo)
        weak_areas = [
            WeakArea(domain="Cloud Concepts", incorrect_rate=70.0),
            WeakArea(domain="Security", incorrect_rate=55.0),
        ]

        result = generator.generate_questions(weak_areas, count_per_area=1)

        assert len(result) == 2
        domains = {q.exam_domain for q in result}
        assert "Cloud Concepts" in domains
        assert "Security" in domains


# =============================================================================
# バリデーション関連テスト
# =============================================================================


class TestValidateGeneratedQuestion:
    """_validate_generated_question のバリデーションテスト"""

    def test_valid_question_passes(self):
        """正しい形式の問題はバリデーションを通過する"""
        mock_user_repo = MagicMock()
        mock_question_repo = MagicMock()
        generator = AIQuestionGenerator(mock_user_repo, mock_question_repo)

        valid_data = {
            "text": "問題テキスト",
            "choice_1": "A",
            "choice_2": "B",
            "choice_3": "C",
            "choice_4": "D",
            "correct_choice_index": 2,
            "ehime_trivia": "トリビア",
            "aws_ai_explanation": "解説",
        }

        assert generator._validate_generated_question(valid_data) is True

    def test_missing_field_fails(self):
        """必須フィールドが欠けている場合はバリデーション失敗"""
        mock_user_repo = MagicMock()
        mock_question_repo = MagicMock()
        generator = AIQuestionGenerator(mock_user_repo, mock_question_repo)

        # text がない
        invalid_data = {
            "choice_1": "A",
            "choice_2": "B",
            "choice_3": "C",
            "choice_4": "D",
            "correct_choice_index": 0,
            "ehime_trivia": "トリビア",
            "aws_ai_explanation": "解説",
        }

        assert generator._validate_generated_question(invalid_data) is False

    def test_invalid_correct_choice_index_fails(self):
        """correct_choice_index が範囲外の場合はバリデーション失敗"""
        mock_user_repo = MagicMock()
        mock_question_repo = MagicMock()
        generator = AIQuestionGenerator(mock_user_repo, mock_question_repo)

        invalid_data = {
            "text": "問題",
            "choice_1": "A",
            "choice_2": "B",
            "choice_3": "C",
            "choice_4": "D",
            "correct_choice_index": 4,
            "ehime_trivia": "トリビア",
            "aws_ai_explanation": "解説",
        }

        assert generator._validate_generated_question(invalid_data) is False

    def test_empty_choice_fails(self):
        """空の選択肢がある場合はバリデーション失敗"""
        mock_user_repo = MagicMock()
        mock_question_repo = MagicMock()
        generator = AIQuestionGenerator(mock_user_repo, mock_question_repo)

        invalid_data = {
            "text": "問題",
            "choice_1": "",
            "choice_2": "B",
            "choice_3": "C",
            "choice_4": "D",
            "correct_choice_index": 0,
            "ehime_trivia": "トリビア",
            "aws_ai_explanation": "解説",
        }

        assert generator._validate_generated_question(invalid_data) is False


# =============================================================================
# _parse_response テスト
# =============================================================================


class TestParseResponse:
    """_parse_response のテスト"""

    def test_parses_json_code_block(self):
        """```json ... ``` 形式のレスポンスを解析できる"""
        mock_user_repo = MagicMock()
        mock_question_repo = MagicMock()
        generator = AIQuestionGenerator(mock_user_repo, mock_question_repo)

        content = '```json\n[{"text": "問題"}]\n```'
        result = generator._parse_response(content)

        assert result == [{"text": "問題"}]

    def test_parses_plain_json(self):
        """プレーンJSON形式のレスポンスを解析できる"""
        mock_user_repo = MagicMock()
        mock_question_repo = MagicMock()
        generator = AIQuestionGenerator(mock_user_repo, mock_question_repo)

        content = '[{"text": "問題"}]'
        result = generator._parse_response(content)

        assert result == [{"text": "問題"}]

    def test_raises_on_invalid_json(self):
        """無効なJSONの場合はValueErrorを送出する"""
        mock_user_repo = MagicMock()
        mock_question_repo = MagicMock()
        generator = AIQuestionGenerator(mock_user_repo, mock_question_repo)

        with pytest.raises(ValueError, match="JSON解析に失敗"):
            generator._parse_response("これはJSONではありません")


# =============================================================================
# タイムアウト設定テスト
# =============================================================================


class TestConfiguration:
    """設定値のテスト"""

    def test_timeout_is_30_seconds(self):
        """AI生成タイムアウトが30秒に設定されている"""
        assert AI_GENERATION_TIMEOUT_SECONDS == 30

    def test_min_incorrect_answers_is_10(self):
        """最低誤答数が10件に設定されている"""
        assert MIN_INCORRECT_ANSWERS_FOR_ANALYSIS == 10
