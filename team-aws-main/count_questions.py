"""Temporary script to count question distributions."""
from app.data.seed_data import QUESTIONS, COURSES
from app.data.seed_data_extra import EXTRA_QUESTIONS
from app.data.seed_data_extra2 import EXTRA_QUESTIONS_3
from collections import Counter

print('=== Question counts ===')
print(f'QUESTIONS (seed_data.py): {len(QUESTIONS)}')
print(f'EXTRA_QUESTIONS (seed_data_extra.py): {len(EXTRA_QUESTIONS)}')
print(f'EXTRA_QUESTIONS_3 (seed_data_extra2.py): {len(EXTRA_QUESTIONS_3)}')
print(f'Total: {len(QUESTIONS) + len(EXTRA_QUESTIONS) + len(EXTRA_QUESTIONS_3)}')

print()
print('=== COURSES count ===')
print(f'COURSES: {len(COURSES)}')

nanyo_q = [q for q in QUESTIONS if q['course_id'].startswith('nanyo-')]
print(f'Nanyo CLF (seed_data.py): {len(nanyo_q)}')

chuyo_extra = [q for q in EXTRA_QUESTIONS if q['course_id'].startswith('chuyo-')]
toyo_extra = [q for q in EXTRA_QUESTIONS if q['course_id'].startswith('toyo-')]
print(f'Chuyo CLF (seed_data_extra.py): {len(chuyo_extra)}')
print(f'Toyo CLF (seed_data_extra.py): {len(toyo_extra)}')

nanyo_aif = [q for q in EXTRA_QUESTIONS_3 if q['course_id'].startswith('nanyo-')]
chuyo_aif = [q for q in EXTRA_QUESTIONS_3 if q['course_id'].startswith('chuyo-')]
toyo_aif = [q for q in EXTRA_QUESTIONS_3 if q['course_id'].startswith('toyo-')]
print(f'Nanyo AIF (seed_data_extra2.py): {len(nanyo_aif)}')
print(f'Chuyo AIF (seed_data_extra2.py): {len(chuyo_aif)}')
print(f'Toyo AIF (seed_data_extra2.py): {len(toyo_aif)}')

print()
print('=== Current course distribution ===')
all_q = QUESTIONS + EXTRA_QUESTIONS + EXTRA_QUESTIONS_3
counter = Counter(q['course_id'] for q in all_q)
for cid in sorted(counter.keys()):
    print(f'  {cid}: {counter[cid]} questions')
