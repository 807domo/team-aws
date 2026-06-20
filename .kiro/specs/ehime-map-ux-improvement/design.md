# Design Document: ehime-map-ux-improvement

## Overview

本設計では、RPGトップ画面（`rpg_top.html`）のSVGマップUXを5つの軸で改善する。

1. **地理的に正確なSVGマップ** — 直線ポリゴンを愛媛県の実形状に近いBézier曲線パスに置換
2. **レスポンシブ横並びレイアウト** — ≥1024pxでマップ左/コースパネル右の2カラム表示
3. **ナロー画面スムーススクロール** — <1024pxでマップクリック後にコースパネルへ自動スクロール
4. **地域ツールチップ** — ホバー時にコース数/進捗サマリーをポップアップ表示
5. **クリックフィードバック強化** — パルスアニメーション、非選択エリア半透明化、ローディングインジケーター

既存のFastAPI + Jinja2 + HTMX + vanilla JS + CSSスタックを維持し、新たなフレームワークやビルドツールを導入しない。

## Architecture

```mermaid
graph TD
    subgraph Browser
        SVG[SVG Map<br/>Bézier paths]
        JS[map-interactions.js<br/>tooltip, scroll, feedback]
        CSS[rpg_map.css<br/>layout, animations]
        HTMX[HTMX<br/>course panel swap]
    end

    subgraph Server["FastAPI Server"]
        Router[top_router.py]
        Template[rpg_top.html<br/>Jinja2]
        Partial[partials/course_panel.html]
        TooltipAPI[GET /api/region-summary/{region}]
    end

    SVG -->|click| JS
    JS -->|trigger| HTMX
    HTMX -->|GET /courses/{region}| Router
    Router -->|render| Partial
    JS -->|hover 400ms| TooltipAPI
    TooltipAPI -->|JSON| JS
    Router -->|render| Template
    Template -->|includes| SVG
    Template -->|links| CSS
    Template -->|links| JS
```

### 設計判断

| 判断 | 選択肢 | 理由 |
|------|--------|------|
| SVGパスデータの取得元 | 国土数値情報の行政区域データ(GeoJSON) → SVGパスへ変換 | 公開データで地理的精度を担保 |
| ツールチップデータ取得 | 軽量JSONエンドポイント `/api/region-summary/{region}` | 初回ページロード時のペイロードを増やさず、ホバー時にオンデマンド取得 |
| レイアウト方式 | CSS Grid + `@media (min-width: 1024px)` | Flexboxより2カラム制御が明快。Tailwind CDNとの併用も容易 |
| スクロール制御 | `element.scrollIntoView({ behavior: 'smooth', block: 'start' })` + scroll-margin-top | CSS scroll-behaviorだけでは offset 80px の制御が難しいため JS併用 |
| アニメーション | CSS @keyframes + JSでクラス付与/除去 | パフォーマンスに優れ、JSバンドル不要 |

## Components and Interfaces

### 1. SVGマップファイル (`app/static/svg/ehime_map.svg`)

現在の直線ポリゴンパスを、GeoJSONから変換したBézier曲線パスに置換する。

```xml
<!-- 変更前: 直線ポリゴン -->
<path d="M 30 120 L 80 80 L 130 70 ..." />

<!-- 変更後: Bézier曲線 -->
<path d="M 30,120 C 45,100 65,85 80,80 C 95,75 115,68 130,70 ..." />
```

各`<g>`要素のID・属性構造は維持:
```xml
<g id="map-region-NANYO" class="map-area" tabindex="0"
   role="button" aria-label="南予エリア" data-region="NANYO">
  <path d="..." />
  <text x="..." y="..." text-anchor="middle">南予</text>
</g>
```

### 2. テンプレート (`app/templates/rpg_top.html`)

レイアウトを2カラムGrid対応に変更:

```html
<!-- 新レイアウト構造 -->
<div class="rpg-main-layout">
  <!-- 左カラム: マップ (sticky) -->
  <section class="rpg-map-column">
    <div class="rpg-map-container" aria-label="愛媛県インタラクティブマップ">
      <svg ...>...</svg>
    </div>
  </section>

  <!-- 右カラム: コースパネル -->
  <section class="rpg-course-column" id="course-section">
    <div id="course-panel">...</div>
  </section>
</div>
```

