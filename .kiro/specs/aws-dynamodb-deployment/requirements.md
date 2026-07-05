# Requirements Document

## Introduction

「愛媛探索AIクイズ」FastAPIアプリケーションのAWS本番デプロイを完了する。既に構築されたDynamoDBリポジトリ層・SAMテンプレート・Dockerfileを基盤として、未完了の項目（sessionsテーブル定義、認証ミドルウェアのDynamoDB対応、シークレット管理、初期データ投入、エンドツーエンド動作確認）を実装し、AWSコンソール経由の手動デプロイで本番稼働可能な状態にする。

## Glossary

- **Application**: FastAPIベースの「愛媛探索AIクイズ」Webアプリケーション
- **SAM_Template**: AWS SAM (Serverless Application Model) の CloudFormation テンプレートファイル (`deploy/template.yaml`)
- **Sessions_Table**: 認証セッショントークンとユーザーIDの対応を保存するDynamoDBテーブル (`EhimeAI2026-sessions`)
- **AuthContext_Middleware**: リクエストごとにログインユーザー名を `request.state` に設定するStarletteミドルウェア
- **Repository_Factory**: 環境変数 `USE_DYNAMODB` に基づきSQLAlchemy/DynamoDBリポジトリを切り替えるファクトリモジュール
- **Secrets_Store**: APIキー等の機密情報を安全に保存・取得するためのAWSマネージドサービス（AWS Systems Manager Parameter Store）
- **Seed_Script**: DynamoDBテーブルに初期データ（コース・問題・用語集）を一括投入するスクリプト
- **Lambda_Function**: AWS Lambda上で動作するDockerコンテナベースのアプリケーション実行環境
- **DynamoDB_Auth_Session_Store**: `sessions` テーブルを使用した認証セッション永続化クラス

## Requirements

### Requirement 1: Sessions テーブルの CloudFormation 定義

**User Story:** As a 運用者, I want sessions テーブルが SAM テンプレートに定義されている, so that CloudFormation デプロイ時に認証セッション用テーブルが自動作成される

#### Acceptance Criteria

1. THE SAM_Template SHALL define a DynamoDB table resource with logical resource ID `SessionsTable`, resource type `AWS::DynamoDB::Table`, TableName property set to `EhimeAI2026-sessions`, partition key `token` (String type, KeyType HASH), and the `token` attribute listed in AttributeDefinitions with AttributeType `S`
2. THE SAM_Template SHALL configure the Sessions_Table with BillingMode set to `PAY_PER_REQUEST`
3. THE SAM_Template SHALL configure a TimeToLiveSpecification on the Sessions_Table with AttributeName set to `expires_at` and Enabled set to `true`
4. THE SAM_Template SHALL include a tag with Key `Project` and Value `EhimeAI2026` on the Sessions_Table resource, using the Tags list format consistent with other DynamoDB table resources in the template

### Requirement 2: 認証ミドルウェアの DynamoDB 対応

**User Story:** As a ユーザー, I want Lambda 環境でもログイン状態が正しく表示される, so that DynamoDB バックエンド使用時にもユーザー名がページに表示される

#### Acceptance Criteria

1. WHILE USE_DYNAMODB=1 が設定されている状態, THE AuthContext_Middleware SHALL AuthService.get_user_id_from_session() でセッショントークンからユーザーIDを取得し、User_Repository 経由で DynamoDB users テーブルから display_name を取得する（SQLAlchemy の SessionLocal および UserModel を使用しない）
2. WHILE USE_DYNAMODB=0 が設定されている状態, THE AuthContext_Middleware SHALL AuthService.get_user_id_from_session() でセッショントークンからユーザーIDを取得し、User_Repository 経由で SQLAlchemy データベースセッションから display_name を取得する（既存動作を保持）
3. WHEN リクエストの "session_token" Cookie に有効なトークン（sessions テーブルにユーザーIDとの対応が存在する）が含まれている場合, THE AuthContext_Middleware SHALL `request.state.current_user_name` を該当ユーザーの display_name に設定する
4. WHEN "session_token" Cookie が存在しない、または Cookie のトークン値が sessions テーブルに存在しない場合, THE AuthContext_Middleware SHALL `request.state.current_user_name` を None に設定する
5. IF セッショントークンから取得した user_id に対応するユーザーレコードが users テーブルに存在しない場合, THEN THE AuthContext_Middleware SHALL `request.state.current_user_name` を None に設定する
6. IF ユーザー検索中に例外が発生した場合, THEN THE AuthContext_Middleware SHALL `request.state.current_user_name` を None に設定し、リクエスト処理を中断せず後続のハンドラーへ処理を継続する

