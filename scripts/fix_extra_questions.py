"""
seed_data_extra.py と seed_data_extra2.py のステージテーマ不一致問題を修正するスクリプト。

各問題のtextフィールドのシナリオ導入部分を、正しいステージテーマに合致する内容に書き換える。
AWS設問部分・選択肢・正解・解説・メタデータは一切変更しない。
"""

import sys
import os
import re

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


# =============================================================================
# ステージテーママッピング（identify_mismatches.pyから転記）
# =============================================================================

STAGE_THEME_MAP = {
    "nanyo-stage-01": {"name": "宇和島城", "keywords": ["宇和島城", "天守", "宇和島藩", "藤堂高虎", "伊達", "勝山"]},
    "nanyo-stage-02": {"name": "遊子水荷浦の段畑", "keywords": ["段畑", "遊子", "水荷浦", "石垣", "だんばた"]},
    "nanyo-stage-03": {"name": "開明学校", "keywords": ["開明学校", "擬洋風", "校舎", "明治", "西予市"]},
    "nanyo-stage-04": {"name": "篠山の原生林", "keywords": ["篠山", "原生林", "自然林", "ブナ", "アケボノツツジ"]},
    "nanyo-stage-05": {"name": "内子座", "keywords": ["内子座", "芝居小屋", "回り舞台", "花道", "内子町", "大正"]},
    "nanyo-stage-06": {"name": "卯之町の町並み", "keywords": ["卯之町", "町並み", "伝統的建造物", "宿場町", "西予市", "重伝建"]},
    "nanyo-stage-07": {"name": "日土小学校", "keywords": ["日土小学校", "モダニズム", "松村正恒", "八幡浜"]},
    "nanyo-stage-08": {"name": "大洲城", "keywords": ["大洲城", "木造復元", "天守", "大洲市", "肱川"]},
    "nanyo-stage-09": {"name": "佐田岬灯台", "keywords": ["佐田岬", "灯台", "四国最西端", "半島", "伊方"]},
    "nanyo-stage-10": {"name": "天赦園", "keywords": ["天赦園", "庭園", "伊達家", "池泉回遊", "藤棚"]},
    "nanyo-stage-11": {"name": "明石寺", "keywords": ["明石寺", "四国霊場", "43番", "札所", "西予市"]},
    "nanyo-stage-12": {"name": "龍光寺", "keywords": ["龍光寺", "神仏習合", "41番", "札所", "宇和町"]},
    "nanyo-stage-13": {"name": "外泊石垣の里", "keywords": ["外泊", "石垣の里", "石垣集落", "愛南町"]},
    "nanyo-stage-14": {"name": "滑床渓谷", "keywords": ["滑床", "渓谷", "雪輪の滝", "松野町", "目黒"]},
    "nanyo-stage-15": {"name": "四万十川源流", "keywords": ["四万十川", "源流", "松野町", "清流"]},
    "nanyo-stage-16": {"name": "南楽園", "keywords": ["南楽園", "日本庭園", "宇和島"]},
    "nanyo-stage-17": {"name": "御荘湾サンゴ", "keywords": ["サンゴ", "御荘", "愛南町", "海中"]},
    "nanyo-stage-18": {"name": "肱川あらし", "keywords": ["肱川あらし", "肱川", "大洲", "気象", "霧"]},
    "nanyo-stage-19": {"name": "宇和島真珠", "keywords": ["真珠", "宇和島", "養殖"]},
    "chuyo-stage-01": {"name": "松山城", "keywords": ["松山城", "天守", "連立式", "勝山", "加藤嘉明"]},
    "chuyo-stage-02": {"name": "道後温泉本館", "keywords": ["道後温泉", "本館", "温泉", "坊っちゃん", "神の湯"]},
    "chuyo-stage-03": {"name": "石手寺", "keywords": ["石手寺", "二王門", "国宝", "51番", "札所"]},
    "chuyo-stage-04": {"name": "太山寺本堂", "keywords": ["太山寺", "本堂", "国宝", "52番"]},
    "chuyo-stage-05": {"name": "萬翠荘", "keywords": ["萬翠荘", "洋館", "大正", "久松定謨"]},
    "chuyo-stage-06": {"name": "伊佐爾波神社", "keywords": ["伊佐爾波", "神社", "八幡造", "道後"]},
    "chuyo-stage-07": {"name": "岩屋寺", "keywords": ["岩屋寺", "岩壁", "巨岩", "45番", "久万高原"]},
    "chuyo-stage-08": {"name": "砥部焼", "keywords": ["砥部焼", "磁器", "伝統工芸", "砥部町"]},
    "chuyo-stage-09": {"name": "湯築城跡", "keywords": ["湯築城", "河野氏", "城跡", "道後公園"]},
    "chuyo-stage-10": {"name": "子規堂", "keywords": ["子規堂", "正岡子規", "俳句", "子規"]},
    "chuyo-stage-11": {"name": "久万高原・面河渓", "keywords": ["久万高原", "面河渓", "渓谷", "面河"]},
    "chuyo-stage-12": {"name": "興居島船踊り", "keywords": ["興居島", "船踊り", "船踊"]},
    "chuyo-stage-13": {"name": "坊っちゃん列車", "keywords": ["坊っちゃん列車", "列車", "伊予鉄"]},
    "chuyo-stage-14": {"name": "愛媛県庁本館", "keywords": ["愛媛県庁", "県庁", "本館"]},
    "chuyo-stage-15": {"name": "松山総合公園", "keywords": ["松山総合公園", "総合公園", "展望台"]},
    "chuyo-stage-16": {"name": "石鎚山系（中予側）", "keywords": ["石鎚", "面河", "久万"]},
    "toyo-stage-01": {"name": "大山祇神社", "keywords": ["大山祇", "神社", "国宝", "甲冑", "大三島"]},
    "toyo-stage-02": {"name": "来島海峡大橋", "keywords": ["来島海峡", "大橋", "吊橋", "しまなみ"]},
    "toyo-stage-03": {"name": "別子銅山遺産", "keywords": ["別子銅山", "銅山", "東平", "マチュピチュ", "新居浜"]},
    "toyo-stage-04": {"name": "四国中央和紙", "keywords": ["和紙", "四国中央", "紙", "伝統"]},
    "toyo-stage-05": {"name": "西条うちぬき", "keywords": ["うちぬき", "西条", "名水", "自噴"]},
    "toyo-stage-06": {"name": "村上海賊ミュージアム", "keywords": ["村上海賊", "水軍", "ミュージアム", "能島"]},
    "toyo-stage-07": {"name": "旧広瀬邸", "keywords": ["広瀬邸", "広瀬", "住友", "新居浜"]},
    "toyo-stage-08": {"name": "石鎚山", "keywords": ["石鎚山", "石鎚", "西日本最高峰", "霊峰"]},
    "toyo-stage-09": {"name": "今治城", "keywords": ["今治城", "水城", "藤堂高虎", "今治市"]},
    "toyo-stage-10": {"name": "西条祭り", "keywords": ["西条祭り", "だんじり", "太鼓台", "西条市"]},
    "toyo-stage-11": {"name": "新居浜太鼓祭り", "keywords": ["新居浜", "太鼓祭り", "太鼓台"]},
    "toyo-stage-12": {"name": "耕三寺", "keywords": ["耕三寺", "西の日光", "生口島"]},
    "toyo-stage-13": {"name": "保国寺", "keywords": ["保国寺", "室町", "古刹"]},
    "toyo-stage-14": {"name": "今治タオル", "keywords": ["今治タオル", "タオル", "今治市", "繊維"]},
}


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


