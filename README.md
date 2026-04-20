# SH-MP-EG: 面向智能家居的多协议边缘智能网关

> Smart-Home Multi-Protocol Edge-Intelligent Gateway
>
> 本科毕业设计项目 — 以树莓派 4B 作为网关核心，集成 Wi-Fi / BLE / MQTT 多协议接入，
> 通过统一 JSON 数据模型、本地 MQTT 代理（EMQX）与 Node-RED 规则引擎实现
> 异构智能家居设备的透明接入、协议转换和边缘自治联动。

---

## 1. 项目简介

本项目属于**感知层 — 边缘层 — 网络层 — 应用层**四层智能家居系统的
**边缘网关侧实现**。设计目标：

- **多协议接入**：支持 Wi-Fi (TCP/HTTP) 与 BLE (GATT) 两类感知层节点；
  预留 ZigBee / LoRa 等扩展接口；
- **统一协议转换**：在网关侧把异构报文解析为**统一 JSON 数据模型**，
  通过规范化 MQTT Topic (`smarthome/v1/...`) 发布；
- **边缘自治联动**：Node-RED + 本地 EMQX 代理 + SQLite 离线缓存，
  断网仍可运行本地规则并在恢复后补传数据；
- **关键性能指标**：
  - 本地控制响应时间 ≤ 500 ms
  - MQTT 传输时延 ≤ 200 ms
  - 丢包率 ≤ 1%（在正常局域网环境下）

## 2. 系统架构

```plaintext
┌─────────────────────────────────────────────────────────────┐
│                      应用层 (Application)                   │
│   上位机 Web UI   |   Node-RED 规则引擎 / Dashboard         │
└─────────────────────────────────────────────────────────────┘
                              ▲  MQTT / HTTP
┌─────────────────────────────────────────────────────────────┐
│                      网络层 (Network)                        │
│                MQTT Broker (EMQX, Docker)                    │
└─────────────────────────────────────────────────────────────┘
                              ▲  统一 JSON
┌─────────────────────────────────────────────────────────────┐
│                    边缘层 (Edge Gateway)                     │
│   Wi-Fi 适配器(Flask/asyncio) | BLE 适配器(bleak) |          │
│   数据融合与协议转换 | 本地缓存 | 下行命令路由               │
└─────────────────────────────────────────────────────────────┘
                              ▲  Wi-Fi / BLE
┌─────────────────────────────────────────────────────────────┐
│                    感知层 (Perception)                       │
│   ESP32-S3（温湿度+蜂鸣器）   STM32F103+HM-10（GY-302+LED）   │
└─────────────────────────────────────────────────────────────┘
```

详细设计见 [`docs/architecture/system_architecture.md`](docs/architecture/system_architecture.md)。

## 3. 目录结构

```text
SH-MP-EG/
├── hardware/           硬件原理图与器件资料
├── software/
│   ├── gateway/        网关(树莓派)程序
│   │   ├── python/     Python 协议适配 + 数据融合
│   │   ├── node-red/   Node-RED 规则流
│   │   └── mqtt-broker/ EMQX 部署配置
│   ├── esp32-s3/       Wi-Fi 节点固件 (PlatformIO)
│   └── stm32f103/      BLE 节点固件 (PlatformIO)
├── tools/              串口监视 / MQTT 压测 / 网络模拟
├── tests/              功能 / 性能 / 稳定性测试脚本
├── docs/               架构、接口、部署文档
├── examples/           简单收发示例
└── images/             架构图、截图等
```

## 4. 快速开始

### 4.1 启动本地 MQTT Broker

```bash
cd software/gateway/mqtt-broker
docker compose pull
docker compose up -d
```

EMQX Dashboard 默认在 <http://<host>:18083> （默认账号 `admin/public`）。

### 4.2 启动网关 Python 程序

```bash
cd software/gateway/python
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py --config config.py
```

默认会同时启动：

- Wi-Fi HTTP/TCP 适配器（端口 `8080`），含 **Web 管理台**（浏览器打开 `http://<网关IP>:8080/admin/`，默认引导账号见 `software/gateway/python/README.md`）
- BLE 扫描适配器（需要 BlueZ/Bluetooth 环境）
- MQTT 发布/订阅客户端（连接至 `127.0.0.1:1883`）

### 4.3 启动 Node-RED（应用层规则）

```bash
node-red
# 浏览器打开 http://localhost:1880 ，导入 software/gateway/node-red/flows.json
```

### 4.4 快速自测

```bash
# 发一条模拟 Wi-Fi 节点数据
python tools/generate_test_data.py --protocol wifi_http --count 1

# 订阅网关发布的统一 JSON
mosquitto_sub -h 127.0.0.1 -t 'smarthome/v1/telemetry/#' -v
```

## 5. 测试与验收

| 类别       | 脚本                                           | 关键指标                 |
| ---------- | ---------------------------------------------- | ------------------------ |
| 功能测试   | `tests/functional/test_data_converter.py`     | 协议转换 / 统一 JSON     |
| 功能测试   | `tests/functional/test_admin_db.py`           | 用户 / 节点台账 / 在线状态 |
| 性能测试   | `tests/performance/e2e_loss_test.py`          | 基线 MQTT 丢包 vs 经网关丢包及差值（论文写法） |
| 性能测试   | `tests/performance/cross_device_perf_subscribe.py` | 真机 Wi‑Fi/BLE：节点→网关→MQTT 时延 / 丢包（需 `send_ns`） |
| 性能测试   | `tests/performance/cross_node_relay_test.py`  | 两节点联动时延 / 丢包：默认仅 Broker+Node-RED（`--stop-at broker`）；`--stop-at device` 测真机收令后经网关回到 MQTT（需刷带 `cmd_ack`/`k` 的固件） |
| 稳定性测试 | `tests/stability/long_run_test.py`             | 24h 无内存泄漏 / 崩溃    |
| 稳定性测试 | `tests/stability/network_recovery_test.py`     | 断网重连 / 离线数据补传  |

## 6. License

本项目基于 MIT License 发布，详见 [LICENSE](LICENSE)。

## 7. 致谢

- [EMQX](https://www.emqx.io/)：开源 MQTT Broker
- [Node-RED](https://nodered.org/)：可视化边缘规则引擎
- [bleak](https://github.com/hbldh/bleak)：跨平台 BLE 库
- [paho-mqtt](https://www.eclipse.org/paho/)：Python MQTT 客户端
