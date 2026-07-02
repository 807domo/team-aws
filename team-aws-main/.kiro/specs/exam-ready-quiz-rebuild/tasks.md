# Implementation Plan: exam-ready-quiz-rebuild

## Overview

愛媛探索AIクイズアプリケーションのクイズ問題（330問）と用語集（150語以上）を全面再構築する。既存のアプリケーションコード・スキーマは変更せず、データファイル（seed_data.py, seed_data_extra.py, seed_data_extra2.py, glossary_seed.py）のみを差し替える。Hypothesisを使ったプロパティベーステストで全データの構造的正当性を検証する。

## Tasks

- [x] 1. コース定義の確認とseed_data_extra2.py新規作成
  - [x] 1.1 `app/data/seed_data_extra2.py` を新規作成し、空の `EXTRA_QUESTIONS_3` リストを定義する
    - ファイルを作成し `EXTRA_QUESTIONS_3: list[dict] = []` を定義
    - docstringでファイルの役割（AIF-C01後半問題格納）を説明
    - _Requirements: 8.4, 8.5_

  - [x] 1.2 `app/data/seed_data.py` の `seed_database()` 関数を更新し、`EXTRA_QUESTIONS_3` をインポートして全問題を統合投入するように修正する
    - `from app.data.seed_data_extra2 import EXTRA_QUESTIONS_3` を追加
    - `all_questions = QUESTIONS + EXTRA_QUESTIONS + EXTRA_QUESTIONS_3` として投入
    - 既存の `EXTRA_QUESTIONS_2` インポートを削除
    - _Requirements: 8.4, 8.5, 2.5_

- [x] 2. CLF-C02問題データの作成（南予 基礎）
  - [x] 2.1 `app/data/seed_data.py` の QUESTIONS リストに南予向けCLF-C02基礎問題（約70問）を作成する
    - Cloud Concepts: 17問、Security and Compliance: 21問、Cloud Technology and Services: 24問、Billing Pricing and Support: 8問
    - ID形式: `nanyo-cc-001`, `nanyo-sc-001`, `nanyo-ct-001`, `nanyo-bp-001` 等
    - course_id: `nanyo-stage-01` 〜 `nanyo-stage-10` に各7問ずつ分配
    - difficulty: すべて "基礎"
    - 南予地域の地名・名所を問題文とehime_triviaに含める（宇和島城、八幡浜港、内子町並み等）
    - _Requirements: 1.1, 1.2, 1.5, 1.6, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 4.4, 7.1_

  - [x] 2.2 `app/data/seed_data.py` の QUESTIONS リストに南予向けCLF-C02基礎問題の残り（約40問）を追加し、合計約110問にする
    - 前タスクで不足しているドメインの問題を補完
    - 全問題のID一意性を確保
    - _Requirements: 1.1, 1.5, 1.6, 2.2, 4.5_

- [x] 3. CLF-C02問題データの作成（中予 中級 + 東予 上級）
  - [x] 3.1 `app/data/seed_data_extra.py` を全面書き換え、中予向けCLF-C02中級問題（約55問）をEXTRA_QUESTIONSリストに格納する
    - Cloud Concepts: 16問、Security and Compliance: 20問、Cloud Technology and Services: 23問、Billing Pricing and Support: 8問の比率で分配（一部は3.2で追加）
    - ID形式: `chuyo-cc-001`, `chuyo-sc-001` 等
    - course_id: `chuyo-stage-01` 〜 `chuyo-stage-08` に分配
    - difficulty: すべて "中級"
    - 中予地域の地名を使用（松山城、道後温泉、石鎚山、砥部焼等）
    - シナリオベースの応用問題として設計
    - _Requirements: 1.1, 1.3, 1.5, 1.6, 2.1, 2.2, 2.3, 3.1, 3.2, 3.4, 4.1, 4.2, 4.3, 4.4, 7.2_

  - [x] 3.2 `app/data/seed_data_extra.py` のEXTRA_QUESTIONSリストに東予向けCLF-C02上級問題（約55問）を追加する
    - Cloud Concepts: 16問、Security and Compliance: 20問、Cloud Technology and Services: 23問、Billing Pricing and Support: 8問の比率で分配（一部は他タスクで補完）
    - ID形式: `toyo-cc-001`, `toyo-sc-001` 等
    - course_id: `toyo-stage-01` 〜 `toyo-stage-10` に分配
    - difficulty: すべて "上級"
    - 東予地域の地名を使用（しまなみ海道、今治タオル、新居浜太鼓祭り、別子銅山等）
    - 複数概念統合・高度シナリオ分析の問題として設計
    - _Requirements: 1.1, 1.4, 1.5, 1.6, 2.1, 2.2, 2.3, 3.1, 3.2, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 7.3_

