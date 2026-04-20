"""
examples/simple_http_sender/sender.py
=====================================

极简 HTTP 上报客户端，模拟 Wi-Fi 节点行为。

用法:
    python sender.py --host 192.168.1.10 --device-id demo-01 --count 10

可搭配 tests/performance/concurrency_test.py 观察网关的并发承载能力。
"""

from __future__ import annotations

import argparse
import random
import time

import requests


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--device-id", default="demo-node-01")
    ap.add_argument("--count", type=int, default=10)
    ap.add_argument("--interval", type=float, default=1.0, help="seconds between sends")
    args = ap.parse_args()

    url = f"http://{args.host}:{args.port}/api/v1/telemetry"
    for seq in range(args.count):
        body = {
            "id": args.device_id,
            "seq": seq,
            # 短字段风格，由网关的 normalize_wifi 展开
            "t": round(22 + random.gauss(2, 0.5), 1),
            "h": round(55 + random.gauss(0, 2), 1),
            "l": int(max(0, random.gauss(400, 80))),
        }
        try:
            r = requests.post(url, json=body, timeout=2.0)
            print(f"[{seq:03d}] {r.status_code} {r.text.strip()}")
        except Exception as e:
            print(f"[{seq:03d}] error: {e}")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