### 3. CSS (`app/static/css/rpg_map.css`) — 追加スタイル

```css
/* Side-by-Side Layout */
@media (min-width: 1024px) {
  .rpg-main-layout {
    display: grid;
    grid-template-columns: 45% 1fr;
    gap: 2rem;
    align-items: start;
  }
  .rpg-map-column {
    position: sticky;
    top: 80px;
  }
  .rpg-course-column {
    max-height: calc(100vh - 160px);
    overflow-y: auto;
  }
}

/* Pulse animation */
@keyframes map-pulse {
  0%   { transform: scale(1); }
  50%  { transform: scale(1.03); }
  100% { transform: scale(1); }
}
.map-area--pulsing {
  animation: map-pulse 200ms ease-out;
  transform-origin: center;
}

/* Non-selected dimming */
.map-area--dimmed {
  opacity: 0.5;
  transition: opacity 150ms ease;
}

/* Loading indicator */
@keyframes map-loading-pulse {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0.6; }
}
.map-area--loading {
  animation: map-loading-pulse 800ms ease-in-out infinite;
}
```

### 4. JavaScript (`app/static/js/map-interactions.js`)

新規ファイルとして、マップのインタラクション処理をモジュール化:

```javascript
// 主要関数
function initMapInteractions() { ... }
function handleMapAreaClick(region) { ... }
function handleSmoothScroll(targetEl) { ... }
function shouldScrollToPanel(panelEl) { ... }
function showTooltip(regionEl, data) { ... }
function hideTooltip() { ... }
function computeTooltipPosition(cursorX, cursorY, tooltipW, tooltipH, viewportW, viewportH) { ... }
function formatTooltipText(regionName, completedCount, totalCount) { ... }
function applySelectionFeedback(selectedRegion, allAreas) { ... }
function startLoadingIndicator(areaEl) { ... }
function stopLoadingIndicator(areaEl) { ... }
```

### 5. APIエンドポイント (`app/presentation/routers/top_router.py`)

ツールチップ用JSONエンドポイントを追加:

```python
@router.get("/api/region-summary/{region}")
async def get_region_summary(region: str, db: Session = Depends(get_db)):
    """ツールチップ用: 地域のコース数と完了数を返す"""
    return {
        "region_name": region_enum.value,  # "中予" etc.
        "total_count": total,
        "completed_count": completed,
    }
```

## Data Models

### RegionSummary (APIレスポンス)

```python
@dataclass
class RegionSummary:
    """ツールチップ表示用の地域サマリー"""
    region_name: str        # "中予", "南予", "東予"
    total_count: int        # 地域内の全コース数
    completed_count: int    # ユーザーが完了したコース数
```

### TooltipPosition (フロントエンド)

```typescript
// JSDoc型定義
/**
 * @typedef {Object} TooltipPosition
 * @property {number} x - ツールチップ左端のpx座標
 * @property {number} y - ツールチップ上端のpx座標
 * @property {'above'|'below'|'left'|'right'} placement - 配置方向
 */
```

### SVGパスデータ構造

SVGパスは静的ファイルとして配置するため、ランタイムのデータモデルは不要。
GeoJSON → SVGパス変換はビルド時（またはワンショットスクリプト）で実行し、結果をテンプレートに直接埋め込む。

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: SVGパスはBézier曲線コマンドを含む

*For any* SVG path `d` attribute string in the Interactive_Map, the path data SHALL contain at least one cubic or quadratic Bézier command (C, c, Q, q, S, s, T, t) and SHALL NOT consist exclusively of straight-line commands (L, l, H, h, V, v).

**Validates: Requirements 1.3**

### Property 2: 全パス座標がviewBox内に収まる

*For any* coordinate point extracted from any SVG path in the Interactive_Map, the point's x-coordinate SHALL be within [padding, viewBox_width - padding] and y-coordinate SHALL be within [padding, viewBox_height - padding], where padding is the uniform padding value defined in the viewBox configuration.

**Validates: Requirements 1.4**

### Property 3: Map_Areaグループは必須属性を全て保持する

*For any* Map_Area group element in the Interactive_Map, the element SHALL have all of the following attributes defined: `id` matching pattern `map-region-(CHUYO|NANYO|TOYO)`, `role="button"`, `tabindex="0"`, `aria-label` (non-empty), `data-region` matching one of (CHUYO, NANYO, TOYO), `hx-get`, `hx-target`, and `hx-swap`.

