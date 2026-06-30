"""
ドメインカバレッジ検証テスト

シードデータ（COURSES, QUESTIONS）が試験範囲のカバレッジ要件を満たしていることを検証する。
各ドメインの問題数、難易度分布、AWSサービス参照、愛媛トリビア多様性を確認する。

Requirements: 10.1, 10.2, 10.3, 10.5, 8.5, 11.1, 11.2, 11.3
"""

import pytest

from app.data.seed_data import COURSES, QUESTIONS


# =============================================================================
# ドメイン定義・定数
# =============================================================================

CLF_C02_DOMAINS = [
    "Cloud Concepts",
    "Security and Compliance",
    "Cloud Technology and Services",
    "Billing Pricing and Support",
]

AIF_C01_DOMAINS = [
    "AI and ML Fundamentals",
    "Generative AI",
    "Responsible AI",
]

ALL_DOMAINS = CLF_C02_DOMAINS + AIF_C01_DOMAINS

# 各ドメインの最低問題数要件 (Requirement 10.2)
DOMAIN_MIN_COUNTS = {
    "Cloud Concepts": 15,
    "Security and Compliance": 15,
    "Cloud Technology and Services": 20,
    "Billing Pricing and Support": 12,
    "AI and ML Fundamentals": 15,
    "Generative AI": 15,
    "Responsible AI": 10,
}

# 各ドメインの難易度別最低数
DOMAIN_DIFFICULTY_MINS = {
    "Cloud Concepts": {"基礎": 4, "中級": 4, "上級": 3},
    "Security and Compliance": {"基礎": 3, "中級": 3, "上級": 3},
    "Cloud Technology and Services": {"基礎": 5, "中級": 5, "上級": 5},
    "Billing Pricing and Support": {"基礎": 2, "中級": 2, "上級": 2},
    "AI and ML Fundamentals": {"基礎": 3, "中級": 3, "上級": 3},
    "Generative AI": {"基礎": 4, "中級": 4, "上級": 4},
    "Responsible AI": {"基礎": 2, "中級": 2, "上級": 2},
}

# AWSサービス名リスト（Requirement 10.3）
AWS_SERVICE_NAMES = [
    "EC2", "S3", "Lambda", "RDS", "DynamoDB", "VPC", "IAM",
    "CloudFront", "SageMaker", "Bedrock", "CloudWatch", "CloudFormation",
    "SQS", "SNS", "KMS", "CloudTrail", "Route 53", "ELB",
    "Glacier", "Trusted Advisor", "ECS", "EBS", "EFS",
    "Step Functions", "Direct Connect", "ElastiCache", "Redshift",
    "Fargate", "Auto Scaling", "Organizations", "Config",
    "Security Hub", "Systems Manager", "Rekognition", "Comprehend",
    "Textract", "Translate", "Forecast", "Personalize",
    "Cost Explorer", "Budgets", "Artifact", "WAF", "Shield",
    "GuardDuty", "Inspector", "Macie", "Athena", "Glue",
    "Kinesis", "EMR", "CodePipeline", "CodeBuild", "CodeDeploy",
    "Elastic Beanstalk", "Lightsail", "Savings Plans",
]

# 愛媛トリビア地域キーワード（Requirement 11.1）
REGION_KEYWORDS = {
    "中予": [
        "松山", "道後", "砥部", "伊予", "石鎚", "坊っちゃん",
        "正岡子規", "愛媛大学", "四国電力",
    ],
    "南予": [
        "宇和島", "内子", "大洲", "八幡浜", "西予", "佐田岬",
        "四国カルスト", "南予", "段畑", "闘牛",
    ],
    "東予": [
        "今治", "新居浜", "西条", "しまなみ", "来島",
        "別子", "タオル", "造船", "うちぬき",
    ],
}

# 愛媛トリビアテーマキーワード（Requirement 11.2）
THEME_KEYWORDS = {
    "歴史的建造物・城郭": ["城", "天守", "石垣", "築城"],
    "温泉・自然景観": ["温泉", "海道", "カルスト", "山", "海峡", "半島"],
    "伝統文化・祭り": ["祭り", "太鼓", "闘牛", "俳句", "文学"],
    "特産品・名産物": ["みかん", "タオル", "真珠", "じゃこ天", "団子"],
    "産業・経済": ["造船", "工場", "銅山", "住友", "産業"],
    "文学・芸術": ["漱石", "子規", "坊っちゃん", "俳句"],
}


