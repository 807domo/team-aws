# Requirements Document

## Introduction

「愛媛探索AIクイズ」アプリケーションのクイズ問題データを拡張し、AWS認定試験（CLF-C02: Cloud Practitioner、AIF-C01: AI Practitioner）の出題範囲を網羅的にカバーする。現在の33問から大幅に問題数を増加させ、7つの試験ドメインすべてにおいて十分な学習素材を提供する。各問題は愛媛県の観光・文化トリビアとAWS/AI概念を組み合わせた独自形式を維持する。

## Glossary

- **Seed_Data_Module**: `app/data/seed_data.py` に定義されるクイズ問題およびコースの初期データ定義モジュール
- **Question_Validator**: `app/domain/question_validator.py` に実装される問題データの妥当性検証モジュール
- **Course**: 愛媛県の地域（中予・南予・東予）と難易度（基礎・中級・上級）を組み合わせたクイズの学習コース
- **Exam_Domain**: AWS認定試験の出題分野（Cloud Concepts, Security and Compliance, Cloud Technology and Services, Billing Pricing and Support, AI and ML Fundamentals, Generative AI, Responsible AI の7分野）
- **Question_Entry**: id, course_id, text, choice_1-4, correct_choice_index, ehime_trivia, aws_ai_explanation, difficulty, exam_domain を持つ問題データ辞書
- **CLF_C02**: AWS Certified Cloud Practitioner 試験（クラウド基礎4ドメイン）
- **AIF_C01**: AWS Certified AI Practitioner 試験（AI/ML 3ドメイン）
- **Ehime_Trivia**: 各問題に付与される愛媛県の観光・文化・歴史に関する豆知識テキスト
- **AWS_AI_Explanation**: 各問題に付与されるAWSサービスまたはAI概念の解説テキスト

## Requirements

### Requirement 1: Cloud Concepts ドメインの問題拡充

**User Story:** As a CLF-C02受験準備者, I want Cloud Concepts ドメインの問題が十分な数存在すること, so that クラウドの価値提案・設計原則・移行戦略を網羅的に学習できる。

#### Acceptance Criteria

1. THE Seed_Data_Module SHALL contain at least 15 Question_Entry items with exam_domain "Cloud Concepts"
2. WHEN a Question_Entry has exam_domain "Cloud Concepts", THE Question_Entry SHALL cover at least one of the following sub-topics: クラウドの価値提案（コスト削減・俊敏性・弾力性）、Well-Architected Frameworkの柱、クラウド移行戦略、グローバルインフラストラクチャ（リージョン・AZ・エッジロケーション）
3. THE Seed_Data_Module SHALL distribute Cloud Concepts questions across difficulty levels with at least 4 questions at "基礎", at least 4 questions at "中級", and at least 3 questions at "上級"
4. THE Seed_Data_Module SHALL include Cloud Concepts questions covering at least 3 of the 4 listed sub-topics
5. WHEN a Question_Entry has exam_domain "Cloud Concepts", THE Question_Entry SHALL contain an ehime_trivia field of at least 30 characters referencing an Ehime prefecture location, culture, or historical fact
6. WHEN a Question_Entry has exam_domain "Cloud Concepts", THE Question_Entry SHALL contain an aws_ai_explanation field of at least 50 characters explaining the relevant AWS cloud concept

### Requirement 2: Security and Compliance ドメインの問題拡充

**User Story:** As a CLF-C02受験準備者, I want Security and Compliance ドメインの問題が十分な数存在すること, so that AWSの共有責任モデル・IAM・データ保護・コンプライアンスを網羅的に学習できる。

#### Acceptance Criteria

1. THE Seed_Data_Module SHALL contain at least 15 Question_Entry items with exam_domain "Security and Compliance"
2. IF a Question_Entry has exam_domain "Security and Compliance", THEN THE Question_Entry SHALL reference in its text or choice fields at least one of the following sub-topics: 共有責任モデル、IAM（ユーザー・グループ・ロール・ポリシー）、MFA・アクセスキー管理、データ暗号化（KMS・保存時・転送時）、AWS CloudTrail・AWS Config・AWS Security Hub、VPCセキュリティ（セキュリティグループ・NACL）、コンプライアンスプログラム・AWS Artifact
3. THE Seed_Data_Module SHALL assign Security and Compliance questions such that each difficulty level ("基礎", "中級", "上級") has at least 3 Question_Entry items
4. THE Seed_Data_Module SHALL include Security and Compliance questions covering at least 5 of the 7 listed sub-topics
5. IF a Question_Entry has exam_domain "Security and Compliance", THEN THE Question_Entry SHALL contain an ehime_trivia field of at least 20 characters referencing an Ehime prefecture location, culture, or historical fact
6. IF a Question_Entry has exam_domain "Security and Compliance", THEN THE Question_Entry SHALL contain an aws_ai_explanation field of at least 20 characters explaining the relevant security or compliance concept

