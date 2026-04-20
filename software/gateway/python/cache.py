"""
cache.py
========

本地离线缓存模块。

场景
----
- MQTT Broker 不可达（如断网或 EMQX 重启）时，``mqtt_publisher`` 把待发送
  消息写入 SQLite；
- 连接恢复后，后台线程按 FIFO 顺序读取并重发，成功后删除。

特点
----
- 使用标准库 ``sqlite3``，无需额外依赖；
- ``WAL`` 模式开启，避免读写阻塞；
- 容量上限（``max_rows``）达到时自动丢弃最老记录，保证嵌入式
  设备上的存储占用可控。
"""

from __future__ import annotations

import os
import sqlite3
import threading
from typing import Iterable, List, Optional, Tuple

from logger import get_logger


logger = get_logger(__name__)


_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS outbox (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    topic      TEXT    NOT NULL,
    payload    TEXT    NOT NULL,
    qos        INTEGER NOT NULL DEFAULT 1,
    created_at REAL    NOT NULL DEFAULT (strftime('%s','now'))
);
"""


class MessageCache:
    """简单的 SQLite 消息持久化队列（FIFO）。

    线程安全：所有公共方法使用内部锁。对象跨线程共享，但
    ``sqlite3.Connection`` 被锁定在创建线程外的访问会报错，
    因此在每次操作时新建短连接，省去跨线程管理成本。
    """

    def __init__(self, db_path: str, max_rows: int = 100_000) -> None:
        self._db_path = db_path
        self._max_rows = max_rows
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(os.path.abspath(db_path)) or ".", exist_ok=True)
        self._init_db()

    # ---------------- 初始化 -------------------------------------------- #
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, timeout=5.0, isolation_level=None)
        # WAL 模式显著降低并发读写时的阻塞
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _init_db(self) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(_CREATE_TABLE_SQL)

    # ---------------- 对外接口 ------------------------------------------ #
    def push(self, topic: str, payload: str, qos: int = 1) -> int:
        """追加一条待发送消息，返回自增 ID。

        若总条数超过 ``max_rows``，删除最老的 N 条（简单 FIFO 溢出策略）。
        """
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO outbox (topic, payload, qos) VALUES (?, ?, ?)",
                (topic, payload, qos),
            )
            # 容量控制 ------------------------------------------------- #
            count = conn.execute("SELECT COUNT(*) FROM outbox").fetchone()[0]
            if count > self._max_rows:
                overflow = count - self._max_rows
                conn.execute(
                    "DELETE FROM outbox WHERE id IN "
                    "(SELECT id FROM outbox ORDER BY id ASC LIMIT ?)",
                    (overflow,),
                )
                logger.warning("cache overflow: dropped %d oldest rows", overflow)
            return int(cur.lastrowid)

    def peek(self, limit: int = 100) -> List[Tuple[int, str, str, int]]:
        """按 ID 升序取出前 ``limit`` 条，用于重发，但不删除。

        返回列表：``[(id, topic, payload, qos), ...]``。
        """
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT id, topic, payload, qos FROM outbox ORDER BY id ASC LIMIT ?",
                (limit,),
            ).fetchall()
            return [tuple(r) for r in rows]

    def delete(self, ids: Iterable[int]) -> None:
        """根据 ID 批量删除。重发成功后调用。"""
        ids = list(ids)
        if not ids:
            return
        placeholders = ",".join("?" * len(ids))
        with self._lock, self._connect() as conn:
            conn.execute(f"DELETE FROM outbox WHERE id IN ({placeholders})", ids)

    def size(self) -> int:
        with self._lock, self._connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM outbox").fetchone()[0])

    def close(self) -> None:
        """占位方法；当前实现每次操作独立连接，无资源需要释放。"""
        logger.debug("MessageCache closed")
