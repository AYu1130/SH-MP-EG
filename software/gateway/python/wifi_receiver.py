"""
wifi_receiver.py
================

Wi-Fi 接入适配器。

对外暴露 *两种接入方式*，节点固件可任选其一：

1. **HTTP / REST**（基于 Flask）
   ``POST /api/v1/telemetry`` ，Body 为 JSON。示例::

       curl -X POST http://<gateway-ip>:8080/api/v1/telemetry \
            -H 'Content-Type: application/json' \
            -d '{"id":"esp32-s3-node-01","t":25.4,"h":56.1}'

   优点：调试方便、生态成熟；MCU 侧无需维护长连接。

2. **TCP 裸流**（``asyncio``）
   MCU 建立 TCP 连接到 ``:9000``，每条报文以 ``\\n`` 结尾的 JSON 行。
   优点：长连接时延更低，更接近真实工业场景。

两种方式接收到的数据都经过 :func:`data_converter.normalize_wifi`
转成统一 JSON 后，通过 :func:`_on_message` 回调交给上层 dispatcher。
"""

from __future__ import annotations

import asyncio
import json
import threading
from typing import Callable, Dict, Optional

from flask import Flask, jsonify, request
from werkzeug.serving import make_server

from config import GatewayConfig
from data_converter import normalize_wifi, validate
from logger import get_logger


logger = get_logger(__name__)

# 回调签名: (unified_message) -> None
OnMessage = Callable[[Dict], None]


# =========================================================================== #
# Flask HTTP 子服务
# =========================================================================== #
def _build_flask_app(
    on_message: OnMessage,
    validate_schema: bool,
    cfg: Optional[GatewayConfig] = None,
) -> Flask:
    """构造 Flask 应用实例。

    把 ``on_message`` / ``validate_schema`` 通过闭包注入，避免使用全局变量。
    """
    app = Flask("shmpeg-wifi-http")
    # 控制 Flask 自身日志级别，减少 INFO 刷屏
    import logging as _lg
    _lg.getLogger("werkzeug").setLevel(_lg.WARNING)

    # --------------- 路由: 健康检查 --------------------------------- #
    @app.get("/health")
    def health():
        return jsonify({"ok": True})

    # --------------- 路由: 遥测上报 --------------------------------- #
    @app.post("/api/v1/telemetry")
    def telemetry():
        try:
            raw = request.get_json(force=True, silent=False)
        except Exception as e:
            logger.warning("wifi HTTP: invalid JSON body: %s", e)
            return jsonify({"ok": False, "error": "invalid json"}), 400

        if not isinstance(raw, dict):
            return jsonify({"ok": False, "error": "payload must be object"}), 400

        try:
            msg = normalize_wifi(raw, transport="http")
            if validate_schema:
                validate(msg, strict=True)
        except Exception as e:
            logger.exception("wifi HTTP normalize error")
            return jsonify({"ok": False, "error": str(e)}), 400

        try:
            on_message(msg)
        except Exception:
            logger.exception("wifi HTTP on_message callback failed")
            return jsonify({"ok": False, "error": "gateway internal error"}), 500

        return jsonify({"ok": True, "device_id": msg["device_id"]})

    if cfg is not None and getattr(cfg, "admin_enabled", True):
        from admin_routes import register_admin_routes

        register_admin_routes(app, cfg)

    return app


class _FlaskThread(threading.Thread):
    """把 werkzeug dev server 放在独立线程中，便于和 asyncio 并存。"""

    def __init__(self, app: Flask, host: str, port: int) -> None:
        super().__init__(daemon=True, name="wifi-http")
        self._srv = make_server(host, port, app, threaded=True)
        self._ctx = app.app_context()
        self._ctx.push()

    def run(self) -> None:
        logger.info("wifi HTTP server listening on %s", self._srv.server_address)
        self._srv.serve_forever()

    def shutdown(self) -> None:
        self._srv.shutdown()


# =========================================================================== #
# asyncio TCP 子服务
# =========================================================================== #
async def _handle_tcp_client(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    on_message: OnMessage,
    validate_schema: bool,
    register_writer: Optional[Callable[[str, asyncio.StreamWriter], None]] = None,
    unregister_writer: Optional[Callable[[str, asyncio.StreamWriter], None]] = None,
) -> None:
    """单个 TCP 连接的处理协程：按行读取 JSON 并转发；按需登记 writer 以支持下行命令。"""
    peer = writer.get_extra_info("peername")
    logger.info("wifi TCP client connected: %s", peer)
    registered_id: Optional[str] = None
    try:
        while True:
            line = await reader.readline()
            if not line:
                break  # 对端关闭
            try:
                raw = json.loads(line.decode("utf-8").strip())
                msg = normalize_wifi(raw, transport="tcp")
                if validate_schema:
                    validate(msg, strict=True)
                if register_writer is not None and msg.get("device_id"):
                    did = str(msg["device_id"])
                    if registered_id != did:
                        registered_id = did
                        register_writer(did, writer)
                on_message(msg)
                writer.write(b'{"ok":true}\n')
                await writer.drain()
            except Exception as e:
                logger.warning("wifi TCP parse error: %s | line=%r", e, line)
                writer.write(b'{"ok":false}\n')
                await writer.drain()
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("wifi TCP connection error")
    finally:
        if registered_id is not None and unregister_writer is not None:
            try:
                unregister_writer(registered_id, writer)
            except Exception:
                pass
        logger.info("wifi TCP client closed: %s", peer)
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


