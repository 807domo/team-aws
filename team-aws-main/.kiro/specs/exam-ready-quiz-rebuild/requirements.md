# Requirements Document

## Introduction

愛媛探索AIクイズアプリケーションのクイズ問題および用語集を全面的に作り直す。AWS Certified Cloud Practitioner（CLF-C02）とAWS Certified AI Practitioner（AIF-C01）の2つの試験に合格できるレベルの問題を、初級（南予）・中級（中予）・上級（東予）の3難易度で体系的に構築する。問題は愛媛県の地域情報をコンテキストとして含め、用語集は両試験の全ドメインを網羅する。

## Glossary

- **Quiz_Application**: 愛媛探索AIクイズ（FastAPI + SQLAlchemy + Jinja2 + HTMXで構築されたWebアプリケーション）
- **Seed_Data**: クイズ問題の初期データを格納するPythonモジュール（app/data/seed_data.py および関連ファイル）
- **Glossary_Seed**: 用語集の初期データを格納するPythonモジュール（app/data/glossary_seed.py）
- **Question_Record**: 問題1件のデータ構造（id, course_id, text, choice_1〜4, correct_choice_index, ehime_trivia, aws_ai_explanation, difficulty, exam_domain）
- **Course**: 各地域内のステージ（コース）。3地域×10ステージ＝30コース
- **CLF_C02**: AWS Certified Cloud Practitioner試験（CLF-C02）
- **AIF_C01**: AWS Certified AI Practitioner試験（AIF-C01）
- **CCP_Domain**: CLF-C02試験のドメイン（Cloud Concepts, Security and Compliance, Cloud Technology and Services, Billing Pricing and Support）
- **AIF_Domain**: AIF-C01試験のドメイン（AI and ML Fundamentals, Generative AI Concepts, Applications of Foundation Models, Guidelines for Responsible AI, Security Compliance and Governance for AI Solutions）
- **Difficulty_Level**: 問題の難易度レベル（初級＝南予＝基本的な用語の記憶・理解、中級＝中予＝応用・シナリオベース、上級＝東予＝複数概念の統合・高度シナリオ）
- **Ehime_Context**: 問題文中に含まれる愛媛県の地域情報（観光地、名産品、文化財、産業など）

## Requirements

### Requirement 1: クイズ問題の全面再構築

**User Story:** As a 資格取得を目指す学習者, I want CLF-C02とAIF-C01の両試験範囲を網羅した問題セットで学習したい, so that このクイズアプリだけで試験合格に十分な知識を身につけられる。

#### Acceptance Criteria

1. THE Seed_Data SHALL contain a minimum of 300 Question_Record entries distributed across all 30 Course instances.
2. WHEN questions are assigned to courses in the 南予 region, THE Seed_Data SHALL set the difficulty field to "基礎" and design the question as basic recall of a single concept or term definition.
3. WHEN questions are assigned to courses in the 中予 region, THE Seed_Data SHALL set the difficulty field to "中級" and design the question as applied knowledge requiring scenario-based reasoning.
4. WHEN questions are assigned to courses in the 東予 region, THE Seed_Data SHALL set the difficulty field to "上級" and design the question as advanced multi-concept integration or complex scenario analysis.
5. THE Seed_Data SHALL distribute questions across CCP_Domain categories with approximate weightings: Cloud Concepts 24%, Security and Compliance 30%, Cloud Technology and Services 34%, Billing Pricing and Support 12%.
6. THE Seed_Data SHALL distribute questions across AIF_Domain categories with approximate weightings: AI and ML Fundamentals 20%, Generative AI Concepts 24%, Applications of Foundation Models 28%, Guidelines for Responsible AI 14%, Security Compliance and Governance for AI Solutions 14%.
7. WHEN a Question_Record is created, THE Seed_Data SHALL assign each question to exactly one exam_domain from either CCP_Domain or AIF_Domain.
8. THE Seed_Data SHALL allocate approximately 5 to 10 Question_Record entries per Course to ensure balanced content distribution.

### Requirement 2: 問題データ構造の維持

**User Story:** As a 開発者, I want 問題データが既存のデータ構造を維持したまま作り直される, so that アプリケーションコードの変更なしに問題を差し替えられる。

#### Acceptance Criteria

