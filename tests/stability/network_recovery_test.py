"""
稳定性测试：断网恢复 / 本地缓存补传。

测试时序
--------
1. 确认网关进程运行，EMQX 运行，订阅端可接收；
2. 向网关持续注入遥测数据 T_pre 秒（基线）；
3. 调用 ``tools/network_simulator/simulate_break.sh break`` 阻断网关 -> Broker；
4. 继续注入 T_break 秒（此期间网关应把消息写入 SQLite cache）；
5. ``simulate_break.sh restore`` 恢复网络；
6. 再观察 T_post 秒，期待所有 seq 最终抵达订阅端（允许乱序）。

验收：最终**丢包率 = 0**（缓存补传成功），且订阅端收到所有 seq。

CLI:
    sudo python tests/stability/network_recovery_test.py \
         --iface eth0 --mqtt-host 127.0.0.1
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from typing import Set

import paho.mqtt.client as mqtt
import requests


SCRIPT = os.path.join(
    os.path.dirname(__file__), "..", "..", "tools", "network_simulator", "simulate_break.sh"
)


def sh(cmd: list[str]) -> int:
    """运行 shell 命令，打印 stderr 但不抛异常。"""
    print(f"$ {' '.join(cmd)}")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.stdout:
        print(r.stdout.rstrip())
    if r.returncode != 0 and r.stderr:
        print(r.stderr.rstrip(), file=sys.stderr)
    return r.returncode


def run(args) -> int:
    url = f"http://{args.http_host}:{args.http_port}/api/v1/telemetry"
    device_id = f"recov-node-{int(time.time())}"

    got: Set[int] = set()
    lock = threading.Lock()

    def on_message(_c, _u, msg):
        try:
            obj = json.loads(msg.payload.decode("utf-8"))
            seq = int(obj["payload"].get("seq", -1))
        except Exception:
            return
        with lock:
            got.add(seq)

    sub = mqtt.Client(client_id="recov-sub")
    sub.on_message = on_message
    sub.connect(args.mqtt_host, args.mqtt_port, 30)
    sub.subscribe(f"smarthome/v1/telemetry/wifi/{device_id}", qos=1)
    sub.loop_start()
    time.sleep(0.3)

    sent = 0
    stop_evt = threading.Event()

    def sender():
        nonlocal sent
        seq = 0
        interval = 1.0 / max(1e-3, args.rate)
        while not stop_evt.is_set():
            try:
                requests.post(url,
                              json={"id": device_id, "seq": seq, "t": 25, "h": 50, "l": 100},
                              timeout=2.0)
                sent += 1
            except Exception:
                pass
            seq += 1
            if interval > 0:
                time.sleep(interval)

    th = threading.Thread(target=sender, daemon=True)
    th.start()

    print(f"[phase 1] baseline {args.t_pre}s")
    time.sleep(args.t_pre)

    print(f"[phase 2] block MQTT to {args.mqtt_host} for {args.t_break}s")
    sh(["bash", SCRIPT, "break", args.mqtt_host])
    time.sleep(args.t_break)

    print("[phase 3] restore network")
    sh(["bash", SCRIPT, "restore", args.mqtt_host])

    print(f"[phase 4] post-recovery observe {args.t_post}s")
    time.sleep(args.t_post)

    stop_evt.set()
    th.join(timeout=2.0)

    # 给订阅端最后几秒收尾
    time.sleep(2.0)
    sub.loop_stop(); sub.disconnect()

    with lock:
        received = len(got)
    loss = (sent - received) / max(1, sent) * 100.0
    print(f"sent={sent}  received={received}  loss={loss:.2f}%")

    if loss > 0:
        print("FAIL: some messages were lost after recovery")
        return 1
    print("PASS: zero message loss after network recovery")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--http-host", default="127.0.0.1")
    ap.add_argument("--http-port", type=int, default=8080)
    ap.add_argument("--mqtt-host", default="127.0.0.1")
    ap.add_argument("--mqtt-port", type=int, default=1883)
    ap.add_argument("--rate", type=float, default=2.0)
    ap.add_argument("--t-pre", type=int, default=10)
    ap.add_argument("--t-break", type=int, default=20)
    ap.add_argument("--t-post", type=int, default=30)
    args = ap.parse_args()
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
