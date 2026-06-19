"""
愛媛探索AIクイズ - Explanation Engine ユニットテスト

ExplanationEngine の各機能をテストする：
- フォールバック解説の返却
- タイムアウト時のフォールバック
- 文字数制約のバリデーション
- Bedrock クライアント未設定時の動作
"""

from __future__ import annotations

import json
import time
from unittest.mock import MagicMock, patch

import pytest

from app.domain.explanation_engine import (
    EXPLANATION_MAX_LENGTH,
    EXPLANATION_MIN_LENGTH,
    EXPLANATION_TIMEOUT_SECONDS,
    ExplanationEngine,
)
from app.domain.models import Difficulty, Explanation, Question


# =============================================================================
# テスト用ヘルパー
# =============================================================================


def make_question(
    ehime_trivia: str = "松山城は日本で12か所しかない現存天守の一つです。加藤嘉明が築城し、約400年の歴史を持ちます。",
    aws_ai_explanation: str = "Amazon S3はオブジェクトストレージサービスで、写真や動画などのファイルをクラウド上に安全に保存できます。99.999999999%の耐久性を持ちます。",
) -> Question:
    """テスト用のQuestionを生成する。"""
    return Question(
        id="q-001",
        course_id="course-chuyo-basic",
        text="松山城の別名は？",
        choice_1="金亀城",
        choice_2="白鷺城",
        choice_3="烏城",
        choice_4="鶴ヶ城",
        correct_choice_index=0,
        ehime_trivia=ehime_trivia,
        aws_ai_explanation=aws_ai_explanation,
        difficulty=Difficulty.BASIC,
        exam_domain="Cloud Concepts",
    )


def make_bedrock_response(ehime_trivia: str, aws_ai_explanation: str) -> dict:
    """Bedrock のレスポンスをモック用に生成する。"""
    body_content = json.dumps(
        {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "ehime_trivia": ehime_trivia,
                            "aws_ai_explanation": aws_ai_explanation,
                        },
                        ensure_ascii=False,
                    ),
                }
            ]
        }
    )

    mock_body = MagicMock()
    mock_body.read.return_value = body_content.encode("utf-8")
    return {"body": mock_body}


# =============================================================================
# テストクラス
# =============================================================================


class TestGetFallbackExplanation:
    """get_fallback_explanation のテスト"""

    def test_returns_preset_explanation(self):
        """プリセット解説をそのまま返す"""
        engine = ExplanationEngine(bedrock_client=None)
        question = make_question()

        result = engine.get_fallback_explanation(question)

        assert isinstance(result, Explanation)
        assert result.ehime_trivia == question.ehime_trivia
        assert result.aws_ai_explanation == question.aws_ai_explanation

    def test_truncates_when_exceeds_max_length(self):
        """合計が500文字を超える場合トランケートする"""
        long_trivia = "あ" * 300
        long_explanation = "い" * 300  # 合計600文字
        engine = ExplanationEngine(bedrock_client=None)
        question = make_question(
            ehime_trivia=long_trivia, aws_ai_explanation=long_explanation
        )

        result = engine.get_fallback_explanation(question)

        total_length = len(result.ehime_trivia) + len(result.aws_ai_explanation)
        assert total_length <= EXPLANATION_MAX_LENGTH

    def test_returns_short_explanation_as_is(self):
        """合計が100文字未満でもプリセットはそのまま返す"""
        engine = ExplanationEngine(bedrock_client=None)
        question = make_question(
            ehime_trivia="短い", aws_ai_explanation="説明"
        )

        result = engine.get_fallback_explanation(question)

        # 短すぎる場合でもプリセットデータはそのまま返される
        assert result.ehime_trivia == "短い"
        assert result.aws_ai_explanation == "説明"


