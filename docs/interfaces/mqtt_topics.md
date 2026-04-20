# MQTT Topic 规范

## 1) 命名规范

统一采用以下结构：

`smarthome/v1/<domain>/<device_type>/<device_id>`

- `domain`：业务域（`telemetry`、`event`、`command`、`status`）
- `device_type`：设备类型（`wifi`、`ble`、`zigbee` 等）
- `device_id`：设备唯一标识

## 2) 上行数据主题

- 遥测数据：`smarthome/v1/telemetry/<device_type>/<device_id>`
- 状态事件：`smarthome/v1/status/<device_type>/<device_id>`

网关将 Wi-Fi/BLE 等协议适配后的统一 JSON 发布到 telemetry 主题。

## 3) 下行控制主题

- 控制命令：`smarthome/v1/command/<device_type>/<device_id>`

可由 Node-RED/应用层发布命令，由边缘网关转发到对应协议设备。

## 4) 样例

Topic:

`smarthome/v1/telemetry/wifi/esp32-s3-node-01`

Payload:

```json
{
  "device_id": "esp32-s3-node-01",
  "device_type": "wifi",
  "transport": "tcp",
  "timestamp": 1713333333,
  "status": "online",
  "payload": {
    "temperature": 25.4,
    "humidity": 56.1,
    "light": 534
  }
}
```