# ステージテーマに基づくシナリオ導入テンプレート
# 各テーマについて、AWS技術の比喩として使えるシナリオパターンを複数用意
SCENARIO_TEMPLATES = {
    "chuyo-stage-01": [
        "松山城の天守閣から城下町を一望するように、{aws_intro}",
        "松山城は加藤嘉明が築城した連立式天守で知られています。{aws_intro}",
        "松山城の勝山に築かれた堅固な石垣のように、{aws_intro}",
        "松山城の天守へ続くロープウェイのように段階的にアクセスする仕組みで、{aws_intro}",
        "松山城の複数の櫓が連立して天守を守る構造のように、{aws_intro}",
    ],
    "chuyo-stage-02": [
        "道後温泉本館では多くの入浴客が同時に訪れます。{aws_intro}",
        "道後温泉の神の湯は3000年の歴史を持つ日本最古の温泉です。{aws_intro}",
        "道後温泉本館の坊っちゃんの間のように特別なアクセスを管理する仕組みで、{aws_intro}",
        "道後温泉本館の湯が絶え間なく湧き出すように、{aws_intro}",
        "道後温泉本館の改修工事中も営業を継続したように、{aws_intro}",
    ],
    "chuyo-stage-03": [
        "石手寺の国宝・二王門をくぐるように認証を通過する仕組みで、{aws_intro}",
        "石手寺は四国霊場第51番札所として巡礼者を迎え入れています。{aws_intro}",
        "石手寺の国宝級の文化財を守るように、{aws_intro}",
        "石手寺の参道を通って本堂へ至るように段階的に処理する仕組みで、{aws_intro}",
        "石手寺の境内に点在する文化財のように分散配置された構成で、{aws_intro}",
    ],
    "chuyo-stage-04": [
        "太山寺本堂は国宝に指定された鎌倉時代の建築です。{aws_intro}",
        "太山寺の国宝本堂を守る堅固な構造のように、{aws_intro}",
        "四国霊場第52番札所・太山寺の参拝者管理システムを構築する際、{aws_intro}",
        "太山寺本堂の荘厳な空間を維持するように、{aws_intro}",
        "太山寺の長い歴史を記録し保存するように、{aws_intro}",
    ],
    "chuyo-stage-05": [
        "萬翠荘は大正時代に建てられたフランス風洋館です。{aws_intro}",
        "萬翠荘の優雅な洋館建築を維持管理するように、{aws_intro}",
        "久松定謨が建てた萬翠荘のように格式高い設計で、{aws_intro}",
        "大正ロマンを感じる萬翠荘の展示品を管理するシステムで、{aws_intro}",
        "萬翠荘の多彩な展覧会運営のように柔軟な対応が求められる場面で、{aws_intro}",
    ],
    "chuyo-stage-06": [
        "伊佐爾波神社は道後に鎮座する八幡造の社殿で知られています。{aws_intro}",
        "道後の伊佐爾波神社の135段の石段を上るように段階的に処理する仕組みで、{aws_intro}",
        "伊佐爾波神社の八幡造の社殿のように重層的な構造で、{aws_intro}",
        "伊佐爾波神社の祭礼を円滑に運営するシステムで、{aws_intro}",
        "道後の伊佐爾波神社参拝者の情報を管理する際、{aws_intro}",
    ],
    "chuyo-stage-07": [
        "岩屋寺は久万高原の巨岩に抱かれた札所です。{aws_intro}",
        "四国霊場第45番札所・岩屋寺の岩壁のように堅固な基盤で、{aws_intro}",
        "久万高原の岩屋寺は巨岩の中に本堂が建つ独特の景観を持ちます。{aws_intro}",
        "岩屋寺の険しい参道を登る巡礼者の安全を管理するシステムで、{aws_intro}",
        "岩屋寺の巨岩が自然の要塞となるように、{aws_intro}",
    ],
    "chuyo-stage-08": [
        "砥部焼は愛媛の伝統工芸品で白磁に藍色の模様が特徴です。{aws_intro}",
        "砥部焼の窯元が作品を管理するシステムで、{aws_intro}",
        "砥部町の伝統工芸・砥部焼のECサイトを構築する際、{aws_intro}",
        "砥部焼の磁器のように精密で美しい設計で、{aws_intro}",
        "砥部焼の窯元100軒が協力して運営するプラットフォームで、{aws_intro}",
    ],
    "chuyo-stage-09": [
        "湯築城跡は河野氏の居城として道後公園に遺構が残ります。{aws_intro}",
        "道後公園の湯築城跡のように歴史データを層状に保存する仕組みで、{aws_intro}",
        "湯築城は河野氏が築いた中世の城郭です。{aws_intro}",
        "湯築城跡の発掘調査データを管理するシステムで、{aws_intro}",
        "道後公園内の湯築城跡の遺構を記録・公開するシステムで、{aws_intro}",
    ],
    "chuyo-stage-10": [
        "子規堂は正岡子規の生家跡に建つ記念堂です。{aws_intro}",
        "正岡子規が詠んだ俳句のように簡潔で効率的な設計で、{aws_intro}",
        "子規堂に保存された俳句資料をデジタル管理するシステムで、{aws_intro}",
        "正岡子規の俳句革新のように、従来の方法を刷新するアプローチで、{aws_intro}",
        "子規堂の展示資料を効率的に管理・公開するシステムで、{aws_intro}",
    ],
    "chuyo-stage-11": [
        "久万高原の面河渓は四国最大の渓谷として知られています。{aws_intro}",
        "面河渓の清流のようにデータが途切れなく流れる仕組みで、{aws_intro}",
        "久万高原町の面河渓では環境モニタリングが行われています。{aws_intro}",
        "面河渓の渓谷のように深く複雑なデータを扱うシステムで、{aws_intro}",
        "久万高原の自然環境を守るモニタリングシステムで、{aws_intro}",
    ],
    "chuyo-stage-12": [
        "興居島の船踊りは海上で行われる伝統芸能です。{aws_intro}",
        "興居島の船踊りのように複数の要素が連携する仕組みで、{aws_intro}",
        "松山沖の興居島では船踊りという独特の伝統行事が伝わっています。{aws_intro}",
        "興居島の船踊りの公演情報を管理するシステムで、{aws_intro}",
        "興居島の船踊り保存会がデジタルアーカイブを構築する際、{aws_intro}",
    ],
    "chuyo-stage-13": [
        "坊っちゃん列車は松山市内を走る観光列車です。{aws_intro}",
        "伊予鉄道の坊っちゃん列車の運行管理のように、{aws_intro}",
        "坊っちゃん列車が決まったルートを正確に走るように、{aws_intro}",
        "伊予鉄の坊っちゃん列車の予約システムを構築する際、{aws_intro}",
        "坊っちゃん列車の運行スケジュールを最適化するシステムで、{aws_intro}",
    ],
    "chuyo-stage-14": [
        "愛媛県庁本館は昭和初期の近代建築として知られています。{aws_intro}",
        "愛媛県庁本館の行政機能を支えるシステムのように、{aws_intro}",
        "県庁本館で県の行政データを一元管理するように、{aws_intro}",
        "愛媛県庁本館の建築的価値を記録・保存するシステムで、{aws_intro}",
        "愛媛県庁の業務を効率化するデジタル基盤で、{aws_intro}",
    ],
    "chuyo-stage-15": [
        "松山総合公園の展望台からは松山市街を360度見渡せます。{aws_intro}",
        "松山総合公園のように市民に広く開かれたプラットフォームで、{aws_intro}",
        "松山総合公園の展望台から全体を見渡すように、{aws_intro}",
        "松山総合公園の来園者情報を管理するシステムで、{aws_intro}",
        "松山総合公園の多目的な施設管理のように、{aws_intro}",
    ],
    "chuyo-stage-16": [
        "石鎚山系の面河渓谷は中予側からのアクセスで人気です。{aws_intro}",
        "石鎚山の久万高原側登山口から山頂を目指すように、{aws_intro}",
        "石鎚山系の面河ルートは自然豊かな登山道です。{aws_intro}",
        "石鎚の面河側の自然環境を監視するシステムで、{aws_intro}",
        "久万高原から石鎚山へ至るルートの安全管理で、{aws_intro}",
    ],
    "toyo-stage-01": [
        "大山祇神社は大三島に鎮座し国宝の甲冑を多数所蔵しています。{aws_intro}",
        "大三島の大山祇神社が国宝級の文化財を守るように、{aws_intro}",
        "大山祇神社の国宝甲冑コレクションを管理するシステムで、{aws_intro}",
        "大山祇神社の境内のように神聖で堅固な環境を構築する際、{aws_intro}",
        "大三島の大山祇神社参拝者の情報を分析するシステムで、{aws_intro}",
    ],
    "toyo-stage-02": [
        "来島海峡大橋はしまなみ海道を代表する世界初の三連吊橋です。{aws_intro}",
        "しまなみ海道の来島海峡大橋のように複数拠点を接続する設計で、{aws_intro}",
        "来島海峡大橋を渡るサイクリストの情報を管理するシステムで、{aws_intro}",
        "しまなみ海道の来島海峡大橋が島々を結ぶように、{aws_intro}",
        "来島海峡大橋の構造モニタリングシステムを構築する際、{aws_intro}",
    ],
    "toyo-stage-03": [
        "別子銅山は新居浜の産業遺産で東洋のマチュピチュと呼ばれます。{aws_intro}",
        "別子銅山の東平エリアに残る産業遺産のように、{aws_intro}",
        "新居浜の別子銅山遺産をデジタルアーカイブ化するシステムで、{aws_intro}",
        "別子銅山の坑道のように階層的にデータを管理する仕組みで、{aws_intro}",
        "別子銅山の採掘データを長期保存するシステムで、{aws_intro}",
    ],
    "toyo-stage-04": [
        "四国中央市は和紙の生産量日本一を誇る紙の町です。{aws_intro}",
        "四国中央和紙の伝統技術を記録するシステムで、{aws_intro}",
        "四国中央市の製紙工場のように大量のデータを処理する仕組みで、{aws_intro}",
        "四国中央和紙の薄くて丈夫な特性のように効率的な設計で、{aws_intro}",
        "四国中央市の紙産業データを管理するシステムで、{aws_intro}",
    ],
    "toyo-stage-05": [
        "西条市のうちぬきは地下水が自噴する名水百選の湧水です。{aws_intro}",
        "西条うちぬきのように絶え間なくデータが流れる仕組みで、{aws_intro}",
        "西条市の名水うちぬきの水質を監視するシステムで、{aws_intro}",
        "西条うちぬきが自噴するように自動的にリソースを提供する仕組みで、{aws_intro}",
        "西条市のうちぬき名水を活用した事業のシステムで、{aws_intro}",
    ],
    "toyo-stage-06": [
        "村上海賊ミュージアムは能島村上水軍の歴史を伝える博物館です。{aws_intro}",
        "村上海賊が瀬戸内海を制したように、{aws_intro}",
        "村上海賊ミュージアムの展示資料をデジタル管理するシステムで、{aws_intro}",
        "能島の村上水軍が海上交通を管理したように、{aws_intro}",
        "村上海賊ミュージアムの来館者データを分析するシステムで、{aws_intro}",
    ],
    "toyo-stage-07": [
        "旧広瀬邸は新居浜の住友ゆかりの近代和風建築です。{aws_intro}",
        "新居浜の旧広瀬邸が住友の歴史を伝えるように、{aws_intro}",
        "旧広瀬邸の建築資料をデジタルアーカイブ化するシステムで、{aws_intro}",
        "広瀬宰平が住友の近代化を推進したように、{aws_intro}",
        "新居浜の旧広瀬邸の文化財保護システムで、{aws_intro}",
    ],
    "toyo-stage-08": [
        "石鎚山は西日本最高峰の霊峰として信仰を集めています。{aws_intro}",
        "霊峰石鎚山の頂を目指すように段階的にスケールする仕組みで、{aws_intro}",
        "石鎚山の登山者安全管理システムを構築する際、{aws_intro}",
        "西日本最高峰・石鎚山の気象観測データを管理するシステムで、{aws_intro}",
        "石鎚山の険しい鎖場のように厳格なアクセス制御で、{aws_intro}",
    ],
    "toyo-stage-09": [
        "今治城は藤堂高虎が築いた日本屈指の水城です。{aws_intro}",
        "今治城の堀に海水を引き込む水城のような独自設計で、{aws_intro}",
        "今治市の今治城の来城者管理システムで、{aws_intro}",
        "今治城が瀬戸内海の交通を見渡したように、{aws_intro}",
        "藤堂高虎が築いた今治城の堅固な設計のように、{aws_intro}",
    ],
    "toyo-stage-10": [
        "西条祭りは西条市で毎年開催されるだんじり祭りです。{aws_intro}",
        "西条祭りの太鼓台が力強く練り歩くように、{aws_intro}",
        "西条市のだんじり祭りの運営情報を管理するシステムで、{aws_intro}",
        "西条祭りで多数のだんじりが同時に動くように並列処理する仕組みで、{aws_intro}",
        "西条祭りの太鼓台の配置を最適化するシステムで、{aws_intro}",
    ],
    "toyo-stage-11": [
        "新居浜太鼓祭りは豪華絢爛な太鼓台で知られる祭りです。{aws_intro}",
        "新居浜の太鼓祭りで多数の太鼓台がかきくらべするように、{aws_intro}",
        "新居浜太鼓祭りの運営システムを構築する際、{aws_intro}",
        "新居浜市の太鼓祭りの映像配信システムで、{aws_intro}",
        "新居浜太鼓祭りの太鼓台が力を競い合うように、{aws_intro}",
    ],
    "toyo-stage-12": [
        "耕三寺は生口島にある西の日光と呼ばれる寺院です。{aws_intro}",
        "耕三寺の精巧な建築のように精密な設計で、{aws_intro}",
        "生口島の耕三寺の文化財を管理するシステムで、{aws_intro}",
        "西の日光と称される耕三寺の荘厳な伽藍のように、{aws_intro}",
        "耕三寺の未来心の丘を訪れる観光客の情報管理で、{aws_intro}",
    ],
    "toyo-stage-13": [
        "保国寺は室町時代創建の古刹として静かに歴史を刻んでいます。{aws_intro}",
        "室町時代から続く保国寺の古刹のように長期的に安定した設計で、{aws_intro}",
        "保国寺の文化財保存データを管理するシステムで、{aws_intro}",
        "保国寺の静寂な境内のようにセキュアな環境で、{aws_intro}",
        "保国寺の古い仏像や建築資料をデジタルアーカイブ化する際、{aws_intro}",
    ],
    "toyo-stage-14": [
        "今治タオルは今治市の高品質な繊維産業ブランドです。{aws_intro}",
        "今治タオルの厳しい品質基準のように確実な仕組みで、{aws_intro}",
        "今治市のタオル工場の生産管理システムで、{aws_intro}",
        "今治タオルの繊維のように細かく織り込まれた設計で、{aws_intro}",
        "今治タオルブランドのECサイトを構築する際、{aws_intro}",
    ],
    "nanyo-stage-15": [
        "四万十川の源流は松野町の森深くに位置しています。{aws_intro}",
        "四万十川源流の清流のようにクリーンなデータフローで、{aws_intro}",
        "松野町の四万十川源流域の環境を監視するシステムで、{aws_intro}",
        "四万十川が源流から大海へ流れるようにデータが処理される仕組みで、{aws_intro}",
        "四万十川源流の清流を守るモニタリングシステムで、{aws_intro}",
    ],
    "nanyo-stage-16": [
        "南楽園は宇和島にある日本庭園で四季の花が楽しめます。{aws_intro}",
        "南楽園の池泉回遊式庭園のように全体を巡回する仕組みで、{aws_intro}",
        "宇和島の南楽園の来園者管理システムで、{aws_intro}",
        "南楽園の日本庭園が四季折々の美しさを見せるように、{aws_intro}",
        "南楽園の広大な庭園を効率的に管理するシステムで、{aws_intro}",
    ],
    "nanyo-stage-17": [
        "御荘湾のサンゴは愛南町の海中に広がる貴重な生態系です。{aws_intro}",
        "愛南町の御荘湾に生息するサンゴの観察データを管理するシステムで、{aws_intro}",
        "御荘湾のサンゴ群落のように多様な要素が共存する環境で、{aws_intro}",
        "愛南町の海中サンゴのモニタリングシステムを構築する際、{aws_intro}",
        "御荘湾のサンゴ保護活動のデータを管理するシステムで、{aws_intro}",
    ],
    "nanyo-stage-18": [
        "肱川あらしは大洲市で冬に発生する霧の気象現象です。{aws_intro}",
        "肱川の霧が大洲盆地から海へ流れ出すように、{aws_intro}",
        "大洲の肱川あらしの気象観測データを分析するシステムで、{aws_intro}",
        "肱川あらしという独特の気象現象を監視するシステムで、{aws_intro}",
        "大洲市の肱川沿いで観測される霧のデータを管理する仕組みで、{aws_intro}",
    ],
    "nanyo-stage-19": [
        "宇和島真珠は養殖技術で育まれる高品質な真珠です。{aws_intro}",
        "宇和島の真珠養殖のように丁寧に品質を管理する仕組みで、{aws_intro}",
        "宇和島市の真珠養殖データを管理するシステムで、{aws_intro}",
        "宇和島真珠が時間をかけて美しく育つように、{aws_intro}",
        "宇和島の養殖真珠の品質管理システムで、{aws_intro}",
    ],
}


