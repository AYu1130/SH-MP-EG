# 示例：简易 HTTP 发送器

对应两段示例代码：

1. `sender.py` — Python 版（可在 PC / Pi / 带 MicroPython 的 MCU 运行）；
2. `sender_arduino.ino` — Arduino / ESP32 风格伪代码，MCU 同学可直接参考改写。

这两份**只给出网络层调用示范**，不涉及真实传感器；目的在于验证
网关 `/api/v1/telemetry` 接口的通路。
