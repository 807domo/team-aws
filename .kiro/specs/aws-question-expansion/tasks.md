# Implementation Plan: AWS Question Expansion

## Overview

既存の「愛媛探索AIクイズ」アプリケーションのシードデータを33問から102問以上に拡張し、AWS認定試験（CLF-C02、AIF-C01）の7ドメインを網羅する。コース構造を4→9に拡充し、バリデータに `exam_domain` 検証・文字数制限を追加する。プロパティベーステスト（Hypothesis）とインテグレーションテストでデータ品質を保証する。

## Tasks

- [x] 1. コース構造の拡充と question_validator.py の拡張
  - [x] 1.1 seed_data.py に新規5コースを追加する
    - `COURSES` リストに `nanyo-basic`, `toyo-intermediate`, `chuyo-advanced`, `nanyo-advanced`, `toyo-basic` の5エントリを追加
    - 各コースは id (max 64文字), name (1-200文字), region ("中予"/"南予"/"東予"), difficulty ("基礎"/"中級"/"上級"), description (非空) を持つ
    - 3地域×3難易度の9コース体制を完成させる
    - _Requirements: 8.1, 8.2_

  - [x] 1.2 question_validator.py に exam_domain 検証を追加する
    - `VALID_EXAM_DOMAINS` セット定数を定義（7つの有効値）
    - `validate_question()` に exam_domain フィールドの存在チェックと有効値チェックを追加
    - 無効な exam_domain の場合にエラーメッセージを errors リストに追加
    - _Requirements: 9.6, 9.1_

  - [x] 1.3 question_validator.py に id フィールド検証と文字数制限を追加する
    - id フィールドの空チェック・50文字上限チェックを追加
    - ehime_trivia の200文字上限チェックを追加
    - choice_1〜4 の200文字上限チェックを追加
    - _Requirements: 9.2, 9.4, 11.3_

  - [x]* 1.4 question_validator.py の新規バリデーションの単体テストを追加する
    - `tests/unit/test_question_validator.py` に exam_domain バリデーションのテストケースを追加
    - id フィールドの境界値テスト（0文字、50文字、51文字）を追加
    - ehime_trivia の文字数境界値テスト（200文字、201文字）を追加
    - choice フィールドの200文字境界値テストを追加
    - _Requirements: 9.2, 9.4, 9.6, 9.8_

- [x] 2. Cloud Concepts / Security and Compliance ドメインの問題追加
  - [x] 2.1 Cloud Concepts ドメインの問題15問を seed_data.py に追加する
    - ID命名: `q-cc-001` 〜 `q-cc-015`
    - 難易度配分: 基礎5問、中級5問、上級5問
    - サブトピック: クラウドの価値提案、Well-Architected Framework、クラウド移行戦略、グローバルインフラストラクチャの4トピック中3以上をカバー
    - 各問題に ehime_trivia (30-200文字) と aws_ai_explanation (50文字以上) を付与
    - course_id は難易度に応じたコースを割り当て
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

  - [x] 2.2 Security and Compliance ドメインの問題15問を seed_data.py に追加する
    - ID命名: `q-sc-001` 〜 `q-sc-015`
    - 難易度配分: 基礎5問、中級5問、上級5問
    - サブトピック: 共有責任モデル、IAM、MFA、暗号化、CloudTrail/Config/Security Hub、VPCセキュリティ、コンプライアンスの7トピック中5以上をカバー
    - 各問題に ehime_trivia (20文字以上) と aws_ai_explanation (20文字以上) を付与
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [x]* 2.3 Property 1 テスト: フィールド長制約の検証
    - `tests/properties/test_seed_data_properties.py` を新規作成
    - Cloud Concepts / Security and Compliance の全問題に対して ehime_trivia (30-200文字) と aws_ai_explanation (ドメイン別最低文字数) の制約を Hypothesis で検証
    - **Property 1: Field length invariants per exam domain**
    - **Validates: Requirements 1.5, 1.6, 2.5, 2.6**

