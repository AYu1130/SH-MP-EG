"""
admin_db.py
===========

Web 管理台使用的 SQLite：用户表、节点表。

与 ``cache.MessageCache`` 类似，每次操作短连接 + 线程锁，适配 Flask 多线程。
"""

from __future__ import annotations

import os
import sqlite3
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from werkzeug.security import check_password_hash, generate_password_hash

from logger import get_logger


logger = get_logger(__name__)

MAX_LOGIN_FAILS = 5
LOCK_SECONDS = 900  # 15 分钟

_SCHEMA = """
CREATE TABLE IF NOT EXISTS admin_users (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    username          TEXT NOT NULL UNIQUE,
    password_hash     TEXT NOT NULL,
    role              TEXT NOT NULL DEFAULT 'user',
    failed_attempts   INTEGER NOT NULL DEFAULT 0,
    locked_until      REAL NOT NULL DEFAULT 0,
    created_at        REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS admin_nodes (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    unified_id         TEXT NOT NULL UNIQUE,
    device_type        TEXT NOT NULL,
    native_device_id   TEXT NOT NULL,
    display_name       TEXT,
    transport          TEXT NOT NULL DEFAULT 'wifi',
    note               TEXT,
    created_at         REAL NOT NULL,
    updated_at         REAL NOT NULL,
    UNIQUE (device_type, native_device_id)
);

CREATE INDEX IF NOT EXISTS idx_admin_nodes_type ON admin_nodes(device_type);

CREATE TABLE IF NOT EXISTS node_presence (
    device_type TEXT NOT NULL,
    device_id   TEXT NOT NULL,
    last_seen   REAL NOT NULL,
    PRIMARY KEY (device_type, device_id)
);

CREATE INDEX IF NOT EXISTS idx_node_presence_seen ON node_presence(last_seen);
"""


def _connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


