"""
愛媛探索AIクイズ - コース選択ルーター

地域別（中予・南予・東予）にグルーピングされたコース一覧を返す。
注意: GET / はRPGトップ画面（top_router.py）に移行済み。
"""

from fastapi import APIRouter

router = APIRouter()
