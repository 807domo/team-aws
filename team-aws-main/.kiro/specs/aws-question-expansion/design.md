# Design Document: AWS Question Expansion

## Overview

本設計は「愛媛探索AIクイズ」アプリケーションのクイズ問題データを33問から100問以上に拡張し、AWS認定試験（CLF-C02およびAIF-C01）の7つの出題ドメインを網羅的にカバーするための技術設計である。

既存の `app/data/seed_data.py` モジュールを拡張し、以下の目標を達成する：

- **問題数**: 33問 → 102問以上（CLF-C02: 62問以上、AIF-C01: 40問以上）
- **ドメインカバレッジ**: 7ドメインすべてを最低要件以上にカバー
- **コース構造**: 既存4コースを9コースに拡充（3地域×3難易度）
- **品質保証**: 全問題が既存バリデータを通過、ID一意性・外部キー整合性を維持
- **愛媛トリビア多様性**: 3地域（中予・南予・東予）× 6テーマをバランスよく配分

### 設計判断

1. **既存アーキテクチャの維持**: `seed_data.py` の `COURSES` / `QUESTIONS` リスト構造をそのまま拡張する。新しいモジュールやテーブルは追加しない。
2. **バリデータの拡張**: `question_validator.py` に `exam_domain` フィールドの検証と文字数制限のチェックを追加する。
3. **段階的拡張**: 既存33問はすべて保持し、新規問題を追加する形式とする。既存テストとの後方互換性を維持。

## Architecture

```mermaid
graph TD
    subgraph "Data Layer"
        A[seed_data.py] -->|COURSES list| B[CourseModel]
        A -->|QUESTIONS list| C[QuestionModel]
    end

    subgraph "Domain Layer"
        D[question_validator.py] -->|validate_question| E[ValidationResult]
        F[domain/models.py] -->|Difficulty, Region enums| D
    end

    subgraph "Database Layer"
        B --> G[(SQLite DB)]
        C --> G
    end

    subgraph "Test Layer"
        H[tests/integration/test_question_bank.py] -->|直接検証| A
        I[tests/properties/test_validation_properties.py] -->|PBT| D
        J[tests/integration/test_coverage.py] -->|カバレッジ検証| A
    end

    A -->|seed_database()| G
    D -->|各問題を検証| A
```

### コンポーネント構成

| コンポーネント | 変更種別 | 内容 |
|---|---|---|
| `app/data/seed_data.py` | 拡張 | COURSES: 4→9、QUESTIONS: 33→102+ |
| `app/domain/question_validator.py` | 拡張 | exam_domain 検証、文字数制限追加 |
| `tests/integration/test_question_bank.py` | 更新 | 最小問題数チェック更新 |
| `tests/integration/test_coverage.py` | 新規 | ドメイン別カバレッジ・トピック検証 |
| `tests/properties/test_seed_data_properties.py` | 新規 | シードデータ品質のPBT |

## Components and Interfaces

### 1. seed_data.py の拡張

#### COURSES リスト（4 → 9コース）

新規追加コース：

| ID | Name | Region | Difficulty |
|---|---|---|---|
| `matsuyama-basic` | 松山城コース（基礎） | 中予 | 基礎 | (既存)
| `uwajima-intermediate` | 宇和島コース（中級） | 南予 | 中級 | (既存)
| `shimanami-advanced` | しまなみ海道コース（上級） | 東予 | 上級 | (既存)
| `dogo-ai-basic` | 道後温泉AIコース（基礎） | 中予 | 基礎 | (既存)
| `nanyo-basic` | 南予探索コース（基礎） | 南予 | 基礎 | (新規)
| `toyo-intermediate` | 東予産業コース（中級） | 東予 | 中級 | (新規)
| `chuyo-advanced` | 中予先端コース（上級） | 中予 | 上級 | (新規)
| `nanyo-advanced` | 南予上級コース（上級） | 南予 | 上級 | (新規)
| `toyo-basic` | 東予基礎コース（基礎） | 東予 | 基礎 | (新規)

#### QUESTIONS リスト（33 → 102+問）

ドメイン別目標問題数配分：

| Exam Domain | 最低要件 | 目標数 | 難易度配分 |
|---|---|---|---|
| Cloud Concepts | 15 | 15 | 基礎5, 中級5, 上級5 |
| Security and Compliance | 15 | 15 | 基礎5, 中級5, 上級5 |
| Cloud Technology and Services | 20 | 22 | 基礎7, 中級8, 上級7 |
| Billing Pricing and Support | 12 | 12 | 基礎4, 中級4, 上級4 |
| AI and ML Fundamentals | 15 | 15 | 基礎5, 中級5, 上級5 |
| Generative AI | 15 | 15 | 基礎5, 中級5, 上級5 |
| Responsible AI | 10 | 10 | 基礎3, 中級4, 上級3 |
| **合計** | **102** | **104** | |