# =============================================================================
# ヘルパー関数
# =============================================================================


def get_questions_by_domain(domain: str) -> list:
    """指定ドメインの問題リストを取得"""
    return [q for q in QUESTIONS if q["exam_domain"] == domain]


def get_question_searchable_text(question: dict) -> str:
    """問題のテキスト、選択肢、解説を結合して検索用テキストを生成"""
    parts = [
        question.get("text", ""),
        question.get("choice_1", ""),
        question.get("choice_2", ""),
        question.get("choice_3", ""),
        question.get("choice_4", ""),
        question.get("aws_ai_explanation", ""),
    ]
    return " ".join(parts)


def detect_aws_services_in_questions() -> set:
    """全問題から参照されているAWSサービス名を検出"""
    found_services = set()
    for q in QUESTIONS:
        text = get_question_searchable_text(q)
        for service in AWS_SERVICE_NAMES:
            if service in text:
                found_services.add(service)
    return found_services


def detect_region_for_trivia(trivia: str) -> set:
    """トリビアテキストから参照されている地域を検出"""
    regions = set()
    for region, keywords in REGION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in trivia:
                regions.add(region)
                break
    return regions


def detect_themes_in_trivia(trivia: str) -> set:
    """トリビアテキストから参照されているテーマを検出"""
    themes = set()
    for theme, keywords in THEME_KEYWORDS.items():
        for keyword in keywords:
            if keyword in trivia:
                themes.add(theme)
                break
    return themes


# =============================================================================
# Task 8.1: ドメインカバレッジ検証テスト
# =============================================================================


class TestDomainMinimumCounts:
    """各ドメインの最低問題数を検証（Requirement 10.2）"""

    @pytest.mark.parametrize("domain,min_count", DOMAIN_MIN_COUNTS.items())
    def test_domain_has_minimum_questions(self, domain: str, min_count: int):
        """各ドメインが要件の最低問題数を満たすこと"""
        questions = get_questions_by_domain(domain)
        assert len(questions) >= min_count, (
            f"ドメイン「{domain}」の問題数が不足: "
            f"{len(questions)}問 (最低{min_count}問必要)"
        )


class TestDifficultyDistribution:
    """各ドメインの難易度分布を検証（Requirements 1.3, 2.3, 3.4, 4.3, 5.3, 6.3, 7.3）"""

    @pytest.mark.parametrize("domain", ALL_DOMAINS)
    def test_domain_difficulty_distribution(self, domain: str):
        """各ドメインの難易度別最低数を満たすこと"""
        questions = get_questions_by_domain(domain)
        mins = DOMAIN_DIFFICULTY_MINS[domain]

        for difficulty, min_count in mins.items():
            count = sum(1 for q in questions if q["difficulty"] == difficulty)
            assert count >= min_count, (
                f"ドメイン「{domain}」の難易度「{difficulty}」が不足: "
                f"{count}問 (最低{min_count}問必要)"
            )


class TestTotalAndCertificationCoverage:
    """全体問題数と認定試験別カバレッジの検証"""

    def test_total_questions_at_least_100(self):
        """問題数が合計100問以上であること（Requirement 10.1）"""
        assert len(QUESTIONS) >= 100, (
            f"総問題数が不足: {len(QUESTIONS)}問 (最低100問必要)"
        )

    def test_clf_c02_domains_at_least_60(self):
        """CLF-C02ドメイン（CC+SC+CT+BP）が60問以上であること（Requirement 10.5）"""
        clf_count = sum(
            1 for q in QUESTIONS if q["exam_domain"] in CLF_C02_DOMAINS
        )
        assert clf_count >= 60, (
            f"CLF-C02ドメインの問題数が不足: {clf_count}問 (最低60問必要)"
        )

    def test_aif_c01_domains_at_least_40(self):
        """AIF-C01ドメイン（AI+GA+RA）が40問以上であること（Requirement 10.5）"""
        aif_count = sum(
            1 for q in QUESTIONS if q["exam_domain"] in AIF_C01_DOMAINS
        )
        assert aif_count >= 40, (
            f"AIF-C01ドメインの問題数が不足: {aif_count}問 (最低40問必要)"
        )


