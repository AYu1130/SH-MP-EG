"""
pytest 全局 fixtures / path 设置。

所有测试脚本都通过 ``from gateway import ...`` 访问网关模块，
本文件把 ``software/gateway/python`` 目录加到 ``sys.path`` 前端，
让测试可以直接 ``import config`` / ``import data_converter``。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent
GATEWAY_PY = PROJECT_ROOT / "software" / "gateway" / "python"
if str(GATEWAY_PY) not in sys.path:
    sys.path.insert(0, str(GATEWAY_PY))


@pytest.fixture(scope="session")
def gateway_python_dir() -> Path:
    """指向网关 Python 代码根目录。"""
    return GATEWAY_PY


@pytest.fixture(scope="session")
def mqtt_host() -> str:
    """便于 CI 覆盖 broker 地址。"""
    return os.environ.get("SHMPEG_TEST_MQTT_HOST", "127.0.0.1")


@pytest.fixture(scope="session")
def mqtt_port() -> int:
    return int(os.environ.get("SHMPEG_TEST_MQTT_PORT", "1883"))


@pytest.fixture(scope="session")
def gateway_http_url() -> str:
    """网关 HTTP 适配器 URL。"""
    host = os.environ.get("SHMPEG_TEST_HTTP_HOST", "127.0.0.1")
    port = os.environ.get("SHMPEG_TEST_HTTP_PORT", "8080")
    return f"http://{host}:{port}"
