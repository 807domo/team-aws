# Requirements Document

## Introduction

愛媛探索AIクイズアプリケーションのクイズ問題を全面的に作り直す。中予（中級）と東予（上級）の問題を各難易度に適した内容に改善し、全3地域（南予・中予・東予）のステージを各10個に統一する。問題はライセンスページに記載されたAWS公式情報源（AWS公式ドキュメント、ホワイトペーパー、認定試験ガイド、AWS Skill Builder、AWS Cloud Practitioner Essentials）を基に作成する。

## Glossary

- **Quiz_System**: 愛媛探索AIクイズアプリケーション全体のクイズ出題・管理システム
- **Seed_Data_Module**: `app/data/seed_data.py`および`app/data/seed_data_extra.py`で定義される問題・コースデータの投入モジュール
- **Course**: ステージに対応するクイズコース（id、名前、地域、難易度、説明で構成）
- **Question**: クイズ問題（問題文、4つの選択肢、正解インデックス、愛媛トリビア、AWS/AI解説、難易度、試験ドメインで構成）
- **Region_Nanyo**: 南予地域（初級レベル、nanyo-stage-01〜10）
- **Region_Chuyo**: 中予地域（中級レベル、chuyo-stage-01〜10）
- **Region_Toyo**: 東予地域（上級レベル、toyo-stage-01〜10）
- **Exam_Domain**: AWS認定試験のドメイン分類（Cloud Concepts, Security and Compliance, Cloud Technology and Services, Billing Pricing and Support, AI and ML Fundamentals, Generative AI, Responsible AI）
- **Ehime_Trivia**: 各問題に付随する愛媛県のローカル情報・トリビア
- **AWS_Information_Source**: ライセンスページに記載されたAWS情報源（docs.aws.amazon.com, aws.amazon.com/whitepapers/, aws.amazon.com/certification/, skillbuilder.aws/, aws.amazon.com/training/classroom/aws-cloud-practitioner-essentials/）

## Requirements

### Requirement 1: 中予コースのステージ数を10個に統一

**User Story:** As a 学習者, I want 中予（中級）コースが10ステージあること, so that 他の地域と同じ学習量でバランスよく学習を進められる。

#### Acceptance Criteria

1. THE Seed_Data_Module SHALL define exactly 10 Course entries for Region_Chuyo with IDs "chuyo-stage-01" through "chuyo-stage-10"
2. WHEN the seed data is loaded, THE Quiz_System SHALL contain 30 total courses (10 for Region_Nanyo, 10 for Region_Chuyo, 10 for Region_Toyo)
3. THE Seed_Data_Module SHALL assign region value "中級" and difficulty value "中級" to all Region_Chuyo courses

### Requirement 2: 南予（初級）問題の作り直し

**User Story:** As a 初学者, I want 南予コースの問題がAWS基礎レベルに適した難易度であること, so that AWSの基本概念を無理なく学べる。

#### Acceptance Criteria

1. THE Seed_Data_Module SHALL define at least 5 Question entries per Region_Nanyo course (minimum 50 questions total for 10 stages)
2. THE Seed_Data_Module SHALL assign difficulty value "基礎" to all questions belonging to Region_Nanyo courses
3. WHEN a Question belongs to a Region_Nanyo course, THE Question SHALL cover AWS Cloud Practitioner level fundamentals (basic cloud concepts, fundamental AWS services, simple billing concepts)
4. THE Seed_Data_Module SHALL distribute questions across all 7 Exam_Domain categories within Region_Nanyo courses
5. WHEN a Question belongs to a Region_Nanyo course, THE Question SHALL include an Ehime_Trivia field referencing a location or cultural fact from the Nanyo area of Ehime prefecture
6. THE Seed_Data_Module SHALL base all Region_Nanyo question content on information available from AWS_Information_Source

### Requirement 3: 中予（中級）問題の作り直し

**User Story:** As a 中級学習者, I want 中予コースの問題が中級レベルの内容であること, so that AWSサービスの連携や設計パターンについて理解を深められる。

#### Acceptance Criteria

