"""exam_domain名を公式試験ガイドの正式名称に一括修正するスクリプト"""
import os

FILES = [
    'app/data/seed_data.py',
    'app/data/seed_data_extra.py',
    'app/data/seed_data_extra2.py',
    'tests/test_seed_data_properties.py',
    'tests/test_seed_data_smoke.py',
]

REPLACEMENTS = [
    ('"Billing Pricing and Support"', '"Billing, Pricing, and Support"'),
    ('"AI and ML Fundamentals"', '"Fundamentals of AI and ML"'),
    ('"Generative AI Concepts"', '"Fundamentals of Generative AI"'),
    ('"Security Compliance and Governance"', '"Security, Compliance, and Governance for AI Solutions"'),
]

for filepath in FILES:
    if not os.path.exists(filepath):
        print(f"SKIP (not found): {filepath}")
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    for old, new in REPLACEMENTS:
        content = content.replace(old, new)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"UPDATED: {filepath}")
    else:
        print(f"NO CHANGE: {filepath}")

print("Done.")
