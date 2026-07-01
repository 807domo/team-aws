"""
愛媛探索AIクイズ - 用語集シードデータ差分投入（upsert）ロジック ユニットテスト

seed_glossary()関数の差分投入ロジックを検証する。
- 空のDBに対して全件投入されること
- 既存データがある場合、新規用語のみ追加されること
- 既存用語が重複投入されないこと

Requirements: 2.5, 2.7
"""

import os
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.data.database import Base
from app.data.glossary_seed import GLOSSARY_SEED_DATA, seed_glossary
from app.data.models import GlossaryTermModel

TEST_DATABASE_URL = "sqlite:///./test_glossary_seed_upsert.db"


@pytest.fixture
def db_session():
    """テスト用のDBセッションを提供する。"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("./test_glossary_seed_upsert.db"):
        os.remove("./test_glossary_seed_upsert.db")


class TestSeedGlossaryUpsert:
    """seed_glossary()の差分投入ロジックテスト"""

    def test_seed_empty_db_inserts_all(self, db_session):
        """空のDBに対して全件投入し、Trueを返す"""
        result = seed_glossary(db_session)

        assert result is True
        count = db_session.query(GlossaryTermModel).count()
        assert count == len(GLOSSARY_SEED_DATA)

    def test_seed_existing_data_adds_only_new_terms(self, db_session):
        """既存データがある場合、新規用語のみ追加する"""
        # 最初の3件だけ投入
        for item in GLOSSARY_SEED_DATA[:3]:
            term = GlossaryTermModel(
                id=str(uuid.uuid4()),
                category=item["category"],
                sort_order=item["sort_order"],
                term=item["term"],
                description=item["description"],
            )
            db_session.add(term)
        db_session.commit()

        initial_count = db_session.query(GlossaryTermModel).count()
        assert initial_count == 3

        # seed_glossaryを実行 — 残りの用語が追加されるはず
        result = seed_glossary(db_session)

        assert result is True
        final_count = db_session.query(GlossaryTermModel).count()
        assert final_count == len(GLOSSARY_SEED_DATA)

    def test_seed_all_existing_returns_false(self, db_session):
        """全ての用語が既に存在する場合、Falseを返す"""
        # 全件投入
        seed_glossary(db_session)

        # もう一度実行 — 追加なしでFalse
        result = seed_glossary(db_session)

        assert result is False
        count = db_session.query(GlossaryTermModel).count()
        assert count == len(GLOSSARY_SEED_DATA)

    def test_no_duplicate_terms_after_multiple_seeds(self, db_session):
        """複数回実行しても重複用語が作成されないこと"""
        seed_glossary(db_session)
        seed_glossary(db_session)
        seed_glossary(db_session)

        count = db_session.query(GlossaryTermModel).count()
        assert count == len(GLOSSARY_SEED_DATA)

    def test_upsert_checks_by_term_name(self, db_session):
        """term名で重複チェックが行われること"""
        # 同じtermだが異なるdescriptionで手動投入
        first_item = GLOSSARY_SEED_DATA[0]
        term = GlossaryTermModel(
            id=str(uuid.uuid4()),
            category=first_item["category"],
            sort_order=first_item["sort_order"],
            term=first_item["term"],
            description="異なる説明文",
        )
        db_session.add(term)
        db_session.commit()

        # seed_glossaryを実行 — term名が同じなのでスキップされる
        seed_glossary(db_session)

        # 最初の用語は1件のまま（重複なし）
        matching = (
            db_session.query(GlossaryTermModel)
            .filter(GlossaryTermModel.term == first_item["term"])
            .all()
        )
        assert len(matching) == 1
        # 元のdescriptionが維持される（上書きされない）
        assert matching[0].description == "異なる説明文"