def extract_aws_question_part(text: str) -> str:
    """問題文からAWS設問部分を抽出する（シナリオ以降の部分）。"""
    aws_question_markers = [
        "AWSで", "AWSの", "AWS で", "Amazonで", "クラウドで",
        "この仮想", "このサービス", "この概念", "この仕組み",
        "どのAWS", "最適なAWS", "適切なAWS",
        "最も適切な", "正しいもの", "正しい説明",
        "最も重要な", "組み合わせはどれ", "はどれですか",
        "どれですか", "として正しい", "として最も",
        "サービスはどれ", "ものはどれ", "設計として",
        "アプローチとして", "戦略として", "方式はどれ",
        "機能はどれ", "利点はどれ", "利点として",
        "目的はどれ", "目的として", "役割として",
        "SageMakerで", "Bedrockで", "Lambdaの",
        "IAMで", "S3の", "EC2の", "VPCで", "CloudFormation",
    ]

    sentences = re.split(r"[。．]", text)

    # Find where the AWS question starts
    for i, sentence in enumerate(sentences):
        if i == 0:
            continue
        is_aws_question = any(marker in sentence for marker in aws_question_markers)
        if is_aws_question:
            aws_part = "。".join(sentences[i:])
            if not aws_part.endswith("？") and not aws_part.endswith("?"):
                aws_part = aws_part.rstrip("。") + "？" if text.endswith("？") else aws_part
            return aws_part

    # If no clear AWS question marker found, try to find by question pattern
    for i, sentence in enumerate(sentences):
        if i == 0:
            continue
        if "？" in sentence or "?" in sentence or "どれ" in sentence:
            aws_part = "。".join(sentences[i:])
            return aws_part

    # Fallback: return everything after first sentence
    if len(sentences) > 1:
        return "。".join(sentences[1:])
    return text


