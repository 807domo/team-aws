# Implementation Plan: 愛媛探索AIクイズ (Ehime Exploration AI Quiz)

## Overview

愛媛県の大学生・高専生向けAI学習プラットフォームの実装計画。FastAPI + SQLAlchemy + Jinja2/HTMX を使用した3層アーキテクチャで構築する。ドメインロジックは純粋関数として実装し、Hypothesisによるプロパティベーステストで正確性を保証する。

## Tasks

- [x] 1. プロジェクト構成とデータモデルの作成
  - [x] 1.1 プロジェクトのディレクトリ構造とパッケージ設定を作成する
    - `pyproject.toml` に依存関係（fastapi, uvicorn, sqlalchemy, jinja2, httpx, hypothesis, pytest, boto3）を定義
    - 以下のディレクトリ構造を作成: `app/`, `app/domain/`, `app/data/`, `app/presentation/`, `app/templates/`, `tests/`, `tests/properties/`, `tests/unit/`, `tests/integration/`
    - `app/__init__.py`, `app/domain/__init__.py`, `app/data/__init__.py`, `app/presentation/__init__.py` を作成
    - _Requirements: 9.1, 9.2_

  - [x] 1.2 Enum定義とデータモデルを作成する
    - `app/domain/models.py` に Region, Difficulty, ExamType, Grade, SessionStatus の Enum を定義
    - Course, Question, User, AnswerRecord, QuizSession, MockExamSession の Pydantic モデルまたは dataclass を定義
    - CourseInfo, AnswerResult, Explanation, CourseSummary, DashboardData, RadarChartData, ExplorationRate, WeakArea 等のレスポンスモデルを定義
    - _Requirements: 1.2, 2.1, 5.1, 6.1, 9.1_

  - [x] 1.3 SQLAlchemy ORM モデルとデータベーススキーマを作成する
    - `app/data/database.py` にデータベース接続設定（SQLite）と SessionLocal を定義
    - `app/data/models.py` に Course, Question, User, AnswerRecord, QuizSession, MockExamSession の SQLAlchemy モデルを定義
    - Question テーブルに unique ID 制約、4つの choice フィールド、correct_choice_index、exam_domain カラムを含める
    - Alembic またはメタデータ create_all によるスキーマ作成処理を実装
    - _Requirements: 9.1, 9.3, 9.5, 7.3_

- [x] 2. 採点モジュールとバリデーション（ドメイン層コア）
  - [x] 2.1 採点モジュール（scoring.py）を実装する
    - `app/domain/scoring.py` に `calculate_accuracy_rate(correct_count, total_count) -> float` を実装（パーセンテージ、小数第1位）
    - `calculate_grade(score_percentage) -> Grade` を実装（A: 90-100, B: 80-89, C: 70-79, D: 60-69, E: 0-59）
    - `calculate_domain_accuracy(answer_records) -> dict[str, float]` を実装
    - `identify_weak_areas(answer_records, threshold=0.5) -> list[WeakArea]` を実装（誤答率50%以上のドメイン特定）
    - すべて純粋関数として実装（副作用なし）
    - _Requirements: 4.2, 4.3, 5.3, 6.1, 6.2, 8.1_

  - [ ]* 2.2 Property 4 のプロパティテストを作成する
    - **Property 4: Accuracy rate calculation**
    - `tests/properties/test_scoring_properties.py` に正答率計算のプロパティテストを実装
    - Hypothesis で correct_count (0〜1000), total_count (1〜1000) を生成し、`round(correct / total * 100, 1)` と一致することを検証
    - コース別・全体の正答率両方をテスト
    - **Validates: Requirements 4.2, 4.3, 2.5**

  - [ ]* 2.3 Property 5 のプロパティテストを作成する
    - **Property 5: Grade assignment from score**
    - `tests/properties/test_scoring_properties.py` にグレード判定のプロパティテストを追加
    - Hypothesis で 0.0〜100.0 のスコアを生成し、閾値に基づくグレード判定を検証
    - **Validates: Requirements 5.3, 6.1**

  - [ ]* 2.4 Property 7 のプロパティテストを作成する
    - **Property 7: Domain-level accuracy calculation**
    - `tests/properties/test_scoring_properties.py` にドメイン別正答率のプロパティテストを追加
    - Hypothesis でドメイン付き回答レコードリストを生成し、各ドメインの正答率が正しく計算されることを検証
    - **Validates: Requirements 6.2**

  - [ ]* 2.5 Property 8 のプロパティテストを作成する
    - **Property 8: Weak area identification**
    - `tests/properties/test_weak_area_properties.py` に弱点特定のプロパティテストを実装
    - Hypothesis で10件以上の誤答を含む回答レコードを生成し、誤答率50%以上のドメインのみが弱点として特定されることを検証
    - **Validates: Requirements 8.1**

  - [x] 2.6 問題バリデーター（question_validator.py）を実装する
    - `app/domain/question_validator.py` に `validate_question(question_data: dict) -> ValidationResult` を実装
    - バリデーション条件: 非空テキスト、正確に4つの非空選択肢、correct_choice_index が 0-3、非空の ehime_trivia、非空の aws_ai_explanation、有効な course_id、有効な difficulty
    - 不正フィールドの特定とエラーメッセージを返す ValidationResult を定義
    - _Requirements: 9.1, 9.6, 2.1, 8.3_

  - [ ]* 2.7 Property 1 のプロパティテストを作成する
    - **Property 1: Question validation accepts valid and rejects invalid**
    - `tests/properties/test_validation_properties.py` に問題バリデーションのプロパティテストを実装
    - Hypothesis で有効/無効な問題データを生成し、バリデーション結果が仕様と一致することを検証
    - **Validates: Requirements 2.1, 5.4, 8.3, 9.1, 9.3, 9.6**