class TestGenerateExplanation:
    """generate_explanation のテスト"""

    def test_falls_back_when_no_client(self):
        """Bedrock クライアント未設定時はフォールバックを返す"""
        engine = ExplanationEngine(bedrock_client=None)
        question = make_question()

        result = engine.generate_explanation(question)

        assert result.ehime_trivia == question.ehime_trivia
        assert result.aws_ai_explanation == question.aws_ai_explanation

    def test_returns_ai_generated_explanation(self):
        """Bedrock からの正常レスポンスでAI生成解説を返す"""
        mock_client = MagicMock()
        ai_trivia = "愛媛県松山市の松山城は、標高132mの勝山に建つ連立式天守を持つ平山城で、日本三大平山城の一つです。"
        ai_explanation = "Amazon S3は高い耐久性と可用性を持つオブジェクトストレージで、城の写真アーカイブのような大量データの保存に最適です。"

        mock_client.invoke_model.return_value = make_bedrock_response(
            ai_trivia, ai_explanation
        )

        engine = ExplanationEngine(bedrock_client=mock_client)
        question = make_question()

        result = engine.generate_explanation(question)

        assert result.ehime_trivia == ai_trivia
        assert result.aws_ai_explanation == ai_explanation

    def test_falls_back_on_api_error(self):
        """Bedrock API エラー時はフォールバックを返す"""
        mock_client = MagicMock()
        mock_client.invoke_model.side_effect = Exception("API Error")

        engine = ExplanationEngine(bedrock_client=mock_client)
        question = make_question()

        result = engine.generate_explanation(question)

        assert result.ehime_trivia == question.ehime_trivia
        assert result.aws_ai_explanation == question.aws_ai_explanation

    def test_falls_back_on_timeout(self):
        """10秒タイムアウト時はフォールバックを返す"""
        import concurrent.futures

        mock_client = MagicMock()

        def slow_invoke(*args, **kwargs):
            time.sleep(5)  # タイムアウトより長い
            return make_bedrock_response("遅い", "レスポンス")

        mock_client.invoke_model.side_effect = slow_invoke

        engine = ExplanationEngine(bedrock_client=mock_client)
        question = make_question()

        # タイムアウトを0.5秒に設定してテストを高速化
        import app.domain.explanation_engine as ee_module

        original_timeout = ee_module.EXPLANATION_TIMEOUT_SECONDS
        ee_module.EXPLANATION_TIMEOUT_SECONDS = 0.5

        try:
            result = engine.generate_explanation(question)
            assert result.ehime_trivia == question.ehime_trivia
            assert result.aws_ai_explanation == question.aws_ai_explanation
        finally:
            ee_module.EXPLANATION_TIMEOUT_SECONDS = original_timeout

    def test_falls_back_on_invalid_json_response(self):
        """不正なJSONレスポンス時はフォールバックを返す"""
        mock_client = MagicMock()
        body_content = json.dumps(
            {"content": [{"type": "text", "text": "これはJSONではありません"}]}
        )
        mock_body = MagicMock()
        mock_body.read.return_value = body_content.encode("utf-8")
        mock_client.invoke_model.return_value = {"body": mock_body}

        engine = ExplanationEngine(bedrock_client=mock_client)
        question = make_question()

        result = engine.generate_explanation(question)

        assert result.ehime_trivia == question.ehime_trivia
        assert result.aws_ai_explanation == question.aws_ai_explanation

    def test_falls_back_when_ai_response_exceeds_length(self):
        """AI生成解説が文字数制約を超える場合はフォールバックを返す"""
        mock_client = MagicMock()
        long_trivia = "あ" * 400
        long_explanation = "い" * 400  # 合計800文字

        mock_client.invoke_model.return_value = make_bedrock_response(
            long_trivia, long_explanation
        )

        engine = ExplanationEngine(bedrock_client=mock_client)
        question = make_question()

        result = engine.generate_explanation(question)

        # フォールバックが使用される
        assert result.ehime_trivia == question.ehime_trivia
        assert result.aws_ai_explanation == question.aws_ai_explanation


class TestLengthValidation:
    """文字数制約のバリデーションテスト"""

    def test_valid_length_passes(self):
        """100〜500文字の範囲内は通過する"""
        engine = ExplanationEngine(bedrock_client=None)
        explanation = Explanation(
            ehime_trivia="あ" * 60,
            aws_ai_explanation="い" * 60,
        )

        result = engine._validate_length(explanation)

        assert result is not None
        assert result == explanation

    def test_too_short_fails(self):
        """合計100文字未満は None を返す"""
        engine = ExplanationEngine(bedrock_client=None)
        explanation = Explanation(
            ehime_trivia="短い",
            aws_ai_explanation="文",
        )

        result = engine._validate_length(explanation)

        assert result is None

    def test_too_long_fails(self):
        """合計500文字超は None を返す"""
        engine = ExplanationEngine(bedrock_client=None)
        explanation = Explanation(
            ehime_trivia="あ" * 300,
            aws_ai_explanation="い" * 300,
        )

        result = engine._validate_length(explanation)

        assert result is None

    def test_exactly_100_passes(self):
        """ちょうど100文字は通過する"""
        engine = ExplanationEngine(bedrock_client=None)
        explanation = Explanation(
            ehime_trivia="あ" * 50,
            aws_ai_explanation="い" * 50,
        )

        result = engine._validate_length(explanation)

        assert result is not None

    def test_exactly_500_passes(self):
        """ちょうど500文字は通過する"""
        engine = ExplanationEngine(bedrock_client=None)
        explanation = Explanation(
            ehime_trivia="あ" * 250,
            aws_ai_explanation="い" * 250,
        )

        result = engine._validate_length(explanation)

        assert result is not None


class TestTruncateExplanation:
    """トランケーション処理のテスト"""

    def test_truncates_proportionally(self):
        """各パートの比率を維持しつつトランケートする"""
        engine = ExplanationEngine(bedrock_client=None)
        ehime = "あ" * 400
        aws = "い" * 400  # 合計800文字

        result = engine._truncate_explanation(ehime, aws)

        total = len(result.ehime_trivia) + len(result.aws_ai_explanation)
        assert total <= EXPLANATION_MAX_LENGTH

    def test_does_not_truncate_within_limit(self):
        """制約内のテキストはトランケートしない"""
        engine = ExplanationEngine(bedrock_client=None)
        ehime = "あ" * 100
        aws = "い" * 100  # 合計200文字

        result = engine._truncate_explanation(ehime, aws)

        assert result.ehime_trivia == ehime
        assert result.aws_ai_explanation == aws
