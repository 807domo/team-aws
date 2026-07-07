"""
ステージテーマとシナリオ内容の不一致問題を全量特定するユーティリティスクリプト

探索テスト（tests/properties/test_stage_theme_alignment_exploration.py）で定義された
STAGE_THEME_MAP、extract_ehime_scenario()、is_related_to_theme()、is_bug_condition()
を使用して、全データファイルの不一致問題を特定・リスト化する。

使用方法:
  python scripts/identify_mismatches.py

出力:
  - ソースファイル別・ステージ別にグループ化された不一致問題リスト
  - 各問題のID、course_id、ステージテーマ、問題のあるキーワード/参照
"""

import sys
import os
import re
from collections import defaultdict

# プロジェクトルートをsys.pathに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.data.seed_data import QUESTIONS
from app.data.seed_data_extra import EXTRA_QUESTIONS
from app.data.seed_data_extra2 import EXTRA_QUESTIONS_2
from app.data.nanyo_questions_new import NANYO_QUESTIONS_NEW
from app.data.bunkazai_questions import BUNKAZAI_QUESTIONS
from app.data.extra_questions import EXTRA_QUESTIONS as EXTRA_QUESTIONS_3


# =============================================================================
# ステージテーママッピング（探索テストから転記）
# =============================================================================