class TestAWSServiceCoverage:
    """AWSサービス参照の網羅性を検証（Requirement 10.3）"""

    def test_at_least_20_distinct_aws_services_referenced(self):
        """全問題で20種以上のAWSサービスが参照されていること"""
        found_services = detect_aws_services_in_questions()
        assert len(found_services) >= 20, (
            f"参照されているAWSサービスが不足: {len(found_services)}種 "
            f"(最低20種必要)\n検出されたサービス: {sorted(found_services)}"
        )


class TestCourseQuestionDistribution:
    """各コースへの問題配分を検証（Requirement 8.5）"""

    def test_each_course_has_at_least_5_questions(self):
        """各コースに最低5問が割り当てられていること"""
        course_ids = {course["id"] for course in COURSES}
        for course_id in course_ids:
            count = sum(
                1 for q in QUESTIONS if q["course_id"] == course_id
            )
            assert count >= 5, (
                f"コース「{course_id}」の問題数が不足: "
                f"{count}問 (最低5問必要)"
            )


# =============================================================================
# Task 8.2: 愛媛トリビア多様性テスト
# =============================================================================


class TestEhimeTriviaRegionDiversity:
    """愛媛トリビアの地域多様性を検証（Requirement 11.1）"""

    def test_trivia_references_all_three_regions(self):
        """3地域（中予・南予・東予）すべてからトリビアが参照されていること"""
        region_counts = {"中予": 0, "南予": 0, "東予": 0}

        for q in QUESTIONS:
            trivia = q.get("ehime_trivia", "")
            detected_regions = detect_region_for_trivia(trivia)
            for region in detected_regions:
                region_counts[region] += 1

        for region, count in region_counts.items():
            assert count >= 5, (
                f"地域「{region}」のトリビア参照が不足: "
                f"{count}問 (最低5問必要)"
            )

    @pytest.mark.parametrize("region", ["中予", "南予", "東予"])
    def test_each_region_has_minimum_5_trivia_references(self, region: str):
        """各地域に最低5問のトリビア参照があること"""
        count = 0
        for q in QUESTIONS:
            trivia = q.get("ehime_trivia", "")
            detected = detect_region_for_trivia(trivia)
            if region in detected:
                count += 1

        assert count >= 5, (
            f"地域「{region}」のトリビア参照が不足: "
            f"{count}問 (最低5問必要)"
        )


class TestEhimeTriviaThemeDiversity:
    """愛媛トリビアのテーマ多様性を検証（Requirement 11.2）"""

    def test_trivia_covers_at_least_4_of_6_themes(self):
        """6テーマ中4テーマ以上がカバーされていること"""
        covered_themes = set()

        for q in QUESTIONS:
            trivia = q.get("ehime_trivia", "")
            detected_themes = detect_themes_in_trivia(trivia)
            covered_themes.update(detected_themes)

        assert len(covered_themes) >= 4, (
            f"カバーされているテーマが不足: {len(covered_themes)}テーマ "
            f"(最低4テーマ必要)\n"
            f"検出されたテーマ: {sorted(covered_themes)}"
        )


class TestEhimeTriviaLength:
    """愛媛トリビアの文字数範囲を検証（Requirement 11.3）"""

    def test_all_trivia_between_30_and_200_characters(self):
        """全問題のehime_triviaが30〜200文字の範囲内であること"""
        violations = []
        for q in QUESTIONS:
            trivia = q.get("ehime_trivia", "")
            length = len(trivia)
            if length < 30 or length > 200:
                violations.append(
                    f"問題 {q['id']}: {length}文字 "
                    f"({'短すぎ' if length < 30 else '長すぎ'})"
                )

        assert len(violations) == 0, (
            f"ehime_triviaの文字数が範囲外の問題が{len(violations)}件:\n"
            + "\n".join(violations[:10])  # 最大10件表示
        )
