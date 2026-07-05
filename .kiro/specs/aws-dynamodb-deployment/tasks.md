# Implementation Plan: AWS DynamoDB Deployment

## Overview

既存のDynamoDBリポジトリ層・SAMテンプレート・Dockerfileを基盤として、セッションテーブル定義、認証ミドルウェアのDynamoDB対応、シークレット管理、シードスクリプト改善、Lambda実行環境の完全性確保、手動デプロイ手順書作成、静的ファイル配信対応を段階的に実装する。

## Tasks

- [x] 1. SAM テンプレートにSessionsテーブルと IAM ポリシーを追加
  - [x] 1.1 SessionsTable DynamoDB リソースを追加
    - `deploy/template.yaml` に `SessionsTable` リソース (AWS::DynamoDB::Table) を追加する
    - TableName: `EhimeAI2026-sessions`、パーティションキー: `token` (String, HASH)
    - BillingMode: `PAY_PER_REQUEST`
    - TimeToLiveSpecification: AttributeName `expires_at`, Enabled `true`
    - Tags: Key `Project`, Value `EhimeAI2026`
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 1.2 Parameter Store アクセス用 IAM ポリシーを追加
    - `deploy/template.yaml` の Lambda 実行ロールに `EhimeAI2026-ssm-access` ポリシーを追加する
    - `ssm:GetParameter` アクションを `/EhimeAI2026/${Environment}/*` パスに制限する
    - _Requirements: 3.2_

  - [ ]* 1.3 SAM テンプレート構造のユニットテストを作成
    - `tests/` 配下にテンプレートのYAMLパースによる構造検証テストを作成する
    - SessionsTable のキー定義、BillingMode、TTL、タグを検証する
    - IAM ポリシーのリソースARNとアクション制限を検証する
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 3.2_

- [x] 2. シークレット管理モジュールの実装
  - [x] 2.1 `app/data/secrets.py` モジュールを新規作成
    - `_get_environment()` 関数: ENVIRONMENT 環境変数を検証 (prod/staging のみ許可)
    - `get_secret(param_name)` 関数: Parameter Store から SecureString を取得しインメモリキャッシュする
    - boto3 クライアントのタイムアウトを5秒に設定する
    - エラーログにシークレット値を含めない
    - 不正な ENVIRONMENT 値で `RuntimeError` を送出する
    - _Requirements: 3.1, 3.3, 3.4, 3.5, 3.6_

  - [ ]* 2.2 シークレット管理モジュールのユニットテストを作成
    - moto を使用した SSM パラメータ取得の成功・失敗テスト
    - キャッシュ動作テスト（2回呼び出しで SSM API 呼び出し1回のみ）
    - ENVIRONMENT 不正値での RuntimeError 送出テスト
    - タイムアウト・権限エラー・パラメータ未登録時のエラーハンドリングテスト
    - _Requirements: 3.1, 3.4, 3.5, 3.6_

- [x] 3. 認証ミドルウェアの DynamoDB 対応
  - [x] 3.1 AuthContextMiddleware を repository_factory パターンに変更
    - `main.py` の `AuthContextMiddleware.dispatch()` を修正する
    - `get_user_repository()` 経由でユーザー情報を取得する（SQLAlchemy直接依存を除去）
    - `AuthService.get_user_id_from_session(token)` でセッション → ユーザーID変換
    - ユーザー未発見時・例外発生時に `request.state.current_user_name = None` を設定し処理続行
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [ ]* 3.2 AuthContextMiddleware のプロパティテストを作成
    - **Property 1: Auth middleware resolves valid session to correct display_name**
    - **Validates: Requirements 2.1, 2.3**
    - moto DynamoDB で sessions/users テーブルをモックし、任意の有効トークン・display_name で正しく解決されることを検証

  - [ ]* 3.3 AuthContextMiddleware の無効セッションのプロパティテストを作成
    - **Property 2: Auth middleware sets None for invalid session states**
    - **Validates: Requirements 2.4, 2.5, 2.6**
    - Cookie なし、トークン不在、ユーザーレコード不在、例外発生時すべてで None が設定されることを検証

- [x] 4. Checkpoint - 認証・シークレット基盤の確認
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. DynamoDB シードスクリプトの改善
  - [x] 5.1 `scripts/seed_dynamodb.py` を改善実装する
    - 25件バッチ制限の明示的処理を実装する
    - UnprocessedItems のリトライ（指数バックオフ付き最大3回）を実装する
    - テーブルアクセスエラー (ResourceNotFoundException等) で早期終了し exit(1) を返す
    - 冪等性: put_item の上書きセマンティクスを使用（条件なし put）
    - 完了時に各テーブルの投入件数を `{table_name}: {count} items inserted` 形式で stdout に出力する
    - データソース: `app/data/seed_data.py` (COURSES, QUESTIONS, EXTRA_QUESTIONS, EXTRA_QUESTIONS_2) と `app/data/glossary_seed.py` (GLOSSARY_SEED_DATA)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_

  - [ ]* 5.2 バッチ書き込みサイズのプロパティテストを作成
    - **Property 3: Batch write sizing invariant**
    - **Validates: Requirements 4.4**
    - 任意長のアイテムリストに対して、バッチ分割が常に25件以下であることを Hypothesis で検証する

  - [ ]* 5.3 シードスクリプト冪等性のプロパティテストを作成
    - **Property 4: Seed script idempotence**
    - **Validates: Requirements 4.6**
    - moto DynamoDB で同一データを2回投入し、テーブル状態が1回実行時と同一であることを検証する

  - [ ]* 5.4 シードスクリプトのユニットテストを作成
    - moto DynamoDB でのデータ投入・件数レポート検証
    - テーブル不在時のエラーハンドリング・exit code 検証
    - UnprocessedItems リトライ動作の検証
    - _Requirements: 4.5, 4.7, 4.8_

