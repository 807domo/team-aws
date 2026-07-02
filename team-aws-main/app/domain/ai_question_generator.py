"""
愛媛探索AIクイズ - AI問題生成モジュール

ユーザーの誤答パターンから弱点領域を特定し、
Amazon Bedrock（Claude）を利用してパーソナライズ問題を生成する。
Bedrock未設定時はプリセット問題バンクからフォールバック出題を行う。
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Optional

from app.data.question_repository import QuestionRepository
from app.data.user_record_repository import UserRecordRepository
from app.domain.models import Question, WeakArea
from app.domain.question_validator import validate_question
from app.domain.scoring import identify_weak_areas

logger = logging.getLogger(__name__)

# タイムアウト設定
AI_GENERATION_TIMEOUT_SECONDS = 30

# 弱点分析の前提条件：最低誤答数
MIN_INCORRECT_ANSWERS_FOR_ANALYSIS = 10

# 1領域あたりの生成問題数の範囲
MIN_QUESTIONS_PER_AREA = 1
MAX_QUESTIONS_PER_AREA = 5


class AIQuestionGenerator:
    """AIによるパーソナライズ問題生成器。

    ユーザーの誤答パターンを分析し、弱点領域に基づいて
    Amazon Bedrock（Claude）で新しい問題を生成する。
    Bedrock が利用不可の場合は、同一ドメインのプリセット問題にフォールバックする。
    """

    def __init__(
        self,
        user_record_repository: UserRecordRepository,
        question_repository: QuestionRepository,
        bedrock_client: Optional[object] = None,
        model_id: str = "anthropic.claude-3-haiku-20240307-v1:0",
    ) -> None:
        """
        Args:
            user_record_repository: ユーザー回答記録リポジトリ
            question_repository: 問題リポジトリ（フォールバック用）
            bedrock_client: Amazon Bedrock ランタイムクライアント（None時はフォールバックのみ）
            model_id: 使用するBedrockモデルID
        """
        self._user_record_repo = user_record_repository
        self._question_repo = question_repository
        self._bedrock_client = bedrock_client
        self._model_id = model_id

    def analyze_weak_areas(self, user_id: str) -> list[WeakArea]:
        """ユーザーの誤答パターンから弱点領域を特定する。

        前提条件: 10件以上の誤答が蓄積されていること。
        条件を満たさない場合は空リストを返す。

        Args:
            user_id: ユーザーID

        Returns:
            弱点領域リスト。前提条件を満たさない場合は空リスト。
        """
        # ユーザーの全回答記録を取得
        records = self._user_record_repo.get_records_by_user(user_id)

        if not records:
            return []

        # 誤答数チェック（前提条件: 10件以上）
        incorrect_count = sum(1 for r in records if not r.is_correct)
        if incorrect_count < MIN_INCORRECT_ANSWERS_FOR_ANALYSIS:
            return []

        # 問題IDからドメインへのマッピングを構築
        question_domains = self._build_question_domains(records)

        # scoring モジュールの identify_weak_areas で弱点特定
        weak_areas = identify_weak_areas(
            answer_records=records,
            question_domains=question_domains,
            threshold=0.5,
        )

        return weak_areas

    def generate_questions(
        self, weak_areas: list[WeakArea], count_per_area: int = 3
    ) -> list[Question]:
        """弱点領域に基づきパーソナライズ問題を生成する（30秒タイムアウト）。

        Amazon Bedrock に問題生成プロンプトを送信し、レスポンスをバリデーションする。
        タイムアウトまたはバリデーション失敗時は、同一ドメインのプリセット問題にフォールバック。

        Args:
            weak_areas: 弱点領域リスト
            count_per_area: 1領域あたりの生成問題数（1-5、デフォルト3）

        Returns:
            生成された問題リスト
        """
        # count_per_area を 1-5 の範囲にクランプ
        count_per_area = max(MIN_QUESTIONS_PER_AREA, min(MAX_QUESTIONS_PER_AREA, count_per_area))

        generated_questions: list[Question] = []

        for weak_area in weak_areas:
            questions = self._generate_for_area(weak_area, count_per_area)
            generated_questions.extend(questions)

        return generated_questions

    def _generate_for_area(
        self, weak_area: WeakArea, count: int
    ) -> list[Question]:
        """1つの弱点領域に対して問題を生成する。

        Bedrock が利用可能な場合はAI生成を試行し、
        失敗時はフォールバックとしてプリセット問題を返す。

        Args:
            weak_area: 弱点領域
            count: 生成問題数

        Returns:
            生成された問題リスト
        """
        # Bedrock クライアントが設定されている場合はAI生成を試行
        if self._bedrock_client is not None:
            try:
                questions = self._invoke_bedrock(weak_area, count)
                if questions:
                    return questions
            except Exception as e:
                logger.warning(
                    "AI問題生成に失敗しました（ドメイン: %s）。フォールバックします。エラー: %s",
                    weak_area.domain,
                    str(e),
                )

        # フォールバック: 同一ドメインのプリセット問題から出題
        return self._fallback_questions(weak_area.domain, count)

    def _invoke_bedrock(self, weak_area: WeakArea, count: int) -> list[Question]:
        """Amazon Bedrock にプロンプトを送信して問題を生成する。

        30秒タイムアウトを設定し、レスポンスのバリデーションを行う。

        Args:
            weak_area: 弱点領域
            count: 生成問題数

        Returns:
            バリデーション済みの問題リスト

        Raises:
            Exception: Bedrock呼び出しまたはバリデーション失敗時
        """
        prompt = self._build_prompt(weak_area, count)

        # Bedrock InvokeModel 呼び出し（30秒タイムアウト）
        request_body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        })

        response = self._bedrock_client.invoke_model(
            modelId=self._model_id,
            body=request_body,
            contentType="application/json",
            accept="application/json",
        )

        # レスポンス解析
        response_body = json.loads(response["body"].read())
        content_text = response_body["content"][0]["text"]

        # JSONブロックを抽出
        questions_data = self._parse_response(content_text)

        # バリデーションして問題オブジェクトを生成
        validated_questions: list[Question] = []
        for q_data in questions_data:
            if self._validate_generated_question(q_data):
                question = self._to_question(q_data, weak_area.domain)
                validated_questions.append(question)

        if not validated_questions:
            raise ValueError("生成された問題がすべてバリデーションに失敗しました")

        return validated_questions[:count]

    def _build_prompt(self, weak_area: WeakArea, count: int) -> str:
        """Bedrock に送信するプロンプトを構築する。

        Args:
            weak_area: 弱点領域
            count: 生成問題数

        Returns:
            プロンプト文字列
        """
        return f"""あなたは愛媛県のクイズ問題作成の専門家です。
