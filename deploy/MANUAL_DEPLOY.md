# 手動デプロイ手順書 — EhimeAI2026（愛媛探索AIクイズ）

本ドキュメントは、AWS コンソールを使用して「愛媛探索AIクイズ」アプリケーションを本番環境にデプロイする手順を記載する。SAM CLI を使用せず、すべて AWS コンソールおよびローカル CLI で実行可能な手順である。

## 前提条件

- AWS アカウントへのアクセス（IAM 権限: ECR, CloudFormation, Lambda, DynamoDB, SSM, API Gateway）
- AWS CLI がインストール・設定済み
- Docker がインストール済み
- Python 3.13 + プロジェクト依存パッケージがインストール済み
- リージョン: **ap-northeast-1**（東京）

---

## デプロイ手順概要

以下の順番で実施する：

1. ECR リポジトリ作成 & Docker イメージ push
2. CloudFormation スタック作成
3. Parameter Store シークレット登録
4. DynamoDB シードデータ投入
5. 動作確認

---

## 1. ECR リポジトリ作成 & Docker イメージ push

### 1.1 ECR リポジトリ作成

AWS コンソールで作成する場合：

1. AWS コンソール → **Amazon ECR** → **リポジトリ** → **リポジトリを作成**
2. リポジトリ名: `ehimeai2026-api`
3. リージョン: `ap-northeast-1`
4. その他設定はデフォルトのまま → **リポジトリを作成**

AWS CLI で作成する場合：

```bash
aws ecr create-repository \
  --repository-name ehimeai2026-api \
  --region ap-northeast-1
```

### 1.2 Docker イメージのビルドと push

```bash
# AWSアカウントIDを取得
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# ECR にログイン
aws ecr get-login-password --region ap-northeast-1 | \
  docker login --username AWS --password-stdin \
  ${AWS_ACCOUNT_ID}.dkr.ecr.ap-northeast-1.amazonaws.com

# Docker イメージをビルド（プロジェクトルートで実行）
docker build -t ehimeai2026-api:latest .

# ECR URI にタグ付け
docker tag ehimeai2026-api:latest \
  ${AWS_ACCOUNT_ID}.dkr.ecr.ap-northeast-1.amazonaws.com/ehimeai2026-api:latest

# ECR に push
docker push \
  ${AWS_ACCOUNT_ID}.dkr.ecr.ap-northeast-1.amazonaws.com/ehimeai2026-api:latest
```

push 完了後、ECR コンソールでイメージが `latest` タグで登録されていることを確認する。

---

## 2. CloudFormation スタック作成

### 2.1 スタック作成手順

1. AWS コンソール → **CloudFormation** → **スタックの作成** → **新しいリソースを使用（標準）**
2. **テンプレートの指定**:
   - 「テンプレートファイルのアップロード」を選択
   - `deploy/template.yaml` をアップロード
3. **スタックの詳細を指定**:
   - スタック名: `EhimeAI2026`
   - パラメータ:
     - Environment: `prod`
4. **スタックオプションの設定**:
   - タグ: Key=`Project`, Value=`EhimeAI2026`（任意）
   - その他はデフォルト
5. **確認と作成**:
   - 「AWS CloudFormation によって IAM リソースがカスタム名で作成される場合があることを承認します。」にチェックを入れる
   - 「AWS CloudFormation によって、次の機能が必要になる場合があることを承認します: CAPABILITY_AUTO_EXPAND」にチェックを入れる
   - **スタックの作成** をクリック

6. リージョン: `ap-northeast-1`（東京）であることを確認してから作成する

### 2.2 作成されるリソース

スタック作成により以下のリソースが自動生成される：

| リソース | 説明 |
|----------|------|
| EhimeAI2026-lambda-execution-role | Lambda 実行用 IAM ロール |
| EhimeAI2026-api | Lambda 関数（Docker ベース） |
| EhimeAI2026HttpApi | API Gateway HTTP API |
| EhimeAI2026-users | DynamoDB テーブル |
| EhimeAI2026-courses | DynamoDB テーブル |
| EhimeAI2026-questions | DynamoDB テーブル |
| EhimeAI2026-sessions | DynamoDB テーブル |
| EhimeAI2026-answer_records | DynamoDB テーブル |
| EhimeAI2026-quiz_sessions | DynamoDB テーブル |
| EhimeAI2026-mock_exam_sessions | DynamoDB テーブル |
| EhimeAI2026-mock_exam_results | DynamoDB テーブル |
| EhimeAI2026-bookmarks | DynamoDB テーブル |
| EhimeAI2026-glossary_terms | DynamoDB テーブル |

スタックのステータスが `CREATE_COMPLETE` になるまで待機する（通常 3〜5 分）。

---

## 3. Parameter Store シークレット登録

### 3.1 Gemini API キーの登録

AWS コンソールで登録する場合：

1. AWS コンソール → **AWS Systems Manager** → **パラメータストア** → **パラメータの作成**
2. 設定:
   - 名前: `/EhimeAI2026/prod/GEMINI_API_KEY`
   - 説明: `Gemini API key for EhimeAI2026 production`
   - 利用枠: 標準
   - タイプ: **SecureString**
   - KMS キーソース: 現在のアカウント（デフォルト）
   - 値: `<Gemini API キーの値を入力>`
3. リージョン: `ap-northeast-1`
4. **パラメータの作成** をクリック

AWS CLI で登録する場合：