- [x] 3. Cloud Technology and Services / Billing Pricing and Support ドメインの問題追加
  - [x] 3.1 Cloud Technology and Services ドメインの問題22問を seed_data.py に追加する
    - ID命名: `q-ct-001` 〜 `q-ct-022`
    - 難易度配分: 基礎7問、中級8問、上級7問
    - サブトピック: コンピューティング、ストレージ、ネットワーキング、データベース、マネジメント、アプリケーション統合の6カテゴリ各2問以上
    - 各問題に ehime_trivia (30-200文字) と aws_ai_explanation (50文字以上) を付与
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [x] 3.2 Billing Pricing and Support ドメインの問題12問を seed_data.py に追加する
    - ID命名: `q-bp-001` 〜 `q-bp-012`
    - 難易度配分: 基礎4問、中級4問、上級4問
    - サブトピック: 料金モデル、無料利用枠、Pricing Calculator、コスト管理、サポートプラン、Organizationsの6トピック中4以上をカバー
    - 各問題に ehime_trivia (30-200文字) と aws_ai_explanation (50文字以上) を付与
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 4. Checkpoint - CLF-C02ドメイン完了確認
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. AI and ML Fundamentals / Generative AI / Responsible AI ドメインの問題追加
  - [x] 5.1 AI and ML Fundamentals ドメインの問題15問を seed_data.py に追加する
    - ID命名: `q-ai-001` 〜 `q-ai-015`
    - 難易度配分: 基礎5問、中級5問、上級5問
    - サブトピック: 教師あり学習、教師なし学習、強化学習、MLパイプライン、SageMaker、Rekognition等、Forecast等の7トピック中5以上をカバー
    - 各問題に ehime_trivia (20文字以上) と aws_ai_explanation (20文字以上) を付与
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [x] 5.2 Generative AI ドメインの問題15問を seed_data.py に追加する
    - ID命名: `q-ga-001` 〜 `q-ga-015`
    - 難易度配分: 基礎5問、中級5問、上級5問
    - サブトピック: 基盤モデル、Bedrock、プロンプトエンジニアリング、RAG、ファインチューニング、テキスト/画像/コード生成、トークン/Temperature、エージェントの8トピック中5以上をカバー
    - 各問題に ehime_trivia (30-200文字) と aws_ai_explanation (50文字以上) を付与
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

  - [x] 5.3 Responsible AI ドメインの問題10問を seed_data.py に追加する
    - ID命名: `q-ra-001` 〜 `q-ra-010`
    - 難易度配分: 基礎3問、中級4問、上級3問
    - サブトピック: 公平性、説明可能性、透明性、プライバシー、Human-in-the-Loop、ガバナンス、セキュリティ、環境影響の8トピック中5以上をカバー
    - 各問題に ehime_trivia (30-200文字) と aws_ai_explanation (30文字以上) を付与
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [x]* 5.4 Property 2 テスト: 全シードデータのバリデーション通過
    - `tests/properties/test_seed_data_properties.py` に追加
    - QUESTIONS リストの全問題に対して `validate_question()` を呼び出し `is_valid=True` かつ `errors=[]` を検証
    - **Property 2: Validation acceptance of all seed data**
    - **Validates: Requirements 9.1**

  - [x]* 5.5 Property 5 テスト: 問題ID一意性・フォーマット制約
    - `tests/properties/test_seed_data_properties.py` に追加
    - 全問題の id が非空・50文字以内・一意であることを Hypothesis で検証
    - **Property 5: Question ID uniqueness and format constraints**
    - **Validates: Requirements 9.2**

- [x] 6. Checkpoint - AIF-C01ドメイン完了確認
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. 既存問題のexam_domain付与と参照整合性の確保
  - [x] 7.1 既存33問に exam_domain フィールドを付与し、ID命名規則に統一する
    - 既存の QUESTIONS エントリすべてに `exam_domain` フィールドを追加（適切なドメインを割り当て）
    - 既存問題の id を `q-{prefix}-{seq:03d}` 形式に更新（新規IDと重複しないよう注意）
    - 既存問題の course_id を新9コース体制に合わせて再配分
    - _Requirements: 8.3, 9.1, 9.2, 9.6_

  - [x]* 7.2 Property 3 テスト: コース参照整合性
    - `tests/properties/test_seed_data_properties.py` に追加
    - 全問題の course_id が COURSES リストの id に存在することを Hypothesis で検証
    - 存在しない course_id を持つデータが拒否されることを検証
    - **Property 3: Referential integrity between questions and courses**
    - **Validates: Requirements 8.3, 8.4**

  - [x]* 7.3 Property 4 テスト: exam_domain 値の検証
    - `tests/properties/test_validation_properties.py` に追加
    - 有効な exam_domain 値が受理されること、無効値が拒否されることを Hypothesis で検証
    - **Property 4: Exam domain value validation**
    - **Validates: Requirements 9.6**

- [x] 8. ドメインカバレッジ検証テストの作成
  - [x] 8.1 test_domain_coverage.py を新規作成する
    - `tests/integration/test_domain_coverage.py` を新規作成
    - 各ドメインの最低問題数チェック（CC≥15, SC≥15, CT≥20, BP≥12, AI≥15, GA≥15, RA≥10）
    - 難易度分布の要件チェック（各ドメインの難易度別最低数）
    - 合計100問以上、CLF-C02≥60問、AIF-C01≥40問のチェック
    - AWSサービス20種以上の参照チェック
    - 各コース最低5問の配分チェック
    - _Requirements: 10.1, 10.2, 10.3, 10.5, 8.5_

  - [x] 8.2 test_domain_coverage.py に愛媛トリビア多様性テストを追加する
    - 3地域（中予・南予・東予）からの参照チェック（各5問以上）
    - 6テーマ中4テーマ以上のカバレッジチェック
    - ehime_trivia の文字数範囲チェック（30-200文字）
    - _Requirements: 11.1, 11.2, 11.3_

  - [x]* 8.3 test_question_bank.py の最小問題数チェックを更新する
    - `tests/integration/test_question_bank.py` の既存テストを更新
    - 最小問題数を33→102以上に更新
    - コース数を4→9に更新
    - _Requirements: 10.1, 8.1_

- [x] 9. Final checkpoint - 全テスト通過確認
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (Hypothesis)
- 既存33問はすべて保持し、新規問題を追加する形式（後方互換性維持）
- テスト実行: `pytest tests/ -v`、プロパティテストのみ: `pytest tests/properties/ -v`

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3"] },
    { "id": 1, "tasks": ["1.4", "7.1"] },
    { "id": 2, "tasks": ["2.1", "2.2"] },
    { "id": 3, "tasks": ["2.3", "3.1", "3.2"] },
    { "id": 4, "tasks": ["5.1", "5.2", "5.3"] },
    { "id": 5, "tasks": ["5.4", "5.5", "7.2", "7.3"] },
    { "id": 6, "tasks": ["8.1", "8.2", "8.3"] }
  ]
}
```
