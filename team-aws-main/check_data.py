"""Temporary script to check current data distribution."""
import sys
sys.path.insert(0, '.')
from collections import Counter
from app.data.seed_data import COURSES, QUESTIONS
from app.data.seed_data_extra import EXTRA_QUESTIONS
from app.data.seed_data_extra2 import EXTRA_QUESTIONS_3

print(f'COURSES: {len(COURSES)}')
print(f'QUESTIONS (seed_data.py): {len(QUESTIONS)}')
print(f'EXTRA_QUESTIONS (seed_data_extra.py): {len(EXTRA_QUESTIONS)}')
print(f'EXTRA_QUESTIONS_3 (seed_data_extra2.py): {len(EXTRA_QUESTIONS_3)}')
print(f'Total: {len(QUESTIONS) + len(EXTRA_QUESTIONS) + len(EXTRA_QUESTIONS_3)}')
print()

def count_by_prefix(qs):
    c = Counter()
    for q in qs:
        prefix = q['course_id'].split('-stage-')[0]
        c[prefix] += 1
    return c

print('QUESTIONS by region:', dict(count_by_prefix(QUESTIONS)))
print('EXTRA_QUESTIONS by region:', dict(count_by_prefix(EXTRA_QUESTIONS)))
print('EXTRA_QUESTIONS_3 by region:', dict(count_by_prefix(EXTRA_QUESTIONS_3)))
print()

all_qs = QUESTIONS + EXTRA_QUESTIONS + EXTRA_QUESTIONS_3
course_counts = Counter(q['course_id'] for q in all_qs)
print('Questions per course:')
for cid in sorted(course_counts.keys()):
    print(f'  {cid}: {course_counts[cid]}')
print()
print(f'Unique course IDs used: {len(set(q["course_id"] for q in all_qs))}')

# Check current COURSES ids
print(f'\nCurrent COURSES ids:')
for c in COURSES:
    print(f'  {c["id"]}')
