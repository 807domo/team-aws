# Requirements Document

## Introduction

既存の愛媛探索AIクイズアプリケーション（FastAPI + Jinja2 + SQLAlchemy）のトップ画面を、愛媛県のインタラクティブマップとRPG要素（経験値・レベル・称号）を組み合わせたRPG風トップ画面に刷新する。ユーザーの学習モチベーション向上、愛媛県の地域と学習内容の結びつき強化、および進捗の可視化を目的とする。

## Glossary

- **Top_Screen**: 愛媛探索AIクイズのトップ画面（ルートURL `/` で表示される画面）
- **Status_Area**: トップ画面に固定表示されるRPG風ステータス表示エリア
- **Interactive_Map**: SVGで描画される愛媛県のインタラクティブ地図コンポーネント
- **Map_Area**: インタラクティブマップ上で分割された地域（中予・南予・東予）
- **XP**: 経験値（Experience Points）。クイズ正解やコース完了で獲得するポイント
- **Level**: ユーザーの現在レベル。累計XPに基づいて算出される
- **Title**: ユーザーの称号。現在のレベルに基づいて決定される
- **XP_Gauge**: 次のレベルアップまでの進捗を視覚的に示すプログレスバー
- **Course_Panel**: マップエリア選択時に表示されるコースカード一覧パネル
- **Progress_Status**: エリアの学習進捗状態（未着手・進行中・コンプリート）
- **XP_Calculator**: 経験値の算出と累計を管理するドメインロジックモジュール
- **Level_Calculator**: 累計XPからレベルを算出するドメインロジックモジュール
- **Title_Master**: レベルと称号の対応関係を管理するマスタデータ
- **Region_Tab**: 既存の地域切り替えタブ（中予・南予・東予）

## Requirements

### Requirement 1: ステータス表示

**User Story:** ユーザーとして、トップ画面で自分のレベル・経験値・称号を常時確認したい。学習の成長を実感し、モチベーションを維持するためである。

#### Acceptance Criteria

1. WHEN Top_Screen is loaded, THE Status_Area SHALL display the user's display_name (truncated to 20 characters with ellipsis if longer), current Level, current Title, and XP_Gauge in a fixed position at the top of the screen below the header
2. THE XP_Gauge SHALL render as a horizontal progress bar showing the percentage of XP earned toward the next level, clamped to the range 0% to 100%
3. WHEN XP_Gauge percentage is calculated, THE Status_Area SHALL compute it as (current_level_xp / required_xp_for_next_level) × 100, where current_level_xp is the XP accumulated since the last level-up and required_xp_for_next_level is the difference between the next level's cumulative XP threshold and the current level's cumulative XP threshold ((N+1)² × 100 − N² × 100 for a user at Level N)
4. WHEN a quiz session is completed and the user returns to Top_Screen, THE Status_Area SHALL reflect the latest XP, Level, and Title values from the backend within 2 seconds of page load
5. IF the user has reached the maximum defined Level and no higher level threshold exists, THEN THE XP_Gauge SHALL display as 100% full and THE Status_Area SHALL continue to show the current Level and Title

### Requirement 2: 経験値算出

**User Story:** ユーザーとして、クイズに正解するたびに経験値を獲得したい。正解する喜びと成長の実感を得るためである。

#### Acceptance Criteria

1. WHEN a user answers a quiz question correctly, THE XP_Calculator SHALL award 10 XP to the user and update the user's cumulative total XP in the user's record
2. WHEN a user answers the last question in a Course and all answers in that Course attempt are correct, THE XP_Calculator SHALL award an additional 100 XP bonus to the user on top of the per-question XP
3. WHEN a user answers a quiz question incorrectly, THE XP_Calculator SHALL award 0 XP for that question
4. IF a user retakes a Course they have previously completed, THEN THE XP_Calculator SHALL award per-question XP and completion bonus XP using the same rules as the first attempt
5. IF the XP_Calculator fails to persist the updated cumulative total XP to the user's record, THEN THE XP_Calculator SHALL display an error message indicating that XP was not saved and SHALL retain the XP award so that persistence can be retried
6. THE XP_Calculator SHALL store the cumulative total XP as a non-negative integer with no upper bound, where the minimum value is 0