### Requirement 3: シークレット管理（APIキー）

**User Story:** As a 運用者, I want APIキーをソースコードや環境変数に直接記載せずに管理したい, so that 機密情報が安全に保護されデプロイ時に自動取得される

#### Acceptance Criteria

1. THE Application SHALL retrieve the Gemini API key from the Secrets_Store (AWS Systems Manager Parameter Store SecureString) at runtime during Lambda cold start initialization
2. THE SAM_Template SHALL grant the Lambda_Function IAM permission to read parameters from the Parameter Store path prefix `/EhimeAI2026/{Environment}/` with least-privilege scope
3. THE Application SHALL use the parameter path `/EhimeAI2026/{Environment}/GEMINI_API_KEY` to retrieve the API key, where `{Environment}` is resolved from the Lambda environment variable `ENVIRONMENT`
4. IF the Secrets_Store parameter retrieval fails due to timeout (exceeding 5 seconds), permission denial, or parameter-not-found, THEN THE Application SHALL log an error message that does not include the secret value and return an error response indicating that the AI feature is temporarily unavailable when AI features are invoked
5. THE Application SHALL cache the retrieved secret value in memory for the Lambda execution lifetime to minimize Parameter Store API calls, and SHALL NOT write the secret value to application logs at any log level
6. IF the Lambda environment variable `ENVIRONMENT` is not set or contains a value other than "prod" or "staging", THEN THE Application SHALL fail to initialize and log an error indicating the invalid environment configuration

### Requirement 4: DynamoDB 初期データ投入スクリプト

**User Story:** As a 運用者, I want DynamoDB テーブルに初期データを投入するスクリプトが用意されている, so that デプロイ後にクイズコンテンツが利用可能になる

#### Acceptance Criteria

