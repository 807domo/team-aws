"""
Reassign course_ids across all seed data files.

Strategy:
- Group all questions by region (nanyo/chuyo/toyo) in the order they appear in each file
- Distribute evenly across stages (some get 5, some get 4 or 6 to use all stages)
- Nanyo: 153 questions -> 31 stages (nanyo-stage-01 ~ nanyo-stage-31)
- Chuyo: 97 questions -> 20 stages (chuyo-stage-01 ~ chuyo-stage-20)
- Toyo: 96 questions -> 20 stages (toyo-stage-01 ~ toyo-stage-20)
"""
import re
import sys

sys.path.insert(0, '.')


def compute_stage_assignments(total_questions, num_stages):
    """
    Compute the stage number for each question index.
    Distributes questions evenly: some stages get ceil(total/stages),
    others get floor(total/stages).
    
    Returns a list of stage numbers (1-indexed) for each question index.
    """
    base = total_questions // num_stages
    remainder = total_questions % num_stages
    
    assignments = []
    for stage in range(1, num_stages + 1):
        # First 'remainder' stages get base+1 questions
        count = base + 1 if stage <= remainder else base
        assignments.extend([stage] * count)
    
    return assignments


def reassign_file(filepath, region_prefix, assignments, start_index):
    """
    Read a file, find all questions with the given region prefix,
    and reassign their course_id based on the assignments list.
    
    Returns the number of questions reassigned.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all course_id lines for this region and replace them
    pattern = re.compile(r'("course_id": "' + region_prefix + r'-stage-)\d{2}(")')
    
    count = 0
    def replacer(match):
        nonlocal count
        idx = start_index + count
        stage = assignments[idx]
        count += 1
        return f'{match.group(1)}{stage:02d}{match.group(2)}'
    
    new_content = pattern.sub(replacer, content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return count


# File paths
seed_data = 'app/data/seed_data.py'
seed_data_extra = 'app/data/seed_data_extra.py'
seed_data_extra2 = 'app/data/seed_data_extra2.py'

# Compute assignments
nanyo_assignments = compute_stage_assignments(153, 31)
chuyo_assignments = compute_stage_assignments(97, 20)
toyo_assignments = compute_stage_assignments(96, 20)

print("Stage distribution:")
print(f"  Nanyo (153 / 31): base=4, remainder=29 -> 29 stages with 5, 2 stages with 4")
from collections import Counter
nc = Counter(nanyo_assignments)
print(f"    Actual: {dict(sorted(Counter(nc.values()).items()))}")
cc = Counter(chuyo_assignments)
print(f"  Chuyo (97 / 20): {dict(sorted(Counter(cc.values()).items()))}")
tc = Counter(toyo_assignments)
print(f"  Toyo (96 / 20): {dict(sorted(Counter(tc.values()).items()))}")

# === Nanyo ===
n1 = reassign_file(seed_data, 'nanyo', nanyo_assignments, 0)
print(f'\nseed_data.py nanyo: {n1} questions reassigned')

n2 = reassign_file(seed_data_extra2, 'nanyo', nanyo_assignments, n1)
print(f'seed_data_extra2.py nanyo: {n2} questions reassigned')

total_nanyo = n1 + n2
print(f'Total nanyo: {total_nanyo}')

# === Chuyo ===
c1 = reassign_file(seed_data_extra, 'chuyo', chuyo_assignments, 0)
print(f'\nseed_data_extra.py chuyo: {c1} questions reassigned')

c2 = reassign_file(seed_data_extra2, 'chuyo', chuyo_assignments, c1)
print(f'seed_data_extra2.py chuyo: {c2} questions reassigned')

total_chuyo = c1 + c2
print(f'Total chuyo: {total_chuyo}')

# === Toyo ===
t1 = reassign_file(seed_data_extra, 'toyo', toyo_assignments, 0)
print(f'\nseed_data_extra.py toyo: {t1} questions reassigned')

t2 = reassign_file(seed_data_extra2, 'toyo', toyo_assignments, t1)
print(f'seed_data_extra2.py toyo: {t2} questions reassigned')

total_toyo = t1 + t2
print(f'Total toyo: {total_toyo}')

print(f'\n=== Summary ===')
print(f'Nanyo: {total_nanyo} questions -> 31 stages')
print(f'Chuyo: {total_chuyo} questions -> 20 stages')
print(f'Toyo: {total_toyo} questions -> 20 stages')
print(f'Total: {total_nanyo + total_chuyo + total_toyo} questions')