- [ ] 4. Checkpoint - CLF-C02問題の構造確認
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. AIF-C01問題データの作成
  - [x] 5.1 `app/data/seed_data_extra2.py` のEXTRA_QUESTIONS_3リストにAIF-C01問題（南予 基礎: 約43問）を作成する
    - AI and ML Fundamentals: 9問、Generative AI Concepts: 10問、Applications of Foundation Models: 12問、Guidelines for Responsible AI: 6問、Security Compliance and Governance: 6問
    - ID形式: `nanyo-ai-001`, `nanyo-ga-001`, `nanyo-fm-001`, `nanyo-ra-001`, `nanyo-sg-001`
    - course_id: `nanyo-stage-01` 〜 `nanyo-stage-10` に分配（CLF問題と合わせて各コース10〜12問になるよう調整）
    - difficulty: すべて "基礎"
    - 南予地域の地名を使用
    - _Requirements: 1.1, 1.2, 1.6, 1.7, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 5.1, 5.2, 5.3, 5.4, 5.5, 7.1_

  - [x] 5.2 `app/data/seed_data_extra2.py` のEXTRA_QUESTIONS_3リストにAIF-C01問題（中予 中級: 約42問）を追加する
    - AI and ML Fundamentals: 8問、Generative AI Concepts: 10問、Applications of Foundation Models: 12問、Guidelines for Responsible AI: 6問、Security Compliance and Governance: 6問
    - ID形式: `chuyo-ai-001`, `chuyo-ga-001` 等
    - course_id: `chuyo-stage-01` 〜 `chuyo-stage-08` に分配
    - difficulty: すべて "中級"
    - 中予地域の地名を使用
    - _Requirements: 1.1, 1.3, 1.6, 1.7, 2.1, 2.2, 2.3, 3.1, 3.2, 3.4, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 7.2_

  - [x] 5.3 `app/data/seed_data_extra2.py` のEXTRA_QUESTIONS_3リストにAIF-C01問題（東予 上級: 約41問）を追加する
    - AI and ML Fundamentals: 8問、Generative AI Concepts: 10問、Applications of Foundation Models: 11問、Guidelines for Responsible AI: 6問、Security Compliance and Governance: 6問
    - ID形式: `toyo-ai-001`, `toyo-ga-001` 等
    - course_id: `toyo-stage-01` 〜 `toyo-stage-10` に分配
    - difficulty: すべて "上級"
    - 東予地域の地名を使用
    - _Requirements: 1.1, 1.4, 1.6, 1.7, 2.1, 2.2, 2.3, 3.1, 3.2, 3.5, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 7.3_

- [ ] 6. Checkpoint - AIF-C01問題の構造確認
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. 用語集データの全面再構築
  - [x] 7.1 `app/data/glossary_seed.py` のGLOSSARY_SEED_DATAリストを全面書き換え、CLF-C02関連の用語（約74語）を定義する
    - カテゴリ: "クラウド基礎"(15語)、"AWSコンピューティング"(12語)、"AWSストレージ・データベース"(15語)、"AWSネットワーキング"(10語)、"AWSセキュリティ"(15語)、"AWS管理・ガバナンス"(12語)、"AWS料金・サポート"(10語)の7カテゴリ分をまず定義
    - 各エントリに category, sort_order, term, description（20文字以上）を含める
    - クイズ問題で参照されるAWSサービス名を全て含める
    - seed_glossary() 関数は既存ロジック維持
    - _Requirements: 6.1, 6.2, 6.3, 6.5, 6.6, 6.7_

  - [x] 7.2 `app/data/glossary_seed.py` のGLOSSARY_SEED_DATAリストにAIF-C01関連の用語（約76語以上）を追加し、合計150語以上にする
    - カテゴリ: "AI・ML基礎"(20語)、"生成AI・基盤モデル"(20語)、"AWS AIサービス"(12語)、"責任あるAI"(10語)の4カテゴリ分を追加
    - クイズ問題で参照されるAI/ML概念を全て含める
    - 用語の重複がないことを確認
    - _Requirements: 6.1, 6.2, 6.4, 6.5, 6.6, 6.7_

