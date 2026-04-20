"""
admin_routes.py
===============

Web 管理：登录、用户 CRUD（管理员）、节点 CRUD（登录用户）、静态页入口。
"""

from __future__ import annotations

import os
from functools import wraps
from typing import Any, Callable, Optional

from flask import Flask, jsonify, request, send_from_directory, session

from admin_db import AdminStore
from config import GatewayConfig
from logger import get_logger


logger = get_logger(__name__)

_ALLOWED_STATIC = frozenset({"login.html", "app.html"})

# 供 main.on_message 记录在线节点（与 Flask 同进程）
_admin_store: Optional[AdminStore] = None


def note_device_seen(device_type: str, device_id: str) -> None:
    """网关收到统一上行时调用，更新 ``node_presence``。"""
    s = _admin_store
    if s is None:
        return
    try:
        s.touch_presence(device_type, device_id)
    except Exception:
        logger.debug("touch_presence failed", exc_info=True)


def _static_admin_dir() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "admin")


def register_admin_routes(app: Flask, cfg: GatewayConfig) -> None:
    """在已有 Flask app 上注册管理 API 与 ``/admin/*`` 静态页。"""
    app.secret_key = cfg.admin_secret_key
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    global _admin_store
    store = AdminStore(cfg.admin_db_path)
    store.seed_bootstrap_admin(cfg.admin_bootstrap_username, cfg.admin_bootstrap_password)
    _admin_store = store

    def login_required(f: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(f)
        def deco(*args: Any, **kwargs: Any):
            if "user_id" not in session:
                return jsonify({"ok": False, "error": "unauthorized"}), 401
            return f(*args, **kwargs)

        return deco

    def admin_required(f: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(f)
        def deco(*args: Any, **kwargs: Any):
            if "user_id" not in session:
                return jsonify({"ok": False, "error": "unauthorized"}), 401
            if session.get("role") != "admin":
                return jsonify({"ok": False, "error": "forbidden"}), 403
            return f(*args, **kwargs)

        return deco

    # ------------------------- 静态页 -------------------------------- #
    @app.get("/admin/")
    def admin_index():
        return send_from_directory(_static_admin_dir(), "login.html")

    @app.get("/admin/<path:name>")
    def admin_static(name: str):
        base = os.path.basename(name)
        if base not in _ALLOWED_STATIC or name != base:
            return jsonify({"ok": False, "error": "not found"}), 404
        return send_from_directory(_static_admin_dir(), base)

    # ------------------------- 认证 API ------------------------------ #
    @app.post("/api/v1/admin/login")
    def admin_login():
        body = request.get_json(silent=True) or {}
        username = body.get("username", "")
        password = body.get("password", "")
        status, payload = store.try_login(username, password)
        if status == "empty_fields":
            return jsonify({"ok": False, "code": "empty_fields", **payload}), 400
        if status == "locked":
            return jsonify({"ok": False, "code": "locked", **payload}), 423
        if status == "bad_credentials":
            return jsonify({"ok": False, "code": "bad_credentials", **payload}), 401
        user = payload
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        session.permanent = True
        logger.info("admin login ok user=%r role=%r", user["username"], user["role"])
        return jsonify({"ok": True, "user": {k: user[k] for k in ("id", "username", "role")}})

    @app.post("/api/v1/admin/logout")
    @login_required
    def admin_logout():
        session.clear()
        return jsonify({"ok": True})

    @app.get("/api/v1/admin/session")
    def admin_session():
        if "user_id" not in session:
            return jsonify({"ok": True, "authenticated": False})
        return jsonify(
            {
                "ok": True,
                "authenticated": True,
                "user": {
                    "id": session["user_id"],
                    "username": session.get("username"),
                    "role": session.get("role"),
                },
            }
        )

    # ------------------------- 用户 API（管理员）--------------------- #
    @app.get("/api/v1/admin/users")
    @admin_required
    def users_list():
        return jsonify({"ok": True, "users": store.list_users()})

    @app.post("/api/v1/admin/users")
    @admin_required
    def users_create():
        body = request.get_json(silent=True) or {}
        try:
            u = store.create_user(
                str(body.get("username", "")),
                str(body.get("password", "")),
                str(body.get("role", "user")),
            )
            return jsonify({"ok": True, "user": u}), 201
        except ValueError as e:
            return jsonify({"ok": False, "error": str(e)}), 400

    @app.patch("/api/v1/admin/users/<int:user_id>")
    @admin_required
    def users_patch(user_id: int):
        body = request.get_json(silent=True) or {}
        pw: Optional[str] = None
        if "password" in body:
            pw = str(body.get("password") or "")
        role: Optional[str] = None
        if "role" in body:
            role = str(body.get("role") or "")
        try:
            store.update_user(user_id, password=pw or None, role=role)
            return jsonify({"ok": True})
        except ValueError as e:
            return jsonify({"ok": False, "error": str(e)}), 400

    @app.delete("/api/v1/admin/users/<int:user_id>")
    @admin_required
    def users_delete(user_id: int):
        actor = int(session["user_id"])
        try:
            store.delete_user(user_id, actor_id=actor)
            return jsonify({"ok": True})
        except ValueError as e:
            return jsonify({"ok": False, "error": str(e)}), 400

    # ------------------------- 节点 API ------------------------------- #
    @app.get("/api/v1/admin/nodes")
    @login_required
    def nodes_list():
        grace = float(getattr(cfg, "admin_online_grace_sec", 120.0))
        nodes = store.list_display_nodes(online_grace_sec=grace)
        return jsonify(
            {
                "ok": True,
                "nodes": nodes,
                "online_grace_sec": grace,
            }
        )

    @app.post("/api/v1/admin/nodes")
    @login_required
    def nodes_create():
        body = request.get_json(silent=True) or {}
        try:
            n = store.create_node(
                unified_id=str(body.get("unified_id", "")),
                device_type=str(body.get("device_type", "")),
                native_device_id=str(body.get("native_device_id", "")),
                display_name=str(body.get("display_name", "")),
                transport=str(body.get("transport", "wifi")),
                note=str(body.get("note", "")),
            )
            return jsonify({"ok": True, "node": n}), 201
        except ValueError as e:
            return jsonify({"ok": False, "error": str(e)}), 400

    @app.patch("/api/v1/admin/nodes/<int:node_id>")
    @login_required
    def nodes_patch(node_id: int):
        body = request.get_json(silent=True) or {}
        kw: dict = {}
        for k in (
            "unified_id",
            "display_name",
            "transport",
            "note",
            "native_device_id",
            "device_type",
        ):
            if k in body:
                kw[k] = body[k]
        try:
            n = store.update_node(node_id, **kw)
            return jsonify({"ok": True, "node": n})
        except ValueError as e:
            return jsonify({"ok": False, "error": str(e)}), 400

    @app.delete("/api/v1/admin/nodes/<int:node_id>")
    @login_required
    def nodes_delete(node_id: int):
        try:
            store.delete_node(node_id)
            return jsonify({"ok": True})
        except ValueError as e:
            return jsonify({"ok": False, "error": str(e)}), 400
