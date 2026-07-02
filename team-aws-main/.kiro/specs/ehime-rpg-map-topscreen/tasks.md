# Implementation Plan: RPG風マップトップ画面

## Overview

既存の愛媛探索AIクイズアプリのトップ画面を、RPG要素（XP・レベル・称号）とインタラクティブSVGマップを統合したRPG風トップ画面に刷新する。既存のレイヤードアーキテクチャ（data → domain → presentation）を維持し、純粋関数モジュール群をドメイン層に追加する。

## Tasks

- [x] 1. データ層: UserModelスキーマ拡張とマイグレーション
  - [x] 1.1 UserModelに total_xp, level カラムを追加する
    - `app/data/models.py` の `UserModel` クラスに `total_xp` (Integer, NOT NULL, default 0) と `level` (Integer, NOT NULL, default 1) カラムを追加する
    - SQLAlchemy の `mapped_column` と `server_default=text("0")` / `text("1")` を使用する
    - _Requirements: 9.1, 9.2, 9.3_

  - [x] 1.2 user_record_repository にXP/Level永続化メソッドを追加する
    - `app/data/user_record_repository.py` に `get_user_xp(user_id)` と `update_user_xp_and_level(user_id, total_xp, level)` メソッドを追加する
    - DB null/不正データ時のフォールバック処理（total_xp=0, level=1）を含める
    - _Requirements: 9.1, 9.2, 9.4, 9.5_

  - [x] 1.3 SQLiteマイグレーションスクリプトを作成する
    - `ALTER TABLE users ADD COLUMN total_xp INTEGER NOT NULL DEFAULT 0;` と `ALTER TABLE users ADD COLUMN level INTEGER NOT NULL DEFAULT 1;` を実行するマイグレーションスクリプトを作成する
    - 既存ユーザーはデフォルト値で初期化される
    - _Requirements: 9.3_

- [x] 2. ドメイン層: XP計算モジュール
  - [x] 2.1 xp_calculator.py を新規作成する
    - `app/domain/xp_calculator.py` に `XP_PER_CORRECT_ANSWER = 10`, `PERFECT_COURSE_BONUS = 100` 定数を定義する
    - `calculate_xp_award(correct_count, total_count) -> int` を実装する: 正解数×10 + パーフェクト時100ボーナス
    - `add_xp(current_xp, award) -> int` を実装する: 引数が負の場合は ValueError を送出
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.6_

  - [x]* 2.2 xp_calculator のプロパティテストを作成する
    - **Property 1: XP計算の正確性**
    - **Property 2: XP非負不変量**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.6**
    - `tests/test_xp_calculator_properties.py` に Hypothesis を使用したプロパティテストを実装する

  - [x]* 2.3 xp_calculator のユニットテストを作成する
    - 0問正解、1問正解、全問正解（5問、10問）の具体例テスト
    - 負値入力時の ValueError テスト
    - _Requirements: 2.1, 2.2, 2.3, 2.6_

- [x] 3. ドメイン層: レベル計算モジュール
  - [x] 3.1 level_calculator.py を新規作成する
    - `app/domain/level_calculator.py` に `MAX_LEVEL = 99`, `MAX_XP = 980_100` 定数を定義する
    - `calculate_level(total_xp) -> int` を実装する: Level N の必要XP = N² × 100, 返り値は1〜99
    - `xp_threshold_for_level(level) -> int` を実装する: level² × 100
    - `calculate_xp_gauge(total_xp, level) -> dict` を実装する: current_level_xp, required_xp, percentage を返す
    - 入力バリデーション: 負値・非整数入力時は ValueError を送出
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 1.2, 1.3, 1.5_

  - [x]* 3.2 level_calculator のプロパティテストを作成する
    - **Property 3: レベル計算ラウンドトリップ**
    - **Property 4: レベル計算入力バリデーション**
    - **Property 7: XPゲージの範囲と計算式正確性**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 1.2, 1.3, 1.5**
    - `tests/test_level_calculator_properties.py` に Hypothesis を使用したプロパティテストを実装する

  - [x]* 3.3 level_calculator のユニットテストを作成する
    - 境界値テスト: XP=0→L1, XP=99→L1, XP=100→L2, XP=400→L3, XP=980100→L99
    - ゲージ計算: Level 1で50XP→50%, Level 2で200XP→33.3%
    - 不正入力テスト: 負値, 浮動小数点, None
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 1.2, 1.3, 1.5_