- [ ] 8. Checkpoint - 用語集の構造確認
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. プロパティベーステストの実装
  - [x] 9.1 `tests/test_seed_data_properties.py` を作成し、Property 1（Region-difficulty consistency）のプロパティテストを実装する
    - **Property 1: Region-difficulty consistency**
    - **Validates: Requirements 1.2, 1.3, 1.4**
    - Hypothesisの `sampled_from` ストラテジーで全問題からサンプリング
    - `@settings(max_examples=200)` で200回以上のイテレーションを実行
    - course_idプレフィックスと difficulty の対応を検証

  - [x] 9.2 `tests/test_seed_data_properties.py` にProperty 2（Question structural validity）のプロパティテストを追加する
    - **Property 2: Question structural validity**
    - **Validates: Requirements 2.1, 2.4, 2.5, 3.2, 3.6, 7.4**
    - 全必須フィールドの存在、文字列フィールドの非空、correct_choice_indexの範囲、4選択肢の相互排他性を検証

  - [x] 9.3 `tests/test_seed_data_properties.py` にProperty 3（Question ID format validity）のプロパティテストを追加する
    - **Property 3: Question ID format validity**
    - **Validates: Requirements 2.2**
    - IDが `{region}-{domain-abbr}-{NNN}` パターンに一致することを正規表現で検証
    - 全問題のID一意性を検証

  - [x] 9.4 `tests/test_seed_data_properties.py` にProperty 4（Question references valid course）のプロパティテストを追加する
    - **Property 4: Question references valid course**
    - **Validates: Requirements 2.3**
    - course_idが30個の有効なコースIDのいずれかであることを検証

  - [x] 9.5 `tests/test_seed_data_properties.py` にProperty 5（Question has valid exam domain）のプロパティテストを追加する
    - **Property 5: Question has valid exam domain**
    - **Validates: Requirements 1.7**
    - exam_domainが9個の認定ドメイン名のいずれかであることを検証

  - [x] 9.6 `tests/test_glossary_properties.py` を作成し、Property 6（Glossary entry structural validity）のプロパティテストを実装する
    - **Property 6: Glossary entry structural validity**
    - **Validates: Requirements 6.2, 6.5, 6.6**
    - Hypothesisの `sampled_from` で全用語からサンプリング
    - カテゴリが11種の有効値のいずれか、sort_orderが非負整数、termが非空、descriptionが20文字以上であることを検証

  - [x] 9.7 `tests/test_glossary_properties.py` にProperty 7（Glossary term uniqueness）のプロパティテストを追加する
    - **Property 7: Glossary term uniqueness**
    - **Validates: Requirements 6.7**
    - 全用語のterm値に重複がないことを検証

- [x] 10. スモークテスト（ユニットテスト）の実装
  - [x] 10.1 `tests/test_seed_data_smoke.py` を作成し、データ量・分布のスモークテストを実装する
    - 全問題数 >= 300 の検証
    - 30コース全てに問題が存在することの検証
    - 各コース5〜15問の範囲であることの検証
    - CLF-C02各ドメインの最低問題数の検証（Cloud Concepts >= 49, Security >= 61, Technology >= 70, Billing >= 24）
    - AIF-C01各ドメインの最低問題数の検証（AI/ML >= 25, GenAI >= 30, FM >= 35, Responsible >= 18, Security/Gov >= 18）
    - 用語数 >= 150 の検証
    - COURSES リストが30件で正しいIDであることの検証
    - _Requirements: 1.1, 1.5, 1.6, 1.8, 4.5, 5.6, 6.1, 8.3_

- [ ] 11. Final checkpoint - 全テスト実行と最終確認
  - Ensure all tests pass, ask the user if questions arise.
  - `pytest tests/test_seed_data_properties.py tests/test_glossary_properties.py tests/test_seed_data_smoke.py --run -v` で全テスト通過を確認

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- 問題作成時は CLF-C02/AIF-C01 公式試験ガイドの出題範囲に忠実に従う
- 各問題の4つの選択肢は相互排他的かつ明確に1つだけ正解であること
- 愛媛県の地域コンテキストは事実に基づく情報であること
- seed_data_extra2.py は新規ファイルのため作成が必要

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["2.1", "3.1", "5.1", "7.1"] },
    { "id": 3, "tasks": ["2.2", "3.2", "5.2", "7.2"] },
    { "id": 4, "tasks": ["5.3"] },
    { "id": 5, "tasks": ["9.1", "9.2", "9.3", "9.4", "9.5", "9.6", "9.7", "10.1"] }
  ]
}
```