### Requirement 3: Cloud Technology and Services ドメインの問題拡充

**User Story:** As a CLF-C02受験準備者, I want Cloud Technology and Services ドメインの問題が十分な数存在すること, so that コンピューティング・ストレージ・ネットワーク・データベース等のAWSサービスを網羅的に学習できる。

#### Acceptance Criteria

1. THE Seed_Data_Module SHALL contain at least 20 Question_Entry items with exam_domain "Cloud Technology and Services"
2. WHEN a Question_Entry has exam_domain "Cloud Technology and Services", THE Question_Entry SHALL have its primary topic matching at least one of the following sub-topics: コンピューティング（EC2・Lambda・ECS・Fargate）、ストレージ（S3・EBS・EFS・S3 Glacier）、ネットワーキング（VPC・CloudFront・Route 53・Direct Connect）、データベース（RDS・DynamoDB・ElastiCache・Redshift）、マネジメント・ガバナンス（CloudWatch・CloudFormation・Systems Manager）、アプリケーション統合（SQS・SNS・Step Functions）
3. WHEN all Question_Entry items with exam_domain "Cloud Technology and Services" are considered as a set, THE Seed_Data_Module SHALL include at least 2 questions from each of the 6 sub-topic categories defined in criterion 2
4. THE Seed_Data_Module SHALL distribute Cloud Technology and Services questions across difficulty levels with at least 5 questions at "基礎", at least 5 questions at "中級", and at least 5 questions at "上級"
5. WHEN a Question_Entry has exam_domain "Cloud Technology and Services", THE Question_Entry SHALL contain a non-empty ehime_trivia of at least 30 characters referencing an Ehime prefecture location, culture, or historical fact
6. WHEN a Question_Entry has exam_domain "Cloud Technology and Services", THE Question_Entry SHALL contain a non-empty aws_ai_explanation of at least 50 characters explaining the relevant AWS service or technology

### Requirement 4: Billing Pricing and Support ドメインの問題拡充

**User Story:** As a CLF-C02受験準備者, I want Billing Pricing and Support ドメインの問題が十分な数存在すること, so that AWSの料金モデル・コスト管理ツール・サポートプランを網羅的に学習できる。

#### Acceptance Criteria

1. THE Seed_Data_Module SHALL contain at least 12 Question_Entry items with exam_domain "Billing Pricing and Support"
2. WHEN a Question_Entry has exam_domain "Billing Pricing and Support", THE Question_Entry SHALL cover at least one of the following sub-topics: 料金モデル（オンデマンド・リザーブド・スポット・Savings Plans）、無料利用枠（12ヶ月無料・常時無料・トライアル）、AWS料金計算ツール（Pricing Calculator）、コスト管理（Cost Explorer・Budgets・Cost and Usage Report）、サポートプラン（Basic・Developer・Business・Enterprise）、AWS Organizations・一括請求. THE Seed_Data_Module SHALL include questions from at least 4 of the 6 listed sub-topics across all Billing Pricing and Support questions.
3. THE Seed_Data_Module SHALL distribute Billing Pricing and Support questions across difficulty levels "基礎", "中級", and "上級" with at least 2 Question_Entry items at each difficulty level
4. WHEN a Question_Entry has exam_domain "Billing Pricing and Support", THE Question_Entry SHALL contain an ehime_trivia field of at least 30 characters referencing a specific Ehime prefecture location, cultural practice, or historical fact
5. WHEN a Question_Entry has exam_domain "Billing Pricing and Support", THE Question_Entry SHALL contain an aws_ai_explanation field of at least 50 characters explaining the relevant pricing model, billing mechanism, or support plan concept

### Requirement 5: AI and ML Fundamentals ドメインの問題拡充

**User Story:** As a AIF-C01受験準備者, I want AI and ML Fundamentals ドメインの問題が十分な数存在すること, so that 機械学習の基礎概念・MLパイプライン・AWSのMLサービスを網羅的に学習できる。

#### Acceptance Criteria

1. THE Seed_Data_Module SHALL contain at least 15 Question_Entry items with exam_domain "AI and ML Fundamentals"
2. WHEN a Question_Entry has exam_domain "AI and ML Fundamentals", THE Question_Entry SHALL cover at least one of the following sub-topics: 教師あり学習（分類・回帰）、教師なし学習（クラスタリング・次元削減）、強化学習、MLパイプライン（データ前処理・特徴量エンジニアリング・訓練・評価）、Amazon SageMaker、Amazon Rekognition・Comprehend・Textract・Translate、Amazon Forecast・Personalize
3. THE Seed_Data_Module SHALL distribute AI and ML Fundamentals questions such that each difficulty level ("基礎", "中級", "上級") has at least 3 Question_Entry items
4. WHEN a Question_Entry has exam_domain "AI and ML Fundamentals", THE Question_Entry SHALL contain a non-empty ehime_trivia of at least 20 characters referencing an Ehime prefecture location, culture, or historical fact
5. WHEN a Question_Entry has exam_domain "AI and ML Fundamentals", THE Question_Entry SHALL contain a non-empty aws_ai_explanation of at least 20 characters explaining the relevant AI/ML concept or AWS service
6. THE Seed_Data_Module SHALL cover at least 5 of the 7 defined sub-topics across all Question_Entry items with exam_domain "AI and ML Fundamentals"