### 2. question_validator.py の拡張

現在のバリデータに以下の検証を追加する：

```python
# 有効な exam_domain 値
VALID_EXAM_DOMAINS = {
    "Cloud Concepts",
    "Security and Compliance",
    "Cloud Technology and Services",
    "Billing Pricing and Support",
    "AI and ML Fundamentals",
    "Generative AI",
    "Responsible AI",
}

def validate_question(question_data: dict) -> ValidationResult:
    # ... 既存の検証 ...
    
    # exam_domain の検証（新規追加）
    exam_domain = question_data.get("exam_domain")
    if not exam_domain or not isinstance(exam_domain, str):
        errors.append("exam_domain: 試験ドメインは必須です")
    elif exam_domain not in VALID_EXAM_DOMAINS:
        errors.append(f"exam_domain: 試験ドメインは {VALID_EXAM_DOMAINS} のいずれかである必要があります")
    
    # id の検証（新規追加）
    question_id = question_data.get("id")
    if not question_id or not isinstance(question_id, str) or not question_id.strip():
        errors.append("id: 問題IDは空にできません")
    elif len(question_id) > 50:
        errors.append("id: 問題IDは50文字以内である必要があります")
    
    # 文字数制限の検証（新規追加）
    if isinstance(ehime_trivia, str) and len(ehime_trivia) > 200:
        errors.append("ehime_trivia: 愛媛トリビアは200文字以内である必要があります")
    
    for field_name in _CHOICE_FIELDS:
        value = question_data.get(field_name)
        if isinstance(value, str) and len(value) > 200:
            errors.append(f"{field_name}: 選択肢は200文字以内である必要があります")
```

### 3. 問題ID命名規則

```
q-{domain_prefix}-{sequence:03d}

domain_prefix:
  cc = Cloud Concepts
  sc = Security and Compliance
  ct = Cloud Technology and Services
  bp = Billing Pricing and Support
  ai = AI and ML Fundamentals
  ga = Generative AI
  ra = Responsible AI

例: q-cc-001, q-sc-015, q-ct-022, q-ga-012
```

### 4. コースへの問題配分ロジック

問題は以下のルールでコースに配分する：

1. **難易度一致**: 問題の `difficulty` とコースの `difficulty` が一致
2. **地域バランス**: 各地域のコースに均等に配分
3. **最低5問/コース**: 各コースに最低5問を保証

配分マッピング：

| Difficulty | 中予 | 南予 | 東予 |
|---|---|---|---|
| 基礎 | matsuyama-basic, dogo-ai-basic | nanyo-basic | toyo-basic |
| 中級 | - | uwajima-intermediate | toyo-intermediate |
| 上級 | chuyo-advanced | nanyo-advanced | shimanami-advanced |

## Data Models

### Question_Entry 辞書構造（変更なし）

```python
Question_Entry = TypedDict("Question_Entry", {
    "id": str,                    # 一意ID (max 50 chars, format: q-{prefix}-{num})
    "course_id": str,             # 外部キー: COURSES[].id
    "text": str,                  # 問題文 (非空)
    "choice_1": str,              # 選択肢1 (非空, max 200 chars)
    "choice_2": str,              # 選択肢2 (非空, max 200 chars)
    "choice_3": str,              # 選択肢3 (非空, max 200 chars)
    "choice_4": str,              # 選択肢4 (非空, max 200 chars)
    "correct_choice_index": int,  # 正解インデックス (0-3)
    "ehime_trivia": str,          # 愛媛トリビア (30-200 chars)
    "aws_ai_explanation": str,    # AWS/AI解説 (50-200 chars or 20+ for some domains)
    "difficulty": str,            # "基礎" | "中級" | "上級"
    "exam_domain": str,           # 7つのドメインのいずれか
})
```

### Course 辞書構造（変更なし）

```python
Course_Entry = TypedDict("Course_Entry", {
    "id": str,           # 一意ID (max 64 chars)
    "name": str,         # コース名 (1-200 chars)
    "region": str,       # "中予" | "南予" | "東予"
    "difficulty": str,   # "基礎" | "中級" | "上級"
    "description": str,  # 説明 (非空)
})
```

### ドメイン別サブトピック定義

各ドメインでカバーすべきサブトピック：