STAGE_THEME_MAP = {
    # 南予（初級）
    "nanyo-stage-01": {
        "name": "宇和島城",
        "keywords": ["宇和島城", "天守", "宇和島藩", "藤堂高虎", "伊達", "勝山"],
    },
    "nanyo-stage-02": {
        "name": "遊子水荷浦の段畑",
        "keywords": ["段畑", "遊子", "水荷浦", "石垣", "だんばた"],
    },
    "nanyo-stage-03": {
        "name": "開明学校",
        "keywords": ["開明学校", "擬洋風", "校舎", "明治", "西予市"],
    },
    "nanyo-stage-04": {
        "name": "篠山の原生林",
        "keywords": ["篠山", "原生林", "自然林", "ブナ", "アケボノツツジ"],
    },
    "nanyo-stage-05": {
        "name": "内子座",
        "keywords": ["内子座", "芝居小屋", "回り舞台", "花道", "内子町", "大正"],
    },
    "nanyo-stage-06": {
        "name": "卯之町の町並み",
        "keywords": ["卯之町", "町並み", "伝統的建造物", "宿場町", "西予市", "重伝建"],
    },
    "nanyo-stage-07": {
        "name": "日土小学校",
        "keywords": ["日土小学校", "モダニズム", "松村正恒", "八幡浜"],
    },
    "nanyo-stage-08": {
        "name": "大洲城",
        "keywords": ["大洲城", "木造復元", "天守", "大洲市", "肱川"],
    },
    "nanyo-stage-09": {
        "name": "佐田岬灯台",
        "keywords": ["佐田岬", "灯台", "四国最西端", "半島", "伊方"],
    },
    "nanyo-stage-10": {
        "name": "天赦園",
        "keywords": ["天赦園", "庭園", "伊達家", "池泉回遊", "藤棚"],
    },
    "nanyo-stage-11": {
        "name": "明石寺",
        "keywords": ["明石寺", "四国霊場", "43番", "札所", "西予市"],
    },
    "nanyo-stage-12": {
        "name": "龍光寺",
        "keywords": ["龍光寺", "神仏習合", "41番", "札所", "宇和町"],
    },
    "nanyo-stage-13": {
        "name": "外泊石垣の里",
        "keywords": ["外泊", "石垣の里", "石垣集落", "愛南町"],
    },
    "nanyo-stage-14": {
        "name": "滑床渓谷",
        "keywords": ["滑床", "渓谷", "雪輪の滝", "松野町", "目黒"],
    },
    "nanyo-stage-15": {
        "name": "四万十川源流",
        "keywords": ["四万十川", "源流", "松野町", "清流"],
    },
    "nanyo-stage-16": {
        "name": "南楽園",
        "keywords": ["南楽園", "日本庭園", "宇和島"],
    },
    "nanyo-stage-17": {
        "name": "御荘湾サンゴ",
        "keywords": ["サンゴ", "御荘", "愛南町", "海中"],
    },
    "nanyo-stage-18": {
        "name": "肱川あらし",
        "keywords": ["肱川あらし", "肱川", "大洲", "気象", "霧"],
    },
    "nanyo-stage-19": {
        "name": "宇和島真珠",
        "keywords": ["真珠", "宇和島", "養殖"],
    },
    # 中予（中級）
    "chuyo-stage-01": {
        "name": "松山城",
        "keywords": ["松山城", "天守", "連立式", "勝山", "加藤嘉明"],
    },
    "chuyo-stage-02": {
        "name": "道後温泉本館",
        "keywords": ["道後温泉", "本館", "温泉", "坊っちゃん", "神の湯"],
    },
    "chuyo-stage-03": {
        "name": "石手寺",
        "keywords": ["石手寺", "二王門", "国宝", "51番", "札所"],
    },
    "chuyo-stage-04": {
        "name": "太山寺本堂",
        "keywords": ["太山寺", "本堂", "国宝", "52番"],
    },
    "chuyo-stage-05": {
        "name": "萬翠荘",
        "keywords": ["萬翠荘", "洋館", "大正", "久松定謨"],
    },
    "chuyo-stage-06": {
        "name": "伊佐爾波神社",
        "keywords": ["伊佐爾波", "神社", "八幡造", "道後"],
    },
    "chuyo-stage-07": {
        "name": "岩屋寺",
        "keywords": ["岩屋寺", "岩壁", "巨岩", "45番", "久万高原"],
    },
    "chuyo-stage-08": {
        "name": "砥部焼",
        "keywords": ["砥部焼", "磁器", "伝統工芸", "砥部町"],
    },
    "chuyo-stage-09": {
        "name": "湯築城跡",
        "keywords": ["湯築城", "河野氏", "城跡", "道後公園"],
    },
    "chuyo-stage-10": {
        "name": "子規堂",
        "keywords": ["子規堂", "正岡子規", "俳句", "子規"],
    },
    "chuyo-stage-11": {
        "name": "久万高原・面河渓",
        "keywords": ["久万高原", "面河渓", "渓谷", "面河"],
    },
    "chuyo-stage-12": {
        "name": "興居島船踊り",
        "keywords": ["興居島", "船踊り", "船踊"],
    },
    "chuyo-stage-13": {
        "name": "坊っちゃん列車",
        "keywords": ["坊っちゃん列車", "列車", "伊予鉄"],
    },
    "chuyo-stage-14": {
        "name": "愛媛県庁本館",
        "keywords": ["愛媛県庁", "県庁", "本館"],
    },
    "chuyo-stage-15": {
        "name": "松山総合公園",
        "keywords": ["松山総合公園", "総合公園", "展望台"],
    },
    "chuyo-stage-16": {
        "name": "石鎚山系（中予側）",
        "keywords": ["石鎚", "面河", "久万"],
    },
    # 東予（上級）
    "toyo-stage-01": {
        "name": "大山祇神社",
        "keywords": ["大山祇", "神社", "国宝", "甲冑", "大三島"],
    },
    "toyo-stage-02": {
        "name": "来島海峡大橋",
        "keywords": ["来島海峡", "大橋", "吊橋", "しまなみ"],
    },
    "toyo-stage-03": {
        "name": "別子銅山遺産",
        "keywords": ["別子銅山", "銅山", "東平", "マチュピチュ", "新居浜"],
    },
    "toyo-stage-04": {
        "name": "四国中央和紙",
        "keywords": ["和紙", "四国中央", "紙", "伝統"],
    },
    "toyo-stage-05": {
        "name": "西条うちぬき",
        "keywords": ["うちぬき", "西条", "名水", "自噴"],
    },
    "toyo-stage-06": {
        "name": "村上海賊ミュージアム",
        "keywords": ["村上海賊", "水軍", "ミュージアム", "能島"],
    },
    "toyo-stage-07": {
        "name": "旧広瀬邸",
        "keywords": ["広瀬邸", "広瀬", "住友", "新居浜"],
    },
    "toyo-stage-08": {
        "name": "石鎚山",
        "keywords": ["石鎚山", "石鎚", "西日本最高峰", "霊峰"],
    },
    "toyo-stage-09": {
        "name": "今治城",
        "keywords": ["今治城", "水城", "藤堂高虎", "今治市"],
    },
    "toyo-stage-10": {
        "name": "西条祭り",
        "keywords": ["西条祭り", "だんじり", "太鼓台", "西条市"],
    },
    "toyo-stage-11": {
        "name": "新居浜太鼓祭り",
        "keywords": ["新居浜", "太鼓祭り", "太鼓台"],
    },
    "toyo-stage-12": {
        "name": "耕三寺",
        "keywords": ["耕三寺", "西の日光", "生口島"],
    },
    "toyo-stage-13": {
        "name": "保国寺",
        "keywords": ["保国寺", "室町", "古刹"],
    },
    "toyo-stage-14": {
        "name": "今治タオル",
        "keywords": ["今治タオル", "タオル", "今治市", "繊維"],
    },
}


