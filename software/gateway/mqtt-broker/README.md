# EMQX 本地 MQTT Broker 部署

> 作为网关的"网络层"核心组件，所有统一 JSON 数据都会发布到这里。

镜像版本：**EMQX 5.8.9**（与 [官方文档](https://www.emqx.io/docs) 的 `docker pull emqx/emqx:5.8.9` 一致）。

## 目录内容

| 文件                  | 作用                                       |
| --------------------- | ------------------------------------------ |
| `docker-compose.yml`  | 一键启动 EMQX 5.8.9 单机节点 + 端口映射    |
| `emqx.conf`           | 监听端口 / 鉴权 / 日志 等自定义参数        |
| `data/`               | EMQX 持久化目录（retain 消息、账号、ACL）  |
| `log/`                | EMQX 运行日志                              |

## 快速启动（推荐）

```bash
cd software/gateway/mqtt-broker
docker compose pull
docker compose up -d
docker compose logs -f emqx
```

## 等价：纯 docker 命令

```bash
docker pull emqx/emqx:5.8.9
docker run -d --name emqx \
  -p 1883:1883 -p 8083:8083 -p 8084:8084 -p 8883:8883 -p 18083:18083 \
  emqx/emqx:5.8.9
```

若已用 compose 创建过 `shmpeg-emqx`，避免与上面的 `--name emqx` 冲突；或先 `docker rm -f emqx`。

- Dashboard：<http://127.0.0.1:18083>（默认账号 `admin` / `public`，首次登录需修改）
- MQTT 端口：`1883`（TCP）、`8083`（WS）、`8084`（WSS）、`8883`（TLS）

## 验证连通

```bash
# 订阅所有 smarthome 主题
mosquitto_sub -h 127.0.0.1 -p 1883 -t 'smarthome/v1/#' -v

# 发布测试消息
mosquitto_pub -h 127.0.0.1 -p 1883 \
  -t 'smarthome/v1/telemetry/wifi/test' \
  -m '{"device_id":"test","device_type":"wifi","transport":"http","timestamp":0,"status":"online","payload":{"temperature":25}}'
```

## 常见问题

- **端口映射**：当前 `docker-compose.yml` 默认使用 `ports:`，Windows / macOS / Linux / 树莓派均适用；本机程序连接 `127.0.0.1:1883` 即可。
- **树莓派想用 host 网络**：编辑 `docker-compose.yml`，注释 `ports:` 段，取消注释 `network_mode: host`（注意：Docker Desktop 仍不支持 host）。
- **想换成 Mosquitto**：本项目代码仅使用标准 MQTT 3.1.1 协议，切换 Broker
  无需改动 Python 代码，但 Node-RED 内的 broker 地址需同步更新。
