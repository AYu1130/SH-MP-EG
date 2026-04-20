"""
端到端 / 基线 丢包率（传输效率）对比。

论文思路
--------
1. **基线（不含网关）**：测试进程直连 EMQX，以与网关相同的 ``telemetry/wifi/<id>``
   主题与统一 JSON 形态发布 QoS1 消息，订阅端按 ``seq`` 去重统计到达数。
2. **经网关路径**：HTTP ``POST /api/v1/telemetry`` → 网关 → MQTT，订阅端同样按 ``seq`` 统计。
3. **网关引入的丢包率（百分点差）**：``gateway_loss_pct - baseline_loss_pct``。
   文中应写清基线定义，避免与「经网关整体丢包」混用同一口径不加说明。

计量：按 **消息条数** 与 **seq 缺号**；每条为固定形态 JSON（体量由字段决定，非论文 4000B 大块）。

前置：EMQX 已启动；``gateway-http`` / ``both`` 模式需网关已运行。

CLI::

    python tests/performance/e2e_loss_test.py --mode baseline-mqtt --count 1000
    python tests/performance/e2e_loss_test.py --mode gateway-http --count 1000
    python tests/performance/e2e_loss_test.py --mode both --count 1000
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
import threading
import time
from typing import Dict, Set, Tuple

import paho.mqtt.client as mqtt

try:
    import requests
except ImportError:
    requests = None  # type: ignore


def _unified_payload(device_id: str, seq: int, transport: str) -> dict:
    return {
        "device_id": device_id,
        "device_type": "wifi",
        "transport": transport,
        "timestamp": int(time.time()),
        "status": "online",
        "payload": {
            "temperature": 25.0,
            "humidity": 50.0,
            "light": 100,
            "seq": seq,
        },
    }


def _telemetry_topic(prefix: str, device_id: str) -> str:
    return f"{prefix.rstrip('/')}/telemetry/wifi/{device_id}"


def _run_subscriber(
    mqtt_host: str,
    mqtt_port: int,
    topic: str,
    qos: int,
) -> Tuple[mqtt.Client, Set[int], threading.Lock]:
    got: Set[int] = set()
    lock = threading.Lock()

    def on_message(_c, _u, msg):
        try:
            obj = json.loads(msg.payload.decode("utf-8"))
            seq = int(obj["payload"]["seq"])
        except Exception:
            return
        with lock:
            got.add(seq)

    sub = mqtt.Client(client_id=f"e2e-loss-sub-{int(time.time()*1000)}")
    sub.on_message = on_message
    sub.connect(mqtt_host, mqtt_port, 30)
    sub.subscribe(topic, qos=qos)
    sub.loop_start()
    time.sleep(0.35)
    return sub, got, lock


def _loss_pct(expected: int, received_seqs: Set[int]) -> float:
    """``expected = N`` 表示 seq 合法区间为 ``0..N-1``，缺号计为丢失。"""
    if expected <= 0:
        return 0.0
    valid = {s for s in received_seqs if 0 <= s < expected}
    lost = expected - len(valid)
    return lost / expected * 100.0


def phase_baseline_mqtt(
    mqtt_host: str,
    mqtt_port: int,
    topic_prefix: str,
    device_id: str,
    count: int,
    qos: int,
    settle_s: float,
) -> Tuple[int, float]:
    topic = _telemetry_topic(topic_prefix, device_id)
    sub, got, _lock = _run_subscriber(mqtt_host, mqtt_port, topic, qos)
    pub = mqtt.Client(client_id=f"e2e-loss-pub-{device_id}")
    pub.connect(mqtt_host, mqtt_port, 30)
    pub.loop_start()
    time.sleep(0.2)
    sent_ok = 0
    for seq in range(count):
        payload = json.dumps(_unified_payload(device_id, seq, "mqtt"))
        info = pub.publish(topic, payload, qos=qos)
        if info.rc == mqtt.MQTT_ERR_SUCCESS:
            sent_ok += 1
        time.sleep(0.001)
    time.sleep(settle_s)
    pub.loop_stop()
    pub.disconnect()
    sub.loop_stop()
    sub.disconnect()
    loss = _loss_pct(count, got)
    return sent_ok, loss


def phase_gateway_http(
    http_host: str,
    http_port: int,
    mqtt_host: str,
    mqtt_port: int,
    topic_prefix: str,
    device_id: str,
    count: int,
    qos: int,
    settle_s: float,
) -> Tuple[int, float]:
    if requests is None:
        raise RuntimeError("需要 requests：pip install requests")
    url = f"http://{http_host}:{http_port}/api/v1/telemetry"
    topic = _telemetry_topic(topic_prefix, device_id)
    sub, got, _lock = _run_subscriber(mqtt_host, mqtt_port, topic, qos)
    sent_ok = 0
    for seq in range(count):
        body = {"id": device_id, "seq": seq, "t": 25.0, "h": 50.0, "l": 100}
        try:
            r = requests.post(url, json=body, timeout=3.0)
            if r.ok:
                sent_ok += 1
        except OSError:
            pass
        time.sleep(0.001)
    time.sleep(settle_s)
    sub.loop_stop()
    sub.disconnect()
    loss = _loss_pct(count, got)
    return sent_ok, loss


def phase_gateway_tcp(
    tcp_host: str,
    tcp_port: int,
    mqtt_host: str,
    mqtt_port: int,
    topic_prefix: str,
    device_id: str,
    count: int,
    qos: int,
    settle_s: float,
) -> Tuple[int, float]:
    topic = _telemetry_topic(topic_prefix, device_id)
    sub, got, _lock = _run_subscriber(mqtt_host, mqtt_port, topic, qos)
    sent_ok = 0
    sock = socket.create_connection((tcp_host, tcp_port), timeout=5.0)
    buf = b""
    try:
        for seq in range(count):
            line = json.dumps(
                {"id": device_id, "seq": seq, "t": 25.0, "h": 50.0, "l": 100}
            ) + "\n"
            sock.sendall(line.encode("utf-8"))
            while b"\n" not in buf:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                buf += chunk
            first, _, buf = buf.partition(b"\n")
            if b'"ok":true' in first or b'"ok": true' in first:
                sent_ok += 1
            time.sleep(0.001)
    finally:
        sock.close()
    time.sleep(settle_s)
    sub.loop_stop()
    sub.disconnect()
    loss = _loss_pct(count, got)
    return sent_ok, loss


def main() -> int:
    ap = argparse.ArgumentParser(
        description="E2E vs baseline MQTT loss rate (thesis-style delta)"
    )
    ap.add_argument(
        "--mode",
        choices=["baseline-mqtt", "gateway-http", "gateway-tcp", "both"],
        default="both",
    )
    ap.add_argument("--mqtt-host", default="127.0.0.1")
    ap.add_argument("--mqtt-port", type=int, default=1883)
    ap.add_argument("--topic-prefix", default="smarthome/v1", help="与网关 TOPIC_PREFIX 一致")
    ap.add_argument("--http-host", default="127.0.0.1")
    ap.add_argument("--http-port", type=int, default=8080)
    ap.add_argument("--tcp-host", default="127.0.0.1")
    ap.add_argument("--tcp-port", type=int, default=9000)
    ap.add_argument("--count", type=int, default=500, help="发送消息条数（seq 0..count-1）")
    ap.add_argument("--qos", type=int, default=1, choices=[0, 1, 2])
    ap.add_argument("--settle", type=float, default=2.0, help="发完后等待订阅落稳的秒数")
    ap.add_argument("--device-suffix", default="", help="设备名后缀，避免与他人测试冲突")
    args = ap.parse_args()

    suf = args.device_suffix or str(int(time.time()) % 100_000)
    dev_base = f"perf-e2e-{suf}"

    loss_baseline: float | None = None
    loss_gateway_http: float | None = None

    if args.mode in ("baseline-mqtt", "both"):
        dev_b = f"{dev_base}-baseline"
        sb, loss_baseline = phase_baseline_mqtt(
            args.mqtt_host,
            args.mqtt_port,
            args.topic_prefix,
            dev_b,
            args.count,
            args.qos,
            args.settle,
        )
        print(
            f"[baseline-mqtt] device_id={dev_b} sent_ok={sb}/{args.count} "
            f"loss_pct={loss_baseline:.4f}%  (不含网关，MQTT 发布+订阅路径)"
        )
    if args.mode in ("gateway-http", "both"):
        dev_g = f"{dev_base}-gateway-http"
        sg, loss_gateway_http = phase_gateway_http(
            args.http_host,
            args.http_port,
            args.mqtt_host,
            args.mqtt_port,
            args.topic_prefix,
            dev_g,
            args.count,
            args.qos,
            args.settle,
        )
        print(
            f"[gateway-http]  device_id={dev_g} sent_ok={sg}/{args.count} "
            f"loss_pct={loss_gateway_http:.4f}%  (HTTP→网关→MQTT)"
        )
    if args.mode == "gateway-tcp":
        dev_t = f"{dev_base}-gateway-tcp"
        st, lt = phase_gateway_tcp(
            args.tcp_host,
            args.tcp_port,
            args.mqtt_host,
            args.mqtt_port,
            args.topic_prefix,
            dev_t,
            args.count,
            args.qos,
            args.settle,
        )
        print(
            f"[gateway-tcp]   device_id={dev_t} sent_ok={st}/{args.count} "
            f"loss_pct={lt:.4f}%  (TCP→网关→MQTT)"
        )

    if args.mode == "both" and loss_baseline is not None and loss_gateway_http is not None:
        delta = loss_gateway_http - loss_baseline
        print(
            f"[delta] gateway_http_loss - baseline_mqtt_loss = {delta:+.4f} % "
            f"(正值表示相对纯 MQTT 基线，经网关路径多丢的比例点)"
        )
        if delta > 1.0:
            print("WARN: delta exceeds 1.0 percentage points (not auto-FAIL)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
