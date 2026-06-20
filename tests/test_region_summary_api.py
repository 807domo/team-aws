"""
愛媛探索AIクイズ - 地域サマリーAPIエンドポイント ユニットテスト

GET /api/region-summary/{region} のテスト。
正常系（各地域）、異常系（不正パラメータ）、エッジケース（コース0件）を検証する。

Requirements: 4.1, 4.5, 4.6
"""

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

from app.data.database import Base, get_db
from app.data.models import UserModel
from app.data.seed_data import seed_database


# テスト用インメモリDB設定
TEST_DATABASE_URL = "sqlite:///./test_region_summary_api.db"


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

    # appをインポートしてオーバーライド設定
    from main import app

    app.dependency_overrides[get_db] = override_get_db

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
    if os.path.exists("./test_region_summary_api.db"):
        os.remove("./test_region_summary_api.db")


@pytest.fixture
def client(test_app):
    """テスト用 FastAPI TestClient。"""
    with TestClient(test_app, raise_server_exceptions=False) as c:
        yield c


# =============================================================================
# 正常系: 各地域のサマリー取得（Requirements: 4.1, 4.5）
# =============================================================================


class TestRegionSummaryNormal:
    """GET /api/region-summary/{region} 正常系テスト"""

    def test_region_summary_chuyo(self, client: TestClient):
        """GET /api/region-summary/CHUYO が200を返し、JSONにregion_name, total_count, completed_countを含む"""
        response = client.get("/api/region-summary/CHUYO")
        assert response.status_code == 200
        data = response.json()
        assert "region_name" in data
        assert "total_count" in data
        assert "completed_count" in data
        assert data["region_name"] == "中予"

    def test_region_summary_nanyo(self, client: TestClient):
        """GET /api/region-summary/NANYO が200を返す"""
        response = client.get("/api/region-summary/NANYO")
        assert response.status_code == 200
        data = response.json()
        assert data["region_name"] == "南予"

    def test_region_summary_toyo(self, client: TestClient):
        """GET /api/region-summary/TOYO が200を返す"""
        response = client.get("/api/region-summary/TOYO")
        assert response.status_code == 200
        data = response.json()
        assert data["region_name"] == "東予"


# =============================================================================
# 異常系: 不正な地域パラメータ時のフォールバック（Requirements: 4.1）
# =============================================================================


class TestRegionSummaryInvalid:
    """GET /api/region-summary/{region} 異常系テスト"""

    def test_region_summary_invalid_falls_back(self, client: TestClient):
        """GET /api/region-summary/INVALID が200を返し、CHUYOデータにフォールバックする"""
        response = client.get("/api/region-summary/INVALID")
        assert response.status_code == 200
        data = response.json()
        # 不正パラメータの場合はCHUYO（中予）にフォールバック
        assert data["region_name"] == "中予"
        assert "total_count" in data
        assert "completed_count" in data


# =============================================================================
# レスポンス形式の検証（Requirements: 4.5, 4.6）
# =============================================================================


class TestRegionSummaryResponseFormat:
    """GET /api/region-summary/{region} レスポンス形式テスト"""

    def test_region_summary_response_format(self, client: TestClient):
        """レスポンスが正確に3つのキー (region_name, total_count, completed_count) を持つ"""
        response = client.get("/api/region-summary/CHUYO")
        assert response.status_code == 200
        data = response.json()
        expected_keys = {"region_name", "total_count", "completed_count"}
        assert set(data.keys()) == expected_keys

    def test_region_summary_counts_non_negative(self, client: TestClient):
        """total_count >= 0 かつ completed_count >= 0"""
        for region in ["CHUYO", "NANYO", "TOYO"]:
            response = client.get(f"/api/region-summary/{region}")
            assert response.status_code == 200
            data = response.json()
            assert data["total_count"] >= 0, f"{region}: total_count is negative"
            assert data["completed_count"] >= 0, f"{region}: completed_count is negative"

    def test_region_summary_completed_lte_total(self, client: TestClient):
        """completed_count <= total_count"""
        for region in ["CHUYO", "NANYO", "TOYO"]:
            response = client.get(f"/api/region-summary/{region}")
            assert response.status_code == 200
            data = response.json()
            assert data["completed_count"] <= data["total_count"], (
                f"{region}: completed_count ({data['completed_count']}) > "
                f"total_count ({data['total_count']})"
            )