### Requirement 6: Generative AI ドメインの問題拡充

**User Story:** As a AIF-C01受験準備者, I want Generative AI ドメインの問題が十分な数存在すること, so that 生成AI技術・基盤モデル・プロンプトエンジニアリング・RAGを網羅的に学習できる。

#### Acceptance Criteria

1. THE Seed_Data_Module SHALL contain at least 15 Question_Entry items with exam_domain "Generative AI"
2. WHEN a Question_Entry has exam_domain "Generative AI", THE Question_Entry SHALL cover at least one of the following sub-topics: 基盤モデル（Foundation Models）・LLM、Amazon Bedrock、プロンプトエンジニアリング（Zero-shot・Few-shot・Chain-of-Thought）、RAG（Retrieval Augmented Generation）、ファインチューニング、テキスト生成・画像生成・コード生成、トークン・コンテキストウィンドウ・Temperature、エージェント・ツール使用
3. THE Seed_Data_Module SHALL distribute Generative AI questions across difficulty levels with at least 4 questions at "基礎", at least 4 questions at "中級", and at least 4 questions at "上級"
4. THE Seed_Data_Module SHALL include Generative AI questions covering at least 5 of the 8 listed sub-topics
5. WHEN a Question_Entry has exam_domain "Generative AI", THE Question_Entry SHALL contain an ehime_trivia field of at least 30 characters referencing an Ehime prefecture location, culture, or historical fact
6. WHEN a Question_Entry has exam_domain "Generative AI", THE Question_Entry SHALL contain an aws_ai_explanation field of at least 50 characters explaining the relevant generative AI concept or AWS service

### Requirement 7: Responsible AI ドメインの問題拡充

**User Story:** As a AIF-C01受験準備者, I want Responsible AI ドメインの問題が十分な数存在すること, so that AI倫理・公平性・透明性・ガバナンスを網羅的に学習できる。

#### Acceptance Criteria

1. THE Seed_Data_Module SHALL contain at least 10 Question_Entry items with exam_domain "Responsible AI"
2. WHEN a Question_Entry has exam_domain "Responsible AI", THE Question_Entry SHALL cover at least one of the following sub-topics: 公平性・バイアス検出（SageMaker Clarify）、説明可能性（Explainability）、透明性・解釈可能性、プライバシー・データ保護、Human-in-the-Loop、AIガバナンス・規制対応、セキュリティ・ロバスト性、環境への影響・持続可能性. THE Seed_Data_Module SHALL cover at least 5 distinct sub-topics across all Responsible AI Question_Entry items.
3. THE Seed_Data_Module SHALL distribute Responsible AI questions across difficulty levels "基礎", "中級", and "上級", with at least 2 Question_Entry items at each difficulty level
4. WHEN a Question_Entry has exam_domain "Responsible AI", THE Question_Entry SHALL contain an ehime_trivia field of at least 30 characters referencing a specific Ehime prefecture location, culture, or historical fact
5. WHEN a Question_Entry has exam_domain "Responsible AI", THE Question_Entry SHALL contain an aws_ai_explanation field of at least 30 characters explaining the relevant responsible AI concept or AWS service used to implement it

### Requirement 8: コース構造の拡充

**User Story:** As a 学習者, I want 増加した問題数に対応したコース構造が整備されていること, so that 地域別・難易度別に体系的に学習を進められる。

#### Acceptance Criteria

1. THE Seed_Data_Module SHALL define at least 6 Course entries such that each of the three regions (中予, 南予, 東予) has at least one Course AND each of the three difficulty levels (基礎, 中級, 上級) has at least one Course
2. WHEN a new Course is added, THE Course SHALL have a unique id of at most 64 characters, a region set to one of "中予", "南予", or "東予", a difficulty set to one of "基礎", "中級", or "上級", a name of at least 1 and at most 200 characters, and a description of at least 1 character
3. THE Seed_Data_Module SHALL assign each Question_Entry to a course_id that matches an existing Course definition's id
4. IF a Question_Entry references a course_id that does not exist in the Course definitions, THEN THE Seed_Data_Module SHALL reject the data and report an error indicating the invalid course_id reference
5. WHEN questions are distributed across courses, THE Seed_Data_Module SHALL ensure each Course has at least 5 Question_Entry items assigned to that course_id