# =========================================================================== #
# 公共接口：WifiReceiver
# =========================================================================== #
class WifiReceiver:
    """Wi-Fi 适配器对外入口。

    同时启动一个 Flask (HTTP) 服务器和一个 asyncio (TCP) 服务器。
    """

    def __init__(self, cfg: GatewayConfig, on_message: OnMessage) -> None:
        self._cfg = cfg
        self._on_message = on_message

        self._flask_thread: Optional[_FlaskThread] = None
        self._tcp_server: Optional[asyncio.AbstractServer] = None
        self._tcp_task: Optional[asyncio.Task] = None

        # device_id -> 最近一次见到的 TCP writer（用于下行命令）
        self._tcp_writers: Dict[str, asyncio.StreamWriter] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    # ------------------------------------------------------------------ #
    # 下行命令：被 main.on_command 调用（线程安全：转发到 asyncio 协程）
    # ------------------------------------------------------------------ #
    def write(self, device_id: str, payload: Dict) -> bool:
        """向已通过 TCP 上线的 Wi-Fi 节点下发一行 JSON 命令。"""
        w = self._tcp_writers.get(device_id)
        loop = self._loop
        if w is None or loop is None or w.is_closing():
            logger.warning("wifi command: device %s not connected via TCP", device_id)
            return False
        try:
            data = (json.dumps(payload) + "\n").encode("utf-8")
        except (TypeError, ValueError) as e:
            logger.warning("wifi command: bad payload for %s: %s", device_id, e)
            return False

        async def _send():
            try:
                w.write(data)
                await w.drain()
            except Exception:
                logger.exception("wifi command: write failed for %s", device_id)

        asyncio.run_coroutine_threadsafe(_send(), loop)
        logger.info("wifi command -> %s: %s", device_id, payload)
        return True

    def _register_writer(self, device_id: str, writer: asyncio.StreamWriter) -> None:
        prev = self._tcp_writers.get(device_id)
        if prev is not None and prev is not writer:
            try:
                prev.close()
            except Exception:
                pass
        self._tcp_writers[device_id] = writer
        logger.info("wifi TCP writer registered: %s", device_id)

    def _unregister_writer(self, device_id: str, writer: asyncio.StreamWriter) -> None:
        cur = self._tcp_writers.get(device_id)
        if cur is writer:
            self._tcp_writers.pop(device_id, None)
            logger.info("wifi TCP writer unregistered: %s", device_id)

    # ------------------------------------------------------------------ #
    # 启动 / 停止
    # ------------------------------------------------------------------ #
    async def start(self) -> None:
        """异步启动两种服务；协程返回后，背景服务继续运行。"""
        # ---- HTTP (Flask, 独立线程) ---------------------------------- #
        app = _build_flask_app(self._on_message, self._cfg.validate_schema, self._cfg)
        self._flask_thread = _FlaskThread(app, self._cfg.wifi_host, self._cfg.wifi_http_port)
        self._flask_thread.start()

        # ---- TCP (asyncio) ------------------------------------------- #
        self._loop = asyncio.get_running_loop()
        self._tcp_server = await asyncio.start_server(
            lambda r, w: _handle_tcp_client(
                r, w, self._on_message, self._cfg.validate_schema,
                register_writer=self._register_writer,
                unregister_writer=self._unregister_writer,
            ),
            host=self._cfg.wifi_host,
            port=self._cfg.wifi_tcp_port,
        )
        addrs = ", ".join(str(s.getsockname()) for s in self._tcp_server.sockets)
        logger.info("wifi TCP server listening on %s", addrs)
        # 用后台 task 持续 serve
        self._tcp_task = asyncio.create_task(
            self._tcp_server.serve_forever(),
            name="wifi-tcp-serve",
        )

    async def stop(self) -> None:
        logger.info("stopping WifiReceiver ...")
        if self._tcp_server is not None:
            self._tcp_server.close()
            try:
                await self._tcp_server.wait_closed()
            except Exception:
                pass
        if self._tcp_task is not None:
            self._tcp_task.cancel()
            try:
                await self._tcp_task
            except (asyncio.CancelledError, Exception):
                pass
        if self._flask_thread is not None:
            self._flask_thread.shutdown()
        logger.info("WifiReceiver stopped")
