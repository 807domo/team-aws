"""
ehime_trivia ミスマッチ検出スクリプト

各問題のcourse_idに対応するステージテーマのキーワードが
ehime_triviaフィールドに含まれているかチェックする。
"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.data.seed_data import QUESTIONS
from app.data.seed_data_extra import EXTRA_QUESTIONS
from app.data.seed_data_extra2 import EXTRA_QUESTIONS_2
from app.data.nanyo_questions_new import NANYO_QUESTIONS_NEW
from app.data.bunkazai_questions import BUNKAZAI_QUESTIONS
from app.data.extra_questions import EXTRA_QUESTIONS as EXTRA_QUESTIONS_3

# =============================================================================
# ステージテーママッピング（test_stage_theme_alignment_exploration.py から転記）
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
# データソース定義
# =============================================================================

DATA_SOURCES = [
    ("app/data/seed_data.py", "QUESTIONS", QUESTIONS),
    ("app/data/seed_data_extra.py", "EXTRA_QUESTIONS", EXTRA_QUESTIONS),
    ("app/data/seed_data_extra2.py", "EXTRA_QUESTIONS_2", EXTRA_QUESTIONS_2),
    ("app/data/extra_questions.py", "EXTRA_QUESTIONS", EXTRA_QUESTIONS_3),
    ("app/data/nanyo_questions_new.py", "NANYO_QUESTIONS_NEW", NANYO_QUESTIONS_NEW),
    ("app/data/bunkazai_questions.py", "BUNKAZAI_QUESTIONS", BUNKAZAI_QUESTIONS),
]


def check_trivia_alignment(question: dict, source_file: str, source_var: str) -> dict | None:
    """ehime_triviaがステージテーマと一致しているかチェック。
    
    不一致の場合はミスマッチ情報を返す。一致の場合はNone。
    """
    course_id = question.get("course_id")
    if not course_id or course_id not in STAGE_THEME_MAP:
        return None

    ehime_trivia = question.get("ehime_trivia", "")
    if not ehime_trivia:
        return None

    stage_theme = STAGE_THEME_MAP[course_id]
    keywords = stage_theme["keywords"]

    # ehime_triviaにキーワードが1つでも含まれていればOK
    if any(keyword in ehime_trivia for keyword in keywords):
        return None

    # ミスマッチ検出
    return {
        "id": question.get("id", "unknown"),
        "course_id": course_id,
        "stage_name": stage_theme["name"],
        "keywords": keywords,
        "ehime_trivia": ehime_trivia,
        "source_file": source_file,
        "source_var": source_var,
    }


def main():
    mismatches = []
    total_checked = 0
    total_skipped = 0

    for source_file, source_var, questions in DATA_SOURCES:
        for q in questions:
            course_id = q.get("course_id")
            if not course_id or course_id not in STAGE_THEME_MAP:
                total_skipped += 1
                continue
            
            total_checked += 1
            result = check_trivia_alignment(q, source_file, source_var)
            if result:
                mismatches.append(result)

    # 結果表示
    print("=" * 70)
    print("ehime_trivia ミスマッチ検出結果")
    print("=" * 70)
    print(f"\n検査対象問題数: {total_checked}")
    print(f"スキップ数（テーマ未定義）: {total_skipped}")
    print(f"ミスマッチ数: {len(mismatches)}")
    print()

    if mismatches:
        print("-" * 70)
        print("ミスマッチ一覧:")
        print("-" * 70)
        for i, m in enumerate(mismatches, 1):
            print(f"\n[{i}] ID: {m['id']}")
            print(f"    ファイル: {m['source_file']} ({m['source_var']})")
            print(f"    course_id: {m['course_id']}")
            print(f"    ステージテーマ: {m['stage_name']}")
            print(f"    期待キーワード: {m['keywords']}")
            print(f"    ehime_trivia: {m['ehime_trivia'][:100]}...")
            print()
    else:
        print("✓ すべてのehime_triviaがステージテーマと一致しています。")

    return mismatches


if __name__ == "__main__":
    mismatches = main()
    sys.exit(1 if mismatches else 0)