1. THE Seed_Data_Module SHALL define at least 5 Question entries per Region_Chuyo course (minimum 50 questions total for 10 stages)
2. THE Seed_Data_Module SHALL assign difficulty value "中級" to all questions belonging to Region_Chuyo courses
3. WHEN a Question belongs to a Region_Chuyo course, THE Question SHALL cover intermediate AWS topics (service integration, architecture patterns, security best practices, cost optimization strategies)
4. THE Seed_Data_Module SHALL distribute questions across all 7 Exam_Domain categories within Region_Chuyo courses
5. WHEN a Question belongs to a Region_Chuyo course, THE Question SHALL include an Ehime_Trivia field referencing a location or cultural fact from the Chuyo area of Ehime prefecture
6. THE Seed_Data_Module SHALL base all Region_Chuyo question content on information available from AWS_Information_Source

### Requirement 4: 東予（上級）問題の作り直し

**User Story:** As a 上級学習者, I want 東予コースの問題が上級レベルの内容であること, so that 複雑なAWSシナリオやベストプラクティスを習得できる。

#### Acceptance Criteria

1. THE Seed_Data_Module SHALL define at least 5 Question entries per Region_Toyo course (minimum 50 questions total for 10 stages)
2. THE Seed_Data_Module SHALL assign difficulty value "上級" to all questions belonging to Region_Toyo courses
3. WHEN a Question belongs to a Region_Toyo course, THE Question SHALL cover advanced AWS topics (complex multi-service architectures, disaster recovery strategies, advanced security scenarios, enterprise-scale design patterns, AI/ML pipeline design)
4. THE Seed_Data_Module SHALL distribute questions across all 7 Exam_Domain categories within Region_Toyo courses
5. WHEN a Question belongs to a Region_Toyo course, THE Question SHALL include an Ehime_Trivia field referencing a location or cultural fact from the Toyo area of Ehime prefecture
6. THE Seed_Data_Module SHALL base all Region_Toyo question content on information available from AWS_Information_Source

### Requirement 5: 問題データ構造の整合性

**User Story:** As a 開発者, I want 全問題データが正しい構造と整合性を持つこと, so that アプリケーションがエラーなく問題を表示・採点できる。

#### Acceptance Criteria

1. THE Seed_Data_Module SHALL assign a unique ID to each Question entry following the pattern "q-{domain_prefix}-{number}"
2. THE Seed_Data_Module SHALL set the correct_choice_index field to a value between 0 and 3 (inclusive) for each Question
3. THE Seed_Data_Module SHALL provide exactly 4 non-empty choice fields (choice_1, choice_2, choice_3, choice_4) for each Question
4. THE Seed_Data_Module SHALL assign a valid Exam_Domain value from the 7 defined domains to each Question
5. THE Seed_Data_Module SHALL provide non-empty aws_ai_explanation and ehime_trivia fields for each Question
6. WHEN a Question references a course_id, THE course_id SHALL correspond to an existing Course entry in the COURSES list

### Requirement 6: 試験ドメインの均等分配

**User Story:** As a 学習者, I want 各地域で全試験ドメインの問題が出題されること, so that 試験範囲を偏りなくカバーできる。

#### Acceptance Criteria

1. THE Seed_Data_Module SHALL include at least 3 questions from each of the 7 Exam_Domain categories within each region (Region_Nanyo, Region_Chuyo, Region_Toyo)
2. THE Seed_Data_Module SHALL distribute Exam_Domain categories across different stages within each region to avoid domain concentration in a single stage
3. WHEN all questions for a region are aggregated, THE question set SHALL cover all 7 Exam_Domain categories

### Requirement 7: 既存シードデータファイルの置き換え

**User Story:** As a 開発者, I want 既存の問題データが新しい問題データに完全に置き換わること, so that 古い問題と新しい問題が混在せず一貫性が保たれる。

#### Acceptance Criteria

1. THE Seed_Data_Module SHALL replace all existing QUESTIONS list entries in seed_data.py with the new question set
2. THE Seed_Data_Module SHALL replace all existing EXTRA_QUESTIONS and EXTRA_QUESTIONS_2 list entries in seed_data_extra.py with new question entries or remove them
3. THE Seed_Data_Module SHALL maintain the existing Python module interface (COURSES list, QUESTIONS list, seed_courses function, seed_questions function)
4. WHEN the seed function executes, THE Quiz_System SHALL populate the database with only the new question set (no legacy questions remain)