def generate_fixed_text(question: dict, template_counter: dict) -> str:
    """不一致問題のtextフィールドを修正する。"""
    course_id = question["course_id"]
    original_text = question["text"]

    if course_id not in SCENARIO_TEMPLATES:
        return original_text

    templates = SCENARIO_TEMPLATES[course_id]

    # Use a counter to cycle through templates for variety
    if course_id not in template_counter:
        template_counter[course_id] = 0
    idx = template_counter[course_id] % len(templates)
    template_counter[course_id] += 1

    template = templates[idx]

    # Extract AWS question part from original text
    aws_part = extract_aws_question_part(original_text)

    # Build new text: scenario intro (from template) + AWS question
    new_text = template.format(aws_intro=aws_part)

    return new_text


def generate_fixed_trivia(question: dict) -> str | None:
    """ehime_triviaがテーマと不一致の場合に修正する。Noneなら変更不要。"""
    course_id = question.get("course_id")
    trivia = question.get("ehime_trivia", "")

    if not course_id or course_id not in STAGE_THEME_MAP:
        return None

    stage_theme = STAGE_THEME_MAP[course_id]
    if is_related_to_theme(trivia, stage_theme):
        return None  # Already matches

    # Generate a new trivia based on stage theme
    theme_name = stage_theme["name"]
    trivia_templates = {
        "chuyo-stage-01": "松山城は加藤嘉明が1602年に築城を開始した現存12天守の一つ。連立式天守は日本で唯一の形式で、標高132mの勝山に建つ姿は松山のシンボルです。",
        "chuyo-stage-02": "道後温泉本館は3000年の歴史を持つ日本最古級の温泉施設。1894年に建てられた現在の建物は国の重要文化財に指定されています。",
        "chuyo-stage-03": "石手寺は四国霊場第51番札所で、国宝の二王門は鎌倉時代の建築。境内には多くの文化財が残り、年間約50万人が参拝します。",
        "chuyo-stage-04": "太山寺本堂は鎌倉時代の建築で国宝に指定。四国霊場第52番札所として多くの遍路が訪れる古刹です。",
        "chuyo-stage-05": "萬翠荘は1922年に旧松山藩主の子孫・久松定謨が建てたフランス・ルネサンス様式の洋館。国の重要文化財に指定されています。",
        "chuyo-stage-06": "伊佐爾波神社は道後温泉近くに鎮座する八幡造の神社。135段の石段の上に社殿が建ち、全国に3例しかない八幡造の社殿は重要文化財です。",
        "chuyo-stage-07": "岩屋寺は四国霊場第45番札所で、久万高原の巨岩の中に本堂が建つ独特の景観が特徴。大師堂は国の重要文化財に指定されています。",
        "chuyo-stage-08": "砥部焼は約240年の歴史を持つ愛媛県の伝統工芸品。白磁に呉須（藍色）の手描き模様が特徴で、約100の窯元が砥部町で活動しています。",
        "chuyo-stage-09": "湯築城跡は道後公園内に残る中世城郭の遺構。河野氏の居城として約250年間使用され、現在は国の史跡に指定されています。",
        "chuyo-stage-10": "子規堂は俳人・正岡子規の生家跡に建てられた記念堂。子規が少年時代を過ごした住居が復元され、直筆の俳句や遺品が展示されています。",
        "chuyo-stage-11": "面河渓は石鎚山の南麓に位置する四国最大の渓谷。澄んだ清流と奇岩が織りなす景観は国の名勝に指定されています。",
        "chuyo-stage-12": "興居島の船踊りは松山沖の興居島に伝わる海上の伝統芸能。漁船の上で踊る独特の舞は県の無形民俗文化財に指定されています。",
        "chuyo-stage-13": "坊っちゃん列車は夏目漱石の小説に登場する汽車を復元した伊予鉄道の観光列車。レトロな外観で松山市内を運行し、観光客に人気です。",
        "chuyo-stage-14": "愛媛県庁本館は1929年竣工の近代建築で、ドーム型屋根が特徴。現役の県庁舎として日本最古級の建物の一つです。",
        "chuyo-stage-15": "松山総合公園は松山市の高台に位置する都市公園。展望台からは松山平野と瀬戸内海を360度見渡すことができます。",
        "chuyo-stage-16": "石鎚山系は中予側の面河渓谷から久万高原を経てアクセスできます。ブナの原生林や高山植物が豊富な自然の宝庫です。",
    }
    trivia_templates.update({
        "toyo-stage-01": "大山祇神社は大三島に鎮座し、全国の山祇神社・三島神社の総本社。国宝・重要文化財の甲冑の約4割を所蔵する武具の宝庫です。",
        "toyo-stage-02": "来島海峡大橋は全長4,105mの世界初の三連吊橋。しまなみ海道の一部として今治市と大島を結び、自転車でも渡れます。",
        "toyo-stage-03": "別子銅山は1691年から283年間採掘された銅山。新居浜市の東平エリアは「東洋のマチュピチュ」と呼ばれる産業遺産です。",
        "toyo-stage-04": "四国中央市は紙・パルプ産業の集積地で、紙製品出荷額日本一。伝統的な手漉き和紙の技術も受け継がれています。",
        "toyo-stage-05": "西条うちぬきは市内に約3000本ある自噴井の総称。名水百選にも選ばれた清冽な水は生活用水や農業用水に利用されています。",
        "toyo-stage-06": "村上海賊ミュージアムは今治市にある能島村上水軍の歴史を伝える博物館。瀬戸内海の海上交通を支配した水軍の遺品を展示しています。",
        "toyo-stage-07": "旧広瀬邸は新居浜市にある住友ゆかりの近代和風建築。別子銅山の近代化に貢献した広瀬宰平の旧宅で、重要文化財に指定されています。",
        "toyo-stage-08": "石鎚山は標高1,982mの西日本最高峰。霊峰として古くから山岳信仰の対象で、毎年多くの登山者が鎖場に挑みます。",
        "toyo-stage-09": "今治城は藤堂高虎が1602年に築いた日本三大水城の一つ。堀に海水を引き込む独特の構造で、今治市のシンボルです。",
        "toyo-stage-10": "西条祭りは毎年10月に行われる四国最大級の祭り。約150台のだんじり・太鼓台が練り歩き、加茂川の川入りは圧巻です。",
        "toyo-stage-11": "新居浜太鼓祭りは毎年10月に開催される四国三大祭りの一つ。金糸で刺繍された豪華な太鼓台が街を練り歩きます。",
        "toyo-stage-12": "耕三寺は生口島にある「西の日光」と呼ばれる寺院。日光東照宮をはじめ各地の名建築を模した堂塔が立ち並びます。",
        "toyo-stage-13": "保国寺は室町時代に創建された古刹。静かな山間に佇む境内には歴史ある仏像や建築が残されています。",
        "toyo-stage-14": "今治タオルは今治市で120年以上の歴史を持つ繊維産業ブランド。厳しい品質基準「5秒ルール」で知られる高品質なタオルです。",
        "nanyo-stage-15": "四万十川の源流は松野町の不入山にあります。日本最後の清流と呼ばれる四万十川の最上流部で、豊かな自然が残されています。",
        "nanyo-stage-16": "南楽園は宇和島市にある日本庭園で、池泉回遊式の広大な園内には四季の花々が咲き誇ります。",
        "nanyo-stage-17": "御荘湾は愛南町にあるサンゴの北限域の一つ。暖流の影響で約150種のサンゴが生息し、海中観光も人気です。",
        "nanyo-stage-18": "肱川あらしは大洲市で冬の朝に発生する霧が肱川を下って海へ流出する珍しい気象現象。白い霧の帯が幻想的な景観を作ります。",
        "nanyo-stage-19": "宇和島真珠は宇和海の豊かな海で養殖される高品質な真珠。生産量は全国トップクラスで、養殖技術の発展に貢献しています。",
    })

    return trivia_templates.get(course_id, trivia)