- [x] 3. Checkpoint - テストを実行して基本的なドメインロジックを確認
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. データアクセス層（リポジトリ）の実装
  - [x] 4.1 Course Repository を実装する
    - `app/data/course_repository.py` に CourseRepository クラスを実装
    - `get_all_courses() -> list[Course]`、`get_courses_by_region(region) -> list[Course]`、`get_course_by_id(course_id) -> Optional[Course]` メソッドを実装
    - 地域別グルーピングのヘルパーメソッドを追加
    - _Requirements: 1.1, 1.2, 1.4, 6.3_

  - [x] 4.2 Question Repository を実装する
    - `app/data/question_repository.py` に QuestionRepository クラスを実装
    - `create_question(question_data) -> Question`（バリデーション付き）、`get_question_by_id(question_id) -> Optional[Question]`、`get_questions_by_course(course_id) -> list[Question]`、`get_questions_by_domain(domain) -> list[Question]` メソッドを実装
    - 問題保存時に validate_question を呼び出し、不正データはリジェクト
    - _Requirements: 9.1, 9.4, 9.5, 9.6, 7.3_

  - [ ]* 4.3 Property 2 と Property 3 のプロパティテストを作成する
    - **Property 2: Question data round-trip preservation**
    - **Property 3: Question ID uniqueness**
    - `tests/properties/test_validation_properties.py` にラウンドトリップと ID 一意性のテストを追加
    - SQLite インメモリDBを使用してテスト実行
    - **Validates: Requirements 9.4, 9.5**

  - [x] 4.4 User Record Repository を実装する
    - `app/data/user_record_repository.py` に UserRecordRepository クラスを実装
    - `save_answer_record(record) -> AnswerRecord`、`get_records_by_user(user_id) -> list[AnswerRecord]`、`get_records_by_user_and_course(user_id, course_id) -> list[AnswerRecord]`、`get_accuracy_by_course(user_id, course_id) -> float`、`get_cumulative_accuracy(user_id) -> float` メソッドを実装
    - 同一問題への再回答も含めて全回答を記録
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.6_