class AdminStore:
    """用户与节点的持久化。"""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._lock = threading.Lock()
        d = os.path.dirname(os.path.abspath(db_path)) or "."
        os.makedirs(d, exist_ok=True)
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock:
            conn = _connect(self._db_path)
            try:
                conn.executescript(_SCHEMA)
                conn.commit()
            finally:
                conn.close()

    def seed_bootstrap_admin(
        self,
        username: str,
        password: str,
    ) -> None:
        """若库中无任何用户，则创建首个管理员。"""
        if not password:
            return
        u = (username or "").strip()
        if not u:
            return
        with self._lock:
            conn = _connect(self._db_path)
            try:
                n = conn.execute("SELECT COUNT(*) AS c FROM admin_users").fetchone()["c"]
                if n > 0:
                    return
                ph = generate_password_hash(password)
                now = time.time()
                conn.execute(
                    "INSERT INTO admin_users (username, password_hash, role, "
                    "failed_attempts, locked_until, created_at) VALUES (?,?,?,?,?,?)",
                    (u, ph, "admin", 0, 0.0, now),
                )
                conn.commit()
                logger.warning(
                    "admin DB seeded first user %r (change password in production)", u
                )
            finally:
                conn.close()

    # -------------------------- 登录 ---------------------------------- #

    def try_login(self, username: str, password: str) -> Tuple[str, Dict[str, Any]]:
        """返回 (status, body)。

        status: ``ok`` | ``empty_fields`` | ``locked`` | ``bad_credentials``
        """
        u = (username or "").strip()
        p = password or ""
        if not u or not p:
            return "empty_fields", {"message": "请输入用户名和密码"}

        now = time.time()
        with self._lock:
            conn = _connect(self._db_path)
            try:
                row = conn.execute(
                    "SELECT * FROM admin_users WHERE username = ?", (u,)
                ).fetchone()
                if row is None:
                    return "bad_credentials", {"message": "用户名或密码错误"}

                if row["locked_until"] and row["locked_until"] > now:
                    remain = int(row["locked_until"] - now)
                    return "locked", {
                        "message": "登录尝试过多，账户已锁定，请稍后再试",
                        "retry_after_sec": remain,
                    }

                if not check_password_hash(row["password_hash"], p):
                    fails = int(row["failed_attempts"]) + 1
                    locked_until = 0.0
                    if fails >= MAX_LOGIN_FAILS:
                        locked_until = now + LOCK_SECONDS
                        fails = 0  # 论文：锁定后计数可重置；锁定期满再登录
                    conn.execute(
                        "UPDATE admin_users SET failed_attempts=?, locked_until=? "
                        "WHERE id=?",
                        (fails if locked_until == 0 else 0, locked_until, row["id"]),
                    )
                    conn.commit()
                    if locked_until:
                        return "locked", {
                            "message": "错误次数过多，已锁定界面",
                            "retry_after_sec": LOCK_SECONDS,
                        }
                    return "bad_credentials", {"message": "用户名或密码错误"}

                conn.execute(
                    "UPDATE admin_users SET failed_attempts=0, locked_until=0 "
                    "WHERE id=?",
                    (row["id"],),
                )
                conn.commit()
                user = {
                    "id": row["id"],
                    "username": row["username"],
                    "role": row["role"],
                }
                return "ok", user
            finally:
                conn.close()

    def is_locked(self, username: str) -> Tuple[bool, int]:
        u = (username or "").strip()
        if not u:
            return False, 0
        now = time.time()
        with self._lock:
            conn = _connect(self._db_path)
            try:
                row = conn.execute(
                    "SELECT locked_until FROM admin_users WHERE username=?", (u,)
                ).fetchone()
                if not row or not row["locked_until"] or row["locked_until"] <= now:
                    return False, 0
                return True, int(row["locked_until"] - now)
            finally:
                conn.close()

    # -------------------------- 用户 CRUD ----------------------------- #

    def list_users(self) -> List[Dict[str, Any]]:
        with self._lock:
            conn = _connect(self._db_path)
            try:
                rows = conn.execute(
                    "SELECT id, username, role, failed_attempts, locked_until, created_at "
                    "FROM admin_users ORDER BY id"
                ).fetchall()
                return [dict(r) for r in rows]
            finally:
                conn.close()

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        with self._lock:
            conn = _connect(self._db_path)
            try:
                row = conn.execute(
                    "SELECT id, username, role, created_at FROM admin_users WHERE id=?",
                    (user_id,),
                ).fetchone()
                return dict(row) if row else None
            finally:
                conn.close()

    def create_user(self, username: str, password: str, role: str) -> Dict[str, Any]:
        u = (username or "").strip()
        if not u or not password:
            raise ValueError("用户名和密码不能为空")
        if role not in ("admin", "user"):
            raise ValueError("role 必须是 admin 或 user")
        ph = generate_password_hash(password)
        now = time.time()
        with self._lock:
            conn = _connect(self._db_path)
            try:
                conn.execute(
                    "INSERT INTO admin_users (username, password_hash, role, "
                    "failed_attempts, locked_until, created_at) VALUES (?,?,?,?,?,?)",
                    (u, ph, role, 0, 0.0, now),
                )
                conn.commit()
                uid = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
                return {"id": uid, "username": u, "role": role}
            except sqlite3.IntegrityError as e:
                raise ValueError("用户名已存在") from e
            finally:
                conn.close()

    def update_user(
        self,
        user_id: int,
        *,
        password: Optional[str] = None,
        role: Optional[str] = None,
    ) -> None:
        if role is not None and role not in ("admin", "user"):
            raise ValueError("role 必须是 admin 或 user")
        sets: List[str] = []
        vals: List[Any] = []
        if password:
            sets.append("password_hash = ?")
            vals.append(generate_password_hash(password))
        if role is not None:
            sets.append("role = ?")
            vals.append(role)
        if not sets:
            return
        vals.append(user_id)
        with self._lock:
            conn = _connect(self._db_path)
            try:
                cur = conn.execute(
                    f"UPDATE admin_users SET {', '.join(sets)} WHERE id=?",
                    vals,
                )
                if cur.rowcount == 0:
                    raise ValueError("用户不存在")
                conn.commit()
            finally:
                conn.close()

    def delete_user(self, user_id: int, actor_id: int) -> None:
        if user_id == actor_id:
            raise ValueError("不能删除当前登录用户")
        with self._lock:
            conn = _connect(self._db_path)
            try:
                row = conn.execute(
                    "SELECT role FROM admin_users WHERE id=?", (user_id,)
                ).fetchone()
                if not row:
                    raise ValueError("用户不存在")
                if row["role"] == "admin":
                    n = conn.execute(
                        "SELECT COUNT(*) AS c FROM admin_users WHERE role='admin'"
                    ).fetchone()["c"]
                    if n <= 1:
                        raise ValueError("不能删除最后一个管理员")
                conn.execute("DELETE FROM admin_users WHERE id=?", (user_id,))
                conn.commit()
            finally:
                conn.close()

    def admin_count(self) -> int:
        with self._lock:
            conn = _connect(self._db_path)
            try:
                return int(
                    conn.execute(
                        "SELECT COUNT(*) AS c FROM admin_users WHERE role='admin'"
                    ).fetchone()["c"]
                )
            finally:
                conn.close()

    # -------------------------- 在线节点（上行心跳）------------------- #

    def touch_presence(self, device_type: str, device_id: str, ts: Optional[float] = None) -> None:
        """记录某设备最近一次经网关转 MQTT 的上行时间（由 main.on_message 调用）。"""
        dt = (device_type or "").strip().lower()
        did = (device_id or "").strip()
        if not dt or not did:
            return
        t = float(ts if ts is not None else time.time())
        with self._lock:
            conn = _connect(self._db_path)
            try:
                conn.execute(
                    "INSERT INTO node_presence (device_type, device_id, last_seen) "
                    "VALUES (?,?,?) ON CONFLICT(device_type, device_id) DO UPDATE SET "
                    "last_seen=excluded.last_seen",
                    (dt, did, t),
                )
                conn.commit()
            finally:
                conn.close()

    def list_display_nodes(self, online_grace_sec: float = 120.0) -> List[Dict[str, Any]]:
        """合并台账 + 实际上线节点，供管理台列表展示。"""
        now = time.time()
        thr = now - max(5.0, float(online_grace_sec))
        with self._lock:
            conn = _connect(self._db_path)
            try:
                pres_rows = conn.execute(
                    "SELECT device_type, device_id, last_seen FROM node_presence"
                ).fetchall()
                reg_rows = conn.execute(
                    "SELECT id, unified_id, device_type, native_device_id, display_name, "
                    "transport FROM admin_nodes ORDER BY id"
                ).fetchall()
            finally:
                conn.close()

        pres_map: Dict[Tuple[str, str], float] = {
            (r["device_type"], r["device_id"]): float(r["last_seen"]) for r in pres_rows
        }
        seen_registry_keys: set = set()
        out: List[Dict[str, Any]] = []

        for r in reg_rows:
            key = (r["device_type"], r["native_device_id"])
            seen_registry_keys.add(key)
            last = pres_map.get(key)
            online = last is not None and last >= thr
            out.append(
                {
                    "registry_id": int(r["id"]),
                    "unified_id": r["unified_id"],
                    "device_type": r["device_type"],
                    "native_device_id": r["native_device_id"],
                    "display_name": r["display_name"] or "",
                    "transport": r["transport"],
                    "online": online,
                    "last_seen": last,
                    "source": "registry",
                }
            )

        for r in pres_rows:
            key = (r["device_type"], r["device_id"])
            if key in seen_registry_keys:
                continue
            last = float(r["last_seen"])
            online = last >= thr
            out.append(
                {
                    "registry_id": None,
                    "unified_id": r["device_id"],
                    "device_type": r["device_type"],
                    "native_device_id": r["device_id"],
                    "display_name": "",
                    "transport": r["device_type"],
                    "online": online,
                    "last_seen": last,
                    "source": "discovered",
                }
            )

        out.sort(key=lambda x: (x["online"], x["last_seen"] or 0.0), reverse=True)
        return out

    # -------------------------- 节点 CRUD ----------------------------- #

    def list_nodes(self) -> List[Dict[str, Any]]:
        with self._lock:
            conn = _connect(self._db_path)
            try:
                rows = conn.execute(
                    "SELECT id, unified_id, device_type, native_device_id, "
                    "display_name, transport, note, created_at, updated_at "
                    "FROM admin_nodes ORDER BY id"
                ).fetchall()
                return [dict(r) for r in rows]
            finally:
                conn.close()

    def create_node(
        self,
        *,
        unified_id: str,
        device_type: str,
        native_device_id: str,
        display_name: str = "",
        transport: str = "wifi",
        note: str = "",
    ) -> Dict[str, Any]:
        uid = (unified_id or "").strip()
        dt = (device_type or "").strip().lower()
        nid = (native_device_id or "").strip()
        if not uid or not dt or not nid:
            raise ValueError("unified_id、device_type、native_device_id 不能为空")
        if transport not in ("wifi", "ble", "zigbee", "lorawan"):
            raise ValueError("transport 无效")
        now = time.time()
        with self._lock:
            conn = _connect(self._db_path)
            try:
                conn.execute(
                    "INSERT INTO admin_nodes (unified_id, device_type, native_device_id, "
                    "display_name, transport, note, created_at, updated_at) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (
                        uid,
                        dt,
                        nid,
                        (display_name or "").strip() or None,
                        transport,
                        (note or "").strip() or None,
                        now,
                        now,
                    ),
                )
                conn.commit()
                iid = int(conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"])
                return self._get_node_by_id(conn, iid)
            except sqlite3.IntegrityError as e:
                raise ValueError("统一 ID 或 (device_type, native_device_id) 已存在") from e
            finally:
                conn.close()

    def _get_node_by_id(self, conn: sqlite3.Connection, node_id: int) -> Dict[str, Any]:
        row = conn.execute(
            "SELECT id, unified_id, device_type, native_device_id, display_name, "
            "transport, note, created_at, updated_at FROM admin_nodes WHERE id=?",
            (node_id,),
        ).fetchone()
        if not row:
            raise ValueError("节点不存在")
        return dict(row)

    def get_node(self, node_id: int) -> Optional[Dict[str, Any]]:
        with self._lock:
            conn = _connect(self._db_path)
            try:
                row = conn.execute(
                    "SELECT id, unified_id, device_type, native_device_id, display_name, "
                    "transport, note, created_at, updated_at FROM admin_nodes WHERE id=?",
                    (node_id,),
                ).fetchone()
                return dict(row) if row else None
            finally:
                conn.close()

    def update_node(
        self,
        node_id: int,
        *,
        unified_id: Optional[str] = None,
        display_name: Optional[str] = None,
        transport: Optional[str] = None,
        note: Optional[str] = None,
        native_device_id: Optional[str] = None,
        device_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        if transport is not None and transport not in ("wifi", "ble", "zigbee", "lorawan"):
            raise ValueError("transport 无效")
        sets: List[str] = ["updated_at = ?"]
        vals: List[Any] = [time.time()]
        if unified_id is not None:
            sets.append("unified_id = ?")
            vals.append(unified_id.strip())
        if display_name is not None:
            sets.append("display_name = ?")
            vals.append(display_name.strip() or None)
        if transport is not None:
            sets.append("transport = ?")
            vals.append(transport)
        if note is not None:
            sets.append("note = ?")
            vals.append(note.strip() or None)
        if native_device_id is not None:
            sets.append("native_device_id = ?")
            vals.append(native_device_id.strip())
        if device_type is not None:
            sets.append("device_type = ?")
            vals.append(device_type.strip().lower())
        vals.append(node_id)
        with self._lock:
            conn = _connect(self._db_path)
            try:
                cur = conn.execute(
                    f"UPDATE admin_nodes SET {', '.join(sets)} WHERE id=?",
                    vals,
                )
                if cur.rowcount == 0:
                    raise ValueError("节点不存在")
                conn.commit()
                return self._get_node_by_id(conn, node_id)
            except sqlite3.IntegrityError as e:
                raise ValueError("统一 ID 或 (device_type, native_device_id) 冲突") from e
            finally:
                conn.close()

    def delete_node(self, node_id: int) -> None:
        with self._lock:
            conn = _connect(self._db_path)
            try:
                cur = conn.execute("DELETE FROM admin_nodes WHERE id=?", (node_id,))
                if cur.rowcount == 0:
                    raise ValueError("节点不存在")
                conn.commit()
            finally:
                conn.close()
