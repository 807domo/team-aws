# Requirements Document

## Introduction

既存のRPG風トップ画面（`rpg_top.html`）のSVGマップとクリック時UXを改善する。現在のマップは直線ベースの簡易ポリゴンで愛媛県3地域を描画しているが、これを愛媛県の実際の地理的形状に近いSVGパスに置き換える。また、マップ地域クリック時にコースパネルがビューポート下部に隠れてしまう問題を解消し、マップ操作の結果がユーザーに即座に視認できるレイアウトとフィードバックを実現する。

## Glossary

- **Interactive_Map**: SVGで描画される愛媛県のインタラクティブ地図コンポーネント
- **Map_Area**: インタラクティブマップ上で分割された地域（中予・南予・東予）
- **Course_Panel**: マップエリア選択時に表示されるコースカード一覧パネル
- **Geographic_Path**: 愛媛県の実際の地形データに基づいたSVGパス要素
- **Side_By_Side_Layout**: ワイドスクリーン時にマップとコースパネルを横並びに配置するレスポンシブレイアウト
- **Region_Tooltip**: マップ地域ホバー時に表示されるコース数と進捗サマリーのポップアップ
- **Scroll_Behavior**: マップクリック後にコースパネルまで自動スクロールする動作
- **Region_Tab**: 既存の地域切り替えタブ（中予・南予・東予）
- **Progress_Status**: エリアの学習進捗状態（未着手・進行中・コンプリート）

## Requirements

### Requirement 1: 地理的に正確なSVGマップ形状

**User Story:** ユーザーとして、愛媛県の実際の形をしたマップを見たい。地域の位置関係を直感的に把握し、学習対象の地理的なつながりを理解するためである。

#### Acceptance Criteria

1. THE Interactive_Map SHALL render the outline of Ehime Prefecture using Geographic_Paths derived from publicly available geographic data (e.g., National Land Numerical Information or equivalent) so that the shape is recognizably Ehime Prefecture to a local resident
2. THE Interactive_Map SHALL divide the prefecture shape into exactly 3 Map_Areas corresponding to 中予, 南予, and 東予 using Geographic_Paths that follow the actual administrative boundaries between these regions
3. WHEN Geographic_Paths are created, THE Interactive_Map SHALL use SVG `<path>` elements with cubic or quadratic Bézier curves to represent coastlines and curved boundaries, replacing the current straight-line polygon approximations
4. THE Interactive_Map SHALL maintain a viewBox that fits the entire prefecture shape with uniform padding on all sides, preserving the geographic aspect ratio of Ehime Prefecture (approximately wider than tall)
5. THE Interactive_Map SHALL preserve all existing interactive attributes on each Map_Area group element: unique ID (`map-region-CHUYO`, `map-region-NANYO`, `map-region-TOYO`), `role="button"`, `tabindex="0"`, `aria-label`, `data-region`, and HTMX attributes (`hx-get`, `hx-target`, `hx-swap`)
6. THE Interactive_Map SHALL ensure each Map_Area has a minimum click target size of 44×44 CSS pixels at viewport width 320px
7. THE Interactive_Map SHALL display the region name ("中予", "南予", "東予") as a text label centered within each Map_Area's geographic boundary

### Requirement 2: レスポンシブ横並びレイアウト

**User Story:** ユーザーとして、マップをクリックした結果（コース一覧）をスクロールせずに確認したい。マップ操作の即時フィードバックを得て、スムーズにコースを選択するためである。

#### Acceptance Criteria

