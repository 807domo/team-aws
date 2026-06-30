"""
愛媛探索AIクイズ - Explanation Engine

クイズ回答後の解説生成を担当するコンポーネント。
Amazon Bedrock (Claude) を使用したAI生成解説と、
タイムアウト時のプリセット解説フォールバックを提供する。
"""

from __future__ import annotations

import json
import logging
import os
import concurrent.futures
from typing import Optional

from app.domain.models import Explanation, Question

logger = logging.getLogger(__name__)

# =============================================================================
# 定数
# =============================================================================

EXPLANATION_TIMEOUT_SECONDS = 10
EXPLANATION_MIN_LENGTH = 100
EXPLANATION_MAX_LENGTH = 500

# Bedrock 設定（環境変数から取得）
DEFAULT_AWS_REGION = "ap-northeast-1"
DEFAULT_BEDROCK_MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"


class ExplanationEngine:
    """解説エンジン。

    Amazon Bedrock (Claude) を使用して、愛媛トリビアと AWS/AI 概念解説を
    AI生成する。10秒以内に応答がない場合や、Bedrock が利用不可の場合は
    問題データに事前登録されたプリセット解説にフォールバックする。
    """

    def __init__(self, bedrock_client: Optional[object] = None) -> None:
        """
        Args:
            bedrock_client: boto3 Bedrock Runtime クライアント。
                           None の場合は環境変数から自動生成を試みる。
                           生成失敗時はフォールバックモードで動作する。
        """
        self._client = bedrock_client
        self._model_id = os.environ.get("BEDROCK_MODEL_ID", DEFAULT_BEDROCK_MODEL_ID)

        if self._client is None:
            self._client = self._create_bedrock_client()

    def generate_explanation(self, question: Question) -> Explanation:
        """AI生成またはプリセット解説を返す（10秒タイムアウト）。

        Amazon Bedrock を呼び出して解説を生成する。以下の場合はフォールバック：
        - Bedrock クライアントが利用不可
        - API呼び出しが10秒以内に完了しない
        - レスポンスのパースに失敗
        - 生成された解説が文字数制約（100〜500文字）を満たさない

        Args:
            question: 解説対象の問題

        Returns:
            Explanation（愛媛トリビア + AWS/AI概念説明）
        """
        # Bedrock クライアントが利用不可の場合は即座にフォールバック
        if self._client is None:
            logger.info("Bedrock クライアント未設定。フォールバック解説を使用します。")
            return self.get_fallback_explanation(question)

        try:
            # タイムアウト付きで Bedrock を呼び出す
            timeout = EXPLANATION_TIMEOUT_SECONDS
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._call_bedrock, question)
                explanation = future.result(timeout=timeout)

            # 文字数制約のバリデーション
            validated = self._validate_length(explanation)
            if validated is not None:
                return validated

            # バリデーション失敗時はフォールバック
            logger.warning(
                "AI生成解説が文字数制約を満たしません。フォールバックを使用します。"
            )
            return self.get_fallback_explanation(question)

        except concurrent.futures.TimeoutError:
            logger.warning(
                "Bedrock API呼び出しが%d秒以内に完了しませんでした。フォールバックを使用します。",
                EXPLANATION_TIMEOUT_SECONDS,
            )
            return self.get_fallback_explanation(question)
        except Exception as e:
            logger.warning(
                "解説生成中にエラーが発生しました: %s。フォールバックを使用します。",
                str(e),
            )
            return self.get_fallback_explanation(question)

    def get_fallback_explanation(self, question: Question) -> Explanation:
        """プリセット解説を返す。

        問題データに事前登録された解説をそのまま返す。
        文字数制約バリデーションを適用し、制約を超える場合はトランケートする。

        Args:
            question: 解説対象の問題

        Returns:
            Explanation（プリセットの愛媛トリビア + AWS/AI概念説明）
        """
        ehime_trivia = question.ehime_trivia
        aws_ai_explanation = question.aws_ai_explanation

        # 文字数制約の適用
        explanation = Explanation(
            ehime_trivia=ehime_trivia,
            aws_ai_explanation=aws_ai_explanation,
        )

        validated = self._validate_length(explanation)
        if validated is not None:
            return validated

        # 制約を超える場合はトランケート
        return self._truncate_explanation(ehime_trivia, aws_ai_explanation)

    # =========================================================================
    # プライベートメソッド
    # =========================================================================

    def _create_bedrock_client(self) -> Optional[object]:
        """環境変数から Bedrock Runtime クライアントを生成する。

        AWS認証情報が利用不可の場合は None を返す（フォールバックモード）。

        Returns:
            boto3 Bedrock Runtime クライアント、または None
        """
        try:
            import boto3

            region = os.environ.get("AWS_REGION", DEFAULT_AWS_REGION)
            client = boto3.client(
                "bedrock-runtime",
                region_name=region,
            )
            # クライアント生成成功（実際のAPI呼び出しまでは認証確認しない）
            return client
        except Exception as e:
            logger.info(
                "Bedrock クライアントの生成に失敗しました: %s。フォールバックモードで動作します。",
                str(e),
            )
            return None

    def _call_bedrock(self, question: Question) -> Explanation:
        """Amazon Bedrock (Claude) を呼び出して解説を生成する。

        Args:
            question: 解説対象の問題

        Returns:
            Explanation（AI生成された解説）

        Raises:
            Exception: API呼び出し失敗時
        """
        prompt = self._build_prompt(question)

        request_body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1024,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            }
        )

        response = self._client.invoke_model(
            modelId=self._model_id,
            contentType="application/json",
            accept="application/json",
            body=request_body,
        )

        response_body = json.loads(response["body"].read())
        content = response_body["content"][0]["text"]

        return self._parse_response(content)

    def _build_prompt(self, question: Question) -> str:
        """Bedrock 用のプロンプトを構築する。

        Args:
            question: 解説対象の問題

        Returns:
            プロンプト文字列
        """
        correct_choice = getattr(
            question, f"choice_{question.correct_choice_index + 1}"
        )

        return (
            "以下のクイズ問題に対する解説を生成してください。\n\n"
            f"【問題】{question.text}\n"
            f"【正解】{correct_choice}\n"
            f"【分野】{question.exam_domain}\n\n"
            "以下の形式でJSON形式で回答してください：\n"
            "{\n"
            '  "ehime_trivia": "愛媛県に関連するトリビア（50〜250文字）",\n'
            '  "aws_ai_explanation": "AWS/AI概念の解説（50〜250文字）"\n'
            "}\n\n"
            "制約:\n"
            "- ehime_trivia と aws_ai_explanation の合計文字数は100〜500文字\n"
            "- プログラミング初心者にもわかりやすい表現を使用\n"
            "- 専門用語には簡潔な説明を添える\n"
            "- 愛媛の地域情報と AWS/AI 概念を関連付けて説明する\n"
            "- JSON以外のテキストは含めない"
        )

    def _parse_response(self, content: str) -> Explanation:
        """Bedrock のレスポンスをパースして Explanation を生成する。

        Args:
            content: Bedrock からのテキストレスポンス

        Returns:
            Explanation オブジェクト

        Raises:
            ValueError: パース失敗時
        """
        # JSON部分を抽出（コードブロックで囲まれている場合に対応）
        text = content.strip()
        if text.startswith("```"):
            # ```json ... ``` の形式
            lines = text.split("\n")
            json_lines = []
            in_block = False
            for line in lines:
                if line.startswith("```") and not in_block:
                    in_block = True
                    continue
                elif line.startswith("```") and in_block:
                    break
                elif in_block:
                    json_lines.append(line)
            text = "\n".join(json_lines)

        data = json.loads(text)

        ehime_trivia = data.get("ehime_trivia", "")
        aws_ai_explanation = data.get("aws_ai_explanation", "")

        if not ehime_trivia or not aws_ai_explanation:
            raise ValueError("解説データが不完全です")

        return Explanation(
            ehime_trivia=ehime_trivia,
            aws_ai_explanation=aws_ai_explanation,
        )

    def _validate_length(self, explanation: Explanation) -> Optional[Explanation]:
        """解説の合計文字数を検証する。

        合計文字数が100〜500文字の範囲内であれば Explanation を返す。
        範囲外の場合は None を返す。

        Args:
            explanation: 検証対象の解説

        Returns:
            制約を満たす場合は Explanation、満たさない場合は None
        """
        total_length = len(explanation.ehime_trivia) + len(
            explanation.aws_ai_explanation
        )

        if EXPLANATION_MIN_LENGTH <= total_length <= EXPLANATION_MAX_LENGTH:
            return explanation

        return None

    def _truncate_explanation(
        self, ehime_trivia: str, aws_ai_explanation: str
    ) -> Explanation:
        """解説を文字数制約に収まるようにトランケートする。

        合計が500文字を超える場合は、各パートを均等にカットする。
        合計が100文字未満の場合はそのまま返す（プリセットデータの品質に依存）。

        Args:
            ehime_trivia: 愛媛トリビア
            aws_ai_explanation: AWS/AI概念説明

        Returns:
            トランケートされた Explanation
        """
        total_length = len(ehime_trivia) + len(aws_ai_explanation)

        if total_length <= EXPLANATION_MAX_LENGTH:
            # 合計が最大値以下ならそのまま返す
            return Explanation(
                ehime_trivia=ehime_trivia,
                aws_ai_explanation=aws_ai_explanation,
            )

        # 最大値を超える場合: 各パートの比率を維持しつつトランケート
        if len(ehime_trivia) == 0:
            return Explanation(
                ehime_trivia=ehime_trivia,
                aws_ai_explanation=aws_ai_explanation[:EXPLANATION_MAX_LENGTH],
            )
        if len(aws_ai_explanation) == 0:
            return Explanation(
                ehime_trivia=ehime_trivia[:EXPLANATION_MAX_LENGTH],
                aws_ai_explanation=aws_ai_explanation,
            )

        ratio = len(ehime_trivia) / total_length
        ehime_max = int(EXPLANATION_MAX_LENGTH * ratio)
        aws_max = EXPLANATION_MAX_LENGTH - ehime_max

        return Explanation(
            ehime_trivia=ehime_trivia[:ehime_max],
            aws_ai_explanation=aws_ai_explanation[:aws_max],
        )
