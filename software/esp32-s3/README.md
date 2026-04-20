# ESP32-S3 Wi-Fi 终端节点固件

基于 PlatformIO + Arduino 框架实现，目标：
- 采集 DHT11 温湿度（GPIO4）；
- 通过 Wi-Fi + TCP 上报扁平 JSON 行到网关 `wifi_receiver`（默认 9000）；
- 本地温度越限本地点亮 RGB LED 红色（共阴模块，R=GPIO7、G=GPIO6、B=GPIO5）；
- 接收网关 / Node-RED 下行 `{"led":...}` / `{"blink":...}` / `{"auto":true}` 命令。

## 目录结构

```
software/esp32-s3/
├── platformio.ini         # PIO 配置
├── include/
│   └── sensors.h          # DHT11 + RGB LED API
└── src/
    ├── sensors.cpp        # DHT11 采样 + 共阴 RGB LED 控制 + 非阻塞 blink
    └── main.cpp           # Wi-Fi/TCP 长连接 + 协议帧 + 本地阈值规则 + 远程命令
```

## 关键宏 / 配置

| 位置 | 宏 / 变量 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `sensors.h` | `PIN_DHT` | 4 | DHT11 数据脚 |
| `sensors.h` | `PIN_LED_R / G / B` | 7 / 6 / 5 | 共阴 RGB LED 三通道 |
| `sensors.h` | `LED_ACTIVE_HIGH` | 1 | 0 表示共阳模块（高电平=灭） |
| `sensors.h` | `DHT_TYPE` | 11 | 可改 `22` 使用 DHT22 |
| `main.cpp` | `WIFI_SSID` / `WIFI_PASSWORD` | `gateway` / `12345678` | 树莓派热点账号 |
| `main.cpp` | `GATEWAY_IP` / `GATEWAY_PORT` | `10.42.0.1:9000` | 树莓派 **NetworkManager 热点**（`wlan1` 常见 `10.42.0.1`）；若用 **hostapd** 多为 `192.168.4.1` |
| `main.cpp` | `SAMPLE_INTERVAL_MS` | 5000 | 上报周期（DHT11 ≥ 1s） |
| `main.cpp` | `TEMP_ALARM_HIGH / LOW` | 30 / 29 | 本地 LED 报警阈值，1℃ 滞回 |
| `main.cpp` | `WiFi.setSleep(false)` | 连接成功后调用 | 关闭 Wi-Fi Modem sleep，降低突发时延 |

## 编译 / 烧录

```powershell
pip install -U platformio
cd software\esp32-s3
pio run
pio run --target upload
pio device monitor
```

## 上行 JSON（扁平，对接 `wifi_receiver` + `normalize_wifi`）

```
{"id":"esp32-s3-abc123","seq":17,"t":25.0,"h":56.0,"battery":100,"alarm":false,"rssi":-58,"ts":1713333333,"send_ns":1713333333123456789}
```

- `seq` 用于 **丢包统计**；
- `send_ns` 在 SNTP 同步成功后写入，用于 **跨设备时延**（见 `tests/performance/cross_device_perf_subscribe.py`）；
- 网关会把未识别字段原样透传到统一 JSON 的 `payload`。

## 下行命令（一行 JSON，结尾 `\n`）

| 命令 | 效果 |
| --- | --- |
| `{"led":"red"}` / `green` / `blue` / `yellow` / `cyan` / `magenta` / `white` / `off` | 立即设置颜色 |
| `{"blink":{"color":"red","on":200,"off":200,"n":3}}` | 非阻塞闪烁 |
| `{"auto":true}` | 释放远程接管，恢复本地阈值规则 |

若命令 JSON 中含 **`src_seq`**（Node-RED 跨节点联动会带），固件在执行 `led` / `blink` 后会**立刻**再发一行上行 JSON，例如 `{"id":"...","cmd_ack":12,"ts":...}`，用于 `tests/performance/cross_node_relay_test.py --stop-at device` 统计端到端时延。

> 网关 `wifi_receiver.WifiReceiver.write` 已实现 **device_id → TCP writer** 映射，
> Node-RED 发布 `smarthome/v1/command/wifi/<device_id>` 时网关会自动写入对应连接。

## 本地边缘智能

- DHT11 采样 + 温度越限本地 LED 红色，正常熄灭（不依赖云端，端到端 ≈ 采样周期）；
- Wi-Fi / TCP 指数退避重连；
- 上电自检蓝色闪 2 下提示硬件正常。

## 故障排查

| 现象 | 可能原因 | 处理 |
| --- | --- | --- |
| 串口持续 `[dht] read failed` | 接线错 / 供电不足 / 间隔 < 1s | 检查 VCC/GND，确认 `SAMPLE_INTERVAL_MS ≥ 1100` |
| 连不上网关 `[tcp] connect failed` | 端口/IP 不对、网关未启动、防火墙 | 确认 `GATEWAY_PORT` == 网关 `wifi_tcp_port` |
| LED 永远不亮 / 反向 | 模块是共阳 | 把 `LED_ACTIVE_HIGH` 设为 0 |
| 没有 `send_ns` | SNTP 未同步 | 等串口出现 `[ntp] wall clock ok` 后再统计时延 |
| 接错的热点 | 用户配置错误 | 修改 `WIFI_SSID/PASSWORD` 后重烧 |
