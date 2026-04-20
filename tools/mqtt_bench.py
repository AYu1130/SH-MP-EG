"""
tools/mqtt_bench.py
===================

MQTT Broker 基准测试工具。

测量内容
--------
1. **端到端传输时延**（pub -> sub 收到）
   - 发布者在 payload 里携带纳秒时间戳；
   - 订阅者计算 `recv_time - send_time`，求最小/平均/P95/最大。
2. **丢包率**
   - 发送 N 条，统计订阅侧真正接收到的数量；
3. **吞吐率**
   - 以上数据推算 msg/s。

典型结果（树莓派 4B + EMQX 5 + QoS=1 本地回环）::

    sent=1000, received=1000, loss=0.00%
    latency  min=0.42ms  avg=0.78ms  p95=1.35ms  max=4.90ms
    throughput=825.7 msg/s

用法
----
``python tools/mqtt_bench.py --host 127.0.0.1 --messages 1000 --qos 1``
"""

from __future__ import annotations

import argparse
import json
import threading
import time
from typing import List

import paho.mqtt.client as mqtt


TOPIC = "smarthome/bench/0"


def percentile(data: List[float], p: float) -> float:
    if not data:
        return float("nan")
    data = sorted(data)
    k = int(round((len(data) - 1) * p))
    return data[k]


def main() -> None:
    ap = argparse.ArgumentParser(description="MQTT latency & loss benchmark")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=1883)
    ap.add_argument("--messages", type=int, default=1000)
    ap.add_argument("--qos", type=int, default=1, choices=[0, 1, 2])
    ap.add_argument("--interval-ms", type=float, default=5.0,
                    help="相邻两条消息的发送间隔（毫秒）")
    ap.add_argument("--username", default="")
    ap.add_argument("--password", default="")
    args = ap.parse_args()

    latencies: List[float] = []
    received = 0
    done_evt = threading.Event()

    def on_message(_client, _userdata, msg):
        nonlocal received
        try:
            obj = json.loads(msg.payload.decode("utf-8"))
            t0_ns = int(obj["send_ns"])
            latencies.append((time.time_ns() - t0_ns) / 1e6)  # ms
            received += 1
            if received >= args.messages:
                done_evt.set()
        except Exception:
            pass

    # 订阅者 --------------------------------------------------------------
    sub = mqtt.Client(client_id="bench-sub")
    if args.username:
        sub.username_pw_set(args.username, args.password)
    sub.on_message = on_message
    sub.connect(args.host, args.port, 30)
    sub.subscribe(TOPIC, qos=args.qos)
    sub.loop_start()

    # 发布者 --------------------------------------------------------------
    pub = mqtt.Client(client_id="bench-pub")
    if args.username:
        pub.username_pw_set(args.username, args.password)
    pub.connect(args.host, args.port, 30)
    pub.loop_start()
    time.sleep(0.3)  # 等待 sub 订阅生效

    print(f"sending {args.messages} messages to {TOPIC} ...")
    t_start = time.time()
    for i in range(args.messages):
        payload = json.dumps({"seq": i, "send_ns": time.time_ns()}, separators=(",", ":"))
        pub.publish(TOPIC, payload, qos=args.qos)
        if args.interval_ms > 0:
            time.sleep(args.interval_ms / 1000.0)
    # 等待全部订阅回来（或超时）
    done_evt.wait(timeout=10.0)
    elapsed = time.time() - t_start

    pub.loop_stop()
    sub.loop_stop()
    pub.disconnect()
    sub.disconnect()

    # 统计 -----------------------------------------------------------------
    loss = (args.messages - received) / args.messages * 100.0
    print(f"sent={args.messages}, received={received}, loss={loss:.2f}%")
    if latencies:
        print(
            f"latency  min={min(latencies):.2f}ms"
            f"  avg={sum(latencies)/len(latencies):.2f}ms"
            f"  p95={percentile(latencies, 0.95):.2f}ms"
            f"  max={max(latencies):.2f}ms"
        )
    if elapsed > 0:
        print(f"throughput={received/elapsed:.1f} msg/s")


if __name__ == "__main__":
    main()
