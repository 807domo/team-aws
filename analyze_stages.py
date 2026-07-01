"""Temporary script to analyze stage distribution."""
from collections import Counter
from app.data.seed_data import QUESTIONS
from app.data.seed_data_extra import EXTRA_QUESTIONS
from app.data.seed_data_extra2 import EXTRA_QUESTIONS_3

ALL_QUESTIONS = QUESTIONS + EXTRA_QUESTIONS + EXTRA_QUESTIONS_3
counter = Counter(q["course_id"] for q in ALL_QUESTIONS)

print(f"Total questions: {len(ALL_QUESTIONS)}")
print(f"  QUESTIONS (seed_data.py): {len(QUESTIONS)}")
print(f"  EXTRA_QUESTIONS (seed_data_extra.py): {len(EXTRA_QUESTIONS)}")
print(f"  EXTRA_QUESTIONS_3 (seed_data_extra2.py): {len(EXTRA_QUESTIONS_3)}")
print()

print("=== ALL stages (showing violations) ===")
VALID_COURSE_IDS = (
    [f"nanyo-stage-{i:02d}" for i in range(1, 11)]
    + [f"chuyo-stage-{i:02d}" for i in range(1, 9)]
    + [f"toyo-stage-{i:02d}" for i in range(1, 11)]
)
for cid in VALID_COURSE_IDS:
    count = counter.get(cid, 0)
    flag = " *** OVER 15 ***" if count > 15 else (" *** UNDER 5 ***" if count < 5 else "")
    print(f"  {cid}: {count}{flag}")

print("\n=== Cloud Concepts questions breakdown ===")
cc_questions = [q for q in ALL_QUESTIONS if q["exam_domain"] == "Cloud Concepts"]
print(f"  Total: {len(cc_questions)}")

# Find which file each nanyo-stage-01 question is in
print("\n=== nanyo-stage-01 questions and their source ===")
q_ids_in_questions = {q["id"] for q in QUESTIONS}
q_ids_in_extra = {q["id"] for q in EXTRA_QUESTIONS}
q_ids_in_extra3 = {q["id"] for q in EXTRA_QUESTIONS_3}
stage01_qs = [q for q in ALL_QUESTIONS if q["course_id"] == "nanyo-stage-01"]
for q in stage01_qs:
    source = "seed_data.py" if q["id"] in q_ids_in_questions else ("seed_data_extra.py" if q["id"] in q_ids_in_extra else "seed_data_extra2.py")
    print(f"  {q['id']} - {q['exam_domain']} [{source}]")

# Find nanyo stages with fewest questions (below 15)
print("\n=== Nanyo stages with room (< 15) ===")
for i in range(1, 11):
    cid = f"nanyo-stage-{i:02d}"
    count = counter.get(cid, 0)
    if count < 15:
        print(f"  {cid}: {count} (room for {15 - count} more)")
