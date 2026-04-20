"""
main.py
=======

网关主入口。

职责
----
- 解析命令行参数、装配 ``GatewayConfig``；
- 初始化 logger / 本地缓存 / MQTT 客户端；
- 并发启动 Wi-Fi (HTTP + TCP) 与 BLE 两个协议适配器；
- 把协议适配器的上行消息 -> :class:`MqttPublisher`；
- 把 MqttPublisher 收到的下行命令 -> 对应协议写回；
- 捕获 SIGINT / SIGTERM，优雅停机。

启动示例
--------
.. code-block:: bash

    # 最小启动（使用默认配置）
    python main.py

    # 自定义端口 / MQTT Broker
    python main.py --mqtt-host 192.168.1.10 --wifi-http-port 8081

    # 禁用 BLE（例如在无蓝牙适配器的开发机上调试）
    python main.py --no-ble
"""

from __future__ import annotations

import argparse
import asyncio
import json
import signal
from typing import Dict, Optional

from config import GatewayConfig
from logger import get_logger, setup_logging


def _compact_ble_mqtt_payload(payload: Dict) -> Dict:
    """STM32 固件只解析 beep/buzzer/auto/src_seq；去掉 reason/src/ts 缩短 HM-10/UART 帧。"""
    slim: Dict = {}
    for k in ("beep", "buzzer", "auto", "src_seq"):
        if k in payload:
            slim[k] = payload[k]
    return slim if slim else payload


