"""
跨节点「互相通信」——**纯模拟数据** 的时延与丢包率测试。

本脚本 **不向真实 ESP/STM32 发 TCP/BLE**，只向 EMQX 发布 **合成的**
``smarthome/v1/telemetry/...`` JSON（与网关统一模型一致），因此 **无需
传感器/执行器在线**；仅需 **EMQX + 已导入 ``flows.json`` 的 Node-RED**
（规则会把 A 的遥测转成 B 的 command，并带回 ``src_seq``）。

设计
----
- 以 ``src_id`` 向 ``telemetry/<src_type>/<src_id>`` 发布带 ``seq`` 的载荷：
  Wi-Fi 侧默认 ``temperature`` 高于阈值触发；BLE 侧默认 ``d=1``、``l=0`` 触发暗光规则。
- 订阅 ``command/<dst_type>/<dst_id>``，在 payload 中匹配 ``src_seq``，
  计算 ``t_cmd_recv - t_telemetry_publish``（ms），统计 min/avg/P95/max；
  超时未配对计 **丢包**。

注意
----
- 度量的是 **遥测进 Broker → Node-RED → 命令出 Broker** 的联动时延，
  **不含** 网关把 MQTT 命令写到 TCP/BLE 物理链路的耗时。
- 默认先发一条 dst 的 **keepalive** 遥测，让 Node-RED ``cache_peer_id``
  缓存到 ``dst_id``；若你改 flow 为固定 ID，可加 ``--no-keepalive`` 跳过。

**真机端到端**（``--stop-at device``）：在 ``broker`` 基础上，订阅对端
``telemetry/<dst_type>/<dst_id>``，配对固件回传的 ``payload.cmd_ack``（ESP32）
或 ``payload.k``（STM32 / HM-10 短 JSON）。需 **网关** 在线且对端已通过
TCP/BLE 连接；固件须刷入带 ack 的版本。

CLI::

    python tests/performance/cross_node_relay_test.py \
        --direction wifi2ble --src-id esp32-s3-AAA --dst-id SHMPEG-BLE --count 30
    python tests/performance/cross_node_relay_test.py \
        --direction both --wifi-id esp32-s3-AAA --ble-id SHMPEG-BLE --count 30
    python tests/performance/cross_node_relay_test.py \
        --direction wifi2ble --stop-at device --src-id ... --dst-id ... --count 20
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import threading
import time
from typing import Dict, List, Literal, Tuple

import paho.mqtt.client as mqtt


def _telemetry_topic(prefix: str, dt: str, did: str) -> str:
    return f"{prefix.rstrip('/')}/telemetry/{dt}/{did}"


def _command_topic(prefix: str, dt: str, did: str) -> str:
    return f"{prefix.rstrip('/')}/command/{dt}/{did}"


def _make_unified(
    src_type: str,
    src_id: str,
    seq: int,
    *,
    wifi_temp_trigger: float,
) -> dict:
    payload: Dict[str, object] = {"seq": seq}
    if src_type == "wifi":
        payload.update(
            {
                "temperature": float(wifi_temp_trigger),
                "humidity": 50.0,
                "light": 100,
            }
        )
    else:
        payload.update({"light": 0, "d": 1, "l": 0})
    return {
        "device_id": src_id,
        "device_type": src_type,
        "transport": "test",
        "timestamp": int(time.time()),
        "status": "online",
        "payload": payload,
    }


def _make_dst_keepalive(dst_type: str, dst_id: str) -> dict:
    payload: Dict[str, object] = {"keepalive": True}
    return {
        "device_id": dst_id,
        "device_type": dst_type,
        "transport": "test",
        "timestamp": int(time.time()),
        "status": "online",
        "payload": payload,
    }


def _summarize(name: str, lat_ms: List[float], total: int, stop_at: str) -> int:
    matched = len(lat_ms)
    loss = (total - matched) / total * 100.0 if total > 0 else 0.0
    tag = "telemetry_e2e" if stop_at == "device" else "broker_cmd"
    if not lat_ms:
        print(
            f"{name} [{tag}]: matched={matched}/{total} loss_pct={loss:.2f}% "
            f"(no lat samples — check Node-RED rule / dst_id / gateway / firmware ack)"
        )
        return 1 if total > 0 else 0
    s = sorted(lat_ms)
    p95 = s[max(0, int(len(s) * 0.95) - 1)]
    avg = statistics.mean(lat_ms)
    print(
        f"{name} [{tag}]: matched={matched}/{total} loss_pct={loss:.2f}% "
        f"min={min(lat_ms):.2f}ms avg={avg:.2f}ms p95={p95:.2f}ms max={max(lat_ms):.2f}ms"
    )
    return 0


def run_direction(
    client: mqtt.Client,
    prefix: str,
    src_type: str,
    src_id: str,
    dst_type: str,
    dst_id: str,
    count: int,
    interval_ms: float,
    timeout_s: float,
    qos: int,
    *,
    wifi_temp_trigger: float,
    send_keepalive: bool,
    stop_at: Literal["broker", "device"],
) -> Tuple[List[float], int]:
    """单方向测试，返回 (lat_ms_list, total_attempted)。"""
    cmd_topic = _command_topic(prefix, dst_type, dst_id)
    src_topic = _telemetry_topic(prefix, src_type, src_id)
    dst_topic = _telemetry_topic(prefix, dst_type, dst_id)
    listen_topic = dst_topic if stop_at == "device" else cmd_topic

    pending: Dict[int, float] = {}
    lat_ms: List[float] = []
    lock = threading.Lock()
    events: Dict[int, threading.Event] = {}

    def on_message(_c, _u, msg):
        if msg.topic != listen_topic:
            return
        try:
            obj = json.loads(msg.payload.decode("utf-8"))
        except Exception:
            return
        if stop_at == "broker":
            seq = obj.get("src_seq")
        else:
            pl = obj.get("payload")
            if not isinstance(pl, dict):
                return
            seq = pl.get("cmd_ack")
            if seq is None:
                seq = pl.get("k")
        if seq is None:
            return
        try:
            seq_i = int(seq)
        except (TypeError, ValueError):
            return
        recv_ns = time.perf_counter_ns()
        with lock:
            t0 = pending.pop(seq_i, None)
            evt = events.pop(seq_i, None)
        if t0 is not None:
            lat_ms.append((recv_ns - t0) / 1e6)
        if evt is not None:
            evt.set()

    client.message_callback_add(listen_topic, on_message)
    client.subscribe(listen_topic, qos=qos)
    time.sleep(0.3)

    if send_keepalive:
        client.publish(dst_topic, json.dumps(_make_dst_keepalive(dst_type, dst_id)), qos=qos)
        time.sleep(0.2)

    for seq in range(count):
        msg = _make_unified(src_type, src_id, seq, wifi_temp_trigger=wifi_temp_trigger)
        evt = threading.Event()
        with lock:
            pending[seq] = time.perf_counter_ns()
            events[seq] = evt
        client.publish(src_topic, json.dumps(msg), qos=qos)
        evt.wait(timeout=timeout_s)
        if interval_ms > 0:
            time.sleep(interval_ms / 1000.0)

    # 兜底再等一会儿，把延迟到的 command / telemetry ack 收掉
    time.sleep(min(2.0, timeout_s))
    client.unsubscribe(listen_topic)
    client.message_callback_remove(listen_topic)
    return lat_ms, count


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Cross-node relay (A->Node-RED->B) latency & loss"
    )
    ap.add_argument("--mqtt-host", default="127.0.0.1")
    ap.add_argument("--mqtt-port", type=int, default=1883)
    ap.add_argument("--topic-prefix", default="smarthome/v1")
    ap.add_argument(
        "--direction",
        choices=["wifi2ble", "ble2wifi", "both"],
        default="both",
    )
    ap.add_argument("--src-id", default="", help="单方向时显式指定 src device_id")
    ap.add_argument("--dst-id", default="", help="单方向时显式指定 dst device_id")
    ap.add_argument("--wifi-id", default="", help="both 模式下 Wi-Fi 节点 device_id")
    ap.add_argument("--ble-id", default="", help="both 模式下 BLE 节点 device_id")
    ap.add_argument("--count", type=int, default=30)
    ap.add_argument("--interval-ms", type=float, default=300.0, help="两次触发的最小间隔")
    ap.add_argument("--timeout-s", type=float, default=3.0, help="单次配对超时")
    ap.add_argument("--qos", type=int, default=1, choices=[0, 1, 2])
    ap.add_argument(
        "--wifi-temp-trigger",
        type=float,
        default=99.0,
        help="模拟 Wi-Fi 遥测里的 temperature，须 >28 以触发 Node-RED 规则",
    )
    ap.add_argument(
        "--no-keepalive",
        action="store_true",
        help="不向 dst 发 keepalive 遥测（仅当你已改 flow 固定对端 ID 时使用）",
    )
    ap.add_argument(
        "--stop-at",
        choices=["broker", "device"],
        default="broker",
        help="broker=仅 MQTT command 主题；device=对端遥测里 cmd_ack/k（需网关+真机固件）",
    )
    args = ap.parse_args()

    client = mqtt.Client(client_id=f"relay-test-{int(time.time())}")
    client.connect(args.mqtt_host, args.mqtt_port, 30)
    client.loop_start()

    rc = 0
    try:
        if args.direction == "wifi2ble":
            if not args.src_id or not args.dst_id:
                print("error: --src-id and --dst-id are required for wifi2ble", file=sys.stderr)
                return 2
            lat, total = run_direction(
                client, args.topic_prefix,
                "wifi", args.src_id, "ble", args.dst_id,
                args.count, args.interval_ms, args.timeout_s, args.qos,
                wifi_temp_trigger=args.wifi_temp_trigger,
                send_keepalive=not args.no_keepalive,
                stop_at=args.stop_at,
            )
            rc |= _summarize("wifi2ble", lat, total, args.stop_at)
        elif args.direction == "ble2wifi":
            if not args.src_id or not args.dst_id:
                print("error: --src-id and --dst-id are required for ble2wifi", file=sys.stderr)
                return 2
            lat, total = run_direction(
                client, args.topic_prefix,
                "ble", args.src_id, "wifi", args.dst_id,
                args.count, args.interval_ms, args.timeout_s, args.qos,
                wifi_temp_trigger=args.wifi_temp_trigger,
                send_keepalive=not args.no_keepalive,
                stop_at=args.stop_at,
            )
            rc |= _summarize("ble2wifi", lat, total, args.stop_at)
        else:  # both
            if not args.wifi_id or not args.ble_id:
                print("error: --wifi-id and --ble-id are required for both", file=sys.stderr)
                return 2
            lat1, t1 = run_direction(
                client, args.topic_prefix,
                "wifi", args.wifi_id, "ble", args.ble_id,
                args.count, args.interval_ms, args.timeout_s, args.qos,
                wifi_temp_trigger=args.wifi_temp_trigger,
                send_keepalive=not args.no_keepalive,
                stop_at=args.stop_at,
            )
            rc |= _summarize("wifi2ble", lat1, t1, args.stop_at)
            lat2, t2 = run_direction(
                client, args.topic_prefix,
                "ble", args.ble_id, "wifi", args.wifi_id,
                args.count, args.interval_ms, args.timeout_s, args.qos,
                wifi_temp_trigger=args.wifi_temp_trigger,
                send_keepalive=not args.no_keepalive,
                stop_at=args.stop_at,
            )
            rc |= _summarize("ble2wifi", lat2, t2, args.stop_at)
            if lat1 and lat2:
                combo = statistics.mean(lat1) + statistics.mean(lat2)
                print(
                    f"round_trip_hint: avg_wifi2ble + avg_ble2wifi = {combo:.2f}ms "
                    f"(两段独立测量之和，非同一 seq 闭环)"
                )
    finally:
        client.loop_stop()
        client.disconnect()
    return rc


if __name__ == "__main__":
    sys.exit(main())
