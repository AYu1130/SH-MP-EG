# tests/

精简后的测试集合，覆盖**功能（单元）/ 性能（节点→网关→MQTT、节点↔节点）/ 稳定性**。

```
tests/
├── conftest.py                      # 把 software/gateway/python 加入 sys.path
├── functional/
│   ├── test_data_converter.py       # 协议转换 / Schema 校验（无需跑网关）
│   └── test_admin_db.py             # 用户 / 节点台账 / 在线状态（无需跑网关）
├── performance/
│   ├── e2e_loss_test.py             # **传输效率**：基线 MQTT vs 经网关，差值
│   ├── cross_device_perf_subscribe.py  # **节点 → 网关 → MQTT** 真机时延 / 丢包
│   └── cross_node_relay_test.py        # **两节点联动** 时延 / 丢包（MQTT 纯模拟载荷，无需真机）
└── stability/
    ├── long_run_test.py             # 长时运行（默认 1 小时，可调）
    └── network_recovery_test.py     # 断网恢复 / 离线补传（需 root iptables）
```

## 快速跑

### 仅单元测试（无需网关）

```bash
pytest tests/functional -v
```

### 性能：节点 → 网关 → MQTT（按论文写法）

**基线 vs 经网关丢包率**（论文「网关引入丢包 = 经网关 − 基线」）：

```bash
python tests/performance/e2e_loss_test.py --mode baseline-mqtt --count 500
python tests/performance/e2e_loss_test.py --mode gateway-http  --count 500
python tests/performance/e2e_loss_test.py --mode both          --count 500
# 可选：经网关 TCP（与 ESP32 上行同协议）
python tests/performance/e2e_loss_test.py --mode gateway-tcp --count 200
```

**真机跨设备时延 / 丢包**（终端 NTP 对时后在 JSON 内打 `send_ns`，订阅侧统计；ESP32 固件已写入）：

```bash
# Wi-Fi 节点
python tests/performance/cross_device_perf_subscribe.py --path wifi --duration 120

# BLE 节点（若设备 JSON 含 send_ns；否则只能算到达率）
python tests/performance/cross_device_perf_subscribe.py --path ble --device-id SHMPEG-BLE --duration 120
```

### 性能：两节点「互相通信」联动（MQTT 模拟数据）

脚本只向 Broker 发布 **合成的** `telemetry/...` JSON，并订阅 `command/...` 配对 `src_seq`，**不需要** ESP32/STM32 在线；需 **EMQX + Node-RED**（导入 `software/gateway/node-red/flows.json`）。网关进程不必参与该段测量。

```bash
# 双向各 30 次（逻辑 ID 与 Node-RED 规则中的 device_id 一致即可，可为任意字符串）
python tests/performance/cross_node_relay_test.py \
    --direction both \
    --wifi-id node-wifi-a \
    --ble-id  node-ble-b \
    --count 30 --interval-ms 300 --timeout-s 3.0
# 若已改 flow 固定对端，可加 --no-keepalive；Wi-Fi 触发温度阈值可调：--wifi-temp-trigger 35
```

默认 `--stop-at broker`：输出 `matched=N/M` 与 `min/avg/p95/max`，度量 **telemetry → broker → Node-RED → command → broker**，**不含** 网关经 TCP/BLE 下发到真机。

**真机收到命令 → 再经网关出现在 MQTT**（需树莓派跑 **网关 + EMQX + Node-RED**，两端刷当前仓库固件）：

```bash
python tests/performance/cross_node_relay_test.py \
    --stop-at device --direction both \
    --wifi-id <与 ESP 上报 id 一致> \
    --ble-id  <与网关 BLE 台账 id 一致> \
    --count 20 --timeout-s 5
```

固件在收到带 `src_seq` 的联动命令后会立即上行 `payload.cmd_ack`（ESP32）或 `payload.k`（STM32，HM-10 单帧 ≤19B）；脚本订阅对端 `telemetry/...` 配对，日志标签为 `[telemetry_e2e]`。

### 稳定性

```bash
nohup python tests/stability/long_run_test.py --duration 86400 > long_run.log 2>&1 &
sudo python tests/stability/network_recovery_test.py
```

## 验收指标对应关系

| 指标                                 | 测试脚本                                                |
| ------------------------------------ | ------------------------------------------------------- |
| 协议转换 / 统一 JSON / Schema 校验   | `functional/test_data_converter.py`                     |
| 用户 / 节点台账 / 登录锁定           | `functional/test_admin_db.py`                           |
| 传输效率（论文式基线 + 差值）        | `performance/e2e_loss_test.py`                          |
| 真机：节点 → 网关 → MQTT 时延/丢包   | `performance/cross_device_perf_subscribe.py`            |
| 节点 ↔ 节点 联动时延 / 丢包          | `performance/cross_node_relay_test.py`（`--stop-at broker` / `device`） |
| 长时运行                             | `stability/long_run_test.py`                            |
| 断网恢复 / 离线补传                  | `stability/network_recovery_test.py`                    |
