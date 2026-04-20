"""
examples/ble_serial_forward/forward.py
======================================

一个"BLE 串口透传"工具：

- 连接指定 MAC 的 HM-10 / BT05 / Nordic UART 设备；
- 订阅 notify characteristic，收到的字节按 UTF-8 打印；
- 从 stdin 读取一行字符串，写入 write characteristic（下行）。

本脚本**独立于网关运行**，主要用于开发/调试阶段验证 BLE 链路。
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from bleak import BleakClient  # type: ignore


# HM-10 默认 UART-over-GATT：0xFFE0 / 0xFFE1
DEFAULT_NOTIFY = "0000ffe1-0000-1000-8000-00805f9b34fb"


async def stdin_loop(client: BleakClient, char: str) -> None:
    """把 stdin 的行原样写到 BLE write char（下行）。"""
    loop = asyncio.get_event_loop()
    while True:
        line = await loop.run_in_executor(None, sys.stdin.readline)
        if not line:
            break
        data = line.rstrip("\n").encode("utf-8")
        try:
            await client.write_gatt_char(char, data, response=False)
            print(f"-> tx: {data!r}")
        except Exception as e:
            print(f"tx error: {e}", file=sys.stderr)


async def amain(address: str, char: str) -> None:
    print(f"connecting {address} ...")
    async with BleakClient(address) as client:
        print("connected.")
        def on_notify(_sender, data: bytearray) -> None:
            try:
                text = bytes(data).decode("utf-8", errors="replace")
            except Exception:
                text = bytes(data).hex()
            print(f"<- rx: {text}")
        await client.start_notify(char, on_notify)

        # 并发跑 stdin 发送
        await stdin_loop(client, char)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--address", required=True, help="BLE MAC or UUID")
    ap.add_argument("--char", default=DEFAULT_NOTIFY,
                    help="characteristic UUID for read/notify/write")
    args = ap.parse_args()
    try:
        asyncio.run(amain(args.address, args.char))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