1. THE Question_Record SHALL contain all required fields: id (unique string), course_id (existing Course id reference), text (question body string), choice_1 through choice_4 (four answer option strings), correct_choice_index (integer 0-3), ehime_trivia (Ehime Prefecture trivia string), aws_ai_explanation (technical explanation string), difficulty (one of "基礎", "中級", "上級"), and exam_domain (domain name string).
2. THE Seed_Data SHALL use the existing id naming convention with format "{region}-{domain-abbreviation}-{sequential-number}" ensuring global uniqueness across all questions.
3. THE Seed_Data SHALL reference only valid course_id values from the existing 30 Course definitions (nanyo-stage-01 through nanyo-stage-10, chuyo-stage-01 through chuyo-stage-08, toyo-stage-01 through toyo-stage-10).
4. THE Question_Record SHALL set correct_choice_index to an integer value between 0 and 3 inclusive, corresponding to choice_1 through choice_4.
5. THE Seed_Data SHALL maintain compatibility with the existing QuestionModel SQLAlchemy schema and seed insertion logic.

### Requirement 3: 愛媛県コンテキストの組み込み

**User Story:** As a クイズ利用者, I want 各問題に愛媛県の地域情報が含まれている, so that AWS知識と愛媛県の文化・観光・産業を同時に学べる。

#### Acceptance Criteria

1. WHEN a Question_Record is created, THE Seed_Data SHALL include Ehime_Context in the text field as an introductory hook or analogy related to Ehime Prefecture.
2. THE Question_Record SHALL contain a non-empty ehime_trivia field providing factual information about the referenced Ehime Prefecture location, product, culture, or industry.
3. WHEN questions are assigned to 南予 region courses, THE Seed_Data SHALL reference locations and features from the 南予 area (宇和島、八幡浜、西予、大洲、内子、愛南 etc.).
4. WHEN questions are assigned to 中予 region courses, THE Seed_Data SHALL reference locations and features from the 中予 area (松山、道後温泉、砥部、伊予、東温 etc.).
5. WHEN questions are assigned to 東予 region courses, THE Seed_Data SHALL reference locations and features from the 東予 area (今治、新居浜、西条、四国中央、しまなみ海道 etc.).
6. THE Question_Record SHALL contain a non-empty aws_ai_explanation field explaining the correct answer with reference to AWS or AI concepts and official terminology.

### Requirement 4: CLF-C02試験ドメインの完全カバレッジ

**User Story:** As a Cloud Practitioner受験者, I want 全4ドメインの重要トピックが問題として出題される, so that 試験範囲の知識を漏れなく学習できる。

#### Acceptance Criteria

1. THE Seed_Data SHALL contain questions covering Cloud Concepts domain topics including: cloud value proposition, AWS global infrastructure, cloud economics, cloud architecture design principles, migration strategies, and Well-Architected Framework.
2. THE Seed_Data SHALL contain questions covering Security and Compliance domain topics including: shared responsibility model, IAM concepts, security best practices, AWS security services (GuardDuty, Inspector, Shield, WAF), compliance frameworks, and data protection.
3. THE Seed_Data SHALL contain questions covering Cloud Technology and Services domain topics including: compute services (EC2, Lambda, ECS), storage services (S3, EBS, EFS, Glacier), database services (RDS, DynamoDB, Aurora), networking services (VPC, CloudFront, Route 53, ELB), and management tools (CloudWatch, CloudTrail, CloudFormation).
4. THE Seed_Data SHALL contain questions covering Billing Pricing and Support domain topics including: pricing models, billing dashboard, Cost Explorer, Budgets, support plans, Trusted Advisor, and pricing calculators.
5. THE Seed_Data SHALL contain a minimum of 70 questions for CLF-C02 Cloud Concepts domain, a minimum of 90 questions for Security and Compliance domain, a minimum of 100 questions for Cloud Technology and Services domain, and a minimum of 35 questions for Billing Pricing and Support domain.

### Requirement 5: AIF-C01試験ドメインの完全カバレッジ

**User Story:** As a AI Practitioner受験者, I want 全5ドメインの重要トピックが問題として出題される, so that AI試験範囲の知識を漏れなく学習できる。

#### Acceptance Criteria

