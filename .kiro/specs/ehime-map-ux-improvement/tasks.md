# Implementation Plan: ehime-map-ux-improvement

## Overview

RPGトップ画面のSVGマップUXを5軸で改善する実装計画。地理的SVGパス置換、レスポンシブ横並びレイアウト、スムーススクロール、ツールチップ、クリックフィードバックを段階的に実装し、既存のFastAPI + Jinja2 + HTMX + vanilla JS + CSSスタックを維持する。

## Tasks

- [x] 1. SVGマップの地理的パス置換とテンプレート構造変更
  - [x] 1.1 Geographic SVGパスデータの作成と配置
    - `app/static/svg/ehime_map.svg`の直線ポリゴンパスをBézier曲線パスに置換
    - 3地域（中予・南予・東予）の各`<g>`要素のID・属性構造を維持
    - viewBoxを愛媛県の地理的アスペクト比に合わせて設定（横長）
    - 各Map_Areaに`role="button"`, `tabindex="0"`, `aria-label`, `data-region`, HTMX属性を保持
    - 各地域名テキストラベルを地理的境界の中心に配置
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

  - [x]* 1.2 SVGパス構造のプロパティテスト
    - **Property 1: SVGパスはBézier曲線コマンドを含む**
    - **Property 2: 全パス座標がviewBox内に収まる**
    - **Property 3: Map_Areaグループは必須属性を全て保持する**
    - **Validates: Requirements 1.3, 1.4, 1.5**

  - [x] 1.3 テンプレートのレイアウト構造変更
    - `app/templates/rpg_top.html`に2カラムGrid対応のHTML構造を追加
    - `.rpg-main-layout` > `.rpg-map-column` + `.rpg-course-column`の構造に変更
    - `#course-section`にid属性を付与（スクロールターゲット用）
    - _Requirements: 2.1, 2.2_

- [x] 2. CSSレスポンシブレイアウトとアニメーション実装
  - [x] 2.1 レスポンシブ横並びレイアウトCSS
    - `app/static/css/rpg_map.css`に`@media (min-width: 1024px)`のGrid定義を追加
    - マップカラム45%幅、sticky position (top: 80px)
    - コースパネルカラムに`max-height: calc(100vh - 160px)` + `overflow-y: auto`
    - 1024px未満では既存のシングルカラムレイアウトを維持
    - _Requirements: 2.1, 2.3, 2.4, 2.6_

  - [x] 2.2 クリックフィードバックアニメーションCSS
    - パルスアニメーション `@keyframes map-pulse`（scale 1→1.03→1, 200ms）
    - 非選択エリア半透明化 `.map-area--dimmed`（opacity: 0.5, transition 150ms）
    - ローディングインジケーター `.map-area--loading`（opacity pulsing 800ms infinite）
    - _Requirements: 5.1, 5.2, 5.4, 5.5_