### Requirement 3: レベルアップ計算

**User Story:** ユーザーとして、経験値を貯めてレベルアップしたい。RPG的な成長感を楽しむためである。

#### Acceptance Criteria

1. THE Level_Calculator SHALL determine the user's Level based on cumulative total XP using the formula: required total XP for Level N = N² × 100 (Level 1 requires 0 XP, Level 2 requires 100 XP, Level 3 requires 400 XP, Level 4 requires 900 XP), where Level ranges from 1 to 99 and XP is a non-negative integer ranging from 0 to 980,100
2. WHEN the user's cumulative XP reaches or exceeds the threshold for the next level, THE Level_Calculator SHALL update the user's Level to the highest Level whose threshold is satisfied by the current cumulative XP (e.g., if XP jumps from 0 to 500, Level SHALL be set to 3 because 400 ≤ 500 < 900)
3. THE Level_Calculator SHALL satisfy the round-trip property: for any XP value from 0 to 980,100, computing the Level from XP and then computing the XP threshold range for that Level SHALL always place the original XP within that range (threshold for computed Level ≤ XP < threshold for computed Level + 1)
4. IF the Level_Calculator receives a negative XP value or a non-integer XP value, THEN THE Level_Calculator SHALL reject the input and return an error indicating the XP value is invalid

### Requirement 4: 称号決定

**User Story:** ユーザーとして、レベルに応じた称号を得たい。学習到達度を象徴するラベルでモチベーションを高めるためである。

#### Acceptance Criteria

1. THE Title_Master SHALL assign titles based on the user's current Level according to the following mapping: Level 1-2 = "伊予の迷い人", Level 3-5 = "愛媛の駆け出しAI研究者", Level 6-9 = "道後を極めしAIエンジニア", Level 10以上 = "伝説の愛媛AIマスター" (Levelの有効範囲は1以上の整数とする)
2. WHEN the user's Level changes, THE Title_Master SHALL update the displayed Title to match the new Level range within the same response that confirms the Level change
3. THE Title_Master SHALL map every Level value within the valid range (1以上の整数) to exactly one Title with no gaps or overlaps in level ranges
4. IF the Level value is less than 1 or is not an integer, THEN THE Title_Master SHALL reject the value and retain the user's current Title unchanged

### Requirement 5: インタラクティブマップ描画

**User Story:** ユーザーとして、愛媛県の地図をビジュアルで確認しながらエリアを選択したい。地域と学習内容の結びつきを直感的に理解するためである。

#### Acceptance Criteria

1. WHEN Top_Screen is loaded, THE Interactive_Map SHALL render an SVG-based map of Ehime Prefecture horizontally centered within the main content area within 3 seconds of page load completion
2. THE Interactive_Map SHALL divide the map into exactly 3 clickable Map_Areas: "中予", "南予", "東予", each with a minimum touch/click target size of 44×44 CSS pixels
3. THE Interactive_Map SHALL assign each Map_Area a distinct SVG path element with a unique identifier corresponding to the Region enum value
4. THE Interactive_Map SHALL display the region name as visible text label within or adjacent to each Map_Area
5. THE Interactive_Map SHALL be responsive on viewport widths from 320px to 1920px such that the map maintains its aspect ratio, no horizontal scrollbar appears, and the map width occupies between 50% and 100% of the available content width
6. IF the SVG map fails to render, THEN THE Interactive_Map SHALL display the region names as a fallback list of clickable text links enabling area selection

### Requirement 6: マップホバー・選択エフェクト

**User Story:** ユーザーとして、マップ上でエリアにホバーやクリックした際に視覚的フィードバックを得たい。操作対象を明確に把握するためである。

#### Acceptance Criteria

