# Implementation Plan: Glossary, License & Difficulty Enhancement

## Overview

本実装計画は愛媛探索AIクイズアプリに対する3つの独立した改善（難易度-地域対応修正、用語集拡充、ライセンスページ拡充）を段階的に実装するためのタスクリストである。各改善は独立しているため並行実装が可能だが、テスト・検証のためにチェックポイントを設ける。

## Tasks

- [x] 1. 難易度と地域の対応関係修正
  - [x] 1.1 Region Enumのメンバー順序と値を修正する
    - `app/domain/models.py` の `Region` クラスを修正
    - メンバー定義順序を `NANYO, CHUYO, TOYO` に変更（現在: `NANYO, TOYO, CHUYO`）
    - CHUYO の値を `"上級"` → `"中級"` に変更
    - TOYO の値を `"中級"` → `"上級"` に変更
    - _Requirements: 1.1, 1.4_

  - [x] 1.2 シードデータのregion値を修正する
    - `app/data/seed_data.py` のCOURSES定義を確認し、中予コースに `"中級"`、東予コースに `"上級"` が設定されていることを確認・修正
    - 東予コースの `"region": "中級"` → `"region": "上級"` に変更
    - 中予コースの `"region": "上級"` → `"region": "中級"` に変更
    - _Requirements: 1.1, 1.5_

  - [x] 1.3 SVGマップテンプレートの地域ラベルを修正する
    - `app/templates/rpg_top.html` 内の `東予（中級）` → `東予（上級）` に変更
    - `app/templates/rpg_top.html` 内の `中予（上級）` → `中予（中級）` に変更
    - _Requirements: 1.2, 1.3_

  - [ ]* 1.4 Region Enumの正当性を検証するプロパティテストを書く
    - **Property 1: Region Enum iteration order matches difficulty progression**
    - Region Enumの反復順序が `["初級", "中級", "上級"]` であることを検証
    - **Validates: Requirements 1.3, 1.4**

  - [ ]* 1.5 コース難易度ラベルの一貫性を検証するプロパティテストを書く
    - **Property 2: Course difficulty label consistency**
    - NANYO="初級", CHUYO="中級", TOYO="上級" の対応が正しいことを検証
    - **Validates: Requirements 1.1, 1.5**

- [x] 2. Checkpoint - 難易度修正の確認
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. 用語集（グロサリー）の網羅的拡充
  - [x] 3.1 seed_glossary関数に差分投入（upsert）ロジックを追加する
    - `app/data/glossary_seed.py` の `seed_glossary()` 関数を修正
    - 既存データがある場合でも、GLOSSARY_SEED_DATAに含まれるがDBに存在しない用語を追加する差分投入ロジックを実装
    - term名で既存データとの重複チェックを行う
    - _Requirements: 2.5, 2.7_

  - [x] 3.2 クラウド基礎カテゴリの用語を拡充する
    - `app/data/glossary_seed.py` の GLOSSARY_SEED_DATA に追加
    - 追加用語: 共有責任モデル、Well-Architected Framework、従量課金、リージョン、アベイラビリティゾーン、CDN、サーバーレス、マネージドサービス
    - 既存の6件に続いて sort_order を連番で割り当て
    - _Requirements: 2.2, 2.5, 2.6_

  - [x] 3.3 AWSサービスカテゴリの用語を拡充する
    - `app/data/glossary_seed.py` の GLOSSARY_SEED_DATA に追加
    - 追加用語: Amazon DynamoDB, Amazon VPC, AWS IAM, Amazon CloudFront, Amazon Route 53, Amazon SQS, AWS CloudFormation, Elastic Load Balancing, Amazon S3 Glacier, AWS KMS, Amazon Rekognition, Amazon Comprehend, Amazon SageMaker, Amazon Bedrock
    - 既存の4件に続いて sort_order を連番で割り当て
    - _Requirements: 2.1, 2.5, 2.6_

  - [x] 3.4 AI基礎カテゴリの用語を拡充する
    - `app/data/glossary_seed.py` の GLOSSARY_SEED_DATA に追加
    - 追加用語: ファインチューニング、転移学習、教師あり学習、教師なし学習、強化学習
    - 既存の9件に続いて sort_order を連番で割り当て
    - _Requirements: 2.3, 2.5, 2.6_

  - [x] 3.5 セキュリティカテゴリ（新規）の用語を追加する
    - `app/data/glossary_seed.py` の GLOSSARY_SEED_DATA に新カテゴリとして追加
    - 追加用語: 多要素認証（MFA）、暗号化、IAMポリシー、セキュリティグループ、最小権限の原則
    - sort_order を 0 から連番で割り当て
    - _Requirements: 2.4, 2.5, 2.6_

  - [ ]* 3.6 用語集データの構造的整合性を検証するプロパティテストを書く
    - **Property 3: Glossary seed data structural integrity**
    - 全エントリに非空のcategory, term, description、非負のsort_orderが存在することを検証
    - **Validates: Requirements 2.5**

  - [ ]* 3.7 カテゴリ内sort_orderの連番性を検証するプロパティテストを書く
    - **Property 4: Glossary sort_order sequential within category**
    - 各カテゴリ内でsort_orderが0から始まる連番でギャップ・重複がないことを検証
    - **Validates: Requirements 2.6**

