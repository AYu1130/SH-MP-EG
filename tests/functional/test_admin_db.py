"""admin_db 单元测试（临时 SQLite，不启动网关）。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "software" / "gateway" / "python"))

from admin_db import AdminStore, MAX_LOGIN_FAILS  # noqa: E402


def test_login_empty_fields(tmp_path):
    db = tmp_path / "a.db"
    s = AdminStore(str(db))
    st, body = s.try_login("", "")
    assert st == "empty_fields"


def test_bootstrap_and_login_ok(tmp_path):
    db = tmp_path / "b.db"
    s = AdminStore(str(db))
    s.seed_bootstrap_admin("root", "secret12")
    st, body = s.try_login("root", "secret12")
    assert st == "ok"
    assert body["username"] == "root"
    assert body["role"] == "admin"


def test_lock_after_max_fails(tmp_path):
    db = tmp_path / "c.db"
    s = AdminStore(str(db))
    s.seed_bootstrap_admin("u", "goodpass")
    for _ in range(MAX_LOGIN_FAILS - 1):
        st, _ = s.try_login("u", "wrong")
        assert st == "bad_credentials"
    st, body = s.try_login("u", "wrong")
    assert st == "locked"
    assert body.get("retry_after_sec", 0) > 0
    st2, _ = s.try_login("u", "goodpass")
    assert st2 == "locked"
    # 模拟锁定期结束
    with s._lock:
        import sqlite3

        conn = sqlite3.connect(str(db))
        conn.execute("UPDATE admin_users SET locked_until=0, failed_attempts=0")
        conn.commit()
        conn.close()
    st3, body3 = s.try_login("u", "goodpass")
    assert st3 == "ok"
    assert body3["username"] == "u"


def test_presence_and_display_nodes(tmp_path):
    db = tmp_path / "e.db"
    s = AdminStore(str(db))
    s.seed_bootstrap_admin("a", "b")
    s.touch_presence("wifi", "esp-99")
    rows = s.list_display_nodes(online_grace_sec=120.0)
    assert any(r["native_device_id"] == "esp-99" and r["source"] == "discovered" for r in rows)
    s.create_node(
        unified_id="u1",
        device_type="wifi",
        native_device_id="esp-99",
        display_name="客厅",
        transport="wifi",
    )
    s.touch_presence("wifi", "esp-99")
    rows2 = s.list_display_nodes(online_grace_sec=120.0)
    reg = [r for r in rows2 if r.get("registry_id") is not None and r["native_device_id"] == "esp-99"]
    assert len(reg) == 1
    assert reg[0]["online"] is True
    assert reg[0]["source"] == "registry"


def test_nodes_crud(tmp_path):
    db = tmp_path / "d.db"
    s = AdminStore(str(db))
    s.seed_bootstrap_admin("a", "b")
    n = s.create_node(
        unified_id="n1",
        device_type="wifi",
        native_device_id="esp-01",
        display_name="客厅",
        transport="wifi",
    )
    assert n["unified_id"] == "n1"
    assert len(s.list_nodes()) == 1
    n2 = s.update_node(n["id"], display_name="卧室")
    assert n2["display_name"] == "卧室"
    s.delete_node(n["id"])
    assert s.list_nodes() == []
