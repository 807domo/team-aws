"""各難易度の問題が正しい地域のキーワードを含んでいるか確認するスクリプト"""
import sys
sys.path.insert(0, '.')

from app.data.seed_data import QUESTIONS
from app.data.seed_data_extra import EXTRA_QUESTIONS
from app.data.seed_data_extra2 import EXTRA_QUESTIONS_2

ALL = QUESTIONS + EXTRA_QUESTIONS + EXTRA_QUESTIONS_2

nanyo_kw = ['宇和島', '八幡浜', '内子', '大洲', '佐田岬', '四国カルスト', '滑床', '愛南', '西予', '卯之町', '松野']
chuyo_kw = ['松山', '道後', '石鎚', '砥部', '坊っちゃん', '伊予鉄', '面河', '久万', '東温', '伊予市']
toyo_kw = ['しまなみ', '今治', '新居浜', '別子', '来島', '西条', '四国中央', '村上海賊', 'タオル']

def check_region(questions, region_name, keywords):
    total = len(questions)
    has_kw = 0
    missing = []
    for q in questions:
        text = q['text'] + q['ehime_trivia']
        if any(kw in text for kw in keywords):
            has_kw += 1
        else:
            missing.append(q['id'])
    pct = has_kw * 100 // total if total > 0 else 0
    print(f'{region_name}: {has_kw}/{total} ({pct}%) に地域キーワードあり')
    if missing:
        print(f'  キーワードなし ({len(missing)}件): {missing[:10]}')

nanyo_qs = [q for q in ALL if q['id'].startswith('nanyo-')]
chuyo_qs = [q for q in ALL if q['id'].startswith('chuyo-')]
toyo_qs = [q for q in ALL if q['id'].startswith('toyo-')]

print(f'問題総数: {len(ALL)}')
print(f'南予: {len(nanyo_qs)}, 中予: {len(chuyo_qs)}, 東予: {len(toyo_qs)}')
print()
check_region(nanyo_qs, '南予(基礎)', nanyo_kw)
print()
check_region(chuyo_qs, '中予(中級)', chuyo_kw)
print()
check_region(toyo_qs, '東予(上級)', toyo_kw)