- [x] 4. ドメイン層: 称号マスタモジュール
  - [x] 4.1 title_master.py を新規作成する
    - `app/domain/title_master.py` に `TITLE_MAPPING` リストと `MAX_TITLE` 定数を定義する
    - `get_title(level) -> str` を実装する: Level 1-2="伊予の迷い人", 3-5="愛媛の駆け出しAI研究者", 6-9="道後を極めしAIエンジニア", 10+="伝説の愛媛AIマスター"
    - 入力バリデーション: levelが1未満または非整数の場合 ValueError を送出
    - _Requirements: 4.1, 4.3, 4.4_

  - [x]* 4.2 title_master のプロパティテストを作成する
    - **Property 5: 称号マッピングの全射性と正確性**
    - **Property 6: 称号マスタ入力バリデーション**
    - **Validates: Requirements 4.1, 4.3, 4.4**
    - `tests/test_title_master_properties.py` に Hypothesis を使用したプロパティテストを実装する

  - [x]* 4.3 title_master のユニットテストを作成する
    - 各レベル範囲境界テスト: L1, L2, L3, L5, L6, L9, L10, L99
    - 不正入力テスト: 0, -1, 浮動小数点
    - _Requirements: 4.1, 4.3, 4.4_

- [x] 5. ドメイン層: 進捗ステータス算出モジュール
  - [x] 5.1 progress_calculator.py を新規作成する
    - `app/domain/progress_calculator.py` に `ProgressStatus` Enum（NOT_STARTED, IN_PROGRESS, COMPLETE）を定義する
    - `calculate_region_progress(region, courses_in_region, user_answer_records, course_questions) -> ProgressStatus` を実装する
    - 判定ロジック: 回答記録なし→未着手、一部コース完了→進行中、全コース全問正解セッション存在→コンプリート
    - ゼロコース地域は「コンプリート」を返す
    - _Requirements: 7.2, 7.4_

  - [x]* 5.2 progress_calculator のプロパティテストを作成する
    - **Property 8: 進捗ステータスの決定性**
    - **Validates: Requirements 7.2, 7.4**
    - `tests/test_progress_calculator_properties.py` に Hypothesis を使用したプロパティテストを実装する

  - [x]* 5.3 progress_calculator のユニットテストを作成する
    - 空コース地域、一部完了地域、全完了地域の具体例テスト
    - ゼロコース地域のテスト
    - _Requirements: 7.2, 7.4_

- [x] 6. Checkpoint - ドメイン層の実装確認
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. ドメイン層: ドメインモデル追加とquiz_service統合
  - [x] 7.1 app/domain/models.py に UserStatus と RegionMapData データクラスを追加する
    - `UserStatus` dataclass: display_name, level, title, total_xp, xp_gauge_percentage, current_level_xp, required_xp
    - `RegionMapData` dataclass: region, progress_status, fill_color, courses
    - _Requirements: 1.1, 7.1_

  - [x] 7.2 quiz_service.py にXP付与ロジックを統合する
    - コース完了時に `xp_calculator.calculate_xp_award()` を呼び出してXP量を算出
    - `xp_calculator.add_xp()` で累計XPを計算
    - `level_calculator.calculate_level()` で新レベルを算出
    - `user_record_repository.update_user_xp_and_level()` で永続化
    - XP永続化失敗時のエラーハンドリング（エラーメッセージ表示、メモリ保持）
    - _Requirements: 2.1, 2.2, 2.4, 2.5, 9.5_

  - [x]* 7.3 XP/レベル整合性のプロパティテストを作成する
    - **Property 9: XP/レベル整合性不変量**
    - **Validates: Requirements 9.5**
    - `tests/test_xp_level_consistency_properties.py` に Hypothesis を使用したプロパティテストを実装する

