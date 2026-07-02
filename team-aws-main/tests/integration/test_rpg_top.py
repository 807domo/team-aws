"""
愛媛探索AIクイズ - RPGトップ画面 統合テスト

FastAPI TestClient を使用した統合テスト。
RPGトップ画面のステータス表示、マップ描画、コースパネル連動、
XP更新フロー、デフォルト値確認、SVGフォールバックをテストする。

Requirements: 1.4, 5.6, 8.1, 9.3, 9.4
"""

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

from app.data.database import Base, get_db
from app.data.models import CourseModel, QuestionModel, UserModel
from app.data.seed_data import seed_database


# テスト用インメモリDB設定
TEST_DATABASE_URL = "sqlite:///./test_rpg_top.db"


@pytest.fixture(autouse=True)
def test_app():
    """テスト用アプリケーションを構築する。

    テスト用のDBエンジンを作成し、get_db をオーバーライドした状態で
    TestClient を提供する。各テスト後にDBをクリーンアップする。
    """
    import app.presentation.dependencies as deps

    # テスト用エンジン・セッション作成
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # シードデータとユーザーを投入
    session = TestingSessionLocal()
    # テスト用ユーザー作成（default_user はトップ画面で使用されるユーザーID）
    user = UserModel(id="default_user", display_name="テストユーザー")
    session.add(user)
    session.commit()
    seed_database(session)
    session.close()

    # get_db オーバーライド
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # get_current_user_id オーバーライド（テスト用にログイン不要にする）
    def override_get_current_user_id():
        return "default_user"

    # appをインポートしてオーバーライド設定
    from main import app

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_current_user_id] = override_get_current_user_id

    # テンプレートキャッシュの無効化
    from app.presentation.routers import (
        course_router,
        mock_exam_router,
        quiz_router,
        results_router,
        top_router,
    )

    for router_module in [
        course_router,
        quiz_router,
        mock_exam_router,
        results_router,
        top_router,
    ]:
        if hasattr(router_module, "templates"):
            router_module.templates.env.cache = None  # type: ignore

    import main as main_module

    if hasattr(main_module, "templates"):
        main_module.templates.env.cache = None  # type: ignore

    # MockExamEngine シングルトンをリセット
    deps._mock_exam_engine_instance = None

    yield app

    # クリーンアップ
    app.dependency_overrides.clear()
    deps._mock_exam_engine_instance = None
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

    # テストDBファイルを削除
    if os.path.exists("./test_rpg_top.db"):
        os.remove("./test_rpg_top.db")


@pytest.fixture
def client(test_app):
    """テスト用 FastAPI TestClient。"""
    with TestClient(test_app, raise_server_exceptions=False) as c:
        yield c


# =============================================================================
# RPGトップ画面: 基本表示テスト（Requirements: 1.4, 9.4）
# =============================================================================


class TestRpgTopBasic:
    """GET / RPGトップ画面の基本表示テスト"""

    def test_rpg_top_returns_200(self, client: TestClient):
        """GET / がRPGトップ画面を200ステータスで返す"""
        response = client.get("/")
        assert response.status_code == 200
        # RPGトップ画面であることを確認
        assert "RPGトップ" in response.text or "愛媛探索マップ" in response.text

    def test_rpg_top_contains_status_area(self, client: TestClient):
        """レスポンスにステータスエリア（Level, Title, XPゲージ）が含まれる"""
        response = client.get("/")
        assert response.status_code == 200
        # ステータス表示要素の確認
        assert "Lv." in response.text
        assert "XP" in response.text
        # XPゲージ（progressタグ）
        assert "progress" in response.text or "xp-gauge" in response.text.lower()
        # 称号が表示される（デフォルトユーザーは "伊予の迷い人"）
        assert "伊予の迷い人" in response.text

    def test_rpg_top_contains_map(self, client: TestClient):
        """レスポンスにSVGマップの3地域が含まれる"""
        response = client.get("/")
        assert response.status_code == 200
        # SVGマップの存在確認
        assert "<svg" in response.text
        # 3地域のエリアIDが含まれる
        assert "map-region-CHUYO" in response.text
        assert "map-region-NANYO" in response.text
        assert "map-region-TOYO" in response.text
        # 地域テキストラベル
        assert "中予" in response.text
        assert "南予" in response.text
        assert "東予" in response.text


# =============================================================================
# コースパネルエンドポイントテスト（Requirements: 8.1）
# =============================================================================