```bash
aws ssm put-parameter \
  --name "/EhimeAI2026/prod/GEMINI_API_KEY" \
  --type SecureString \
  --value "<Gemini API キーの値>" \
  --region ap-northeast-1
```

---

## 4. DynamoDB シードデータ投入

### 4.1 前提条件

- Python 3.13 がインストールされていること
- プロジェクトの依存パッケージがインストール済みであること（`pip install -r requirements.txt`）
- AWS 認証情報が設定済みであること（DynamoDB への書き込み権限が必要）
- CloudFormation スタックが `CREATE_COMPLETE` 状態であること（DynamoDB テーブルが存在すること）

### 4.2 実行コマンド

プロジェクトルートで以下を実行する：

```bash
python scripts/seed_dynamodb.py
```

### 4.3 期待される出力

正常完了時、以下のような出力が表示される：

```
EhimeAI2026-courses: 20 items inserted
EhimeAI2026-questions: 200 items inserted
EhimeAI2026-glossary_terms: 50 items inserted
```

※ 件数はデータソースの内容により変動する。

シードスクリプトは冪等であり、再実行しても重複レコードは作成されない（既存アイテムは上書きされる）。

---

## 5. 動作確認

### 5.1 API Gateway エンドポイント URL の確認

1. AWS コンソール → **CloudFormation** → スタック `EhimeAI2026` → **出力** タブ
2. `ApiUrl` の値を確認する

URL の形式:
```
https://<api-id>.execute-api.ap-northeast-1.amazonaws.com/prod/
```

### 5.2 HTTP 200 レスポンスの確認

ブラウザまたは curl で API Gateway エンドポイントにアクセスし、HTTP 200 が返ることを確認する：

```bash
curl -s -o /dev/null -w "%{http_code}" \
  https://<api-id>.execute-api.ap-northeast-1.amazonaws.com/prod/
```

期待結果: `200`

### 5.3 DynamoDB テーブル件数の確認

以下のコマンドで各テーブルにデータが存在することを確認する：

```bash
# courses テーブル
aws dynamodb scan \
  --table-name EhimeAI2026-courses \
  --select COUNT \
  --region ap-northeast-1

# questions テーブル
aws dynamodb scan \
  --table-name EhimeAI2026-questions \
  --select COUNT \
  --region ap-northeast-1

# glossary_terms テーブル
aws dynamodb scan \
  --table-name EhimeAI2026-glossary_terms \
  --select COUNT \
  --region ap-northeast-1
```

各テーブルの `Count` が 1 以上であることを確認する。

---

## 6. トラブルシューティング

### 6.1 ECR push 認証失敗

**症状:** `docker push` 時に `no basic auth credentials` または `denied: Your authorization token has expired` エラーが発生する。

**原因:** ECR ログイントークンの有効期限切れ（12時間）、またはログインコマンドの実行漏れ。

**対処:**

1. ECR ログインコマンドを再実行する:
   ```bash
   aws ecr get-login-password --region ap-northeast-1 | \
     docker login --username AWS --password-stdin \
     ${AWS_ACCOUNT_ID}.dkr.ecr.ap-northeast-1.amazonaws.com
   ```
2. AWS CLI の認証情報（`aws configure` または環境変数）が正しいことを確認する
3. IAM ユーザー/ロールに `ecr:GetAuthorizationToken` と `ecr:BatchCheckLayerAvailability`, `ecr:PutImage` 等の権限があることを確認する

**確認場所:** AWS コンソール → **IAM** → 該当ユーザー/ロールのポリシー

### 6.2 CloudFormation スタック作成ロールバック

**症状:** スタックのステータスが `ROLLBACK_COMPLETE` または `CREATE_FAILED` になる。

**原因:** IAM 権限不足、リソース名の競合、テンプレートの構文エラー、Lambda イメージが見つからない等。

**対処:**

1. AWS コンソール → **CloudFormation** → スタック → **イベント** タブでエラーの詳細を確認する
2. よくある原因と対処：
   - `Resource already exists`: 同名のリソース（テーブル等）が既に存在する → 既存リソースを削除するか、スタック名を変更する
   - `IAM capability required`: スタック作成画面で IAM リソース作成の承認チェックが入っていない → チェックを入れて再作成する
   - `Image does not exist`: ECR にイメージが push されていない → 手順 1 を再実行する
3. `ROLLBACK_COMPLETE` のスタックは削除してから再作成する必要がある

**確認場所:** AWS コンソール → **CloudFormation** → スタック → **イベント** タブ

### 6.3 シードスクリプト DynamoDB アクセス拒否

**症状:** `scripts/seed_dynamodb.py` 実行時に `AccessDeniedException` または `ResourceNotFoundException` エラーが発生する。

**原因:** AWS 認証情報の権限不足、またはテーブルが未作成（CloudFormation スタックが完了していない）。

**対処:**

1. CloudFormation スタックのステータスが `CREATE_COMPLETE` であることを確認する
2. AWS 認証情報を確認する:
   ```bash
   aws sts get-caller-identity
   ```
3. DynamoDB テーブルの存在を確認する:
   ```bash
   aws dynamodb list-tables --region ap-northeast-1 | grep EhimeAI2026
   ```
4. IAM ユーザー/ロールに DynamoDB への `PutItem` / `BatchWriteItem` 権限があることを確認する
5. 環境変数 `AWS_DEFAULT_REGION` が `ap-northeast-1` に設定されていることを確認する

**確認場所:** AWS コンソール → **DynamoDB** → **テーブル** で `EhimeAI2026-*` テーブルが存在することを確認