1. THE Seed_Data SHALL contain questions covering AI and ML Fundamentals domain topics including: types of machine learning (supervised, unsupervised, reinforcement), neural networks, training and evaluation, feature engineering, bias and variance, and AWS ML services (SageMaker).
2. THE Seed_Data SHALL contain questions covering Generative AI Concepts domain topics including: foundation models, large language models, transformers architecture, training methods (pre-training, fine-tuning, RLHF), prompt engineering techniques, and model evaluation.
3. THE Seed_Data SHALL contain questions covering Applications of Foundation Models domain topics including: Amazon Bedrock, RAG architecture, agents, embeddings, model selection criteria, inference optimization, and multi-modal AI applications.
4. THE Seed_Data SHALL contain questions covering Guidelines for Responsible AI domain topics including: fairness, transparency, explainability, bias detection and mitigation, human oversight, and AWS responsible AI tools.
5. THE Seed_Data SHALL contain questions covering Security Compliance and Governance for AI Solutions domain topics including: data privacy in ML pipelines, model access controls, AI governance frameworks, regulatory compliance, and AWS AI security services.
6. THE Seed_Data SHALL contain a minimum of 25 questions for AI and ML Fundamentals domain, a minimum of 30 questions for Generative AI Concepts domain, a minimum of 35 questions for Applications of Foundation Models domain, a minimum of 18 questions for Guidelines for Responsible AI domain, and a minimum of 18 questions for Security Compliance and Governance for AI Solutions domain.

### Requirement 6: 用語集の全面再構築

**User Story:** As a 学習者, I want 両試験に登場するすべてのAWSサービス名・AI/ML概念・セキュリティ用語が用語集に掲載されている, so that クイズで出てきた知らない用語をすぐに確認できる。

#### Acceptance Criteria

1. THE Glossary_Seed SHALL contain a minimum of 150 glossary term entries covering both CLF-C02 and AIF-C01 exam scopes.
2. THE Glossary_Seed SHALL organize terms into the following categories: "クラウド基礎", "AWSコンピューティング", "AWSストレージ・データベース", "AWSネットワーキング", "AWSセキュリティ", "AWS管理・ガバナンス", "AWS料金・サポート", "AI・ML基礎", "生成AI・基盤モデル", "AWS AIサービス", "責任あるAI".
3. THE Glossary_Seed SHALL contain entries for every AWS service name referenced in any Question_Record in the Seed_Data.
4. THE Glossary_Seed SHALL contain entries for every AI and ML concept referenced in any Question_Record in the Seed_Data.
5. WHEN a glossary entry is created, THE Glossary_Seed SHALL include category (non-empty string), sort_order (non-negative integer sequential within category), term (non-empty string), and description (non-empty string of at least 20 characters explaining the term).
6. THE Glossary_Seed SHALL maintain compatibility with the existing GlossaryTermModel schema and seed_glossary insertion logic.
7. THE Glossary_Seed SHALL ensure no duplicate term values exist across all categories.

### Requirement 7: 問題品質基準の遵守

**User Story:** As a 学習者, I want 各問題が試験レベルの品質を持つ, so that 実際の試験形式に慣れながら正確な知識を習得できる。

#### Acceptance Criteria

1. WHEN a Question_Record is created for 初級 difficulty, THE Seed_Data SHALL design the question to test recall of a single fact, definition, or basic concept with one clearly correct answer and three plausible but incorrect distractors.
2. WHEN a Question_Record is created for 中級 difficulty, THE Seed_Data SHALL design the question to require application of knowledge to a scenario, with distractors that represent common misconceptions or partially correct answers.
3. WHEN a Question_Record is created for 上級 difficulty, THE Seed_Data SHALL design the question to require synthesis of multiple concepts, evaluation of trade-offs, or analysis of complex multi-service architectures.
4. THE Question_Record SHALL provide exactly four answer choices where exactly one choice is correct and the remaining three are plausible distractors.
5. THE Question_Record SHALL ensure the aws_ai_explanation field explains why the correct answer is correct and provides context about the underlying AWS or AI concept.
6. THE Question_Record SHALL ensure all answer choices are mutually exclusive and unambiguous in determining the single correct answer.

### Requirement 8: 既存シードデータの完全置換

**User Story:** As a 開発者, I want 既存の問題データと用語集データを完全に新しいデータに置換する, so that 古い問題が残らず一貫性のある新しい問題セットが利用できる。

#### Acceptance Criteria

1. WHEN the new Seed_Data is deployed, THE Quiz_Application SHALL replace all existing Question_Record entries with the new question set.
2. WHEN the new Glossary_Seed is deployed, THE Quiz_Application SHALL replace all existing glossary entries with the new glossary set.
3. THE Seed_Data SHALL maintain the existing 30 Course definitions (id, name, region, difficulty, description) without modification.
4. THE Seed_Data SHALL preserve the existing Python module structure (seed_data.py with COURSES and QUESTIONS lists, glossary_seed.py with GLOSSARY_SEED_DATA list).
5. IF the total question count exceeds the practical limit of a single Python file, THEN THE Seed_Data SHALL split questions into multiple files (seed_data.py, seed_data_extra.py, etc.) following the existing pattern of importing EXTRA_QUESTIONS.
