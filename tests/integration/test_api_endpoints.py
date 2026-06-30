"""
愛媛探索AIクイズ - API エンドポイント統合テスト

FastAPI TestClient を使用した統合テスト。
コース選択→クイズ開始→回答→解説→完了のフロー、模擬試験フロー、
結果ダッシュボードの正常系をテストする。

Requirements: 1.3, 2.1, 2.3, 2.4, 2.5, 3.4, 5.1
"""

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from starlette.testclient import TestClient

from app.data.database import Base, get_db
from app.data.models import CourseModel, QuestionModel, UserModel
from app.data.seed_data import seed_database


# テスト用インメモリDB設定
TEST_DATABASE_URL = "sqlite:///./test_integration.db"


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
    # テスト用ユーザー作成
    user = UserModel(id="default-user", display_name="テストユーザー")
    session.add(user)
    user2 = UserModel(id="user-001", display_name="模擬テストユーザー")
    session.add(user2)
    user3 = UserModel(id="default_user", display_name="結果ユーザー")
    session.add(user3)
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

    # テンプレートキャッシュの無効化（Jinja2 LRUCache のハッシュ問題を回避）
    from app.presentation.routers import course_router, quiz_router, mock_exam_router, results_router, top_router
    for router_module in [course_router, quiz_router, mock_exam_router, results_router, top_router]:
        if hasattr(router_module, 'templates'):
            router_module.templates.env.cache = None  # type: ignore

    # main.py のテンプレート環境も設定
    import main as main_module
    if hasattr(main_module, 'templates'):
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
    if os.path.exists("./test_integration.db"):
        os.remove("./test_integration.db")


@pytest.fixture
def client(test_app):
    """テスト用 FastAPI TestClient。"""
    with TestClient(test_app, raise_server_exceptions=False) as c:
        yield c


# =============================================================================
# コース選択画面テスト（Requirements: 1.3）
# =============================================================================


class TestCourseSelect:
    """GET / RPGトップ画面のテスト"""

    def test_returns_200_with_rpg_top(self, client: TestClient):
        """RPGトップ画面が200で返り、ステータスとマップを含む"""
        response = client.get("/")
        assert response.status_code == 200
        assert "コース一覧" in response.text

    def test_displays_all_three_regions(self, client: TestClient):
        """3地域（中予・南予・東予）がすべて表示される"""
        response = client.get("/")
        assert response.status_code == 200
        assert "中予" in response.text
        assert "南予" in response.text
        assert "東予" in response.text

    def test_displays_default_region_course_names(self, client: TestClient):
        """デフォルト選択地域（中予）のコース名が表示される"""
        response = client.get("/")
        assert response.status_code == 200
        assert "松山城コース（基礎）" in response.text


# =============================================================================
# クイズフローテスト（Requirements: 2.1, 2.3, 2.4, 3.4）
# =============================================================================


