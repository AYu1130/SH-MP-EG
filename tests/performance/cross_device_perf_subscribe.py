"""
跨设备性能观测：在树莓派/PC 上订阅 MQTT，统计时延与丢包。

适用场景
--------
- **Wi‑Fi（ESP32 TCP/HTTP）**：终端在 JSON 中携带 ``send_ns``（Unix 纳秒，需 NTP 对时）
  与 ``seq``；本脚本计算 ``recv_ns - send_ns`` 得到近似端到端时延。
- **BLE**：若广播/GATT JSON 中含 ``send_ns`` 与 ``seq``，统计方式相同；否则仅统计
  到达率与到达间隔（不输出时延列）。

与 ``e2e_latency_test.py`` 的区别：本脚本**不**向网关发 HTTP，只被动订阅，适合
真实 ESP/BLE 设备已向网关推数时的现场测试。

CLI::

    python tests/performance/cross_device_perf_subscribe.py --path wifi --duration 60
    python tests/performance/cross_device_perf_subscribe.py --path ble --device-id SHMPEG-BLE
"""

from __future__ import annotations

import argparse
import json
import signal
import statistics
import sys
import time
from typing import Optional, Set, Tuple

import paho.mqtt.client as mqtt


def _parse_seq_payload(obj: dict) -> Tuple[Optional[int], Optional[int]]:
    """返回 (seq, send_ns) 若存在。"""
    try:
        pl = obj.get("payload") or {}
        seq = pl.get("seq")
        send_ns = pl.get("send_ns")
        if seq is None:
            return None, None
        return int(seq), int(send_ns) if send_ns is not None else None
    except (TypeError, ValueError):
        return None, None


def run(
    mqtt_host: str,
    mqtt_port: int,
    topic: str,
    qos: int,
    duration_s: float,
    device_filter: str,
) -> int:
    lat_ms: list[float] = []
    seen_seq: Set[int] = set()
    min_seq: Optional[int] = None
    max_seq = -1
    msg_count = 0
    stop = {"done": False}

    def on_message(_c, _u, msg):
        nonlocal min_seq, max_seq, msg_count
        if stop["done"]:
            return
        try:
            obj = json.loads(msg.payload.decode("utf-8"))
        except Exception:
            return
        did = str(obj.get("device_id", ""))
        if device_filter and did != device_filter:
            return
        seq, send_ns = _parse_seq_payload(obj)
        msg_count += 1
        recv_ns = time.time_ns()
        if seq is not None:
            seen_seq.add(seq)
            min_seq = seq if min_seq is None else min(min_seq, seq)
            max_seq = max(max_seq, seq)
        if send_ns is not None and send_ns > 0:
            lat_ms.append((recv_ns - send_ns) / 1e6)

    client = mqtt.Client(client_id=f"cross-sub-{int(time.time())}")
    client.on_message = on_message
    client.connect(mqtt_host, mqtt_port, 30)
    client.subscribe(topic, qos=qos)
    client.loop_start()

    def _sig(_a, _b):
        stop["done"] = True

    signal.signal(signal.SIGINT, _sig)
    signal.signal(signal.SIGTERM, _sig)

    t0 = time.time()
    while time.time() - t0 < duration_s and not stop["done"]:
        time.sleep(0.2)

    stop["done"] = True
    time.sleep(0.3)
    client.loop_stop()
    client.disconnect()

    print(f"topic={topic} messages={msg_count} duration_s={duration_s:.1f}")
    if max_seq >= 0 and min_seq is not None:
        # 订阅窗口可能从任意 seq 开始，不应默认从 0 起算。
        expected = max_seq - min_seq + 1
        missing = max(0, expected - len(seen_seq))
        loss_pct = (missing / expected * 100.0) if expected > 0 else 0.0
        print(
            f"seq range {min_seq}..{max_seq} unique_seq={len(seen_seq)} "
            f"missing~{missing} loss_pct~{loss_pct:.3f}%"
        )
    if lat_ms:
        s = sorted(lat_ms)
        p95 = s[max(0, int(len(s) * 0.95) - 1)]
        print(
            f"latency_ms (send_ns in payload): n={len(lat_ms)} "
            f"min={min(lat_ms):.2f} avg={statistics.mean(lat_ms):.2f} "
            f"p95={p95:.2f} max={max(lat_ms):.2f}"
        )
    else:
        print(
            "no send_ns in payload — enable NTP on device and add send_ns to JSON "
            "(see esp32-s3 main.cpp) for cross-clock latency."
        )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Subscribe-side cross-device perf")
    ap.add_argument("--mqtt-host", default="127.0.0.1")
    ap.add_argument("--mqtt-port", type=int, default=1883)
    ap.add_argument(
        "--path",
        choices=["wifi", "ble", "all"],
        default="wifi",
        help="订阅 smarthome/v1/telemetry/wifi|ble/# 或两者",
    )
    ap.add_argument("--topic-prefix", default="smarthome/v1")
    ap.add_argument("--duration", type=float, default=60.0)
    ap.add_argument("--qos", type=int, default=1, choices=[0, 1, 2])
    ap.add_argument("--device-id", default="", help="仅统计该 device_id")
    args = ap.parse_args()
    pfx = args.topic_prefix.rstrip("/")
    if args.path == "wifi":
        topic = f"{pfx}/telemetry/wifi/#"
    elif args.path == "ble":
        topic = f"{pfx}/telemetry/ble/#"
    else:
        topic = f"{pfx}/telemetry/#"
    return run(
        args.mqtt_host,
        args.mqtt_port,
        topic,
        args.qos,
        args.duration,
        args.device_id,
    )


if __name__ == "__main__":
    sys.exit(main())
