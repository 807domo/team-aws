"""
愛媛探索AIクイズ - Gemini AI問題自動生成モジュール

ユーザーの学習結果（弱点ドメイン）に基づいて、
Google Gemini APIを使い4択問題を自動生成する。
APIキー未設定時はフォールバック（プリセット問題）を返す。
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from typing import Optional

from app.domain.models import Difficulty, Question, WeakArea

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.5-flash"
GENERATION_TIMEOUT_SECONDS = 30


class GeminiQuestionGenerator:
    """Google Gemini APIによる問題自動生成器。

    弱点ドメインに基づいてAWS/AI関連の4択問題を生成する。
    GEMINI_API_KEY 環境変数が未設定の場合は利用不可を通知する。
    ユーザーごとのAPIキーにも対応。
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self._client = None

        if self._api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self._api_key)
                logger.info("Gemini API 初期化成功")
            except Exception as e:
                logger.warning("Gemini API 初期化失敗: %s", str(e))
                self._client = None

    @property
    def is_available(self) -> bool:
        """Gemini APIが利用可能かどうか。"""
        return self._client is not None

    def generate_questions(
        self,
        weak_areas: list[WeakArea],
        count_per_area: int = 3,
    ) -> list[Question]:
        """弱点領域に基づいて問題を自動生成する。

        Args:
            weak_areas: 弱点領域リスト
            count_per_area: 1領域あたりの生成問題数（1-5）

        Returns:
            生成された問題リスト。API未設定時は空リスト。
        """
        if not self.is_available:
            logger.warning("Gemini API未設定のため問題生成をスキップ")
            return []

        count_per_area = max(1, min(5, count_per_area))
        all_questions: list[Question] = []

        for weak_area in weak_areas:
            try:
                questions = self._generate_for_area(weak_area, count_per_area)
                all_questions.extend(questions)
            except Exception as e:
                error_str = str(e)
                logger.error("問題生成失敗（ドメイン: %s）: %s", weak_area.domain, error_str)
                # 429/503エラーはクォータ超過 — 以降の生成もスキップ
                if "429" in error_str or "503" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    logger.warning("クォータ超過のため問題生成を中止します")
                    break

        return all_questions

    def generate_questions_batch(
        self, weak_areas: list[WeakArea], total_count: int = 10
    ) -> list[Question]:
        """複数の弱点領域をまとめて1回のAPIコールで問題生成する（クォータ節約）。

        Args:
            weak_areas: 弱点領域リスト
            total_count: 生成する総問題数

        Returns:
            生成された問題リスト
        """
        if not self.is_available:
            return []

        total_count = max(1, min(10, total_count))
        domains_text = "\n".join(
            f"- {wa.domain}（誤答率: {wa.incorrect_rate:.1f}%）" for wa in weak_areas
        )

        prompt = f"""あなたはAWS認定資格の問題作成の専門家です。
以下の弱点ドメインに基づいて、合計{total_count}問の4択クイズ問題をJSON配列で生成してください。

## 弱点ドメイン
{domains_text}

## 条件
- テーマ: AWSクラウドサービスとAI/ML（愛媛要素は不要）
- 形式: 4択問題（正解は1つのみ）
- 各ドメインからバランスよく出題すること
- 難易度: 基礎〜中級レベルで理解を深める内容にする

## 出力形式（JSON配列のみ返すこと）
[
  {{
    "text": "問題文",
    "choice_1": "選択肢1",
    "choice_2": "選択肢2",
    "choice_3": "選択肢3",
    "choice_4": "選択肢4",
    "correct_choice_index": 0,
    "explanation": "正解の解説（100-200文字）",
    "difficulty": "中級",
    "exam_domain": "ドメイン名"
  }}
]

注意:
- correct_choice_index は 0-3 の整数
- difficulty は "基礎", "中級", "上級" のいずれか
- exam_domain は弱点ドメインのいずれかを設定
- 実務で役立つ実践的な問題にすること"""

        try:
            from google.genai import types
            response = self._client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.8,
                    max_output_tokens=8192,
                    response_mime_type="application/json",
                ),
            )

            questions_data = self._parse_response(response.text)
            validated: list[Question] = []
            for q_data in questions_data:
                if self._validate(q_data):
                    domain = q_data.get("exam_domain", weak_areas[0].domain if weak_areas else "")
                    validated.append(self._to_question(q_data, domain))

            return validated[:total_count]

        except Exception as e:
            logger.error("バッチ問題生成失敗: %s", str(e))
            return []

    def _generate_for_area(
        self, weak_area: WeakArea, count: int
    ) -> list[Question]:
        """1つの弱点領域に対して問題を生成する。"""
        prompt = self._build_prompt(weak_area, count)

        from google.genai import types
        response = self._client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.8,
                max_output_tokens=4096,
                response_mime_type="application/json",
            ),
        )

        questions_data = self._parse_response(response.text)
        validated: list[Question] = []

        for q_data in questions_data:
            if self._validate(q_data):
                validated.append(self._to_question(q_data, weak_area.domain))

        return validated[:count]

    def _build_prompt(self, weak_area: WeakArea, count: int) -> str:
        """問題生成プロンプトを構築する。"""
        return f"""あなたはAWS認定資格の問題作成の専門家です。
以下の条件で{count}問の4択クイズ問題をJSON配列で生成してください。

## 条件
- 弱点ドメイン: {weak_area.domain}（誤答率: {weak_area.incorrect_rate:.1f}%）
- テーマ: AWSクラウドサービスとAI/ML（愛媛要素は不要）
- 形式: 4択問題（正解は1つのみ）
- 難易度: 誤答率が高いため基礎〜中級レベルで出題し、理解を深める内容にする
- 解説: 各問題に概念の説明を含めること

## 出力形式（JSON配列のみ返すこと）
[
  {{
    "text": "問題文",
    "choice_1": "選択肢1",
    "choice_2": "選択肢2",
    "choice_3": "選択肢3",
    "choice_4": "選択肢4",
    "correct_choice_index": 0,
    "explanation": "正解の解説（100-200文字）",
    "difficulty": "中級"
  }}
]

注意:
- correct_choice_index は 0-3 の整数
- difficulty は "基礎", "中級", "上級" のいずれか
- 実務で役立つ実践的な問題にすること
- 正解以外の選択肢も「もっともらしい」がなぜ不正解かわかるようにすること"""

    def _parse_response(self, text: str) -> list[dict]:
        """AIレスポンスからJSONを抽出する。"""
        # コードブロック内のJSONを探す
        json_match = re.search(
            r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL
        )
        json_str = json_match.group(1).strip() if json_match else text.strip()

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON解析失敗: {e}")

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
        raise ValueError("予期しないレスポンス形式")

    def _validate(self, q: dict) -> bool:
        """生成された問題をバリデーションする。"""
        required = ["text", "choice_1", "choice_2", "choice_3", "choice_4",
                    "correct_choice_index"]
        if not all(k in q for k in required):
            return False
        idx = q.get("correct_choice_index")
        if not isinstance(idx, int) or idx < 0 or idx > 3:
            return False
        if not q.get("text", "").strip():
            return False
        return True

    def _to_question(self, q_data: dict, domain: str) -> Question:
        """辞書をQuestionドメインオブジェクトに変換する。"""
        difficulty_str = q_data.get("difficulty", "中級")
        try:
            difficulty = Difficulty(difficulty_str)
        except ValueError:
            difficulty = Difficulty.INTERMEDIATE

        return Question(
            id=f"ai-{uuid.uuid4().hex[:12]}",
            course_id="ai-generated",
            text=q_data["text"],
            choice_1=q_data["choice_1"],
            choice_2=q_data["choice_2"],
            choice_3=q_data["choice_3"],
            choice_4=q_data["choice_4"],
            correct_choice_index=q_data["correct_choice_index"],
            ehime_trivia="",
            aws_ai_explanation=q_data.get("explanation", ""),
            difficulty=difficulty,
            exam_domain=domain,
        )