class TestQuizFlow:
    """クイズ出題・回答フローのテスト"""

    def test_start_quiz_redirects_to_question(self, client: TestClient):
        """POST /quiz/start/{course_id} が問題画面にリダイレクトする"""
        response = client.post(
            "/quiz/start/matsuyama-basic", follow_redirects=False
        )
        assert response.status_code == 303
        assert "/quiz/" in response.headers["location"]
        assert "question?index=0" in response.headers["location"]

    def test_show_question_page(self, client: TestClient):
        """GET /quiz/{session_id}/question?index=0 がクイズ問題を表示する"""
        # まずセッションを作成
        response = client.post(
            "/quiz/start/matsuyama-basic", follow_redirects=False
        )
        redirect_url = response.headers["location"]

        # 問題画面にアクセス
        response = client.get(redirect_url)
        assert response.status_code == 200
        # 問題テキストの一部が含まれることを確認（松山城コースの問題）
        assert "松山城" in response.text or "道後温泉" in response.text or "みかん" in response.text or "坊っちゃん" in response.text or "松山空港" in response.text or "松山市" in response.text or "愛媛マラソン" in response.text

    def test_submit_answer_redirects_to_explanation(self, client: TestClient):
        """POST /quiz/{session_id}/answer が解説画面にリダイレクトする"""
        # セッション作成
        response = client.post(
            "/quiz/start/matsuyama-basic", follow_redirects=False
        )
        redirect_url = response.headers["location"]
        # session_id を抽出
        session_id = redirect_url.split("/quiz/")[1].split("/question")[0]

        # 回答送信
        response = client.post(
            f"/quiz/{session_id}/answer",
            data={
                "question_id": "q-cc-001",
                "choice_index": 0,
                "question_index": 0,
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "/explanation/" in response.headers["location"]

    def test_explanation_page_shows_trivia_and_next_button(self, client: TestClient):
        """解説ページに愛媛トリビアと「次へ」ボタンが表示される"""
        # セッション作成
        response = client.post(
            "/quiz/start/matsuyama-basic", follow_redirects=False
        )
        redirect_url = response.headers["location"]
        session_id = redirect_url.split("/quiz/")[1].split("/question")[0]

        # 回答送信してリダイレクト先に進む
        response = client.post(
            f"/quiz/{session_id}/answer",
            data={
                "question_id": "q-cc-001",
                "choice_index": 0,
                "question_index": 0,
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        # 愛媛トリビアセクションが含まれる
        assert "愛媛トリビア" in response.text
        # 次へボタンが存在する（最終問題でなければ「次へ」、最終なら「結果を見る」）
        assert "次へ" in response.text or "結果を見る" in response.text

    def test_course_complete_shows_summary(self, client: TestClient):
        """GET /quiz/{session_id}/complete がコース完了サマリーを表示する"""
        # セッション作成（dogo-ai-basic: 問題数が少ないコースを使用）
        response = client.post(
            "/quiz/start/dogo-ai-basic", follow_redirects=False
        )
        redirect_url = response.headers["location"]
        session_id = redirect_url.split("/quiz/")[1].split("/question")[0]

        # dogo-ai-basic コースの問題IDリスト（シードデータから）
        dogo_question_ids = [
            "q-ai-001", "q-ai-002", "q-ai-003",
            "q-ga-001", "q-ga-002", "q-ga-005", "q-ra-003",
        ]

        # 全問に回答する
        for i, qid in enumerate(dogo_question_ids):
            client.post(
                f"/quiz/{session_id}/answer",
                data={
                    "question_id": qid,
                    "choice_index": 1,
                    "question_index": i,
                },
                follow_redirects=False,
            )

        # コース完了画面へアクセス
        response = client.get(f"/quiz/{session_id}/complete")
        assert response.status_code == 200
        assert "道後温泉AIコース" in response.text

    def test_full_quiz_flow_start_to_complete(self, client: TestClient):
        """フルフロー: コース選択→クイズ開始→回答→完了"""
        # 1. コース選択画面が表示される
        response = client.get("/")
        assert response.status_code == 200

        # 2. クイズ開始（dogo-ai-basic: 問題数少なめ）
        response = client.post(
            "/quiz/start/dogo-ai-basic", follow_redirects=False
        )
        assert response.status_code == 303
        redirect_url = response.headers["location"]
        session_id = redirect_url.split("/quiz/")[1].split("/question")[0]

        # 3. 最初の問題を表示
        response = client.get(redirect_url)
        assert response.status_code == 200

        # 4. dogo-ai-basic コースの問題IDリスト
        dogo_question_ids = [
            "q-ai-001", "q-ai-002", "q-ai-003",
            "q-ga-001", "q-ga-002", "q-ga-005", "q-ra-003",
        ]

        # 5. 全問回答
        for i, qid in enumerate(dogo_question_ids):
            response = client.post(
                f"/quiz/{session_id}/answer",
                data={
                    "question_id": qid,
                    "choice_index": 1,
                    "question_index": i,
                },
                follow_redirects=False,
            )
            assert response.status_code == 303

        # 6. コース完了
        response = client.get(f"/quiz/{session_id}/complete")
        assert response.status_code == 200
        assert "道後温泉AIコース" in response.text


# =============================================================================
# 模擬試験フローテスト（Requirements: 5.1）
# =============================================================================


class TestMockExamFlow:
    """模擬試験フローのテスト"""

    def test_mock_exam_select_page(self, client: TestClient):
        """GET /mock-exam/select が試験タイプ選択画面を表示する"""
        response = client.get("/mock-exam/select")
        assert response.status_code == 200
        assert "Cloud Practitioner" in response.text
        assert "AI Practitioner" in response.text

    def test_mock_exam_start_redirects_to_question(self, client: TestClient):
        """POST /mock-exam/start が最初の問題にリダイレクトする"""
        response = client.post(
            "/mock-exam/start",
            data={"exam_type": "AWS Certified Cloud Practitioner"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "/mock-exam/" in response.headers["location"]
        assert "/question/0" in response.headers["location"]


# =============================================================================
# 結果ダッシュボードテスト（Requirements: 2.5）
# =============================================================================


class TestResultsDashboard:
    """結果ダッシュボードのテスト"""

    def test_dashboard_returns_200(self, client: TestClient):
        """GET /results/dashboard が200で返る"""
        response = client.get("/results/dashboard")
        assert response.status_code == 200
        assert "結果ダッシュボード" in response.text

    def test_dashboard_no_history_shows_message(self, client: TestClient):
        """学習履歴がない場合に適切なメッセージが表示される"""
        response = client.get("/results/dashboard")
        assert response.status_code == 200
        assert "まだ学習履歴がありません" in response.text
