# Unified JSON Schema (Draft)

该文档定义边缘网关统一后的数据模型，用于协议适配后的上行发布。

## 字段说明

- `device_id` (string, required): 设备唯一标识
- `device_type` (string, required): 设备类型，例如 `wifi`、`ble`
- `transport` (string, required): 接入传输协议，例如 `tcp`、`ble`
- `timestamp` (integer, required): Unix 时间戳（秒）
- `status` (string, required): 设备状态，建议值：`online`/`offline`/`fault`
- `payload` (object, required): 业务测量数据对象

## JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "GatewayUnifiedMessage",
  "type": "object",
  "required": [
    "device_id",
    "device_type",
    "transport",
    "timestamp",
    "status",
    "payload"
  ],
  "properties": {
    "device_id": { "type": "string", "minLength": 1 },
    "device_type": { "type": "string", "minLength": 1 },
    "transport": { "type": "string", "minLength": 1 },
    "timestamp": { "type": "integer", "minimum": 0 },
    "status": { "type": "string", "enum": ["online", "offline", "fault"] },
    "payload": {
      "type": "object",
      "properties": {
        "temperature": { "type": "number" },
        "humidity": { "type": "number" },
        "light": { "type": "number" },
        "battery": { "type": "number" },
        "co2": { "type": "number" },
        "pm25": { "type": "number" }
      },
      "additionalProperties": true
    }
  },
  "additionalProperties": true
}
```