### Requirement 9: 問題データの品質保証

**User Story:** As a 開発者, I want すべての新規問題がバリデーション規則に適合すること, so that アプリケーション実行時にデータエラーが発生しない。

#### Acceptance Criteria

1. THE Question_Validator SHALL accept every Question_Entry defined in the Seed_Data_Module and return a ValidationResult with is_valid equal to true and an empty errors list
2. WHEN a Question_Entry is defined, THE Question_Entry SHALL have a unique id value among all Question_Entry records, formatted as a non-empty string with a maximum length of 50 characters
3. WHEN a Question_Entry is defined, THE Question_Entry SHALL have correct_choice_index as an integer in the range 0 to 3
4. WHEN a Question_Entry is defined, THE Question_Entry SHALL have all four choice fields (choice_1, choice_2, choice_3, choice_4) as non-empty strings each containing at least 1 non-whitespace character and no more than 200 characters
5. WHEN a Question_Entry is defined, THE Question_Entry SHALL have difficulty as one of "基礎", "中級", or "上級"
6. WHEN a Question_Entry is defined, THE Question_Entry SHALL have exam_domain as one of the 7 defined Exam_Domain values: "Cloud Concepts", "Security and Compliance", "Cloud Technology and Services", "Billing Pricing and Support", "AI and ML Fundamentals", "Generative AI", "Responsible AI"
7. WHEN a Question_Entry is defined, THE Question_Entry SHALL have text, ehime_trivia, aws_ai_explanation, and course_id as non-empty strings each containing at least 1 non-whitespace character
8. IF a Question_Entry fails any validation rule, THEN THE Question_Validator SHALL return a ValidationResult with is_valid equal to false and an errors list containing one error description string per failed rule

### Requirement 10: 試験カバレッジの網羅性

**User Story:** As a AWS認定試験受験者, I want 問題セット全体がCLF-C02とAIF-C01の出題範囲を網羅していること, so that 試験準備に必要なすべてのトピックを学習できる。

#### Acceptance Criteria

1. THE Seed_Data_Module SHALL contain at least 100 Question_Entry items in total across all 7 exam domains
2. THE Seed_Data_Module SHALL have at least the following minimum counts per exam_domain: Cloud Concepts ≥ 15, Security and Compliance ≥ 15, Cloud Technology and Services ≥ 20, Billing Pricing and Support ≥ 12, AI and ML Fundamentals ≥ 15, Generative AI ≥ 15, Responsible AI ≥ 10
3. THE Seed_Data_Module SHALL include questions covering at least 20 distinct AWS services referenced in question text, choice fields, or aws_ai_explanation (例: EC2, S3, Lambda, RDS, DynamoDB, VPC, IAM, CloudFront, SageMaker, Bedrock, CloudWatch, CloudFormation, SQS, SNS, KMS, CloudTrail, Route 53, ELB, Glacier, Trusted Advisor)
4. WHEN a Question_Entry references an AWS service in aws_ai_explanation, THE aws_ai_explanation SHALL name the service, state its primary purpose, and describe at least one functional characteristic
5. THE Seed_Data_Module SHALL distribute questions such that CLF-C02 domains (Cloud Concepts + Security and Compliance + Cloud Technology and Services + Billing Pricing and Support) contain at least 60 questions and AIF-C01 domains (AI and ML Fundamentals + Generative AI + Responsible AI) contain at least 40 questions

### Requirement 11: 愛媛トリビアの多様性

**User Story:** As a 学習者, I want 愛媛トリビアが多様な地域・テーマにわたること, so that 愛媛県全体の魅力を楽しみながら学習できる。

#### Acceptance Criteria

1. THE Seed_Data_Module SHALL include ehime_trivia content referencing locations or topics from all three regions: 中予（松山市・道後温泉等）、南予（宇和島・四万十等）、東予（今治・西条・新居浜等）, with a minimum of 5 question entries per region
2. THE Seed_Data_Module SHALL include ehime_trivia content covering at least 4 of the following 6 themes: 歴史的建造物・城郭、温泉・自然景観、伝統文化・祭り、特産品・名産物、産業・経済、文学・芸術, with a minimum of 2 question entries per covered theme
3. WHEN a Question_Entry has ehime_trivia, THE ehime_trivia SHALL contain a statement about Ehime prefecture that references a specific place name, product name, historical figure, or cultural practice identifiable within Ehime, and SHALL be between 30 and 200 characters in length
4. IF a Question_Entry's ehime_trivia does not reference a location or topic attributable to at least one of the three regions (中予, 南予, 東予), THEN THE Seed_Data_Module SHALL reject the entry and indicate the missing region attribution
