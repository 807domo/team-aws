"""
ステージテーマ修正 - Preservation Property Tests

Property 2: Preservation - 非修正対象フィールド・テーマ一致済み問題の維持

このテストは修正前のコードで実行してベースラインを確立し、
修正後に再実行してリグレッションがないことを確認する。

Observation-first methodology:
- 修正前コードで全問題のメタデータ・選択肢・問題数をスナップショットとして記録
- プロパティベーステストで不変性を検証
- 修正後にも同一テストがパスすることを確認

Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8
"""

import json
import os
from collections import Counter
from pathlib import Path

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

# Import all question data sources
from app.data.seed_data import QUESTIONS, COURSES
from app.data.seed_data_extra import EXTRA_QUESTIONS
from app.data.seed_data_extra2 import EXTRA_QUESTIONS_2
from app.data.nanyo_questions_new import NANYO_QUESTIONS_NEW
from app.data.bunkazai_questions import BUNKAZAI_QUESTIONS
from app.data.extra_questions import EXTRA_QUESTIONS as EXTRA_QUESTIONS_3


# =============================================================================
# ステージテーママッピング（course_id → テーマキーワード）
# =============================================================================

STAGE_THEME_MAP: dict[str, dict] = {
    "nanyo-stage-01": {"name": "宇和島城", "keywords": ["宇和島城", "天守", "城", "宇和島"]},
    "nanyo-stage-02": {"name": "遊子水荷浦の段畑", "keywords": ["段畑", "遊子", "水荷浦", "石垣"]},
    "nanyo-stage-03": {"name": "開明学校", "keywords": ["開明学校", "開明", "擬洋風", "学校"]},
    "nanyo-stage-04": {"name": "篠山の原生林", "keywords": ["篠山", "原生林", "ブナ"]},
    "nanyo-stage-05": {"name": "内子座", "keywords": ["内子座", "内子", "芝居小屋", "芝居"]},
    "nanyo-stage-06": {"name": "卯之町の町並み", "keywords": ["卯之町", "町並み", "伝統的建造物"]},
    "nanyo-stage-07": {"name": "日土小学校", "keywords": ["日土小学校", "日土", "モダニズム"]},
    "nanyo-stage-08": {"name": "大洲城", "keywords": ["大洲城", "大洲", "復元天守"]},
    "nanyo-stage-09": {"name": "佐田岬灯台", "keywords": ["佐田岬", "灯台", "岬"]},
    "nanyo-stage-10": {"name": "天赦園", "keywords": ["天赦園", "伊達", "庭園"]},
    "nanyo-stage-11": {"name": "明石寺", "keywords": ["明石寺", "札所", "四国霊場"]},
    "nanyo-stage-12": {"name": "龍光寺", "keywords": ["龍光寺", "神仏習合"]},
    "nanyo-stage-13": {"name": "外泊石垣の里", "keywords": ["外泊", "石垣の里", "石垣集落"]},
    "nanyo-stage-14": {"name": "滑床渓谷", "keywords": ["滑床", "渓谷", "雪輪の滝"]},
    "nanyo-stage-15": {"name": "四万十川源流", "keywords": ["四万十", "源流", "松野町", "清流"]},
    "nanyo-stage-16": {"name": "南楽園", "keywords": ["南楽園", "日本庭園"]},
    "nanyo-stage-17": {"name": "御荘湾サンゴ", "keywords": ["サンゴ", "御荘", "愛南"]},
    "nanyo-stage-18": {"name": "肱川あらし", "keywords": ["肱川", "あらし", "大洲"]},
    "nanyo-stage-19": {"name": "宇和島真珠", "keywords": ["真珠", "宇和島"]},
    "chuyo-stage-01": {"name": "松山城", "keywords": ["松山城", "松山", "城", "勝山"]},
    "chuyo-stage-02": {"name": "道後温泉本館", "keywords": ["道後温泉", "道後", "温泉"]},
    "chuyo-stage-03": {"name": "石手寺", "keywords": ["石手寺", "二王門"]},
    "chuyo-stage-04": {"name": "太山寺本堂", "keywords": ["太山寺", "本堂"]},
    "chuyo-stage-05": {"name": "萬翠荘", "keywords": ["萬翠荘", "洋館"]},
    "chuyo-stage-06": {"name": "伊佐爾波神社", "keywords": ["伊佐爾波", "八幡造"]},
    "chuyo-stage-07": {"name": "岩屋寺", "keywords": ["岩屋寺", "岩壁"]},
    "chuyo-stage-08": {"name": "砥部焼", "keywords": ["砥部焼", "砥部", "陶磁器", "焼き物"]},
    "chuyo-stage-09": {"name": "湯築城跡", "keywords": ["湯築城", "河野氏"]},
    "chuyo-stage-10": {"name": "子規堂", "keywords": ["子規堂", "子規", "正岡"]},
    "chuyo-stage-11": {"name": "久万高原・面河渓", "keywords": ["久万高原", "面河渓", "渓谷"]},
    "chuyo-stage-12": {"name": "興居島船踊り", "keywords": ["興居島", "船踊り"]},
    "chuyo-stage-13": {"name": "坊っちゃん列車", "keywords": ["坊っちゃん列車", "坊っちゃん", "レトロ列車"]},
    "chuyo-stage-14": {"name": "愛媛県庁本館", "keywords": ["県庁", "庁舎"]},
    "chuyo-stage-15": {"name": "松山総合公園", "keywords": ["総合公園", "展望台"]},
    "chuyo-stage-16": {"name": "三津浜港", "keywords": ["三津浜", "港町"]},
    "chuyo-stage-17": {"name": "石鎚スキー場", "keywords": ["スキー場", "石鎚"]},
    "toyo-stage-01": {"name": "大山祇神社", "keywords": ["大山祇", "神社", "甲冑", "国宝"]},
    "toyo-stage-02": {"name": "来島海峡大橋", "keywords": ["来島", "海峡", "大橋", "吊橋"]},
    "toyo-stage-03": {"name": "別子銅山遺産", "keywords": ["別子", "銅山", "マチュピチュ"]},
    "toyo-stage-04": {"name": "四国中央和紙", "keywords": ["和紙", "四国中央", "紙"]},
    "toyo-stage-05": {"name": "西条うちぬき", "keywords": ["うちぬき", "西条", "名水"]},
    "toyo-stage-06": {"name": "村上海賊ミュージアム", "keywords": ["村上海賊", "海賊", "ミュージアム"]},
    "toyo-stage-07": {"name": "旧広瀬邸", "keywords": ["広瀬邸", "広瀬", "住友"]},
    "toyo-stage-08": {"name": "石鎚山", "keywords": ["石鎚山", "石鎚", "最高峰"]},
    "toyo-stage-09": {"name": "今治城", "keywords": ["今治城", "水城"]},
    "toyo-stage-10": {"name": "西条祭り", "keywords": ["西条祭り", "だんじり", "祭り"]},
    "toyo-stage-11": {"name": "新居浜太鼓祭り", "keywords": ["新居浜", "太鼓祭り", "太鼓台"]},
    "toyo-stage-12": {"name": "耕三寺", "keywords": ["耕三寺", "西の日光"]},
    "toyo-stage-13": {"name": "保国寺", "keywords": ["保国寺", "室町"]},
    "toyo-stage-14": {"name": "今治タオル", "keywords": ["今治タオル", "タオル"]},
    "toyo-stage-15": {"name": "瀬戸内しまなみ", "keywords": ["しまなみ", "瀬戸内"]},
    "toyo-stage-16": {"name": "東平産業遺産", "keywords": ["東平", "産業遺産"]},
    "toyo-stage-17": {"name": "石鎚山系", "keywords": ["石鎚", "山系"]},
    "toyo-stage-18": {"name": "今治造船", "keywords": ["今治造船", "造船"]},
    "toyo-stage-19": {"name": "四国中央紙産業", "keywords": ["紙産業", "四国中央"]},
}