- [x] 6. Lambda 実行環境の完全性確保
  - [x] 6.1 未処理例外ハンドラーを有効化する
    - `main.py` の `unhandled_exception_handler` を有効化（コメントアウト解除・修正）する
    - HTML エラーページ (`error.html` テンプレート) を返す
    - エラーログにスタックトレースを記録し、クライアントには公開しない
    - _Requirements: 5.6_

  - [x] 6.2 Lambda 環境変数と Mangum ハンドラーの設定確認・修正
    - `deploy/template.yaml` で Lambda の `USE_DYNAMODB` を `"1"` に設定する
    - `deploy/template.yaml` で Lambda メモリを 512MB に設定する
    - `main.handler` が Mangum アダプターのエントリーポイントであることを確認する
    - Lifespan 関数で USE_DYNAMODB=1 時に SQLite 初期化スキップとログ出力を確認する
    - _Requirements: 5.2, 5.3, 5.4, 5.5, 7.4_

  - [ ]* 6.3 未処理例外ハンドラーのプロパティテストを作成
    - **Property 5: Unhandled exceptions produce HTML error page**
    - **Validates: Requirements 5.6**
    - 各登録ルートに対してランダムな例外を注入し、常に HTML 500 エラーページが返されることを検証する

  - [ ]* 6.4 全ルート応答のインテグレーションテストを作成
    - TestClient で各登録ルート (top, auth, course, quiz, mock_exam, ai_practice, custom_stage, study, review, results) に GET リクエストを送信し、2xx/3xx を確認する
    - _Requirements: 5.1_

- [x] 7. 静的ファイル配信の Lambda 対応確認
  - [x] 7.1 静的ファイル配信の設定確認・修正
    - `main.py` で StaticFiles マウント (`/static` → `app/static/`) が正しく設定されていることを確認する
    - Dockerfile で `app/static/` がコンテナイメージに含まれていることを確認する
    - 不足があれば修正する
    - _Requirements: 7.1, 7.5_

  - [ ]* 7.2 静的ファイル Content-Type のプロパティテストを作成
    - **Property 6: Static file Content-Type correctness**
    - **Validates: Requirements 7.2**
    - `.css`, `.js`, `.svg`, `.mp3` ファイルに対して正しい Content-Type が返されることを検証する

  - [ ]* 7.3 存在しない静的ファイルの 404 プロパティテストを作成
    - **Property 7: Non-existent static file returns 404**
    - **Validates: Requirements 7.3**
    - `/static/` 配下の存在しないパスに対して常に 404 が返されることを Hypothesis で検証する

- [x] 8. Checkpoint - 全機能の動作確認
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. デプロイ手順書の作成
  - [x] 9.1 `deploy/MANUAL_DEPLOY.md` を作成する
    - ECR リポジトリ作成手順（リポジトリ名、ap-northeast-1 リージョン、Docker build & push コマンド）
    - CloudFormation スタック作成手順（template.yaml アップロード、スタック名 "EhimeAI2026"、ap-northeast-1、Environment パラメータ）
    - Parameter Store シークレット登録手順（パラメータパス、SecureString 型、ap-northeast-1）
    - DynamoDB シードスクリプト実行手順（前提条件、実行コマンド、期待出力）
    - 動作確認手順（API Gateway エンドポイント URL、HTTP 200 確認、DynamoDB テーブル件数確認）
    - トラブルシューティング（ECR 認証失敗、CloudFormation ロールバック、シードスクリプト権限エラー）
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_

- [x] 10. Final checkpoint - 全テスト通過確認
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- Python (FastAPI) is the implementation language throughout
- moto is used for AWS service mocking in tests
- Hypothesis is used for property-based testing (already in project dependencies)

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "2.1"] },
    { "id": 1, "tasks": ["1.3", "2.2", "3.1", "5.1"] },
    { "id": 2, "tasks": ["3.2", "3.3", "5.2", "5.3", "5.4"] },
    { "id": 3, "tasks": ["6.1", "6.2", "7.1"] },
    { "id": 4, "tasks": ["6.3", "6.4", "7.2", "7.3"] },
    { "id": 5, "tasks": ["9.1"] }
  ]
}
```