- [x] 4. Checkpoint - 用語集拡充の確認
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. ライセンスページの帰属情報拡充
  - [x] 5.1 愛媛県オープンデータの帰属情報セクションを追加する
    - `app/templates/licenses.html` に新セクションを追加
    - ソース名: 愛媛県オープンデータ
    - ライセンス: CC BY 4.0
    - URL: https://www.pref.ehime.jp/opendata-catalog/
    - 既存の2セクション（愛媛県地図データ、その他のライブラリ）は維持
    - _Requirements: 3.1, 3.6, 3.7_

  - [x] 5.2 愛媛県文化財データの帰属情報セクションを追加する
    - `app/templates/licenses.html` に新セクションを追加
    - ソース名: 愛媛県文化財データ
    - URL: https://www.pref.ehime.jp/site/ehimenotakara/ および https://ehime-kyoiku.esnet.ed.jp/bunkazai/shitei-itiran
    - _Requirements: 3.2, 3.6, 3.7_

  - [x] 5.3 AWS公式ドキュメントの帰属情報セクションを追加する
    - `app/templates/licenses.html` に新セクションを追加
    - ソース名: AWS公式ドキュメント
    - 内容: 試験ガイド、サービスドキュメント、ホワイトペーパー
    - _Requirements: 3.3, 3.6, 3.7_

  - [x] 5.4 AI用語参考文献の帰属情報セクションを追加する
    - `app/templates/licenses.html` に新セクションを追加
    - ソース名: AI用語参考文献
    - 参照先: Stanford HAI, MIT Media Lab, Wikipedia
    - _Requirements: 3.4, 3.6, 3.7_

  - [x] 5.5 AWS学習リソースの帰属情報セクションを追加する
    - `app/templates/licenses.html` に新セクションを追加
    - ソース名: AWS学習リソース
    - 内容: AWS Skill Builder, AWS Cloud Practitioner Essentials
    - _Requirements: 3.5, 3.6, 3.7_

  - [ ]* 5.6 ライセンスページの帰属情報完全性を検証するプロパティテストを書く
    - **Property 5: License page attribution completeness**
    - 各帰属セクションにソース名、ライセンス種別/利用条件、有効なハイパーリンクが含まれることを検証
    - **Validates: Requirements 3.7**

- [x] 6. Final checkpoint - 全体の検証
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- 3つの改善は独立しているため、タスク1, 3, 5は並行して実装可能
- seed_glossary()の差分投入は既存DB環境で用語集拡充を反映するために必要
- Region Enum修正後、既存DBにデータがある場合はマイグレーションスクリプトでの対応も必要だが、シードデータの修正で新規DB投入は正しく動作する

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "3.1", "5.1"] },
    { "id": 1, "tasks": ["1.2", "1.3", "3.2", "3.3", "5.2", "5.3"] },
    { "id": 2, "tasks": ["1.4", "1.5", "3.4", "3.5", "5.4", "5.5"] },
    { "id": 3, "tasks": ["3.6", "3.7", "5.6"] }
  ]
}
```