- [x] 8. プレゼンテーション層: SVGマップとテンプレート
  - [x] 8.1 愛媛県SVGマップファイルを作成する
    - `app/static/svg/ehime_map.svg` に愛媛県3地域マップを作成する
    - 3地域（中予・南予・東予）の `<g>` 要素にユニークID (`map-region-CHUYO`, `map-region-NANYO`, `map-region-TOYO`) を付与
    - `role="button"`, `tabindex="0"`, `aria-label` でアクセシビリティ対応
    - 各エリアのクリックターゲットサイズが44×44 CSS px以上であることを確保
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 6.4_

  - [x] 8.2 RPGトップ画面テンプレート rpg_top.html を作成する
    - `app/templates/rpg_top.html` に base.html を継承するテンプレートを作成する
    - ステータスエリア: display_name, Level, Title, XP_Gaugeプログレスバーを表示
    - SVGマップ: ehime_map.svg をインラインでインクルード
    - コースパネル: 地域タブとコースカード一覧を表示
    - 進捗色（未着手=#D1D5DB, 進行中=#FED7AA, コンプリート=#F97316）の適用
    - HTMX属性: マップクリック時に `hx-get="/courses/{region}"` でコースパネルを差し替え
    - _Requirements: 1.1, 1.2, 5.1, 7.1, 7.5, 8.1, 8.4_

  - [x] 8.3 マップ用CSSスタイルを作成する
    - `app/static/css/rpg_map.css` にマップのホバー・選択・フォーカスエフェクトのスタイルを定義する
    - ホバー: fill-opacity +20%, drop-shadow 4px blur, transition 150ms
    - 選択: 3px border（fill色と視覚的に区別可能）, transition 150ms
    - 選択中ホバー: 選択状態を維持（ホバーエフェクト非適用）
    - フォーカス: 2px以上のoutline
    - レスポンシブ: 320px〜1920px, アスペクト比維持, 横スクロールなし
    - _Requirements: 5.5, 6.1, 6.2, 6.3, 6.5_

- [x] 9. プレゼンテーション層: ルーターとエンドポイント
  - [x] 9.1 top_router.py を新規作成する
    - `app/presentation/routers/top_router.py` に FastAPI `APIRouter` を作成する
    - `GET /` エンドポイント: ユーザーのXP/レベル/称号/ゲージ/進捗を算出し `rpg_top.html` を返す
    - `safe_get_user_status()` ヘルパー: DB異常時のフォールバック値（Level 1, 0 XP, "伊予の迷い人"）対応
    - デフォルト選択地域: 中予
    - _Requirements: 1.1, 1.4, 8.4, 9.4_

  - [x] 9.2 HTMX用コースパネルエンドポイントを追加する
    - `GET /courses/{region}` エンドポイント: 指定地域のコースカードHTMLフラグメントを返す
    - コースゼロ地域の場合は「コースは現在準備中です」メッセージを返す
    - HTMXリクエストへのレスポンスとして部分HTMLを返す
    - _Requirements: 8.1, 8.5_

  - [x] 9.3 main.py にルーターを登録する
    - `app/presentation/routers/top_router.py` のルーターを `main.py` に登録する
    - 既存のルーターとの競合がないことを確認する
    - _Requirements: 1.1_

- [x] 10. プレゼンテーション層: マップ↔タブ連動のクライアントサイドロジック
  - [x] 10.1 マップ選択とタブ連動のJavaScriptを実装する
    - マップエリアクリック時にHTMX経由でコースパネルを更新するロジックを実装する
    - タブクリック時にマップの選択状態を同期するロジックを実装する
    - マップ選択状態の排他制御（1エリアのみ選択可能）
    - Enterキーでのマップ選択をサポートする
    - _Requirements: 6.2, 6.3, 8.1, 8.2, 8.3_

- [x] 11. Checkpoint - 全体結合確認
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. 統合テストとフォールバック確認
  - [x]* 12.1 統合テストを作成する
    - GET `/` がRPGトップ画面HTMLを返すことの確認テスト
    - GET `/courses/{region}` が正しいコースフラグメントを返すことの確認テスト
    - クイズ完了後のXP更新→トップ画面反映フローのテスト
    - マイグレーション後の既存ユーザーデフォルト値確認テスト
    - SVGフォールバック（テキストリンク）の動作確認テスト
    - _Requirements: 1.4, 5.6, 8.1, 9.3, 9.4_

- [x] 13. Final checkpoint - 最終確認
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (Properties 1-9 from design)
- Unit tests validate specific examples and edge cases
- Python (FastAPI + SQLAlchemy + Jinja2 + HTMX + Hypothesis) is the implementation stack
- 既存の `scoring.py` パターンに倣い、新モジュールは副作用のない純粋関数群として実装する

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.3"] },
    { "id": 1, "tasks": ["1.2", "2.1", "3.1", "4.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "3.2", "3.3", "4.2", "4.3", "5.1"] },
    { "id": 3, "tasks": ["5.2", "5.3", "7.1"] },
    { "id": 4, "tasks": ["7.2", "8.1"] },
    { "id": 5, "tasks": ["7.3", "8.2", "8.3"] },
    { "id": 6, "tasks": ["9.1", "9.2"] },
    { "id": 7, "tasks": ["9.3", "10.1"] },
    { "id": 8, "tasks": ["12.1"] }
  ]
}
```