- [ ] 5. ドメインサービスの実装
  - [x] 5.1 Quiz Service を実装する
    - `app/domain/quiz_service.py` に QuizService クラスを実装
    - `get_courses(region)`: 地域別コース一覧取得（地域グルーピング含む）
    - `start_course(user_id, course_id)`: QuizSession の作成と問題リスト取得
    - `submit_answer(session_id, question_id, choice_index)`: 正誤判定（correct_choice_index との比較）、AnswerRecord 保存、正答率再計算
    - `complete_course(session_id)`: コース完了サマリー（正解数/総問題数）生成
    - 地域に1つもコースがない場合は「準備中」状態を返すロジック
    - _Requirements: 1.1, 1.3, 1.4, 1.5, 2.1, 2.3, 2.4, 2.5, 4.1, 4.2_

  - [ ]* 5.2 Property 6 と Property 11 のプロパティテストを作成する
    - **Property 6: Course grouping by region**
    - **Property 11: Answer correctness determination**
    - `tests/properties/test_quiz_properties.py` にコース地域グルーピングと正誤判定のプロパティテストを実装
    - **Validates: Requirements 1.1, 2.3**

  - [x] 5.3 Results Service を実装する
    - `app/domain/results_service.py` に ResultsService クラスを実装
    - `get_dashboard_data(user_id)`: スコア、グレード、レーダーチャートデータ、探索率、学習履歴を集約
    - `get_radar_chart_data(user_id, exam_type)`: ドメイン別正答率の計算
    - `get_exploration_rate(user_id)`: 完了コース数/全コース数、完了地域数の計算
    - `get_attempt_history(user_id)`: 時系列順の試験結果リスト取得
    - 学習履歴なしの場合のメッセージ処理
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 5.4 Property 9 と Property 13 のプロパティテストを作成する
    - **Property 9: Exploration rate calculation**
    - **Property 13: Chronological ordering of attempts**
    - `tests/properties/test_results_properties.py` に探索率と時系列順のプロパティテストを実装
    - **Validates: Requirements 6.3, 6.4**

  - [x] 5.5 Mock Exam Engine を実装する
    - `app/domain/mock_exam_engine.py` に MockExamEngine クラスを実装
    - `start_exam(user_id, exam_type)`: 65問・90分のセッション作成（タイマー開始）
    - `submit_answer(session_id, question_id, choice_index)`: 回答記録（即時フィードバックなし）
    - `navigate_to_question(session_id, question_index)`: 問題間ナビゲーション
    - `get_remaining_time(session_id)`: 残り時間計算（max(0, expires_at - now)）
    - `finish_exam(session_id)`: 試験終了、未回答を不正解扱い、スコア・グレード計算
    - タイマー期限切れ時の自動終了処理
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.6_

  - [ ]* 5.6 Property 10 のプロパティテストを作成する
    - **Property 10: Mock exam remaining time calculation**
    - `tests/properties/test_mock_exam_properties.py` に残り時間計算のプロパティテストを実装
    - Hypothesis で start_time と current_time を生成し、残り時間が `max(0, (start + 90min) - current)` と一致することを検証
    - **Validates: Requirements 5.2**

- [x] 6. Checkpoint - サービス層のテストを実行して確認
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. プレゼンテーション層（API + テンプレート）
  - [x] 7.1 FastAPI アプリケーション基盤を構成する
    - `main.py` に FastAPI アプリケーション作成、Jinja2Templates 設定、静的ファイルマウント、ルーター登録を実装
    - `app/presentation/dependencies.py` に DI（Dependency Injection）を定義（リポジトリ・サービスの注入）
    - DB初期化とテーブル作成の起動時処理を追加
    - _Requirements: 1.1, 1.3_

  - [x] 7.2 コース選択画面のAPIエンドポイントとテンプレートを作成する
    - `app/presentation/routers/course_router.py` に `GET /` (コース選択画面) を実装
    - `app/templates/course_select.html` に地域別グルーピング表示のテンプレート作成（HTMX対応）
    - 地域タブ（中予・南予・東予）切り替えUIを実装
    - コースがない地域は「準備中」表示
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [x] 7.3 クイズ出題・回答画面のAPIエンドポイントとテンプレートを作成する
    - `app/presentation/routers/quiz_router.py` に `POST /quiz/start/{course_id}`, `GET /quiz/{session_id}/question`, `POST /quiz/{session_id}/answer` を実装
    - `app/templates/quiz.html` に1問ずつの4択クイズUI、正誤フィードバック表示（HTMX部分更新）を実装
    - `app/templates/explanation.html` に解説画面（愛媛トリビア + AWS/AI解説）と「次へ」ボタンを実装
    - `app/templates/course_complete.html` にコース完了サマリー画面を実装
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.4_

  - [x] 7.4 模擬試験画面のAPIエンドポイントとテンプレートを作成する
    - `app/presentation/routers/mock_exam_router.py` に `POST /mock-exam/start`, `GET /mock-exam/{session_id}`, `POST /mock-exam/{session_id}/answer`, `POST /mock-exam/{session_id}/finish` を実装
    - `app/templates/mock_exam_select.html` に試験タイプ選択（CCP / AI Practitioner）画面を実装
    - `app/templates/mock_exam.html` にカウントダウンタイマー、問題ナビゲーション、ページ離脱確認ダイアログ（JavaScript）を実装
    - `app/templates/mock_exam_result.html` に試験結果画面を実装
    - _Requirements: 5.1, 5.2, 5.3, 5.5, 5.6_

  - [x] 7.5 結果ダッシュボード画面のAPIエンドポイントとテンプレートを作成する
    - `app/presentation/routers/results_router.py` に `GET /results/dashboard` を実装
    - `app/templates/dashboard.html` にスコア・グレード表示、Chart.js レーダーチャート（ドメイン別正答率）、愛媛探索率、学習履歴グラフを実装
    - 学習履歴なしの場合の「まだ学習履歴がありません」メッセージ表示を実装
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 8. AI連携（Explanation Engine + AI Question Generator）
  - [x] 8.1 Explanation Engine を実装する
    - `app/domain/explanation_engine.py` に ExplanationEngine クラスを実装
    - `generate_explanation(question)`: Amazon Bedrock (Claude) を呼び出し、愛媛トリビア + AWS/AI解説を生成
    - 10秒タイムアウト処理と、タイムアウト時のフォールバック（question.ehime_trivia + question.aws_ai_explanation をそのまま返す）
    - 解説文字数制約（合計100〜500文字）のバリデーション
    - _Requirements: 3.1, 3.2, 3.3, 3.5_

  - [ ]* 8.2 Property 12 のプロパティテストを作成する
    - **Property 12: Explanation length constraint**
    - `tests/properties/test_quiz_properties.py` に解説文字数制約のプロパティテストを追加
    - Hypothesis で解説テキストを生成し、100〜500文字制約が守られることを検証
    - **Validates: Requirements 3.3**

  - [x] 8.3 AI Question Generator を実装する
    - `app/domain/ai_question_generator.py` に AIQuestionGenerator クラスを実装
    - `analyze_weak_areas(user_id)`: UserRecordRepository から回答データ取得し、scoring.identify_weak_areas を呼び出し
    - `generate_questions(weak_areas, count_per_area)`: Amazon Bedrock に弱点ドメイン情報を含むプロンプトを送信し、1〜5問/領域のパーソナライズ問題を生成
    - 30秒タイムアウト処理、不正形式レスポンスのバリデーション（4択・1正解）
    - フォールバック：同一ドメインのプリセット問題バンクから出題
    - 10件以上の誤答蓄積チェック（前提条件）
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 9. 初期データの投入とエラーハンドリング
  - [x] 9.1 初期問題データ（シードデータ）を作成する
    - `app/data/seed_data.py` に最低30問の初期問題データを作成
    - 3コース以上（中予・南予・東予それぞれ1コース以上）に分配
    - 各問題に exam_domain ラベルを付与（CCP: Cloud Concepts, Security, Technology, Billing / AI: Fundamentals, Generative AI, Responsible AI）
    - 各ドメイン最低3問を確保
    - 問題は愛媛シナリオ + AWS/AI概念の形式で作成
    - _Requirements: 9.2, 7.1, 7.2, 7.3, 7.4, 7.5, 1.4_

  - [x] 9.2 エラーハンドリングとリトライ機構を実装する
    - 成績記録保存失敗時のエラーメッセージ表示とリトライ処理を QuizService に追加
    - DB接続リトライ（最大3回、1秒待機）を database.py に実装
    - 模擬試験中ページ離脱の確認ダイアログをテンプレートJSに追加（既に7.4で基本実装済みの場合は統合）
    - APIレベルのエラーハンドラー（HTTPException）を FastAPI に登録
    - _Requirements: 4.5, 3.5, 5.5_