# --------------------------------------------------------------------------- #
# 命令行参数 -> GatewayConfig
# --------------------------------------------------------------------------- #
def parse_args() -> GatewayConfig:
    """从命令行读取参数并合并进 ``GatewayConfig`` 默认值。"""
    cfg = GatewayConfig()  # 先读环境变量和默认值

    p = argparse.ArgumentParser(description="SH-MP-EG edge gateway")
    p.add_argument("--log-level", default=cfg.log_level,
                   choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    p.add_argument("--log-file", default=cfg.log_file)

    p.add_argument("--mqtt-host", default=cfg.mqtt_host)
    p.add_argument("--mqtt-port", type=int, default=cfg.mqtt_port)
    p.add_argument("--mqtt-username", default=cfg.mqtt_username)
    p.add_argument("--mqtt-password", default=cfg.mqtt_password)
    p.add_argument("--mqtt-client-id", default=cfg.mqtt_client_id)

    p.add_argument("--wifi-host", default=cfg.wifi_host)
    p.add_argument("--wifi-http-port", type=int, default=cfg.wifi_http_port)
    p.add_argument("--wifi-tcp-port", type=int, default=cfg.wifi_tcp_port)

    p.add_argument("--no-wifi", dest="wifi_enabled", action="store_false",
                   default=cfg.wifi_enabled, help="禁用 Wi-Fi 适配器")
    p.add_argument("--no-ble", dest="ble_enabled", action="store_false",
                   default=cfg.ble_enabled, help="禁用 BLE 适配器")
    p.add_argument("--no-cache", dest="cache_enabled", action="store_false",
                   default=cfg.cache_enabled, help="禁用本地 SQLite 缓存")
    p.add_argument("--no-validate", dest="validate_schema", action="store_false",
                   default=cfg.validate_schema, help="跳过统一 JSON Schema 校验")

    p.add_argument("--no-admin", dest="admin_enabled", action="store_false",
                   default=cfg.admin_enabled, help="禁用 Web 管理（用户/节点 API 与 /admin 页面）")

    args = p.parse_args()

    # 用命令行覆盖默认值
    for k, v in vars(args).items():
        setattr(cfg, k, v)
    return cfg


# --------------------------------------------------------------------------- #
# 主协程
# --------------------------------------------------------------------------- #
async def amain(cfg: GatewayConfig) -> None:
    """异步主流程。"""
    # 日志在最早初始化，使后续模块都能直接使用 get_logger
    setup_logging(level=cfg.log_level, log_file=cfg.log_file)
    log = get_logger("gateway.main")
    log.info("SH-MP-EG gateway starting ...")
    log.debug("config: %s", cfg.to_dict())

    # paho 在独立线程回调 on_command；BLE 写入必须用主事件循环线程调度
    loop = asyncio.get_running_loop()

    # ---- 本地缓存 ---------------------------------------------------- #
    cache = None
    if cfg.cache_enabled:
        from cache import MessageCache
        cache = MessageCache(cfg.cache_db_path, max_rows=cfg.cache_max_rows)
        log.info("cache enabled: %s (queue=%d)", cfg.cache_db_path, cache.size())

    # ---- 适配器占位（后面赋值） ------------------------------------- #
    wifi_recv = None
    ble_recv = None

    # ---- 下行命令分发器 --------------------------------------------- #
    # MQTT 收到 smarthome/v1/command/<type>/<id> 时会回调这里
    def on_command(device_type: str, device_id: str, payload: Dict) -> None:
        log.info("[cmd] %s/%s <- %s", device_type, device_id, payload)
        # #region agent log
        try:
            from debug_agent_log import agent_log

            agent_log(
                "H_WIFI_RELEASE",
                "main.py:on_command",
                "command_received",
                {
                    "device_type": device_type,
                    "device_id": device_id,
                    "keys": sorted(str(k) for k in payload.keys()),
                    "reason": payload.get("reason"),
                },
            )
        except Exception:
            pass
        # #endregion
        if device_type == "ble" and ble_recv is not None:
            # payload 约定 {"raw_hex": "01020304"} 或 {"text": "LED:ON"}
            # 或 Node-RED 下发的 JSON 对象（beep/buzzer/auto 等）-> 整帧 UTF-8 行给 HM-10
            data: Optional[bytes] = None
            if "raw_hex" in payload:
                try:
                    data = bytes.fromhex(str(payload["raw_hex"]))
                except ValueError:
                    log.warning("cmd.raw_hex invalid: %r", payload["raw_hex"])
            elif "text" in payload:
                data = str(payload["text"]).encode("utf-8")
            else:
                slim = _compact_ble_mqtt_payload(payload)
                line = json.dumps(slim, separators=(",", ":")) + "\n"
                data = line.encode("utf-8")
            if data is not None:
                asyncio.run_coroutine_threadsafe(ble_recv.write(device_id, data), loop)
        elif device_type == "wifi" and wifi_recv is not None:
            ok = wifi_recv.write(device_id, payload)
            # #region agent log
            try:
                from debug_agent_log import agent_log

                agent_log(
                    "H_WIFI_TCP",
                    "main.py:on_command",
                    "wifi_write_result",
                    {
                        "device_id": device_id,
                        "ok": bool(ok),
                        "keys": sorted(str(k) for k in payload.keys()),
                    },
                )
            except Exception:
                pass
            # #endregion
            if not ok:
                log.warning("wifi command dropped (no live TCP): %s/%s", device_type, device_id)
        else:
            log.warning("unknown command target: %s/%s", device_type, device_id)

    # ---- MQTT 发布器 ------------------------------------------------- #
    from mqtt_publisher import MqttPublisher
    mqtt_pub = MqttPublisher(cfg, cache=cache, on_command=on_command)
    mqtt_pub.start()

    # 上行分发：适配器 -> MQTT
    def on_message(msg: Dict) -> None:
        log.info(
            "[up] %s/%s payload=%s",
            msg.get("device_type"), msg.get("device_id"), msg.get("payload"),
        )
        if cfg.admin_enabled:
            try:
                from admin_routes import note_device_seen

                note_device_seen(
                    str(msg.get("device_type") or ""),
                    str(msg.get("device_id") or ""),
                )
            except Exception:
                pass
        mqtt_pub.publish_unified(msg)

    # ---- Wi-Fi 适配器 ------------------------------------------------ #
    if cfg.wifi_enabled:
        from wifi_receiver import WifiReceiver
        wifi_recv = WifiReceiver(cfg, on_message=on_message)
        await wifi_recv.start()

    # ---- BLE 适配器 -------------------------------------------------- #
    if cfg.ble_enabled:
        from ble_receiver import BleReceiver
        ble_recv = BleReceiver(cfg, on_message=on_message)
        await ble_recv.start()

    # ---- 信号处理：优雅停机 ----------------------------------------- #
    stop_evt = asyncio.Event()

    def _handle_signal(signame: str) -> None:
        log.warning("received %s, shutting down ...", signame)
        stop_evt.set()

    loop = asyncio.get_running_loop()
    try:
        # Linux/Mac
        loop.add_signal_handler(signal.SIGINT, _handle_signal, "SIGINT")
        loop.add_signal_handler(signal.SIGTERM, _handle_signal, "SIGTERM")
    except NotImplementedError:
        # Windows 下不支持 add_signal_handler，退化为 KeyboardInterrupt
        pass

    log.info("gateway started. press Ctrl+C to stop.")
    try:
        await stop_evt.wait()
    except KeyboardInterrupt:
        pass

    # ---- 收尾 ------------------------------------------------------- #
    if ble_recv is not None:
        await ble_recv.stop()
    if wifi_recv is not None:
        await wifi_recv.stop()
    mqtt_pub.stop()
    if cache is not None:
        cache.close()
    log.info("gateway stopped cleanly.")


def main() -> None:
    cfg = parse_args()
    try:
        asyncio.run(amain(cfg))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
