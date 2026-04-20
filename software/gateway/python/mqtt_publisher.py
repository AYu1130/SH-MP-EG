"""
mqtt_publisher.py
=================

MQTT 发布 / 订阅客户端（基于 paho-mqtt）。

职责
----
1. 把网关整理后的 **统一 JSON 消息** 发布到 ``smarthome/v1/telemetry/...``；
2. 订阅 ``smarthome/v1/command/+/+`` 下行主题，并通过 ``on_command`` 回调
   把命令转发到具体协议（Wi-Fi/BLE）；
3. 断开重连 + 本地 SQLite 缓存补传，保证 **断网恢复** 验收项：
   - 连接失败时消息写入 cache；
   - 后台线程周期性尝试重连，连接恢复后按 FIFO 重发。

该模块对外暴露 :class:`MqttPublisher`，由 :mod:`main` 装配。
"""

from __future__ import annotations

import threading
import time
from typing import Callable, Dict, Optional

import paho.mqtt.client as mqtt

from cache import MessageCache
from config import GatewayConfig
from data_converter import to_json
from logger import get_logger


logger = get_logger(__name__)


# 下行命令回调签名: (device_type, device_id, payload_dict) -> None
OnCommand = Callable[[str, str, Dict], None]


class MqttPublisher:
    """MQTT 客户端封装。线程安全的发布接口 + 后台重发。"""

    def __init__(
        self,
        cfg: GatewayConfig,
        cache: Optional[MessageCache] = None,
        on_command: Optional[OnCommand] = None,
    ) -> None:
        self._cfg = cfg
        self._cache = cache
        self._on_command = on_command

        self._connected = threading.Event()
        self._stop_evt = threading.Event()

        # paho-mqtt v1 API（v2 的回调签名略有不同，这里用 v1 兼容）
        self._client = mqtt.Client(
            client_id=cfg.mqtt_client_id,
            clean_session=True,
            protocol=mqtt.MQTTv311,
        )
        if cfg.mqtt_username:
            self._client.username_pw_set(cfg.mqtt_username, cfg.mqtt_password)

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_mqtt_message

        # 遗言：宣告网关离线
        lwt_topic = f"{cfg.topic_prefix}/status/gateway/{cfg.mqtt_client_id}"
        self._client.will_set(
            lwt_topic,
            payload=to_json(
                {
                    "device_id": cfg.mqtt_client_id,
                    "device_type": "gateway",
                    "transport": "mqtt",
                    "timestamp": int(time.time()),
                    "status": "offline",
                    "payload": {},
                }
            ),
            qos=1,
            retain=True,
        )

        self._retry_thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------ #
    # 生命周期
    # ------------------------------------------------------------------ #
    def start(self) -> None:
        """启动 MQTT 连接与后台重发线程。"""
        logger.info("connecting MQTT %s:%d ...", self._cfg.mqtt_host, self._cfg.mqtt_port)
        # connect_async 不阻塞，loop_start 使用独立线程跑 select
        self._client.connect_async(
            host=self._cfg.mqtt_host,
            port=self._cfg.mqtt_port,
            keepalive=self._cfg.mqtt_keepalive,
        )
        self._client.loop_start()

        if self._cache is not None:
            self._retry_thread = threading.Thread(
                target=self._retry_loop, name="mqtt-retry", daemon=True
            )
            self._retry_thread.start()

    def stop(self) -> None:
        logger.info("stopping MqttPublisher ...")
        self._stop_evt.set()
        try:
            self._client.loop_stop()
            self._client.disconnect()
        except Exception:
            pass
        if self._retry_thread is not None:
            self._retry_thread.join(timeout=2.0)
        logger.info("MqttPublisher stopped")

    # ------------------------------------------------------------------ #
    # 对外：发布
    # ------------------------------------------------------------------ #
    def publish_unified(self, message: Dict) -> None:
        """发布一条已校验的统一 JSON 消息到 telemetry 主题。"""
        topic = self._cfg.telemetry_topic(
            device_type=str(message["device_type"]),
            device_id=str(message["device_id"]),
        )
        self.publish(topic, to_json(message), qos=self._cfg.mqtt_qos)

    def publish(self, topic: str, payload: str, qos: int = 1, retain: bool = False) -> None:
        """通用发布接口；离线时写入本地缓存。"""
        if not self._connected.is_set():
            if self._cache is not None:
                cache_id = self._cache.push(topic, payload, qos)
                logger.warning(
                    "mqtt offline, cached msg id=%d topic=%s (queue=%d)",
                    cache_id, topic, self._cache.size(),
                )
            else:
                logger.warning("mqtt offline, no cache, drop msg topic=%s", topic)
            return

        info = self._client.publish(topic, payload, qos=qos, retain=retain)
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            logger.warning("mqtt publish rc=%d topic=%s", info.rc, topic)
            if self._cache is not None:
                self._cache.push(topic, payload, qos)

    # ------------------------------------------------------------------ #
    # paho 回调
    # ------------------------------------------------------------------ #
    def _on_connect(self, client, userdata, flags, rc) -> None:
        if rc == 0:
            self._connected.set()
            logger.info("mqtt connected (rc=%d)", rc)
            # 订阅下行命令主题
            topic = self._cfg.command_topic_wildcard()
            client.subscribe(topic, qos=self._cfg.mqtt_qos)
            logger.info("mqtt subscribed: %s", topic)

            # 发布网关在线状态（retain）
            status_topic = f"{self._cfg.topic_prefix}/status/gateway/{self._cfg.mqtt_client_id}"
            client.publish(
                status_topic,
                payload=to_json(
                    {
                        "device_id": self._cfg.mqtt_client_id,
                        "device_type": "gateway",
                        "transport": "mqtt",
                        "timestamp": int(time.time()),
                        "status": "online",
                        "payload": {},
                    }
                ),
                qos=1,
                retain=True,
            )
        else:
            self._connected.clear()
            logger.error("mqtt connect failed rc=%d", rc)

    def _on_disconnect(self, client, userdata, rc) -> None:
        self._connected.clear()
        logger.warning("mqtt disconnected rc=%d, will auto-reconnect", rc)

    def _on_mqtt_message(self, client, userdata, msg) -> None:
        """收到下行命令时调用；解析并派发给上层 on_command。"""
        try:
            topic = msg.topic
            # Topic: <prefix>/command/<device_type>/<device_id>
            parts = topic.split("/")
            if len(parts) < 5 or parts[-3] != "command":
                logger.debug("mqtt unexpected topic: %s", topic)
                return
            device_type = parts[-2]
            device_id = parts[-1]
            try:
                import json as _json
                payload = _json.loads(msg.payload.decode("utf-8"))
                if not isinstance(payload, dict):
                    raise ValueError("payload must be object")
            except Exception as e:
                logger.warning("mqtt command json error: %s", e)
                return
            logger.info("mqtt command -> %s/%s: %s", device_type, device_id, payload)
            if self._on_command is not None:
                self._on_command(device_type, device_id, payload)
        except Exception:
            logger.exception("mqtt on_message handler error")

    # ------------------------------------------------------------------ #
    # 缓存重发
    # ------------------------------------------------------------------ #
    def _retry_loop(self) -> None:
        """周期性从缓存里取出消息重发。"""
        assert self._cache is not None
        interval = max(0.5, self._cfg.cache_retry_interval_s)
        while not self._stop_evt.is_set():
            if self._connected.is_set() and self._cache.size() > 0:
                rows = self._cache.peek(limit=100)
                ok_ids = []
                for _id, topic, payload, qos in rows:
                    info = self._client.publish(topic, payload, qos=qos)
                    if info.rc == mqtt.MQTT_ERR_SUCCESS:
                        ok_ids.append(_id)
                    else:
                        # 遇到发送错误中断本轮，避免持续失败刷日志
                        break
                if ok_ids:
                    self._cache.delete(ok_ids)
                    logger.info("mqtt resent %d cached msgs, remaining=%d",
                                len(ok_ids), self._cache.size())
            # sleep 支持被 stop_evt 提前唤醒
            self._stop_evt.wait(interval)