- [x] 3. Checkpoint - レイアウトとCSS確認
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. JavaScriptインタラクション実装
  - [x] 4.1 map-interactions.js の基本構造とクリックフィードバック
    - `app/static/js/map-interactions.js`を新規作成
    - `initMapInteractions()` でDOMContentLoaded時にイベントリスナー登録
    - `handleMapAreaClick(region)` でパルスアニメーション付与・非選択エリア半透明化
    - `applySelectionFeedback(selectedRegion, allAreas)` で選択状態管理
    - `startLoadingIndicator(areaEl)` / `stopLoadingIndicator(areaEl)` でHTMXリクエスト中のUI
    - HTMXイベント(`htmx:afterSwap`)でローディングインジケーター停止
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x]* 4.2 選択状態opacity管理のプロパティテスト
    - **Property 7: 地域選択時のopacity状態一貫性**
    - **Validates: Requirements 5.2, 5.3**

  - [x] 4.3 スムーススクロール実装
    - `handleSmoothScroll(targetEl)` でnarrow画面時にコースパネルへスクロール
    - `shouldScrollToPanel(panelEl)` でパネルが既に可視か判定
    - `scroll-margin-top: 80px`をCSS側に設定
    - HTMXの`htmx:afterSwap`イベント後にスクロール発火（300ms以内）
    - ワイド画面(≥1024px)ではスクロールしない
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x]* 4.4 スクロール判定ロジックのプロパティテスト
    - **Property 4: パネルが既に可視ならスクロールしない**
    - **Validates: Requirements 3.3**

  - [x] 4.5 ツールチップ実装
    - `showTooltip(regionEl, data)` / `hideTooltip()` でツールチップ表示制御
    - 400msホバー遅延（setTimeout + clearTimeout）
    - `computeTooltipPosition(cursorX, cursorY, tooltipW, tooltipH, viewportW, viewportH)` でビューポート内に収まる位置計算
    - `formatTooltipText(regionName, completedCount, totalCount)` でテキスト生成
    - `@media (hover: none)` でタッチデバイス向けにツールチップ無効化
    - ツールチップDOM要素の動的生成と除去
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [x]* 4.6 ツールチップ位置計算のプロパティテスト
    - **Property 5: ツールチップはビューポート内に収まる**
    - **Validates: Requirements 4.3**

  - [x]* 4.7 ツールチップテキストフォーマットのプロパティテスト
    - **Property 6: ツールチップテキストフォーマットの正確性**
    - **Validates: Requirements 4.5, 4.6**

- [x] 5. Checkpoint - フロントエンドインタラクション確認
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. APIエンドポイントとバックエンド実装
  - [x] 6.1 地域サマリーAPIエンドポイント実装
    - `app/presentation/routers/top_router.py`に`GET /api/region-summary/{region}`を追加
    - リクエストパラメータバリデーション（CHUYO, NANYO, TOYOのみ許可）
    - 不正パラメータ時はデフォルト地域(CHUYO)にフォールバック
    - レスポンス形式: `{"region_name": "中予", "total_count": N, "completed_count": M}`
    - DBからコース数・完了数を取得するクエリ実装
    - _Requirements: 4.1, 4.5, 4.6_

  - [x]* 6.2 APIエンドポイントのユニットテスト
    - 正常系: 各地域のサマリー取得
    - 異常系: 不正な地域パラメータ時のフォールバック
    - エッジケース: コース0件の地域
    - _Requirements: 4.1, 4.5, 4.6_

- [x] 7. 結合とエラーハンドリング
  - [x] 7.1 ツールチップとAPIの結合
    - `map-interactions.js`からfetchでAPIを呼び出し、ツールチップデータを取得
    - API失敗時のサイレントフェイル処理（console.warnのみ）
    - HTMXタイムアウト5秒後のローディングインジケーター自動停止と「読み込みに失敗しました」メッセージ表示
    - テンプレートにmap-interactions.jsのscriptタグ追加
    - _Requirements: 4.1, 5.5_

  - [x] 7.2 テンプレートへのJS/CSS結合確認
    - `rpg_top.html`に`map-interactions.js`のscriptタグを追加
    - CSSアニメーションクラスとJS制御の連携確認
    - 既存のHTMXフローとの統合（hx-get, hx-target, hx-swap属性の維持）
    - _Requirements: 1.5, 2.5, 5.5_

- [x] 8. Final checkpoint - 全テスト実行と最終確認
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (Hypothesis, Python)
- フロントエンドのプロパティテスト（Property 4, 5, 6, 7）は純粋関数をPythonで再実装してHypothesisでテスト、またはNode.js側でfast-checkを使用
- SVG構造のプロパティテスト（Property 1, 2, 3）はPythonのxml.etreeでパース+Hypothesisでバリデーション
- 既存のHTMXフローを壊さないよう、属性の維持を各タスクで確認すること

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1", "2.2"] },
    { "id": 1, "tasks": ["1.2", "1.3", "4.1"] },
    { "id": 2, "tasks": ["4.2", "4.3", "4.5", "6.1"] },
    { "id": 3, "tasks": ["4.4", "4.6", "4.7", "6.2"] },
    { "id": 4, "tasks": ["7.1", "7.2"] }
  ]
}
```
