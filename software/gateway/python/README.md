# Gateway / Python 程序

树莓派 4B 上运行的网关程序。

## 模块一览

| 文件                | 作用                                                      |
| ------------------- | --------------------------------------------------------- |
| `main.py`           | 启动入口：装配配置、并行启动各适配器、优雅停机            |
| `config.py`         | `GatewayConfig` 数据类，支持环境变量和命令行覆盖          |
| `logger.py`         | 统一日志：控制台彩色 + 轮转文件                           |
| `data_converter.py` | 异构 -> 统一 JSON 模型的适配与 Schema 校验                |
| `wifi_receiver.py`  | Wi-Fi 接入：Flask HTTP (8080) + asyncio TCP (9000)        |
| `ble_receiver.py`   | BLE 接入：bleak 扫描 + GATT Notification 订阅 + 下行写入  |
| `mqtt_publisher.py` | 连接本地 EMQX，发布 telemetry、订阅 command、缓存重发     |
| `cache.py`          | SQLite 离线缓存（FIFO，WAL，容量上限）                    |
| `admin_db.py`       | Web 管理台：用户 / 节点 SQLite 持久化                     |
| `admin_routes.py`   | 登录、会话、用户与节点 REST API + `/admin` 静态页       |

## Web 管理台（用户 / 节点）

1. 启动网关后浏览器打开：`http://<树莓派IP>:8080/admin/`（HTTP 端口见 `SHMPEG_WIFI_HTTP_PORT`）。
2. 首次启动若库为空，会根据 `SHMPEG_ADMIN_BOOTSTRAP_USERNAME` / `SHMPEG_ADMIN_BOOTSTRAP_PASSWORD` 创建管理员（默认 `admin` / `admin`，**务必修改**）。
3. **生产环境**请设置 `SHMPEG_ADMIN_SECRET_KEY`（Flask 会话密钥）。禁用管理台：`python main.py --no-admin`。
4. API 前缀：`/api/v1/admin/login`、`/api/v1/admin/nodes`、`/api/v1/admin/users`（用户 API 仅 `admin` 角色）。
5. **节点在线状态**：网关每收到一条上行统一消息会更新 `node_presence`；管理台列表合并「台账 + 自动发现」。超过 `SHMPEG_ADMIN_ONLINE_GRACE_SEC`（默认 120）未再上报则显示离线。
6. **跨设备性能（Wi‑Fi/BLE）**：在树莓派运行 `python tests/performance/cross_device_perf_subscribe.py --path wifi|ble`，设备 JSON 的 `payload` 内需含 `send_ns`（纳秒）与 `seq`（ESP32 TCP 固件已写 `send_ns`，需 SNTP 成功）。

## 运行

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 确保本地 MQTT Broker 已经运行（见 ../mqtt-broker/）
python main.py
```

## 配置

支持三种方式，优先级：**命令行 > 环境变量 > 代码默认值**。
常用环境变量（前缀 `SHMPEG_`）：

```bash
export SHMPEG_MQTT_HOST=192.168.1.10
export SHMPEG_MQTT_PORT=1883
export SHMPEG_WIFI_HTTP_PORT=8080
export SHMPEG_LOG_LEVEL=DEBUG
```

详见 `config.py` 中 `GatewayConfig` 的字段与注释。

## 消息流

```
┌────────────┐      ┌─────────────────┐
│  ESP32-S3  │─WiFi─▶  wifi_receiver  │──┐
└────────────┘      └─────────────────┘  │   ┌──────────────────┐
                                          ├──▶│ data_converter   │
┌────────────┐      ┌─────────────────┐  │   │ (unified JSON)   │
│ STM32+HM10 │─BLE──▶  ble_receiver   │──┘   └────────┬─────────┘
└────────────┘      └─────────────────┘                │
                                                       ▼
                                           ┌──────────────────────┐
                                           │   mqtt_publisher     │
                                           │  (EMQX, qos=1, LWT)  │
                                           └──────────┬───────────┘
                                                      │
                 断网 ──▶ cache.MessageCache(SQLite) ──┘
```

## 调试建议

1. **单测模块**：`pytest tests/functional -v`；
2. **快速灌数据**：`python tools/generate_test_data.py --protocol wifi --count 5`；
3. **订阅所有消息**：`mosquitto_sub -h 127.0.0.1 -t 'smarthome/v1/#' -v`；
4. **无 BLE 环境**：加 `--no-ble` 避免扫描失败刷日志；
5. **无 broker 环境**：消息会自动进 cache，启动 broker 后几秒内补传。