# =============================================================================
# ヘルパー関数（探索テストから転記）
# =============================================================================


def extract_ehime_scenario(text: str) -> str:
    """問題文から愛媛シナリオ導入部分を抽出する。"""
    aws_question_markers = [
        "AWSで", "AWSの", "AWS で", "Amazonで", "クラウドで",
        "この仮想", "このサービス", "この概念", "この仕組み",
        "どのAWS", "最適なAWS", "適切なAWS",
    ]

    sentences = re.split(r"[。．]", text)

    scenario_parts = []
    for sentence in sentences:
        is_aws_question = any(marker in sentence for marker in aws_question_markers)
        if is_aws_question and scenario_parts:
            break
        scenario_parts.append(sentence)

    if not scenario_parts:
        return text

    return "。".join(scenario_parts)


def is_related_to_theme(scenario: str, stage_theme: dict) -> bool:
    """シナリオがステージテーマに関連するかを判定する。"""
    keywords = stage_theme["keywords"]
    return any(keyword in scenario for keyword in keywords)


def is_bug_condition(question: dict) -> bool:
    """問題がバグ条件に該当するかを判定する。"""
    course_id = question.get("course_id")
    if course_id is None or course_id not in STAGE_THEME_MAP:
        return False

    stage_theme = STAGE_THEME_MAP[course_id]
    scenario = extract_ehime_scenario(question["text"])
    return not is_related_to_theme(scenario, stage_theme)


def find_problematic_references(text: str, course_id: str) -> list[str]:
    """問題文から、割り当てステージとは別のテーマへの参照を検出する。

    他ステージのキーワードや、一般的に無関係な参照を返す。
    """
    scenario = extract_ehime_scenario(text)
    problematic = []

    # 他ステージのキーワードが含まれていないか確認
    for other_course_id, theme_info in STAGE_THEME_MAP.items():
        if other_course_id == course_id:
            continue
        for keyword in theme_info["keywords"]:
            if keyword in scenario and len(keyword) >= 3:  # 短すぎるキーワードは除外
                problematic.append(
                    f"「{keyword}」({theme_info['name']}={other_course_id})"
                )

    # 一般的な無関係参照パターン
    generic_patterns = [
        ("愛媛マラソン", "スポーツイベント"),
        ("愛媛大学", "教育機関"),
        ("道の駅", "一般施設"),
        ("闘牛", "イベント"),
        ("水産養殖", "産業"),
        ("水産加工", "産業"),
        ("真珠選別", "産業"),
        ("水産研究", "研究機関"),
        ("観光牧場", "一般施設"),
        ("四国電力", "企業"),
        ("カルスト", "地形"),
    ]

    for pattern, category in generic_patterns:
        if pattern in scenario:
            problematic.append(f"「{pattern}」({category})")

    return problematic


# =============================================================================
# データソース定義
# =============================================================================

DATA_SOURCES = [
    ("app/data/seed_data.py", "QUESTIONS", QUESTIONS),
    ("app/data/seed_data_extra.py", "EXTRA_QUESTIONS", EXTRA_QUESTIONS),
    ("app/data/seed_data_extra2.py", "EXTRA_QUESTIONS_2", EXTRA_QUESTIONS_2),
    ("app/data/extra_questions.py", "EXTRA_QUESTIONS", EXTRA_QUESTIONS_3),
    ("app/data/bunkazai_questions.py", "BUNKAZAI_QUESTIONS", BUNKAZAI_QUESTIONS),
    ("app/data/nanyo_questions_new.py", "NANYO_QUESTIONS_NEW", NANYO_QUESTIONS_NEW),
]


# =============================================================================
# メイン処理
# =============================================================================