- [x] 10. 統合テストとワイヤリング
  - [x] 10.1 APIエンドポイントの統合テストを作成する
    - `tests/integration/test_api_endpoints.py` に FastAPI TestClient を使った統合テストを実装
    - コース選択→クイズ開始→回答→解説→完了のフロー、模擬試験フロー、結果ダッシュボードの正常系テスト
    - _Requirements: 1.3, 2.1, 2.3, 2.4, 2.5, 3.4, 5.1_

  - [x] 10.2 問題バンクの初期データ要件を検証する統合テストを作成する
    - `tests/integration/test_question_bank.py` にシードデータ検証テストを実装
    - 30問以上存在すること、3コース以上であること、各ドメイン3問以上であること、各問題に exam_domain ラベルがあることを検証
    - _Requirements: 9.2, 7.1, 7.2, 7.3_

- [x] 11. Final Checkpoint - 全テスト実行と最終確認
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties defined in the design document
- Unit tests validate specific examples and edge cases
- Amazon Bedrock の API キーや認証情報は環境変数で管理する（コードにハードコードしない）
- 初期開発では SQLite を使用し、本番環境では PostgreSQL に切り替え可能な設計とする

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["1.3"] },
    { "id": 3, "tasks": ["2.1", "2.6"] },
    { "id": 4, "tasks": ["2.2", "2.3", "2.4", "2.5", "2.7"] },
    { "id": 5, "tasks": ["4.1", "4.2", "4.4"] },
    { "id": 6, "tasks": ["4.3"] },
    { "id": 7, "tasks": ["5.1", "5.3", "5.5"] },
    { "id": 8, "tasks": ["5.2", "5.4", "5.6"] },
    { "id": 9, "tasks": ["7.1"] },
    { "id": 10, "tasks": ["7.2", "7.3", "7.4", "7.5"] },
    { "id": 11, "tasks": ["8.1", "8.3"] },
    { "id": 12, "tasks": ["8.2"] },
    { "id": 13, "tasks": ["9.1", "9.2"] },
    { "id": 14, "tasks": ["10.1", "10.2"] }
  ]
}
```
