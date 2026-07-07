"""
ステージテーマとシナリオ内容の一致性を検証する探索テスト

Property 1: Bug Condition - ステージテーマとシナリオ不一致検出

各問題のcourse_idに対応するステージテーマキーワードが、textフィールドの
シナリオ部分に含まれるかを検証する。

このテストは修正前コードで「失敗」することが期待される。
失敗は、バグの存在を確認するカウンターサンプルを提示する。

Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7
"""

from hypothesis import given, settings
from hypothesis.strategies import sampled_from

from app.data.seed_data import QUESTIONS, COURSES
from app.data.seed_data_extra import EXTRA_QUESTIONS
from app.data.seed_data_extra2 import EXTRA_QUESTIONS_2
from app.data.nanyo_questions_new import NANYO_QUESTIONS_NEW
from app.data.bunkazai_questions import BUNKAZAI_QUESTIONS
from app.data.extra_questions import EXTRA_QUESTIONS as EXTRA_QUESTIONS_3


# =============================================================================
# 全問題データの統合
# =============================================================================

ALL_QUESTIONS = (
    QUESTIONS
    + EXTRA_QUESTIONS
    + EXTRA_QUESTIONS_2
    + NANYO_QUESTIONS_NEW
)

# =============================================================================
# ステージテーママッピング（course_id → テーマ名・キーワード）
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
# ヘルパー関数
# =============================================================================


def extract_ehime_scenario(text: str) -> str:
    """問題文から愛媛シナリオ導入部分を抽出する。

    問題文は「[愛媛シナリオ]...[AWS設問]」の構造を持つ。
    AWS技術に関する質問部分の直前までをシナリオとして返す。

    シンプルなヒューリスティック: 「〜はどれですか？」「〜どれですか？」
    「〜何ですか？」等の設問パターンの直前までをシナリオ部分とする。
    """
    import re

    # AWS設問部分のパターン（質問文の開始を検出）
    # 典型パターン: 「AWSで〜」「この〜」「次の〜」「どの〜」
    patterns = [
        r"(AWS|Amazon|クラウド)で.*?(はどれですか|でしょうか|を選んでください)",
        r"(この|その|次の|どの).*?(はどれですか|でしょうか|を選んでください|ですか)",
    ]

    # 最初のAWS関連質問文の開始位置を見つける
    # 「AWSで」「AWSの」「Amazonの」等で始まる文を検出
    aws_question_markers = [
        "AWSで", "AWSの", "AWS で", "Amazonで", "クラウドで",
        "この仮想", "このサービス", "この概念", "この仕組み",
        "どのAWS", "最適なAWS", "適切なAWS",
    ]

    # テキスト全体から、後半のAWS設問部分を除いたシナリオ部分を抽出
    # 句読点で文を分割し、AWS技術キーワードが初出する文の直前まで取得
    sentences = re.split(r"[。．]", text)

    scenario_parts = []
    for sentence in sentences:
        # AWS設問の開始を検出（AWSサービス名や技術用語への問いかけ）
        is_aws_question = any(marker in sentence for marker in aws_question_markers)
        if is_aws_question and scenario_parts:
            # 既にシナリオ部分がある場合、AWS設問に入ったので終了
            break
        scenario_parts.append(sentence)

    # シナリオ部分が見つからない場合はテキスト全体を返す
    if not scenario_parts:
        return text

    return "。".join(scenario_parts)


def is_related_to_theme(scenario: str, stage_theme: dict) -> bool:
    """シナリオがステージテーマに関連するかを判定する。

    ステージテーマのキーワードリストのうち、少なくとも1つが
    シナリオ部分に含まれていればテーマに関連していると判定する。
    """
    keywords = stage_theme["keywords"]
    return any(keyword in scenario for keyword in keywords)


def is_bug_condition(question: dict) -> bool:
    """問題がバグ条件に該当するかを判定する。

    バグ条件: 問題文のシナリオ部分がステージテーマと不一致
    """
    course_id = question.get("course_id")
    if course_id is None or course_id not in STAGE_THEME_MAP:
        return False

    stage_theme = STAGE_THEME_MAP[course_id]
    scenario = extract_ehime_scenario(question["text"])
    return not is_related_to_theme(scenario, stage_theme)


# =============================================================================
# Property 1: Bug Condition - ステージテーマとシナリオ不一致検出
# =============================================================================

# テスト対象: テーママッピングが定義されているステージの問題のみ
QUESTIONS_WITH_THEME = [
    q for q in ALL_QUESTIONS
    if q.get("course_id") in STAGE_THEME_MAP
]


@settings(max_examples=len(QUESTIONS_WITH_THEME))
@given(question=sampled_from(QUESTIONS_WITH_THEME))
def test_stage_theme_scenario_alignment(question):
    """
    Feature: stage-theme-content-alignment, Property 1: Bug Condition

    ステージテーマとシナリオ不一致検出

    For any question assigned to a stage (via course_id), the text field's
    Ehime scenario introduction MUST contain at least one keyword related
    to the assigned stage's theme (tourist spot / cultural asset).

    This test is EXPECTED TO FAIL on unfixed code - failure confirms the
    bug exists (問題文のシナリオ部分がステージテーマと不一致).

    **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7**
    """
    course_id = question["course_id"]
    stage_theme = STAGE_THEME_MAP[course_id]
    scenario = extract_ehime_scenario(question["text"])

    assert is_related_to_theme(scenario, stage_theme), (
        f"\n{'='*60}\n"
        f"Bug Condition Detected!\n"
        f"{'='*60}\n"
        f"Question ID: {question['id']}\n"
        f"Course ID: {course_id}\n"
        f"Stage Theme: {stage_theme['name']}\n"
        f"Theme Keywords: {stage_theme['keywords']}\n"
        f"Scenario (extracted): {scenario[:200]}\n"
        f"Full text: {question['text'][:300]}\n"
        f"{'='*60}\n"
        f"問題文のシナリオ部分がステージテーマ「{stage_theme['name']}」と不一致です。\n"
        f"テーマキーワード {stage_theme['keywords']} のいずれもシナリオに含まれていません。"
    )
