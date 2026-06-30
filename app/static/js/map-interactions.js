/**
 * map-interactions.js
 * マップエリアのクリックフィードバック・選択状態管理・ローディングインジケーター
 * スムーススクロール（ナロー画面）・ツールチップ表示
 *
 * Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.1, 5.2, 5.3, 5.4, 5.5
 *
 * 既存のインラインJS（selectMapRegion, syncTabs）の上に
 * アニメーションレイヤーを追加する。HTMXのfetch処理は重複させず、
 * CSSクラスの付与/除去のみを担当する。
 */
(function () {
  'use strict';

  // =========================================================================
  // Constants
  // =========================================================================
  var LOADING_TIMEOUT_MS = 5000;
  var WIDE_BREAKPOINT_PX = 1024;
  var SCROLL_DELAY_MS = 50;
  var TOOLTIP_HOVER_DELAY_MS = 400;
  var TOOLTIP_FADEOUT_MS = 150;
  var TOOLTIP_OFFSET = 12; // px offset from cursor

  // =========================================================================
  // State
  // =========================================================================
  var loadingTimers = {};
  var tooltipHoverTimer = null;
  var tooltipEl = null;

  // =========================================================================
  // Initialization
  // =========================================================================

  /**
   * DOMContentLoaded時にマップインタラクションのイベントリスナーを登録する。
   */
  function initMapInteractions() {
    var allAreas = document.querySelectorAll('.map-area');

    // 各マップエリアにクリックイベントを登録
    allAreas.forEach(function (area) {
      area.addEventListener('click', function () {
        var region = this.dataset.region;
        handleMapAreaClick(region, allAreas);
      });
    });

    // パルスアニメーション終了時にクラスを除去
    allAreas.forEach(function (area) {
      area.addEventListener('animationend', function (e) {
        if (e.animationName === 'map-pulse') {
          this.classList.remove('map-area--pulsing');
        }
      });
    });

    // HTMXレスポンス受信時にローディングインジケーターを停止し、スムーススクロール
    document.body.addEventListener('htmx:afterSwap', function (e) {
      if (e.detail.target && e.detail.target.id === 'course-panel') {
        stopAllLoadingIndicators(allAreas);

        // DOMが更新された後にスクロール（narrow画面のみ）
        setTimeout(function () {
          var courseSection = document.getElementById('course-section');
          handleSmoothScroll(courseSection);
        }, SCROLL_DELAY_MS);
      }
    });

    // ツールチップ: タッチデバイスでなければホバーイベントを登録
    if (!isTouchDevice()) {
      allAreas.forEach(function (area) {
        area.addEventListener('mouseenter', function (e) {
          var regionEl = this;
          var region = regionEl.dataset.region;

          // 400ms遅延後にツールチップ表示
          tooltipHoverTimer = setTimeout(function () {
            fetchAndShowTooltip(regionEl, region, e);
          }, TOOLTIP_HOVER_DELAY_MS);
        });

        area.addEventListener('mousemove', function (e) {
          // ツールチップが既に表示されている場合、位置を追従
          if (tooltipEl) {
            updateTooltipPosition(e.clientX, e.clientY);
          }
        });

        area.addEventListener('mouseleave', function () {
          // タイマーをクリアし、ツールチップを非表示にする
          if (tooltipHoverTimer) {
            clearTimeout(tooltipHoverTimer);
            tooltipHoverTimer = null;
          }
          hideTooltip();
        });
      });
    }
  }

  // =========================================================================
  // Click Handling
  // =========================================================================

  /**
   * マップエリアクリック時の処理。
   * パルスアニメーション付与・非選択エリア半透明化・ローディング開始。
   *
   * @param {string} region - クリックされた地域名 (CHUYO, NANYO, TOYO)
   * @param {NodeList} allAreas - 全マップエリア要素
   */
  function handleMapAreaClick(region, allAreas) {
    // 選択フィードバック（dimming + pulse）を適用
    applySelectionFeedback(region, allAreas);

    // ローディングインジケーター開始
    var clickedArea = document.querySelector(
      '.map-area[data-region="' + region + '"]'
    );
    if (clickedArea) {
      startLoadingIndicator(clickedArea);
    }
  }

  // =========================================================================
  // Selection Feedback
  // =========================================================================

  /**
   * 選択状態を管理する。
   * 選択されたエリアにパルスアニメーションを付与し、
   * その他のエリアを半透明化する。
   *
   * @param {string} selectedRegion - 選択された地域名
   * @param {NodeList} allAreas - 全マップエリア要素
   */
  function applySelectionFeedback(selectedRegion, allAreas) {
    allAreas.forEach(function (area) {
      var isSelected = area.dataset.region === selectedRegion;

      if (isSelected) {
        // 選択エリア: パルスアニメーション付与、dimmed除去
        area.classList.remove('map-area--dimmed');
        area.classList.add('map-area--pulsing');
      } else {
        // 非選択エリア: 半透明化、パルス除去
        area.classList.add('map-area--dimmed');
        area.classList.remove('map-area--pulsing');
      }
    });
  }

  // =========================================================================
  // Loading Indicator
  // =========================================================================

  /**
   * HTMXリクエスト中のローディングインジケーターを開始する。
   * タイムアウト（5秒）後に自動停止する。
   *
   * @param {Element} areaEl - ローディング対象のマップエリア要素
   */
  function startLoadingIndicator(areaEl) {
    var region = areaEl.dataset.region;

    // 既存のタイマーをクリア
    if (loadingTimers[region]) {
      clearTimeout(loadingTimers[region]);
    }

    areaEl.classList.add('map-area--loading');

    // タイムアウト後に自動停止し、エラーメッセージを表示
    loadingTimers[region] = setTimeout(function () {
      stopLoadingIndicator(areaEl);
      showLoadingErrorMessage();
    }, LOADING_TIMEOUT_MS);
  }

  /**
   * ローディングインジケーターを停止する。
   *
   * @param {Element} areaEl - ローディング停止対象のマップエリア要素
   */
  function stopLoadingIndicator(areaEl) {
    var region = areaEl.dataset.region;

    areaEl.classList.remove('map-area--loading');

    if (loadingTimers[region]) {
      clearTimeout(loadingTimers[region]);
      loadingTimers[region] = null;
    }
  }

  /**
   * 全エリアのローディングインジケーターを停止する。
   *
   * @param {NodeList} allAreas - 全マップエリア要素
   */
  function stopAllLoadingIndicators(allAreas) {
    allAreas.forEach(function (area) {
      stopLoadingIndicator(area);
    });
  }

  /**
   * ローディングタイムアウト時に「読み込みに失敗しました」メッセージを
   * コースパネルに表示する。
   */
  function showLoadingErrorMessage() {
    var coursePanel = document.getElementById('course-panel');
    if (coursePanel) {
      coursePanel.innerHTML =
        '<div class="loading-error text-center py-8 text-gray-500">' +
          '<p class="text-3xl mb-2">⚠️</p>' +
          '<p class="font-medium">読み込みに失敗しました</p>' +
          '<p class="text-sm">もう一度エリアを選択してください。</p>' +
        '</div>';
    }
  }

  // =========================================================================
  // Smooth Scroll (narrow viewport only)
  // =========================================================================

  /**
   * パネルが既にビューポート内に完全に可視かどうかを判定する。
   * パネルの上端がビューポート上端以上、かつ下端がビューポート下端以下の場合にtrue。
   *
   * @param {Element} panelEl - 判定対象のパネル要素
   * @returns {boolean} パネルが完全に可視ならtrue
   */
  function shouldScrollToPanel(panelEl) {
    if (!panelEl) {
      return true;
    }
    var rect = panelEl.getBoundingClientRect();
    var viewportHeight = window.innerHeight || document.documentElement.clientHeight;

    // パネルが完全にビューポート内に収まっている場合はスクロール不要
    if (rect.top >= 0 && rect.bottom <= viewportHeight) {
      return false;
    }
    return true;
  }

  /**
   * ナロー画面（<1024px）でコースパネルへスムーススクロールする。
   * ワイド画面ではスクロールしない（横並びレイアウトでは不要）。
   * パネルが既に可視の場合もスクロールしない。
   *
   * scroll-margin-top: 80px がCSS側で設定されているため、
   * scrollIntoView({ block: 'start' }) で自動的に80px下に配置される。
   *
   * @param {Element} targetEl - スクロール先の要素
   */
  function handleSmoothScroll(targetEl) {
    // ワイド画面ではスクロールしない
    if (window.innerWidth >= WIDE_BREAKPOINT_PX) {
      return;
    }

    if (!targetEl) {
      return;
    }

    // パネルが既に可視ならスクロールしない
    if (!shouldScrollToPanel(targetEl)) {
      return;
    }

    targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  // =========================================================================
  // Tooltip (Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6)
  // =========================================================================

  /**
   * タッチデバイスかどうかを判定する。
   * hover: none のメディアクエリにマッチする場合はタッチデバイスとみなす。
   *
   * @returns {boolean} タッチデバイスならtrue
   */
  function isTouchDevice() {
    return window.matchMedia('(hover: none)').matches;
  }

  /**
   * ツールチップのテキストをフォーマットする。
   *
   * @param {string} regionName - 地域名（例: "中予"）
   * @param {number} completedCount - 完了コース数
   * @param {number} totalCount - 全コース数
   * @returns {string} フォーマット済みテキスト
   */
  function formatTooltipText(regionName, completedCount, totalCount) {
    if (totalCount > 0) {
      return regionName + ' - ' + completedCount + '/' + totalCount + ' コース完了';
    }
    return regionName + ' - コース準備中';
  }

  /**
   * ツールチップがビューポート内に収まる位置を計算する。
   * デフォルトはカーソルの右下に配置。
   * 右にはみ出す場合は左に、下にはみ出す場合は上に配置する。
   *
   * @param {number} cursorX - カーソルのX座標（viewport相対）
   * @param {number} cursorY - カーソルのY座標（viewport相対）
   * @param {number} tooltipW - ツールチップの幅
   * @param {number} tooltipH - ツールチップの高さ
   * @param {number} viewportW - ビューポートの幅
   * @param {number} viewportH - ビューポートの高さ
   * @returns {{x: number, y: number}} ツールチップの配置位置
   */
  function computeTooltipPosition(cursorX, cursorY, tooltipW, tooltipH, viewportW, viewportH) {
    var x = cursorX + TOOLTIP_OFFSET;
    var y = cursorY + TOOLTIP_OFFSET;

    // 右にはみ出す場合は左に配置
    if (x + tooltipW > viewportW) {
      x = cursorX - tooltipW - TOOLTIP_OFFSET;
    }

    // 下にはみ出す場合は上に配置
    if (y + tooltipH > viewportH) {
      y = cursorY - tooltipH - TOOLTIP_OFFSET;
    }

    // 左端・上端からはみ出さないようにクランプ
    if (x < 0) {
      x = 0;
    }
    if (y < 0) {
      y = 0;
    }

    return { x: x, y: y };
  }

  /**
   * APIから地域サマリーを取得してツールチップを表示する。
   *
   * @param {Element} regionEl - マップエリア要素
   * @param {string} region - 地域コード (CHUYO, NANYO, TOYO)
   * @param {MouseEvent} e - マウスイベント
   */
  function fetchAndShowTooltip(regionEl, region, e) {
    // まず「Loading...」ツールチップを表示
    showTooltip(regionEl, { text: 'Loading...' }, e.clientX, e.clientY);

    // APIからデータを取得
    fetch('/api/region-summary/' + region)
      .then(function (response) {
        if (!response.ok) {
          throw new Error('API error: ' + response.status);
        }
        return response.json();
      })
      .then(function (data) {
        // ツールチップがまだ表示中の場合のみ更新
        if (tooltipEl) {
          var text = formatTooltipText(
            data.region_name,
            data.completed_count,
            data.total_count
          );
          tooltipEl.textContent = text;
        }
      })
      .catch(function (err) {
        // API失敗時はサイレントフェイル（ツールチップを非表示にする）
        console.warn('[map-interactions] tooltip API failed:', err.message);
        hideTooltip();
      });
  }

  /**
   * ツールチップDOM要素を生成して表示する。
   *
   * @param {Element} regionEl - マップエリア要素
   * @param {Object} data - 表示データ（{ text: string }）
   * @param {number} cursorX - カーソルX座標
   * @param {number} cursorY - カーソルY座標
   */
  function showTooltip(regionEl, data, cursorX, cursorY) {
    // 既存のツールチップがあれば除去
    if (tooltipEl) {
      tooltipEl.remove();
      tooltipEl = null;
    }

    // ツールチップ要素を生成
    tooltipEl = document.createElement('div');
    tooltipEl.className = 'map-tooltip';
    tooltipEl.setAttribute('role', 'tooltip');
    tooltipEl.setAttribute('aria-live', 'polite');
    tooltipEl.textContent = data.text || '';
    document.body.appendChild(tooltipEl);

    // 位置を計算して設定
    updateTooltipPosition(cursorX, cursorY);

    // フェードイン
    tooltipEl.style.opacity = '1';
  }

  /**
   * ツールチップの位置を更新する。
   *
   * @param {number} cursorX - カーソルX座標
   * @param {number} cursorY - カーソルY座標
   */
  function updateTooltipPosition(cursorX, cursorY) {
    if (!tooltipEl) return;

    var tooltipW = tooltipEl.offsetWidth;
    var tooltipH = tooltipEl.offsetHeight;
    var viewportW = window.innerWidth || document.documentElement.clientWidth;
    var viewportH = window.innerHeight || document.documentElement.clientHeight;

    var pos = computeTooltipPosition(cursorX, cursorY, tooltipW, tooltipH, viewportW, viewportH);
    tooltipEl.style.left = pos.x + 'px';
    tooltipEl.style.top = pos.y + 'px';
  }

  /**
   * ツールチップを非表示にして除去する。
   * 150msのフェードアウト後にDOMから除去する。
   */
  function hideTooltip() {
    if (!tooltipEl) return;

    var el = tooltipEl;
    el.style.opacity = '0';

    setTimeout(function () {
      if (el && el.parentNode) {
        el.parentNode.removeChild(el);
      }
      if (tooltipEl === el) {
        tooltipEl = null;
      }
    }, TOOLTIP_FADEOUT_MS);
  }

  // =========================================================================
  // Bootstrap
  // =========================================================================

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMapInteractions);
  } else {
    // DOMContentLoaded already fired
    initMapInteractions();
  }
})();