def main():
    print("=" * 80)
    print("ステージテーマとシナリオ内容の不一致問題 全量特定レポート")
    print("=" * 80)
    print()

    total_questions = 0
    total_mismatches = 0
    total_skipped = 0  # STAGE_THEME_MAPに無いcourse_idの問題

    # ファイル別集計
    file_results = {}

    for source_file, var_name, questions in DATA_SOURCES:
        file_mismatches = defaultdict(list)
        file_question_count = len(questions)
        file_mismatch_count = 0
        file_skipped = 0

        for q in questions:
            course_id = q.get("course_id")
            if course_id is None or course_id not in STAGE_THEME_MAP:
                file_skipped += 1
                continue

            if is_bug_condition(q):
                file_mismatch_count += 1
                stage_theme = STAGE_THEME_MAP[course_id]
                scenario = extract_ehime_scenario(q["text"])
                problematic_refs = find_problematic_references(q["text"], course_id)

                file_mismatches[course_id].append({
                    "id": q["id"],
                    "course_id": course_id,
                    "stage_theme": stage_theme["name"],
                    "theme_keywords": stage_theme["keywords"],
                    "scenario_excerpt": scenario[:150],
                    "problematic_references": problematic_refs,
                    "full_text_excerpt": q["text"][:200],
                })

        file_results[source_file] = {
            "var_name": var_name,
            "total": file_question_count,
            "mismatches": file_mismatch_count,
            "skipped": file_skipped,
            "details": dict(file_mismatches),
        }

        total_questions += file_question_count
        total_mismatches += file_mismatch_count
        total_skipped += file_skipped

    # === サマリー出力 ===
    print("【サマリー】")
    print(f"  全問題数: {total_questions}")
    print(f"  テーマ対象問題数: {total_questions - total_skipped}")
    print(f"  不一致問題数: {total_mismatches}")
    print(f"  テーママップ外問題数: {total_skipped}")
    print(f"  不一致率: {total_mismatches}/{total_questions - total_skipped} "
          f"({100*total_mismatches/(total_questions - total_skipped):.1f}%)" if (total_questions - total_skipped) > 0 else "")
    print()

    # === ファイル別詳細出力 ===
    for source_file, result in file_results.items():
        print("-" * 80)
        print(f"📁 {source_file} ({result['var_name']})")
        print(f"   問題数: {result['total']} | 不一致: {result['mismatches']} | "
              f"テーママップ外: {result['skipped']}")
        print("-" * 80)

        if result["mismatches"] == 0:
            print("   ✅ 不一致問題なし")
            print()
            continue

        # ステージ別にグループ化して出力
        for course_id in sorted(result["details"].keys()):
            items = result["details"][course_id]
            stage_theme = STAGE_THEME_MAP[course_id]
            print(f"\n  【{course_id}】テーマ: {stage_theme['name']}")
            print(f"  テーマキーワード: {stage_theme['keywords']}")
            print(f"  不一致問題数: {len(items)}")
            print()

            for item in items:
                print(f"    ❌ {item['id']}")
                print(f"       course_id: {item['course_id']}")
                print(f"       ステージテーマ: {item['stage_theme']}")
                if item["problematic_references"]:
                    print(f"       問題のある参照: {', '.join(item['problematic_references'])}")
                else:
                    print(f"       問題のある参照: (テーマキーワードが見つからない)")
                print(f"       シナリオ抜粋: {item['scenario_excerpt']}...")
                print()

        print()

    # === ステージ別集約 ===
    print("=" * 80)
    print("【ステージ別不一致集約】")
    print("=" * 80)

    stage_aggregation = defaultdict(list)
    for source_file, result in file_results.items():
        for course_id, items in result["details"].items():
            for item in items:
                stage_aggregation[course_id].append({
                    "source_file": source_file,
                    **item,
                })

    for course_id in sorted(stage_aggregation.keys()):
        items = stage_aggregation[course_id]
        stage_theme = STAGE_THEME_MAP[course_id]
        print(f"\n  {course_id} ({stage_theme['name']}): {len(items)}問")
        for item in items:
            refs = ', '.join(item['problematic_references']) if item['problematic_references'] else '(テーマキーワード未検出)'
            print(f"    - {item['id']} [{item['source_file']}] → {refs}")

    print()
    print("=" * 80)
    print(f"修正対象合計: {total_mismatches}問")
    print("=" * 80)


if __name__ == "__main__":
    main()