def load_questions_from_file(filepath: str, var_name: str) -> list:
    """ファイルからPythonデータを安全に読み込む。"""
    full_path = os.path.join(project_root, filepath)
    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()
    namespace = {}
    exec(compile(content, filepath, "exec"), namespace)
    return namespace[var_name]


def fix_file(filepath: str, var_name: str):
    """ファイル内の不一致問題を修正してファイルを上書きする。"""
    print(f"\n{'='*60}")
    print(f"Processing: {filepath} ({var_name})")
    print(f"{'='*60}")

    # Read the file
    full_path = os.path.join(project_root, filepath)
    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Load questions directly
    questions = load_questions_from_file(filepath, var_name)

    template_counter = {}
    fix_count = 0
    skip_count = 0

    for q in questions:
        if not is_bug_condition(q):
            continue

        course_id = q["course_id"]
        if course_id not in STAGE_THEME_MAP:
            skip_count += 1
            continue

        # Generate fixed text
        new_text = generate_fixed_text(q, template_counter)

        # Replace in file content
        old_text_escaped = q["text"].replace("\\", "\\\\")
        # Use exact string replacement
        old_marker = f'"text": "{q["text"]}"'
        new_marker = f'"text": "{new_text}"'

        if old_marker in content:
            content = content.replace(old_marker, new_marker, 1)
            fix_count += 1
        else:
            # Try with different quote styles
            old_marker2 = f"'text': '{q['text']}'"
            if old_marker2 in content:
                new_marker2 = f"'text': '{new_text}'"
                content = content.replace(old_marker2, new_marker2, 1)
                fix_count += 1
            else:
                print(f"  WARNING: Could not find text for {q['id']}")
                print(f"    First 80 chars: {q['text'][:80]}")

        # Fix trivia if needed
        new_trivia = generate_fixed_trivia(q)
        if new_trivia:
            old_trivia = f'"ehime_trivia": "{q["ehime_trivia"]}"'
            new_trivia_marker = f'"ehime_trivia": "{new_trivia}"'
            if old_trivia in content:
                content = content.replace(old_trivia, new_trivia_marker, 1)

    # Write back
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  Fixed: {fix_count} questions")
    print(f"  Skipped (unmapped): {skip_count} questions")


def main():
    print("Fixing stage theme mismatches in seed_data_extra.py and seed_data_extra2.py")
    fix_file("app/data/seed_data_extra.py", "EXTRA_QUESTIONS")
    fix_file("app/data/seed_data_extra2.py", "EXTRA_QUESTIONS_2")
    print("\nDone!")


if __name__ == "__main__":
    main()