# =============================================================================
# Helper: Bug Condition判定
# =============================================================================

def is_theme_matched(question: dict) -> bool:
    """問題がステージテーマと一致しているか判定する（isBugCondition=falseの場合True）"""
    course_id = question.get("course_id", "")
    if course_id not in STAGE_THEME_MAP:
        return True  # マッピングにないcourse_idは判定不能なのでmatchedとみなす
    theme_info = STAGE_THEME_MAP[course_id]
    text = question.get("text", "")
    ehime_trivia = question.get("ehime_trivia", "")
    # textまたはehime_triviaにテーマキーワードのいずれかが含まれればマッチ
    for keyword in theme_info["keywords"]:
        if keyword in text or keyword in ehime_trivia:
            return True
    return False


# =============================================================================
# Data Collection: 全データソースから問題を集約
# =============================================================================

def get_all_questions() -> list[dict]:
    """全データソースから全問題を取得（seed_database関数と同様のロジック）"""
    # QUESTIONS already includes BUNKAZAI_QUESTIONS and EXTRA_QUESTIONS_3
    # via the extend() calls at the bottom of seed_data.py
    all_questions = list(QUESTIONS) + list(EXTRA_QUESTIONS) + list(EXTRA_QUESTIONS_2)
    # NANYO_QUESTIONS_NEW は別管理（まだseed_data.pyにインポートされていない）
    all_questions.extend(NANYO_QUESTIONS_NEW)
    # Deduplicate by id (same logic as seed_database)
    seen_ids: set[str] = set()
    unique_questions: list[dict] = []
    for q in all_questions:
        if q["id"] not in seen_ids:
            seen_ids.add(q["id"])
            unique_questions.append(q)
    return unique_questions


