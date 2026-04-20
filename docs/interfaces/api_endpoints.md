# 网关 REST API

除 MQTT 外，网关还暴露一组 HTTP/REST 接口，供：

- **感知层 Wi-Fi 节点**上报数据（主要用途）；
- 运维/调试工具做健康检查。

基础 URL: `http://<gateway_ip>:8080`

---

## 1. Health Check

- 方法: `GET /health`
- 返回: `{"ok": true}`
- 用途: 启动校验、容器 liveness probe。

```bash
curl http://192.168.1.10:8080/health
# {"ok":true}
```

---

## 2. 遥测上报（Wi-Fi 节点 -> 网关）

- 方法: `POST /api/v1/telemetry`
- Header: `Content-Type: application/json`
- Body: 节点原始 JSON，支持以下两种字段风格，网关会统一归一化：

### 2.1 短字段风格（推荐 MCU 使用，节省带宽）

| 字段 | 类型   | 必填 | 说明                                                   |
| ---- | ------ | ---- | ------------------------------------------------------ |
| `id` | string | ✔    | 设备唯一标识，推荐 `<type>-<mac_suffix>`               |
| `t`  | number | ○    | 温度 °C                                                |
| `h`  | number | ○    | 湿度 %RH                                               |
| `l`  | number | ○    | 光照 lux                                               |
| `b`  | number | ○    | 电量百分比                                             |
| `ts` | int    | ○    | Unix 秒；未提供时用网关时间                            |

### 2.2 长字段风格（HTTP 直连服务端也能用）

```json
{
  "device_id": "esp32-s3-node-01",
  "temperature": 25.4,
  "humidity": 56.1,
  "light": 534,
  "status": "online",
  "timestamp": 1713333333
}
```

### 2.3 成功响应

```json
{ "ok": true, "device_id": "esp32-s3-node-01" }
```

### 2.4 失败响应

- `400 Bad Request`：JSON 非法或 schema 校验失败。
- `500 Internal Server Error`：网关内部回调异常。

### 2.5 TCP 等价通道

若 MCU 带宽紧张或需要更低时延，可建立 TCP 长连接到 **端口 9000**，
每条消息为 UTF-8 JSON + `\n`，网关回 `{"ok":true}\n`。Body 规范与 HTTP 一致。

---

## 3. 错误码

| HTTP 码 | 描述                                    |
| ------- | --------------------------------------- |
| 200     | 成功                                    |
| 400     | 请求体非 JSON / Schema 校验失败         |
| 500     | 内部回调错误（MQTT 等）                 |

---

## 4. 鉴权（规划中）

当前实验室环境为**匿名访问**；生产部署建议：

- 所有节点带 `X-Device-Token` header；
- 网关侧维护 token -> device_id 映射；
- 非法 token 返回 `401`。
