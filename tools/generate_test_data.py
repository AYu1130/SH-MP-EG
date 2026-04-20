"""
tools/generate_test_data.py
===========================

向网关灌入**模拟节点数据**，用于功能 / 性能验证。

支持三种协议目标：

- ``--protocol wifi_http`` (默认)：POST JSON 到 ``/api/v1/telemetry``；
- ``--protocol wifi_tcp``       ：建立 TCP 连接后按行写 JSON；
- ``--protocol mqtt``           ：绕过适配器，直接发到 EMQX，用于对比。

示例
----
.. code-block:: bash

    # 以 10 Hz 连续灌 60 条 Wi-Fi HTTP 数据
    python tools/generate_test_data.py --protocol wifi_http --count 60 --rate 10

    # 模拟大量设备并发
    python tools/generate_test_data.py --devices 20 --count 100 --rate 20
"""

from __future__ import annotations

import argparse
import json
import random
import socket
import sys
import threading
import time
from typing import Any, Dict

try:
    import requests  # type: ignore
except ImportError:
    requests = None

try:
    import paho.mqtt.client as mqtt  # type: ignore
except ImportError:
    mqtt = None  # type: ignore


def make_payload(device_id: str, seq: int) -> Dict[str, Any]:
    """生成一条模拟测量数据。温/湿/光带轻微随机扰动。"""
    return {
        "id": device_id,
        "seq": seq,
        # 短字段，匹配 data_converter.normalize_wifi 的别名表
        "t": round(22 + random.gauss(2, 0.8), 2),
        "h": round(55 + random.gauss(0, 3), 2),
        "l": int(max(0, random.gauss(400, 120))),
        "ts": int(time.time()),
    }


# --------------------------------------------------------------------------- #
# 发送实现
# --------------------------------------------------------------------------- #
def send_http(host: str, port: int, body: Dict[str, Any]) -> bool:
    if requests is None:
        raise RuntimeError("requests 未安装，请 pip install requests")
    url = f"http://{host}:{port}/api/v1/telemetry"
    try:
        r = requests.post(url, json=body, timeout=2.0)
        return r.ok
    except Exception as e:
        print(f"http error: {e}", file=sys.stderr)
        return False


def send_tcp(sock: socket.socket, body: Dict[str, Any]) -> bool:
    try:
        sock.sendall((json.dumps(body) + "\n").encode("utf-8"))
        return True
    except Exception as e:
        print(f"tcp error: {e}", file=sys.stderr)
        return False


def send_mqtt(client: "mqtt.Client", device_id: str, body: Dict[str, Any]) -> bool:
    # 将 make_payload 的短字段手动展开成统一 JSON，使 test 更贴近真实网关发布
    unified = {
        "device_id": device_id,
        "device_type": "wifi",
        "transport": "mqtt",
        "timestamp": int(time.time()),
        "status": "online",
        "payload": {
            "temperature": body["t"],
            "humidity": body["h"],
            "light": body["l"],
        },
    }
    topic = f"smarthome/v1/telemetry/wifi/{device_id}"
    info = client.publish(topic, json.dumps(unified), qos=1)
    return info.rc == mqtt.MQTT_ERR_SUCCESS


# --------------------------------------------------------------------------- #
# 工作线程
# --------------------------------------------------------------------------- #
def device_worker(protocol: str, device_idx: int, args, stats: Dict[str, int]) -> None:
    device_id = f"{args.id_prefix}{device_idx:02d}"
    interval = 1.0 / max(1e-3, args.rate)

    # 为 tcp/mqtt 预先建立长连接
    sock: socket.socket = None  # type: ignore
    mqtt_client = None
    if protocol == "wifi_tcp":
        sock = socket.create_connection((args.host, args.tcp_port), timeout=5.0)
    elif protocol == "mqtt":
        if mqtt is None:
            raise RuntimeError("paho-mqtt 未安装")
        mqtt_client = mqtt.Client(client_id=f"gen-{device_id}")
        mqtt_client.connect(args.mqtt_host, args.mqtt_port, 30)
        mqtt_client.loop_start()

    try:
        for seq in range(args.count):
            body = make_payload(device_id, seq)
            ok = False
            if protocol == "wifi_http":
                ok = send_http(args.host, args.http_port, body)
            elif protocol == "wifi_tcp":
                ok = send_tcp(sock, body)
            elif protocol == "mqtt":
                ok = send_mqtt(mqtt_client, device_id, body)
            stats["sent"] += 1
            stats["ok" if ok else "fail"] += 1
            if interval > 0:
                time.sleep(interval)
    finally:
        if sock is not None:
            sock.close()
        if mqtt_client is not None:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate simulated telemetry data")
    ap.add_argument("--protocol", choices=["wifi_http", "wifi_tcp", "mqtt"],
                    default="wifi_http")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--http-port", type=int, default=8080)
    ap.add_argument("--tcp-port", type=int, default=9000)
    ap.add_argument("--mqtt-host", default="127.0.0.1")
    ap.add_argument("--mqtt-port", type=int, default=1883)

    ap.add_argument("--count", type=int, default=10, help="每个设备发送条数")
    ap.add_argument("--rate", type=float, default=1.0, help="每秒发送多少条")
    ap.add_argument("--devices", type=int, default=1, help="并发设备数")
    ap.add_argument("--id-prefix", default="gen-node-")
    args = ap.parse_args()

    stats = {"sent": 0, "ok": 0, "fail": 0}
    threads = []
    t0 = time.time()
    for i in range(args.devices):
        t = threading.Thread(
            target=device_worker,
            args=(args.protocol, i, args, stats),
            daemon=True,
        )
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    elapsed = time.time() - t0

    print(
        f"done protocol={args.protocol} devices={args.devices} "
        f"sent={stats['sent']} ok={stats['ok']} fail={stats['fail']} "
        f"elapsed={elapsed:.2f}s"
    )


if __name__ == "__main__":
    main()