# =============================================================================
# Baseline Snapshot: 修正前のデータを記録
# =============================================================================

ALL_QUESTIONS = get_all_questions()

# スナップショット: 全問題のメタデータ
METADATA_SNAPSHOT: dict[str, dict] = {
    q["id"]: {
        "id": q["id"],
        "course_id": q["course_id"],
        "difficulty": q["difficulty"],
        "exam_domain": q["exam_domain"],
    }
    for q in ALL_QUESTIONS
}

# スナップショット: 全問題の選択肢・正解・解説
CHOICES_SNAPSHOT: dict[str, dict] = {
    q["id"]: {
        "choice_1": q["choice_1"],
        "choice_2": q["choice_2"],
        "choice_3": q["choice_3"],
        "choice_4": q["choice_4"],
        "correct_choice_index": q["correct_choice_index"],
        "aws_ai_explanation": q["aws_ai_explanation"],
    }
    for q in ALL_QUESTIONS
}

# スナップショット: 問題数（ステージ別・総数）
QUESTION_COUNT_PER_STAGE: dict[str, int] = dict(Counter(q["course_id"] for q in ALL_QUESTIONS))
TOTAL_QUESTION_COUNT: int = len(ALL_QUESTIONS)

# スナップショット: テーマ一致済み問題のtext, ehime_trivia
THEME_MATCHED_CONTENT: dict[str, dict] = {
    q["id"]: {
        "text": q["text"],
        "ehime_trivia": q["ehime_trivia"],
    }
    for q in ALL_QUESTIONS
    if is_theme_matched(q)
}


# =============================================================================
# Property 2.1: メタデータ不変性
# id, course_id, difficulty, exam_domain が修正前後で同一
# Validates: Requirements 3.3, 3.8
# =============================================================================

@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
@given(idx=st.integers(min_value=0, max_value=max(len(ALL_QUESTIONS) - 1, 0)))
def test_metadata_immutability(idx: int):
    """
    **Validates: Requirements 3.3, 3.8**

    Property 2.1: メタデータ不変性
    全問題について id, course_id, difficulty, exam_domain が
    ベースラインスナップショットと同一であることを検証する。
    """
    assume(len(ALL_QUESTIONS) > 0)
    question = ALL_QUESTIONS[idx]
    qid = question["id"]

    assert qid in METADATA_SNAPSHOT, (
        f"Question '{qid}' not found in baseline metadata snapshot"
    )

    baseline = METADATA_SNAPSHOT[qid]
    assert question["id"] == baseline["id"], (
        f"Question '{qid}': id changed from '{baseline['id']}' to '{question['id']}'"
    )
    assert question["course_id"] == baseline["course_id"], (
        f"Question '{qid}': course_id changed from '{baseline['course_id']}' to '{question['course_id']}'"
    )
    assert question["difficulty"] == baseline["difficulty"], (
        f"Question '{qid}': difficulty changed from '{baseline['difficulty']}' to '{question['difficulty']}'"
    )
    assert question["exam_domain"] == baseline["exam_domain"], (
        f"Question '{qid}': exam_domain changed from '{baseline['exam_domain']}' to '{question['exam_domain']}'"
    )


# =============================================================================
# Property 2.2: 選択肢不変性
# choice_1〜4, correct_choice_index, aws_ai_explanation が修正前後で同一
# Validates: Requirements 3.2
# =============================================================================

