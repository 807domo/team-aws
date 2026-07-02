"""
SVGマップ構造のプロパティテスト

Feature: ehime-map-ux-improvement
Validates: Requirements 1.3, 1.4, 1.5

SVGファイル (app/static/svg/ehime_map.svg) をパースし、以下のプロパティを検証する:
- Property 1: SVGパスはBézier曲線コマンドを含む
- Property 2: 全パス座標がviewBox内に収まる
- Property 3: Map_Areaグループは必須属性を全て保持する
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

# SVGファイルパス
SVG_PATH = Path(__file__).parent.parent / "app" / "static" / "svg" / "ehime_map.svg"

# viewBox定義
VIEWBOX_WIDTH = 500
VIEWBOX_HEIGHT = 350
PADDING_TOLERANCE = 20  # 座標のパディング許容値

# 有効な地域値
VALID_REGIONS = {"CHUYO", "NANYO", "TOYO"}

# Bézier曲線コマンド（大文字=絶対座標、小文字=相対座標）
BEZIER_COMMANDS = {"C", "c", "Q", "q", "S", "s", "T", "t"}

# SVG namespace
SVG_NS = "http://www.w3.org/2000/svg"


@pytest.fixture(scope="module")
def svg_tree():
    """SVGファイルをパースしてElementTreeを返す"""
    assert SVG_PATH.exists(), f"SVGファイルが存在しません: {SVG_PATH}"
    tree = ET.parse(SVG_PATH)
    return tree


@pytest.fixture(scope="module")
def svg_root(svg_tree):
    """SVGルート要素を返す"""
    return svg_tree.getroot()


@pytest.fixture(scope="module")
def map_area_groups(svg_root):
    """class='map-area'の全<g>要素を返す"""
    groups = []
    for g in svg_root.iter(f"{{{SVG_NS}}}g"):
        if "map-area" in (g.get("class") or ""):
            groups.append(g)
    return groups


@pytest.fixture(scope="module")
def all_paths(svg_root):
    """SVG内の全<path>要素を返す"""
    return list(svg_root.iter(f"{{{SVG_NS}}}path"))


def extract_commands(d_attr: str) -> set:
    """SVGパスのd属性からコマンド文字を抽出する"""
    # SVGパスコマンドは単一のアルファベット文字
    return set(re.findall(r"[A-Za-z]", d_attr))


def extract_coordinates(d_attr: str) -> list:
    """SVGパスのd属性から全ての座標ペアを抽出する

    Returns:
        list of (x, y) tuples
    """
    coords = []
    # 数値パターン: 整数、小数、負の数に対応
    numbers = re.findall(r"-?\d+\.?\d*", d_attr)

    # 座標はペアで出現する（x, y）
    for i in range(0, len(numbers) - 1, 2):
        x = float(numbers[i])
        y = float(numbers[i + 1])
        coords.append((x, y))

    return coords


class TestProperty1BezierCurves:
    """Property 1: SVGパスはBézier曲線コマンドを含む

    **Validates: Requirements 1.3**

    For any SVG path `d` attribute string in the Interactive_Map, the path data
    SHALL contain at least one cubic or quadratic Bézier command (C, c, Q, q, S, s, T, t)
    and SHALL NOT consist exclusively of straight-line commands.
    """

    def test_all_paths_contain_bezier_commands(self, all_paths):
        """全てのパスが少なくとも1つのBézier曲線コマンドを含むこと"""
        assert len(all_paths) > 0, "SVG内にパスが見つかりません"

        for path in all_paths:
            d_attr = path.get("d")
            assert d_attr is not None, "パスにd属性がありません"

            commands = extract_commands(d_attr)
            bezier_found = commands & BEZIER_COMMANDS

            assert len(bezier_found) > 0, (
                f"パスにBézier曲線コマンドが含まれていません。"
                f"検出コマンド: {commands}"
            )

    def test_paths_not_exclusively_straight_lines(self, all_paths):
        """パスが直線コマンドのみで構成されていないこと"""
        straight_line_commands = {"L", "l", "H", "h", "V", "v"}

        for path in all_paths:
            d_attr = path.get("d")
            commands = extract_commands(d_attr)
            # M/m（MoveTo）とZ/z（ClosePath）を除いた描画コマンド
            drawing_commands = commands - {"M", "m", "Z", "z"}

            assert not drawing_commands.issubset(straight_line_commands), (
                f"パスが直線コマンドのみで構成されています。"
                f"描画コマンド: {drawing_commands}"
            )


class TestProperty2CoordinatesWithinViewBox:
    """Property 2: 全パス座標がviewBox内に収まる

    **Validates: Requirements 1.4**

    For any coordinate point extracted from any SVG path in the Interactive_Map,
    the point's x-coordinate SHALL be within [padding, viewBox_width - padding]
    and y-coordinate SHALL be within [padding, viewBox_height - padding].
    """

    def test_viewbox_is_correct(self, svg_root):
        """viewBoxが期待値(0 0 500 350)であること"""
        viewbox = svg_root.get("viewBox")
        assert viewbox is not None, "SVGにviewBox属性がありません"
        parts = viewbox.split()
        assert len(parts) == 4, f"viewBoxの値が不正です: {viewbox}"
        assert parts[0] == "0" and parts[1] == "0"
        assert int(parts[2]) == VIEWBOX_WIDTH
        assert int(parts[3]) == VIEWBOX_HEIGHT

    def test_all_coordinates_within_viewbox(self, all_paths):
        """全パス座標がviewBox内に収まること（パディング許容あり）"""
        assert len(all_paths) > 0, "SVG内にパスが見つかりません"

        min_x = -PADDING_TOLERANCE
        max_x = VIEWBOX_WIDTH + PADDING_TOLERANCE
        min_y = -PADDING_TOLERANCE
        max_y = VIEWBOX_HEIGHT + PADDING_TOLERANCE

        for path in all_paths:
            d_attr = path.get("d")
            coords = extract_coordinates(d_attr)
            assert len(coords) > 0, f"パスから座標を抽出できませんでした: {d_attr[:50]}..."

            for x, y in coords:
                assert min_x <= x <= max_x, (
                    f"x座標がviewBox外です: x={x} "
                    f"(許容範囲: {min_x}〜{max_x})"
                )
                assert min_y <= y <= max_y, (
                    f"y座標がviewBox外です: y={y} "
                    f"(許容範囲: {min_y}〜{max_y})"
                )


class TestProperty3MapAreaAttributes:
    """Property 3: Map_Areaグループは必須属性を全て保持する

    **Validates: Requirements 1.5**

    For any Map_Area group element in the Interactive_Map, the element SHALL have
    all of the following attributes defined: id matching pattern map-region-(CHUYO|NANYO|TOYO),
    role="button", tabindex="0", aria-label (non-empty), data-region matching one of
    (CHUYO, NANYO, TOYO), hx-get, hx-target, and hx-swap.
    """

    def test_exactly_three_map_areas_exist(self, map_area_groups):
        """map-areaグループが正確に3つ存在すること"""
        assert len(map_area_groups) == 3, (
            f"map-areaグループは3つ必要ですが、{len(map_area_groups)}つ見つかりました"
        )

    def test_id_matches_pattern(self, map_area_groups):
        """各グループのidがmap-region-(CHUYO|NANYO|TOYO)パターンに一致すること"""
        id_pattern = re.compile(r"^map-region-(CHUYO|NANYO|TOYO)$")
        found_regions = set()

        for g in map_area_groups:
            group_id = g.get("id")
            assert group_id is not None, "map-areaグループにid属性がありません"
            assert id_pattern.match(group_id), (
                f"idがパターンに一致しません: {group_id}"
            )
            found_regions.add(group_id.replace("map-region-", ""))

        assert found_regions == VALID_REGIONS, (
            f"全地域が揃っていません。検出: {found_regions}, 期待: {VALID_REGIONS}"
        )

    def test_role_attribute(self, map_area_groups):
        """各グループにrole='button'が設定されていること"""
        for g in map_area_groups:
            assert g.get("role") == "button", (
                f"id={g.get('id')}: role属性が'button'ではありません: {g.get('role')}"
            )

    def test_tabindex_attribute(self, map_area_groups):
        """各グループにtabindex='0'が設定されていること"""
        for g in map_area_groups:
            assert g.get("tabindex") == "0", (
                f"id={g.get('id')}: tabindex属性が'0'ではありません: {g.get('tabindex')}"
            )

    def test_aria_label_attribute(self, map_area_groups):
        """各グループに非空のaria-labelが設定されていること"""
        for g in map_area_groups:
            aria_label = g.get("aria-label")
            assert aria_label is not None and aria_label.strip() != "", (
                f"id={g.get('id')}: aria-label属性が空または未設定です"
            )

    def test_data_region_attribute(self, map_area_groups):
        """各グループのdata-regionが有効な地域値であること"""
        for g in map_area_groups:
            data_region = g.get("data-region")
            assert data_region in VALID_REGIONS, (
                f"id={g.get('id')}: data-region属性が不正です: {data_region}. "
                f"有効値: {VALID_REGIONS}"
            )

    def test_htmx_attributes(self, map_area_groups):
        """各グループにHTMX属性(hx-get, hx-target, hx-swap)が設定されていること"""
        htmx_attrs = ["hx-get", "hx-target", "hx-swap"]

        for g in map_area_groups:
            for attr in htmx_attrs:
                value = g.get(attr)
                assert value is not None and value.strip() != "", (
                    f"id={g.get('id')}: {attr}属性が空または未設定です"
                )

    def test_hx_get_matches_region(self, map_area_groups):
        """各グループのhx-getが対応する地域のURLを指していること"""
        for g in map_area_groups:
            data_region = g.get("data-region")
            hx_get = g.get("hx-get")
            assert data_region in hx_get, (
                f"id={g.get('id')}: hx-get '{hx_get}' に "
                f"data-region '{data_region}' が含まれていません"
            )
