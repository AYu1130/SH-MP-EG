"""
稳定性测试：长时运行。

持续以固定速率向网关发送遥测，并周期性采样：

- 网关进程 ``rss``（若 psutil 可用）；
- 丢包计数；
- MQTT 订阅侧的消息间隔是否有异常；

验收：默认 24h 运行不崩溃、无明显内存泄漏（rss 增长 < 50%）。

CLI:
    python tests/stability/long_run_test.py --duration 3600
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from typing import Optional

import paho.mqtt.client as mqtt
import requests

try:
    import psutil  # type: ignore
except ImportError:
    psutil = None  # type: ignore


def find_gateway_process() -> Optional["psutil.Process"]:
    if psutil is None:
        return None
    for p in psutil.process_iter(["name", "cmdline"]):
        try:
            cmd = " ".join(p.info.get("cmdline") or [])
            if "main.py" in cmd and "software/gateway/python" in cmd.replace("\\", "/"):
                return p
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None


def run(args) -> int:
    url = f"http://{args.http_host}:{args.http_port}/api/v1/telemetry"
    end_time = time.time() + args.duration

    sub_received = 0
    last_seq = -1
    gap_events = 0
    lock = threading.Lock()

    def on_message(_c, _u, msg):
        nonlocal sub_received, last_seq, gap_events
        try:
            obj = json.loads(msg.payload.decode("utf-8"))
            seq = int(obj["payload"].get("seq", -1))
        except Exception:
            return
        with lock:
            if last_seq >= 0 and seq != last_seq + 1:
                gap_events += 1
            last_seq = seq
            sub_received += 1

    sub = mqtt.Client(client_id="stab-sub")
    sub.on_message = on_message
    sub.connect(args.mqtt_host, args.mqtt_port, 30)
    sub.subscribe(f"smarthome/v1/telemetry/wifi/{args.device_id}", qos=1)
    sub.loop_start()

    gw = find_gateway_process()
    rss_start = gw.memory_info().rss if gw else None
    print(
        f"long-run start: duration={args.duration}s rate={args.rate}/s "
        f"device={args.device_id} gateway_pid={gw.pid if gw else 'N/A'}"
    )

    sent = 0
    seq = 0
    interval = 1.0 / max(1e-3, args.rate)
    next_report = time.time() + args.report_interval

    try:
        while time.time() < end_time:
            body = {"id": args.device_id, "seq": seq, "t": 25, "h": 50, "l": 100}
            try:
                requests.post(url, json=body, timeout=2.0)
                sent += 1
            except Exception:
                pass
            seq += 1
            if interval > 0:
                time.sleep(interval)

            if time.time() >= next_report:
                with lock:
                    recv_now = sub_received
                    gap_now = gap_events
                rss_now = gw.memory_info().rss if gw else None
                rss_str = f" rss={rss_now/1024/1024:.1f}MB" if rss_now else ""
                loss = (sent - recv_now) / max(1, sent) * 100.0
                print(
                    f"[t+{int(time.time()-(end_time-args.duration))}s] "
                    f"sent={sent} recv={recv_now} loss={loss:.2f}% "
                    f"seq_gaps={gap_now}{rss_str}"
                )
                next_report = time.time() + args.report_interval
    except KeyboardInterrupt:
        print("interrupted by user")

    sub.loop_stop(); sub.disconnect()

    loss_pct = (sent - sub_received) / max(1, sent) * 100.0
    print(
        f"long-run end: sent={sent} received={sub_received} "
        f"loss={loss_pct:.2f}% seq_gaps={gap_events}"
    )
    if gw and rss_start:
        rss_end = gw.memory_info().rss
        growth = (rss_end - rss_start) / rss_start * 100.0
        print(f"rss: start={rss_start/1024/1024:.1f}MB "
              f"end={rss_end/1024/1024:.1f}MB growth={growth:+.1f}%")
        if growth > 50.0:
            print("FAIL: rss growth exceeds 50%")
            return 1
    if loss_pct > 1.0:
        print("FAIL: loss exceeds 1%")
        return 1
    print("PASS")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--http-host", default="127.0.0.1")
    ap.add_argument("--http-port", type=int, default=8080)
    ap.add_argument("--mqtt-host", default="127.0.0.1")
    ap.add_argument("--mqtt-port", type=int, default=1883)
    ap.add_argument("--device-id", default="stab-node-01")
    ap.add_argument("--duration", type=int, default=3600,
                    help="总运行秒数（默认 1 小时；答辩建议 24h=86400）")
    ap.add_argument("--rate", type=float, default=2.0)
    ap.add_argument("--report-interval", type=int, default=60,
                    help="控制台报告间隔秒数")
    args = ap.parse_args()
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