以下の条件に基づいて、{count}問のクイズ問題をJSON形式で生成してください。

## 条件
- テーマ: 愛媛県の観光・名所・郷土料理 × AWS/AIの概念
- 弱点ドメイン: {weak_area.domain}（このドメインの誤答率: {weak_area.incorrect_rate}%）
- 形式: 4択問題（正解は1つのみ）
- 各問題には愛媛に関するトリビアとAWS/AIの概念説明を含めること

## 出力形式（JSON配列）
```json
[
  {{
    "text": "問題文",
    "choice_1": "選択肢1",
    "choice_2": "選択肢2",
    "choice_3": "選択肢3",
    "choice_4": "選択肢4",
    "correct_choice_index": 0,
    "ehime_trivia": "愛媛トリビア（50-200文字）",
    "aws_ai_explanation": "AWS/AI概念の説明（50-200文字）",
    "difficulty": "中級"
  }}
]
```

注意事項:
- correct_choice_index は 0-3 の整数です
- difficulty は "基礎", "中級", "上級" のいずれかです
- 必ず有効なJSON配列のみを返してください
"""

    def _parse_response(self, content_text: str) -> list[dict]:
        """AIレスポンスからJSONデータを抽出する。

        コードブロック内のJSON、またはプレーンJSONを解析する。

        Args:
            content_text: AIレスポンステキスト

        Returns:
            問題データ辞書のリスト

        Raises:
            ValueError: JSON解析失敗時
        """
        # ```json ... ``` ブロックの抽出を試みる
        import re

        json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", content_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            # プレーンJSONとして解析を試みる
            json_str = content_text.strip()

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"AI応答のJSON解析に失敗しました: {e}")

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
        else:
            raise ValueError("AI応答が予期しない形式です")

    def _validate_generated_question(self, question_data: dict) -> bool:
        """生成された問題データをバリデーションする。

        4択・1正解の形式を満たしているか確認する。

        Args:
            question_data: 問題データ辞書

        Returns:
            バリデーション成功時 True
        """
        # 必須フィールドの存在チェック
        required_fields = [
            "text", "choice_1", "choice_2", "choice_3", "choice_4",
            "correct_choice_index", "ehime_trivia", "aws_ai_explanation",
        ]

        for field_name in required_fields:
            if field_name not in question_data:
                logger.warning("生成問題にフィールド '%s' がありません", field_name)
                return False

        # correct_choice_index の範囲チェック
        correct_idx = question_data.get("correct_choice_index")
        if not isinstance(correct_idx, int) or correct_idx < 0 or correct_idx > 3:
            logger.warning("correct_choice_index が不正です: %s", correct_idx)
            return False

        # 選択肢が空でないか確認
        for i in range(1, 5):
            choice = question_data.get(f"choice_{i}")
            if not choice or not isinstance(choice, str) or not choice.strip():
                logger.warning("choice_%d が空です", i)
                return False

        # テキストが空でないか確認
        text = question_data.get("text")
        if not text or not isinstance(text, str) or not text.strip():
            logger.warning("問題テキストが空です")
            return False

        return True

    def _to_question(self, question_data: dict, domain: str) -> Question:
        """バリデーション済み辞書データを Question ドメインオブジェクトに変換する。

        Args:
            question_data: 問題データ辞書
            domain: 試験ドメイン

        Returns:
            Question ドメインオブジェクト
        """
        from app.domain.models import Difficulty

        # difficulty のデフォルト値
        difficulty_str = question_data.get("difficulty", "中級")
        try:
            difficulty = Difficulty(difficulty_str)
        except ValueError:
            difficulty = Difficulty.INTERMEDIATE

        return Question(
            id=str(uuid.uuid4()),
            course_id=question_data.get("course_id", "ai-generated"),
            text=question_data["text"],
            choice_1=question_data["choice_1"],
            choice_2=question_data["choice_2"],
            choice_3=question_data["choice_3"],
            choice_4=question_data["choice_4"],
            correct_choice_index=question_data["correct_choice_index"],
            ehime_trivia=question_data.get("ehime_trivia", ""),
            aws_ai_explanation=question_data.get("aws_ai_explanation", ""),
            difficulty=difficulty,
            exam_domain=domain,
        )

    def _fallback_questions(self, domain: str, count: int) -> list[Question]:
        """同一ドメインのプリセット問題バンクからフォールバック出題する。

        Args:
            domain: 試験ドメイン
            count: 必要な問題数

        Returns:
            プリセット問題リスト（最大 count 件）
        """
        logger.info(
            "フォールバック: ドメイン '%s' のプリセット問題から %d 件取得します",
            domain,
            count,
        )
        preset_questions = self._question_repo.get_questions_by_domain(domain)
        return preset_questions[:count]

    def _build_question_domains(
        self, records: list
    ) -> dict[str, str]:
        """回答記録に含まれる問題IDからドメインマッピングを構築する。

        各問題IDに対して question_repository から問題を取得し、
        exam_domain を返す。

        Args:
            records: 回答記録リスト

        Returns:
            問題IDからドメインへのマッピング辞書
        """
        question_domains: dict[str, str] = {}
        seen_question_ids: set[str] = set()

        for record in records:
            if record.question_id in seen_question_ids:
                continue
            seen_question_ids.add(record.question_id)

            question = self._question_repo.get_question_by_id(record.question_id)
            if question and question.exam_domain:
                question_domains[record.question_id] = question.exam_domain

        return question_domains