```python
DOMAIN_SUBTOPICS = {
    "Cloud Concepts": [
        "クラウドの価値提案（コスト削減・俊敏性・弾力性）",
        "Well-Architected Frameworkの柱",
        "クラウド移行戦略",
        "グローバルインフラストラクチャ（リージョン・AZ・エッジロケーション）",
    ],
    "Security and Compliance": [
        "共有責任モデル",
        "IAM（ユーザー・グループ・ロール・ポリシー）",
        "MFA・アクセスキー管理",
        "データ暗号化（KMS・保存時・転送時）",
        "AWS CloudTrail・AWS Config・AWS Security Hub",
        "VPCセキュリティ（セキュリティグループ・NACL）",
        "コンプライアンスプログラム・AWS Artifact",
    ],
    "Cloud Technology and Services": [
        "コンピューティング（EC2・Lambda・ECS・Fargate）",
        "ストレージ（S3・EBS・EFS・S3 Glacier）",
        "ネットワーキング（VPC・CloudFront・Route 53・Direct Connect）",
        "データベース（RDS・DynamoDB・ElastiCache・Redshift）",
        "マネジメント・ガバナンス（CloudWatch・CloudFormation・Systems Manager）",
        "アプリケーション統合（SQS・SNS・Step Functions）",
    ],
    "Billing Pricing and Support": [
        "料金モデル（オンデマンド・リザーブド・スポット・Savings Plans）",
        "無料利用枠（12ヶ月無料・常時無料・トライアル）",
        "AWS料金計算ツール（Pricing Calculator）",
        "コスト管理（Cost Explorer・Budgets・Cost and Usage Report）",
        "サポートプラン（Basic・Developer・Business・Enterprise）",
        "AWS Organizations・一括請求",
    ],
    "AI and ML Fundamentals": [
        "教師あり学習（分類・回帰）",
        "教師なし学習（クラスタリング・次元削減）",
        "強化学習",
        "MLパイプライン（データ前処理・特徴量エンジニアリング・訓練・評価）",
        "Amazon SageMaker",
        "Amazon Rekognition・Comprehend・Textract・Translate",
        "Amazon Forecast・Personalize",
    ],
    "Generative AI": [
        "基盤モデル（Foundation Models）・LLM",
        "Amazon Bedrock",
        "プロンプトエンジニアリング（Zero-shot・Few-shot・Chain-of-Thought）",
        "RAG（Retrieval Augmented Generation）",
        "ファインチューニング",
        "テキスト生成・画像生成・コード生成",
        "トークン・コンテキストウィンドウ・Temperature",
        "エージェント・ツール使用",
    ],
    "Responsible AI": [
        "公平性・バイアス検出（SageMaker Clarify）",
        "説明可能性（Explainability）",
        "透明性・解釈可能性",
        "プライバシー・データ保護",
        "Human-in-the-Loop",
        "AIガバナンス・規制対応",
        "セキュリティ・ロバスト性",
        "環境への影響・持続可能性",
    ],
}
```



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Field length invariants per exam domain

*For any* Question_Entry in the seed data, the `ehime_trivia` field SHALL have a length between 30 and 200 characters, AND the `aws_ai_explanation` field SHALL meet the minimum length requirement for its exam domain (50 characters for Cloud Concepts, Cloud Technology and Services, Billing Pricing and Support, and Generative AI; 20 characters for Security and Compliance, AI and ML Fundamentals; 30 characters for Responsible AI).

**Validates: Requirements 1.5, 1.6, 2.5, 2.6, 3.5, 3.6, 4.4, 4.5, 5.4, 5.5, 6.5, 6.6, 7.4, 7.5, 11.3**

### Property 2: Validation acceptance of all seed data

*For any* Question_Entry defined in the QUESTIONS list of the Seed_Data_Module, calling `validate_question()` SHALL return a ValidationResult with `is_valid=True` and an empty `errors` list.

**Validates: Requirements 9.1**

### Property 3: Referential integrity between questions and courses

*For any* Question_Entry in the QUESTIONS list, its `course_id` value SHALL match the `id` of exactly one entry in the COURSES list. Conversely, *for any* generated question data with a `course_id` that does not appear in the COURSES list, the system SHALL reject that data.

**Validates: Requirements 8.3, 8.4**

### Property 4: Exam domain value validation

*For any* Question_Entry, the `exam_domain` field SHALL be one of exactly 7 valid values: "Cloud Concepts", "Security and Compliance", "Cloud Technology and Services", "Billing Pricing and Support", "AI and ML Fundamentals", "Generative AI", "Responsible AI". *For any* question data with an `exam_domain` value not in this set, `validate_question()` SHALL return `is_valid=False` with an error identifying the `exam_domain` field.

