import sys
sys.path.insert(0, '.')
from app.data.seed_data import QUESTIONS
from app.data.bunkazai_questions import BUNKAZAI_QUESTIONS
from app.data.extra_questions import EXTRA_QUESTIONS

from collections import Counter
all_q = QUESTIONS + BUNKAZAI_QUESTIONS + EXTRA_QUESTIONS
counter = Counter(q['course_id'] for q in all_q)
for cid in sorted(counter.keys()):
    print(f'{cid}: {counter[cid]}')
print(f'\nTotal: {len(all_q)}')
