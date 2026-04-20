"""
tools/serial_monitor.py
=======================

简易串口监视 / 交互工具（基于 pyserial）。

用途
----
- 盯 ESP32-S3 串口日志：``python serial_monitor.py --port COM5 --baud 115200``
- 给 STM32 发送 AT 命令：按 ``CTRL+T`` 后粘贴命令再回车（简单实现，仅示例）

对比 PuTTY/screen 的好处：
1. 跨平台一致；
2. 可以记录日志到文件（``--log``）；
3. 方便集成到 CI / 自动化测试。
"""

from __future__ import annotations

import argparse
import sys
import threading
import time
from typing import Optional

try:
    import serial  # type: ignore
except ImportError:
    print("ERROR: 需要 pyserial，请执行 pip install pyserial", file=sys.stderr)
    sys.exit(1)


def _reader(ser: "serial.Serial", logfile: Optional[object]) -> None:
    """后台线程：持续读串口并打印 / 落盘。"""
    while True:
        try:
            data = ser.readline()
        except Exception as e:
            print(f"[reader error] {e}", file=sys.stderr)
            return
        if not data:
            continue
        text = data.decode("utf-8", errors="replace").rstrip("\r\n")
        ts = time.strftime("%H:%M:%S")
        line = f"[{ts}] {text}"
        print(line)
        if logfile is not None:
            logfile.write(line + "\n")
            logfile.flush()


def main() -> None:
    p = argparse.ArgumentParser(description="Simple serial monitor")
    p.add_argument("--port", required=True, help="串口号，如 COM5 / /dev/ttyUSB0")
    p.add_argument("--baud", type=int, default=115200)
    p.add_argument("--log", help="把所有输出追加写入该文件")
    args = p.parse_args()

    ser = serial.Serial(args.port, args.baud, timeout=0.2)
    print(f"opened {args.port} @ {args.baud}, Ctrl+C to quit")

    log_fp = open(args.log, "a", encoding="utf-8") if args.log else None
    t = threading.Thread(target=_reader, args=(ser, log_fp), daemon=True)
    t.start()

    try:
        while True:
            # 从 stdin 读入一行，回写给串口（方便发送 AT 命令）
            try:
                line = input()
            except EOFError:
                break
            ser.write((line + "\n").encode("utf-8"))
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()
        if log_fp is not None:
            log_fp.close()


if __name__ == "__main__":
    main()