**Validates: Requirements 9.6**

### Property 5: Question ID uniqueness and format constraints

*For any* Question_Entry in the QUESTIONS list, the `id` field SHALL be a non-empty string of at most 50 characters containing at least one non-whitespace character, AND all `id` values across the entire QUESTIONS list SHALL be distinct from one another.

**Validates: Requirements 9.2**

## Error Handling

### バリデーションエラー

| エラー条件 | エラーメッセージ | 対処 |
|---|---|---|
| exam_domain が無効 | `"exam_domain: 試験ドメインは {VALID_EXAM_DOMAINS} のいずれかである必要があります"` | 7つの有効値のいずれかに修正 |
| id が空 | `"id: 問題IDは空にできません"` | 命名規則に従いID付与 |
| id が50文字超 | `"id: 問題IDは50文字以内である必要があります"` | IDを短縮 |
| course_id が存在しないコース参照 | `"course_id: コースIDは空にできません"` or DB外部キー制約違反 | COURSES に定義されたIDを使用 |
| ehime_trivia が200文字超 | `"ehime_trivia: 愛媛トリビアは200文字以内である必要があります"` | テキストを短縮 |
| choice が200文字超 | `"{field_name}: 選択肢は200文字以内である必要があります"` | 選択肢テキストを短縮 |

### データベースシーディングエラー

| エラー条件 | 挙動 | 対処 |
|---|---|---|
| 既にデータ存在（冪等性） | `seed_database()` が `False` を返しスキップ | 正常動作、対処不要 |
| 外部キー制約違反 | SQLAlchemy IntegrityError 発生 | course_id を修正 |
| 重複ID | SQLAlchemy IntegrityError 発生 | ID命名を確認 |

### エラー集約

`validate_question()` は複数のエラーを同時に検出し、すべてのエラーを `errors` リストに集約して返す。これにより、問題データ作成者は一度の検証で全ての修正点を把握できる。

## Testing Strategy

### テスト構成

```
tests/
├── properties/
│   ├── test_validation_properties.py      (既存: 更新)
│   └── test_seed_data_properties.py       (新規: シードデータ品質PBT)
├── integration/
│   ├── test_question_bank.py              (既存: 更新)
│   └── test_domain_coverage.py            (新規: ドメイン別カバレッジ検証)
└── unit/
    └── test_question_validator.py         (既存: 更新)
```

### Property-Based Testing（Hypothesis）

PBTライブラリ: **Hypothesis** (既にプロジェクトで使用中、`hypothesis>=6.98.0`)

各プロパティテストは最低100イテレーションで実行する。

| Property | テストファイル | 検証内容 |
|---|---|---|
| Property 1 | `test_seed_data_properties.py` | 全問題のフィールド長制約 |
| Property 2 | `test_seed_data_properties.py` | 全問題のバリデーション通過 |
| Property 3 | `test_seed_data_properties.py` | course_id参照整合性 |
| Property 4 | `test_validation_properties.py` | exam_domain検証（有効値受理/無効値拒否） |
| Property 5 | `test_seed_data_properties.py` | ID一意性・フォーマット制約 |

**タグ形式**: `Feature: aws-question-expansion, Property {number}: {property_text}`

### Unit Tests（例示ベース）

- exam_domain バリデーションの具体的なテストケース
- id フィールドのバウンダリ値テスト（0文字、50文字、51文字）
- ehime_trivia の文字数境界値テスト（29文字、30文字、200文字、201文字）

### Integration Tests（カバレッジ検証）

`test_domain_coverage.py` で以下を検証：

- 各ドメインの最低問題数（Requirements 1.1〜7.1, 10.2）
- 難易度分布の要件（Requirements 1.3, 2.3, 3.4, 4.3, 5.3, 6.3, 7.3）
- サブトピックカバレッジ（Requirements 1.4, 2.4, 3.3, 4.2, 5.6, 6.4, 7.2）
- 合計100問以上（Requirement 10.1）
- CLF-C02 ≥ 60問、AIF-C01 ≥ 40問（Requirement 10.5）
- AWSサービス20種以上の参照（Requirement 10.3）
- 愛媛トリビアの地域・テーマ多様性（Requirements 11.1, 11.2）
- 各コース最低5問の配分（Requirement 8.5）
- コース構造の要件（Requirement 8.1, 8.2）

### テスト実行

```bash
# 全テスト実行
pytest tests/ -v

# プロパティテストのみ
pytest tests/properties/ -v

# カバレッジ検証のみ
pytest tests/integration/test_domain_coverage.py -v
```