1. THE Seed_Script SHALL read course definitions from app/data/seed_data.py (COURSES list) and insert all items into the DynamoDB "{TABLE_PREFIX}courses" table
2. THE Seed_Script SHALL read question data from app/data/seed_data.py (QUESTIONS, EXTRA_QUESTIONS, EXTRA_QUESTIONS_2 lists) and insert all items into the DynamoDB "{TABLE_PREFIX}questions" table
3. THE Seed_Script SHALL read glossary terms from app/data/glossary_seed.py (GLOSSARY_SEED_DATA list) and insert all items into the DynamoDB "{TABLE_PREFIX}glossary_terms" table
4. THE Seed_Script SHALL use DynamoDB batch_write operations to insert data in batches of up to 25 items per request
5. IF a batch_write operation returns UnprocessedItems, THEN THE Seed_Script SHALL retry those items up to 3 times with exponential backoff before reporting the failure to stdout and exiting with a non-zero status code
6. THE Seed_Script SHALL be idempotent by using put_item overwrite semantics (unconditional puts keyed by each item's "id" field), so that re-running the script does not create duplicate records
7. WHEN the script completes successfully, THE Seed_Script SHALL print to stdout the count of items written for each table in the format "{table_name}: {count} items inserted"
8. IF the target DynamoDB table is not accessible (e.g., ResourceNotFoundException or connection error), THEN THE Seed_Script SHALL print an error message indicating the table name and exit with a non-zero status code without proceeding to subsequent tables

### Requirement 5: Lambda 実行環境の完全性

**User Story:** As a 開発者, I want Lambda 環境で全ルートが正しく動作する, so that ユーザーがすべての機能を利用できる

#### Acceptance Criteria

1. WHEN a request is received for any registered route (top, auth, course, quiz, mock_exam, ai_practice, custom_stage, study, review, results), THE Lambda_Function SHALL return an HTTP response with status code 2xx or 3xx within 30 seconds via API Gateway HTTP API proxy routing (/{proxy+} and /)
2. THE Lambda_Function SHALL use the Mangum adapter to convert API Gateway events to ASGI requests, with the handler entry point set to `main.handler`
3. THE Lambda_Function SHALL have the environment variable `USE_DYNAMODB` set to `"1"`
4. THE Lambda_Function SHALL have IAM role permissions granting GetItem, PutItem, UpdateItem, DeleteItem, Query, Scan, BatchWriteItem, and BatchGetItem actions on all DynamoDB tables matching the pattern `EhimeAI2026-*` and their Global Secondary Indexes (tables: users, courses, questions, answer_records, quiz_sessions, mock_exam_sessions, mock_exam_results, bookmarks, glossary_terms)
5. WHEN the Lambda_Function starts (cold start) with `USE_DYNAMODB` set to `"1"`, THE Application SHALL skip SQLite table creation, migrations, and seed data initialization, and log the message "DynamoDB モードで起動（SQLite初期化スキップ）"
6. IF a request to any registered route results in an unhandled exception, THEN THE Lambda_Function SHALL return an HTML error page with HTTP status code 500 instead of exposing a raw stack trace to the client
7. IF the Lambda_Function does not complete processing within the 30-second timeout, THEN API Gateway SHALL return an HTTP 503 response to the client

### Requirement 6: AWS コンソール手動デプロイ手順書

**User Story:** As a 運用者, I want AWSコンソールを使った手動デプロイ手順が文書化されている, so that SAM CLI なしでもデプロイ作業を正確に実行できる

#### Acceptance Criteria

1. THE Application SHALL include a deployment guide document (`deploy/MANUAL_DEPLOY.md`) describing the AWS Console deployment process as a numbered sequence of procedures in the following order: ECR repository creation, Docker image push, CloudFormation stack creation, Parameter Store registration, DynamoDB seed data投入, and deployment verification
2. THE deployment guide SHALL document the ECR repository creation procedure including the repository name, the ap-northeast-1 region setting, and the Docker image build and push commands with the ECR URI and "latest" tag
3. THE deployment guide SHALL document the CloudFormation stack creation procedure including uploading the `deploy/template.yaml` file, specifying the stack name "EhimeAI2026", selecting the ap-northeast-1 region, and setting the Environment parameter value
4. THE deployment guide SHALL document the Parameter Store secret registration procedure including the parameter path, the selection of SecureString type, and the ap-northeast-1 region for the Gemini API key
5. THE deployment guide SHALL document the DynamoDB seed script execution procedure including the prerequisites (Python environment with project dependencies installed, AWS credentials configured with DynamoDB write permissions), the execution command (`python scripts/seed_dynamodb.py`), and the expected terminal output indicating completion
6. THE deployment guide SHALL document the verification steps including accessing the API Gateway endpoint URL from the CloudFormation stack Outputs, confirming an HTTP 200 response from the root path, and confirming that DynamoDB tables (EhimeAI2026-courses, EhimeAI2026-questions, EhimeAI2026-glossary_terms) contain at least 1 item each
7. IF a procedure step fails, THEN THE deployment guide SHALL provide a troubleshooting reference indicating the likely cause and the AWS Console page to check for each of the following: ECR push authentication failure, CloudFormation stack creation rollback, and seed script DynamoDB access denial

### Requirement 7: Static ファイル配信の Lambda 対応

**User Story:** As a ユーザー, I want CSS と JavaScript が正しく読み込まれる, so that ページのスタイルと動作が正しく機能する

#### Acceptance Criteria

1. THE Lambda_Function SHALL serve static files (CSS, JavaScript, SVG, audio) from the application package by mounting FastAPI's StaticFiles at the `/static` path pointing to the `app/static/` directory
2. WHEN a request for a static file is received, THE Application SHALL return the file with a Content-Type header matching the file extension: `text/css` for .css files, `application/javascript` for .js files, `image/svg+xml` for .svg files, and `audio/mpeg` for .mp3 files
3. IF a request is received for a static file path that does not exist in the `app/static/` directory, THEN THE Application SHALL return a 404 status code
4. THE SAM_Template SHALL configure the Lambda_Function memory to 512MB
5. THE Dockerfile SHALL copy the `app/` directory (including `app/static/`) into the Lambda container image at the task root path