**Validates: Requirements 1.5**

### Property 4: パネルが既に可視ならスクロールしない

*For any* viewport state where the Course_Panel's top edge is at or above `(viewport_height - panel_height)` and its bottom edge is at or below `viewport_height` (i.e., fully visible), the `shouldScrollToPanel()` function SHALL return `false`.

**Validates: Requirements 3.3**

### Property 5: ツールチップはビューポート内に収まる

*For any* cursor position (x, y) where 0 ≤ x ≤ viewport_width and 0 ≤ y ≤ viewport_height, and *for any* tooltip dimensions (w, h) where w > 0 and h > 0, the computed tooltip position (tx, ty) SHALL satisfy: 0 ≤ tx, tx + w ≤ viewport_width, 0 ≤ ty, and ty + h ≤ viewport_height.

**Validates: Requirements 4.3**

### Property 6: ツールチップテキストフォーマットの正確性

*For any* region name string (non-empty) and *for any* pair of non-negative integers (completed_count, total_count) where completed_count ≤ total_count:
- IF total_count > 0, THEN `formatTooltipText(region_name, completed_count, total_count)` SHALL return `"{region_name} - {completed_count}/{total_count} コース完了"`
- IF total_count == 0, THEN `formatTooltipText(region_name, completed_count, total_count)` SHALL return `"{region_name} - コース準備中"`

**Validates: Requirements 4.5, 4.6**

### Property 7: 地域選択時のopacity状態一貫性

*For any* sequence of Map_Area click events and *at any* point after a click, exactly one Map_Area (the most recently clicked) SHALL have opacity 1.0, and all other Map_Areas SHALL have opacity 0.5. When a new region is clicked, the previous selection's opacity SHALL be restored before the new selection is applied.

**Validates: Requirements 5.2, 5.3**

## Error Handling

| シナリオ | 対処 |
|----------|------|
| ツールチップAPI失敗 (ネットワークエラー/500) | ツールチップを表示せず、サイレントに失敗。コンソールにwarningログ |
| SVGパスの描画エラー | テキストリンクによるフォールバックUIを表示（既存の`rpg-map-fallback`クラスを活用） |
| HTMXリクエストタイムアウト | ローディングインジケーターを5秒後に自動停止し、「読み込みに失敗しました」メッセージを表示 |
| `scrollIntoView`非対応ブラウザ | `scroll-behavior: smooth`へのCSS フォールバック。JSが使えない場合はスクロール動作なし |
| hover非対応デバイス (タッチ) | `@media (hover: none)` でツールチップを無効化。代わりにマップ内テキストラベルに進捗情報を含める |
| Region APIパラメータ不正 | デフォルト地域(CHUYO)にフォールバック（既存実装と同様） |

## Testing Strategy

### テスト構成

本機能は以下のテスト層で検証する:

#### 1. プロパティベーステスト (Hypothesis)

Property-based testingが適切な領域:
- ツールチップ位置計算（純粋関数、入力空間が広い）
- ツールチップテキストフォーマット（純粋関数）
- スクロール判定ロジック（純粋関数）
- SVG構造バリデーション（構造解析）
- 選択状態のopacity管理（状態遷移ロジック）

**ライブラリ**: Hypothesis (Python, 既にdevDependencyに含まれている)
**設定**: 最低100イテレーション/プロパティ
**タグフォーマット**: `Feature: ehime-map-ux-improvement, Property {number}: {property_text}`

各Correctness Property (1〜7) に対して1つのproperty-based testを実装する。

#### 2. ユニットテスト (pytest)

- SVGパスパーサーのエッジケース（空パス、不正フォーマット）
- APIレスポンスの具体例（0コース、全完了、部分完了）
- CSS クラス付与/除去の具体的シナリオ

#### 3. 統合テスト

- HTMX swap後のDOM状態検証
- レスポンシブレイアウトのブレークポイント動作（Playwright推奨）
- ツールチップの表示/非表示タイミング
- ローディングインジケーターのHTMXイベント連動

#### 4. 手動テスト / ビジュアルレビュー

- SVGマップの地理的正確性（愛媛県在住者によるレビュー）
- アニメーションの視覚的品質
- タッチデバイスでの操作感
- 最小クリックターゲットサイズ (44×44px at 320px viewport)