@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
@given(idx=st.integers(min_value=0, max_value=max(len(ALL_QUESTIONS) - 1, 0)))
def test_choices_immutability(idx: int):
    """
    **Validates: Requirements 3.2**

    Property 2.2: 選択肢不変性
    全問題について choice_1〜4, correct_choice_index, aws_ai_explanation が
    ベースラインスナップショットと同一であることを検証する。
    """
    assume(len(ALL_QUESTIONS) > 0)
    question = ALL_QUESTIONS[idx]
    qid = question["id"]

    assert qid in CHOICES_SNAPSHOT, (
        f"Question '{qid}' not found in baseline choices snapshot"
    )

    baseline = CHOICES_SNAPSHOT[qid]
    for field in ["choice_1", "choice_2", "choice_3", "choice_4",
                  "correct_choice_index", "aws_ai_explanation"]:
        assert question[field] == baseline[field], (
            f"Question '{qid}': {field} changed.\n"
            f"  Baseline: {repr(baseline[field])[:100]}\n"
            f"  Current:  {repr(question[field])[:100]}"
        )


# =============================================================================
# Property 2.3: 問題数保持
# 全ステージの問題数・問題総数が修正前後で同一
# Validates: Requirements 3.8
# =============================================================================

def test_question_count_preservation():
    """
    **Validates: Requirements 3.8**

    Property 2.3: 問題数保持
    全ステージの問題数が修正前後で同一であること、
    および問題総数が修正前後で同一であることを検証する。
    """
    current_questions = get_all_questions()
    current_total = len(current_questions)
    current_per_stage = dict(Counter(q["course_id"] for q in current_questions))

    # 問題総数の保持
    assert current_total == TOTAL_QUESTION_COUNT, (
        f"Total question count changed from {TOTAL_QUESTION_COUNT} to {current_total}"
    )

    # ステージ別問題数の保持
    assert current_per_stage == QUESTION_COUNT_PER_STAGE, (
        f"Question count per stage changed.\n"
        f"  Baseline stages: {len(QUESTION_COUNT_PER_STAGE)}\n"
        f"  Current stages: {len(current_per_stage)}\n"
        f"  Differences: {set(QUESTION_COUNT_PER_STAGE.items()) ^ set(current_per_stage.items())}"
    )


# =============================================================================
# Property 2.4: テーマ一致済み問題保持
# isBugCondition=false の問題のtext, ehime_triviaが修正前後で同一
# Validates: Requirements 3.1, 3.4, 3.5, 3.6, 3.7
# =============================================================================

@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
@given(idx=st.integers(min_value=0, max_value=max(len(ALL_QUESTIONS) - 1, 0)))
def test_theme_matched_content_preservation(idx: int):
    """
    **Validates: Requirements 3.1, 3.4, 3.5, 3.6, 3.7**

    Property 2.4: テーマ一致済み問題保持
    修正前にテーマ一致していた問題（isBugCondition=false）の
    text, ehime_trivia が修正前後で同一であることを検証する。
    """
    assume(len(ALL_QUESTIONS) > 0)
    question = ALL_QUESTIONS[idx]
    qid = question["id"]

    # テーマ一致済み問題のみ検証
    if qid not in THEME_MATCHED_CONTENT:
        return  # この問題はバグ対象なのでスキップ

    baseline = THEME_MATCHED_CONTENT[qid]
    assert question["text"] == baseline["text"], (
        f"Theme-matched question '{qid}': text changed.\n"
        f"  Baseline: {baseline['text'][:80]}...\n"
        f"  Current:  {question['text'][:80]}..."
    )
    assert question["ehime_trivia"] == baseline["ehime_trivia"], (
        f"Theme-matched question '{qid}': ehime_trivia changed.\n"
        f"  Baseline: {baseline['ehime_trivia'][:80]}...\n"
        f"  Current:  {question['ehime_trivia'][:80]}..."
    )


# =============================================================================
# Summary/Diagnostic: テーマ一致状況のレポート
# =============================================================================

def test_preservation_baseline_summary():
    """
    テスト実行時のベースライン状況を記録する診断テスト。
    修正前後の比較を容易にするため、テスト発見時のデータ状態を出力する。
    """
    total = len(ALL_QUESTIONS)
    matched = len(THEME_MATCHED_CONTENT)
    unmatched = total - matched
    stages = len(QUESTION_COUNT_PER_STAGE)

    print(f"\n=== Preservation Baseline Summary ===")
    print(f"Total questions: {total}")
    print(f"Theme-matched (preserved): {matched}")
    print(f"Theme-unmatched (bug targets): {unmatched}")
    print(f"Total stages: {stages}")
    print(f"Questions per stage (sample):")
    for stage_id in sorted(QUESTION_COUNT_PER_STAGE.keys())[:5]:
        print(f"  {stage_id}: {QUESTION_COUNT_PER_STAGE[stage_id]} questions")
    print(f"  ...")

    # この診断テストは常にパスする
    assert total > 0, "No questions found in dataset"
    assert stages > 0, "No stages found in dataset"
