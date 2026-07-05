"""
Secrets management via AWS Systems Manager Parameter Store.

Lambda cold start 時に一度だけ Parameter Store からシークレットを取得し、
インメモリにキャッシュする。
"""

import os
import logging
from typing import Optional

import boto3
from botocore.config import Config

logger = logging.getLogger(__name__)

_secrets_cache: dict[str, str] = {}

SSM_TIMEOUT = 5  # seconds


def _get_environment() -> str:
    """ENVIRONMENT 環境変数を検証して返す。"""
    env = os.environ.get("ENVIRONMENT", "")
    if env not in ("prod", "staging"):
        raise RuntimeError(
            f"Invalid ENVIRONMENT: '{env}'. Must be 'prod' or 'staging'."
        )
    return env


def get_secret(param_name: str) -> Optional[str]:
    """Parameter Store からシークレットを取得する（キャッシュ付き）。"""
    if param_name in _secrets_cache:
        return _secrets_cache[param_name]

    environment = _get_environment()
    param_path = f"/EhimeAI2026/{environment}/{param_name}"

    try:
        config = Config(connect_timeout=SSM_TIMEOUT, read_timeout=SSM_TIMEOUT)
        ssm = boto3.client("ssm", config=config)
        response = ssm.get_parameter(Name=param_path, WithDecryption=True)
        value = response["Parameter"]["Value"]
        _secrets_cache[param_name] = value
        return value
    except Exception as e:
        logger.error(
            "Parameter Store retrieval failed for %s: %s",
            param_path,
            type(e).__name__,
        )
        return None