1. WHILE the viewport width is 1024px or wider, THE layout SHALL place the Interactive_Map and the Course_Panel in a Side_By_Side_Layout where the map occupies the left column and the course panel occupies the right column, both visible within the viewport without vertical scrolling
2. WHILE the viewport width is less than 1024px, THE layout SHALL stack the Interactive_Map above the Course_Panel in a single-column layout (existing behavior maintained)
3. WHILE in Side_By_Side_Layout, THE Interactive_Map column SHALL occupy between 40% and 50% of the available content width, and the Course_Panel column SHALL occupy the remaining width
4. WHILE in Side_By_Side_Layout, THE Course_Panel SHALL have a maximum height equal to the viewport height minus the status area and header, with vertical scrolling enabled within the panel if content exceeds this height
5. WHEN a Map_Area is clicked while in Side_By_Side_Layout, THE Course_Panel SHALL update its content via HTMX swap without page scroll, keeping both the map and panel visible simultaneously
6. WHILE in Side_By_Side_Layout, THE Interactive_Map SHALL remain in a sticky position so that it stays visible while the user scrolls within the Course_Panel

### Requirement 3: ナロー画面でのスムーススクロール

**User Story:** ユーザーとして、モバイルでマップをクリックした際にコースパネルが自動的に画面内に表示されてほしい。スクロール操作なしでクリック結果を確認するためである。

#### Acceptance Criteria

1. WHEN a Map_Area is clicked while the viewport width is less than 1024px, THE Scroll_Behavior SHALL smooth-scroll the page to bring the Course_Panel into view within 300 milliseconds after the HTMX content swap completes
2. WHEN smooth-scrolling to the Course_Panel, THE Scroll_Behavior SHALL position the top of the Course_Panel at 80px below the viewport top to maintain context of the map above
3. IF the Course_Panel is already fully visible within the viewport at the time of Map_Area click, THEN THE Scroll_Behavior SHALL not perform any scroll action
4. THE Scroll_Behavior SHALL use the CSS `scroll-behavior: smooth` property or equivalent JavaScript smooth scroll to provide a fluid scrolling animation

### Requirement 4: 地域ツールチップ表示

**User Story:** ユーザーとして、マップの各地域にホバーした際にコース数と進捗情報を確認したい。クリックする前にどの地域に取り組むか判断するためである。

#### Acceptance Criteria

1. WHEN the user hovers over a Map_Area for 400 milliseconds or longer, THE Region_Tooltip SHALL appear near the cursor position displaying the region name, the total number of courses in that region, and the number of completed courses
2. WHEN the cursor leaves the Map_Area, THE Region_Tooltip SHALL disappear within 150 milliseconds
3. THE Region_Tooltip SHALL be positioned so that it does not overflow the viewport boundaries, adjusting its placement (above, below, left, or right of the cursor) as needed
4. WHILE on a touch device (no hover capability detected), THE Region_Tooltip SHALL not be displayed, and the course summary information SHALL instead be shown in the region label text within the map
5. THE Region_Tooltip SHALL display text in the format: "{region_name} - {completed_count}/{total_count} コース完了"
6. IF a region has zero courses, THEN THE Region_Tooltip SHALL display "{region_name} - コース準備中"

### Requirement 5: マップクリック時のビジュアルフィードバック強化

**User Story:** ユーザーとして、マップをクリックした瞬間に視覚的な応答を得たい。クリックが認識されたことを即座に確認するためである。

#### Acceptance Criteria

1. WHEN a Map_Area is clicked, THE Interactive_Map SHALL apply a brief scale pulse animation (scale to 1.03 then return to 1.0) on the clicked area within 200 milliseconds to provide immediate click feedback
2. WHEN a Map_Area is clicked, THE Interactive_Map SHALL transition the non-selected Map_Areas to a reduced opacity (0.5) within 150 milliseconds to visually emphasize the selected region
3. WHEN a different Map_Area is subsequently clicked, THE Interactive_Map SHALL restore all Map_Areas to their default opacity and apply the new selection effects within 150 milliseconds
4. THE click feedback animation SHALL not interfere with the existing hover and selection effects defined in the previous specification (3px selected border, fill-opacity increase on hover)
5. WHILE an HTMX request triggered by a Map_Area click is in progress, THE Interactive_Map SHALL display a subtle loading indicator (pulsing opacity animation) on the selected Map_Area until the response is received