1. WHEN the user hovers over a Map_Area that is not in selected state, THE Interactive_Map SHALL highlight that area by increasing its fill opacity by 20% from the default value and applying a drop-shadow filter with a 4px blur radius, with the visual transition completing within 150 milliseconds
2. WHEN the user clicks a Map_Area, THE Interactive_Map SHALL set that area to a selected state indicated by a 3px-wide border that is visually distinct from the fill color, with the visual transition completing within 150 milliseconds
3. WHEN a Map_Area is in selected state and another Map_Area is clicked, THE Interactive_Map SHALL revert the previously selected area to its default appearance and apply the selected state to the newly clicked area
4. THE Interactive_Map SHALL provide keyboard navigation support allowing users to move focus between Map_Areas using the Tab key, activate selection using the Enter key, and display a visible focus indicator with at least 2px outline width around the focused Map_Area
5. WHILE a Map_Area is in selected state, IF the user hovers over that selected Map_Area, THEN THE Interactive_Map SHALL maintain the selected state appearance without applying the hover effect

### Requirement 7: 進捗度に応じたマップ変化

**User Story:** ユーザーとして、各エリアの学習進捗をマップの色で一目で確認したい。学習完了エリアの達成感を視覚的に得るためである。

#### Acceptance Criteria

1. WHEN Top_Screen is loaded, THE Interactive_Map SHALL display each Map_Area with a fill color based on its Progress_Status: 未着手 = light gray (#D1D5DB), 進行中 = light orange (#FED7AA), コンプリート = vivid mikan orange (#F97316)
2. THE Interactive_Map SHALL determine Progress_Status for each Map_Area as follows: 未着手 = no courses in the area have any answer records for the current user, 進行中 = at least one course has answer records but not all courses in the area are fully completed (all questions answered correctly in at least one session), コンプリート = all courses in the area have been fully completed (each course has at least one session where all questions were answered correctly)
3. WHEN a quiz session is completed, THE Interactive_Map SHALL update the corresponding Map_Area's Progress_Status and fill color upon the next Top_Screen load
4. IF a region has zero courses assigned, THEN THE Interactive_Map SHALL display that Map_Area in the コンプリート color (#F97316) since there is nothing left to complete
5. THE Progress_Status fill color SHALL serve as the base color for hover and selection effects defined in Requirement 6 (hover increases opacity from the progress color, selection adds border to the progress-colored area)

### Requirement 8: コース選択パネル連動

**User Story:** ユーザーとして、マップ上でエリアをクリックしたときに該当エリアのコース一覧を表示したい。マップから直感的にコースを選択するためである。

#### Acceptance Criteria

1. WHEN a Map_Area is clicked, THE Course_Panel SHALL replace its content with the list of course cards filtered by the selected region within 500 milliseconds of the click event
2. WHEN a Map_Area is clicked, THE Region_Tab SHALL synchronize its active state to match the clicked Map_Area's region
3. WHEN a Region_Tab is clicked, THE Interactive_Map SHALL update its selected state to highlight the corresponding Map_Area and THE Course_Panel SHALL replace its content with the list of course cards filtered by the clicked tab's region
4. WHEN Top_Screen is loaded with no prior Map_Area selection, THE Course_Panel SHALL display courses for the default region (中予), THE Region_Tab SHALL show 中予 as the active tab, and THE Interactive_Map SHALL display the 中予 Map_Area in selected state
5. IF the selected region contains zero courses, THEN THE Course_Panel SHALL display a message indicating that no courses are available for the selected region

### Requirement 9: ステータスデータ永続化

**User Story:** ユーザーとして、ログイン時にこれまでの累計XPとレベルが保持されていることを期待する。学習の継続性を維持するためである。

#### Acceptance Criteria

1. THE system SHALL store the user's cumulative total_xp as a non-negative integer column (minimum value 0) in the users table
2. THE system SHALL store the user's current level as a positive integer column (minimum value 1) in the users table
3. WHEN the users table is migrated, THE system SHALL set default values of total_xp = 0 and level = 1 for existing user records
4. IF the database returns null, negative, or non-integer XP data for a user, THEN THE Status_Area SHALL display Level 1, 0 XP, and the default title "伊予の迷い人"
5. WHEN total_xp is updated, THE system SHALL recalculate and persist the level value using the Level_Calculator formula so that total_xp and level remain consistent
