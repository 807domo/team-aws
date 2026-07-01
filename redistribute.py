"""
Redistribution script: Reassigns course_ids in all seed data files
to achieve ~5 questions per stage.
"""
import re
import traceback


def generate_courses_text():
    """Generate the full COURSES list Python text."""
    lines = []
    lines.append("COURSES = [")
    # Nanyo: 31 stages
    for i in range(1, 32):
        lines.append("    {")
        lines.append(f'        "id": "nanyo-stage-{i:02d}",')
        lines.append(f'        "name": "ステージ{i}：南予コース",')
        lines.append(f'        "region": "初級",')
        lines.append(f'        "difficulty": "基礎",')
        lines.append(f'        "description": "初級レベルのAWS学習コース（ステージ{i}）",')
        lines.append("    },")
    # Chuyo: 20 stages
    for i in range(1, 21):
        lines.append("    {")
        lines.append(f'        "id": "chuyo-stage-{i:02d}",')
        lines.append(f'        "name": "ステージ{i}：中予コース",')
        lines.append(f'        "region": "中級",')
        lines.append(f'        "difficulty": "中級",')
        lines.append(f'        "description": "中級レベルのAWS学習コース（ステージ{i}）",')
        lines.append("    },")
    # Toyo: 20 stages
    for i in range(1, 21):
        lines.append("    {")
        lines.append(f'        "id": "toyo-stage-{i:02d}",')
        lines.append(f'        "name": "ステージ{i}：東予コース",')
        lines.append(f'        "region": "上級",')
        lines.append(f'        "difficulty": "上級",')
        lines.append(f'        "description": "上級レベルのAWS学習コース（ステージ{i}）",')
        lines.append("    },")
    lines.append("]")
    return "\n".join(lines)


def distribute_questions(total, num_stages):
    """Distribute total questions across num_stages."""
    base = total // num_stages
    remainder = total % num_stages
    distribution = []
    for i in range(num_stages):
        if i < remainder:
            distribution.append(base + 1)
        else:
            distribution.append(base)
    return distribution


def reassign_course_ids(content, region_prefix, num_stages):
    """Reassign course_ids for a given region prefix in content."""
    pattern = rf'"course_id": "{region_prefix}-stage-\d{{2}}"'
    matches = list(re.finditer(pattern, content))

    if not matches:
        print(f"  No {region_prefix} questions found")
        return content

    total = len(matches)
    dist = distribute_questions(total, num_stages)
    print(f"  {region_prefix}: {total} questions -> {num_stages} stages, dist range [{min(dist)},{max(dist)}]")

    # Build stage assignments
    stage_assignments = []
    for stage_num, count in enumerate(dist, 1):
        for _ in range(count):
            stage_assignments.append(f'{region_prefix}-stage-{stage_num:02d}')

    assert len(stage_assignments) == total

    # Replace in reverse order
    for i, match in reversed(list(enumerate(matches))):
        new_val = f'"course_id": "{stage_assignments[i]}"'
        content = content[:match.start()] + new_val + content[match.end():]

    return content


def main():
    base_path = r"c:\Users\omasa\OneDrive\ドキュメント\2026Q1\大学院PBL\team-aws\app\data"

    # ---- seed_data.py ----
    seed_path = base_path + "\\seed_data.py"
    print(f"Reading {seed_path}")
    with open(seed_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace COURSES block
    courses_text = generate_courses_text()
    
    # Find COURSES = [ and its matching ]
    start = content.find("COURSES = [")
    if start == -1:
        print("ERROR: Could not find COURSES = [")
        return
    
    # Find matching closing bracket
    bracket_count = 0
    end = start
    for i in range(start, len(content)):
        if content[i] == '[':
            bracket_count += 1
        elif content[i] == ']':
            bracket_count -= 1
            if bracket_count == 0:
                end = i + 1
                break

    print(f"  COURSES block: position {start} to {end} ({end-start} chars)")
    content = content[:start] + courses_text + content[end:]

    # Reassign nanyo in seed_data.py
    content = reassign_course_ids(content, "nanyo", 31)

    with open(seed_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  Written: {seed_path}")

    # ---- seed_data_extra.py ----
    extra_path = base_path + "\\seed_data_extra.py"
    print(f"\nReading {extra_path}")
    with open(extra_path, 'r', encoding='utf-8') as f:
        content = f.read()

    content = reassign_course_ids(content, "chuyo", 20)
    content = reassign_course_ids(content, "toyo", 20)

    with open(extra_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  Written: {extra_path}")

    # ---- seed_data_extra2.py ----
    extra2_path = base_path + "\\seed_data_extra2.py"
    print(f"\nReading {extra2_path}")
    with open(extra2_path, 'r', encoding='utf-8') as f:
        content = f.read()

    content = reassign_course_ids(content, "nanyo", 31)
    content = reassign_course_ids(content, "chuyo", 20)
    content = reassign_course_ids(content, "toyo", 20)

    with open(extra2_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  Written: {extra2_path}")

    print("\nDone!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        traceback.print_exc()