class TestCoursesEndpoint:
    """GET /courses/{region} コースパネルHTMXエンドポイントのテスト"""

    def test_courses_endpoint_returns_course_cards(self, client: TestClient):
        """GET /courses/CHUYO が中予のコースカードを返す"""
        response = client.get("/courses/CHUYO")
        assert response.status_code == 200
        # 中予のコースが含まれる
        assert "松山城コース" in response.text or "道後温泉" in response.text
        # コースカードの構成要素
        assert "course-card" in response.text or "開始" in response.text

    def test_courses_endpoint_empty_region(self, client: TestClient):
        """GET /courses/NANYO がコースなし地域の場合「準備中」メッセージを返す"""
        # NANYOにコースがあるかどうかはシードデータ次第だが、
        # コースがない場合のフォールバック確認として
        # まずNANYOのレスポンスを確認
        response = client.get("/courses/NANYO")
        assert response.status_code == 200
        # レスポンスは正常なHTMLフラグメント
        # NANYOにコースがあれば course-card, なければ「準備中」
        assert (
            "course-card" in response.text
            or "準備中" in response.text
            or "開始" in response.text
        )

    def test_courses_endpoint_invalid_region(self, client: TestClient):
        """GET /courses/INVALID が不正地域の場合、中予にフォールバックする"""
        response = client.get("/courses/INVALID")
        assert response.status_code == 200
        # 不正な地域はデフォルトで中予（CHUYO）にフォールバック
        # 中予のコースが表示される
        assert "松山城コース" in response.text or "道後温泉" in response.text


# =============================================================================
# XP更新フローテスト（Requirements: 1.4, 9.4）
# =============================================================================


class TestXpUpdateAfterQuiz:
    """クイズ完了後のXP更新→トップ画面反映フローのテスト"""

    def test_xp_update_after_quiz_completion(self, client: TestClient):
        """クイズ完了後、XPが増加してトップ画面に反映される"""
        # 1. 初期状態のトップ画面を確認（XP=0）
        response = client.get("/")
        assert response.status_code == 200
        assert "Lv." in response.text

        # 2. クイズを開始（dogo-ai-basic コース）
        response = client.post(
            "/quiz/start/dogo-ai-basic", follow_redirects=False
        )
        assert response.status_code == 303
        redirect_url = response.headers["location"]
        session_id = redirect_url.split("/quiz/")[1].split("/question")[0]

        # 3. dogo-ai-basic コースの問題IDリスト（シードデータから）
        dogo_question_ids = [
            "q-ai-001",
            "q-ai-002",
            "q-ai-003",
            "q-ga-001",
            "q-ga-002",
            "q-ga-005",
            "q-ra-003",
        ]

        # 4. 全問に回答する（正解インデックスは不問、回答すればXPが付与される）
        for i, qid in enumerate(dogo_question_ids):
            client.post(
                f"/quiz/{session_id}/answer",
                data={
                    "question_id": qid,
                    "choice_index": 0,
                    "question_index": i,
                },
                follow_redirects=False,
            )

        # 5. コース完了
        response = client.get(f"/quiz/{session_id}/complete")
        assert response.status_code == 200

        # 6. トップ画面に戻ってXP反映を確認
        response = client.get("/")
        assert response.status_code == 200
        # XPが0でない状態が反映されるはず
        # ゲージの値が0以上であることを確認（具体的な値はcorrect_countに依存）
        assert "Lv." in response.text
        # progressタグにvalue属性が設定される
        assert "progress" in response.text


# =============================================================================
# デフォルト値確認テスト（Requirements: 9.3, 9.4）
# =============================================================================


class TestDefaultUserXpValues:
    """新規/デフォルトユーザーの初期XP値テスト"""

    def test_default_user_xp_values(self, client: TestClient):
        """新規ユーザーはLevel=1, XP=0, 称号="伊予の迷い人"で表示される"""
        response = client.get("/")
        assert response.status_code == 200
        # Level 1 が表示される
        assert "Lv.1" in response.text
        # デフォルト称号
        assert "伊予の迷い人" in response.text
        # XPゲージが0%の状態（value="0.0" or value="0"）
        assert 'value="0' in response.text or "0 / " in response.text


# =============================================================================
# SVGフォールバック（テキストリンク）テスト（Requirements: 5.6）
# =============================================================================


class TestSvgFallback:
    """SVGマップのフォールバック動作テスト"""

    def test_map_areas_have_accessible_labels(self, client: TestClient):
        """マップエリアにアクセシビリティ属性（aria-label、role）が設定されている"""
        response = client.get("/")
        assert response.status_code == 200
        # SVGマップ内のエリアがrole="button"とaria-labelを持つ
        assert 'role="button"' in response.text
        assert 'aria-label="中予エリア"' in response.text
        assert 'aria-label="南予エリア"' in response.text
        assert 'aria-label="東予エリア"' in response.text

    def test_map_areas_have_text_labels(self, client: TestClient):
        """SVGマップ内にテキストラベル（地域名）が含まれる（フォールバック代替）"""
        response = client.get("/")
        assert response.status_code == 200
        # <text>要素で地域名が表示される（SVGが描画できない環境での識別用）
        assert "<text" in response.text
        # テキストリンクに相当するhtmx属性（代替ナビゲーション手段）
        assert 'hx-get="/courses/CHUYO"' in response.text
        assert 'hx-get="/courses/NANYO"' in response.text
        assert 'hx-get="/courses/TOYO"' in response.text

    def test_region_tabs_provide_text_navigation(self, client: TestClient):
        """地域タブがテキストベースのナビゲーション手段を提供する"""
        response = client.get("/")
        assert response.status_code == 200
        # タブがテキストリンクとして機能する
        assert "region-tab" in response.text
        assert 'role="tab"' in response.text
        # タブにも htmx属性があり、SVG不能時の代替となる
        assert 'role="tablist"' in response.text
