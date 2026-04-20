# EMQX 部署与运维指南

本项目选用 [EMQX 5.x](https://www.emqx.io/) 作为本地 MQTT Broker，
当前锁定镜像 **`emqx/emqx:5.8.9`**，容器化部署，一键启停。

## 1. 启动

```bash
cd software/gateway/mqtt-broker
docker compose pull
docker compose up -d
docker compose ps
```

## 2. Dashboard

- URL: <http://<gateway-ip>:18083>
- 默认账号 `admin` / `public`（首次登录需修改）
- 可视化：查看在线客户端、订阅、Retain 消息、指标；

## 3. 监听端口

| 端口  | 协议       | 用途                        |
| ----- | ---------- | --------------------------- |
| 1883  | MQTT TCP   | 网关 Python / Node-RED 连接 |
| 8083  | MQTT WS    | Web UI 连接（可选）         |
| 8084  | MQTT WSS   | WebSocket over TLS（可选）  |
| 8883  | MQTT TLS   | 预留                        |
| 18083 | HTTP       | Dashboard                   |

## 4. 鉴权 & 授权

本项目为毕业设计环境，默认 **允许匿名**。若要开启 JWT / 用户名密码：

1. Dashboard -> "访问控制" -> "认证" -> "添加"；
2. 选择 `Password-Based` -> `Built-in Database`；
3. 创建账号 `shmpeg-gw` / 强密码；
4. 在 `config.py` 或环境变量中填入：
   ```bash
   export SHMPEG_MQTT_USERNAME=shmpeg-gw
   export SHMPEG_MQTT_PASSWORD=xxxxx
   ```

## 5. 日志

```bash
docker compose logs -f emqx          # 容器 stdout
tail -f software/gateway/mqtt-broker/log/emqx.log   # 宿主文件
```

## 6. 持久化

`software/gateway/mqtt-broker/data/` 会保存：

- Retain 消息（例如网关 online/offline 状态）；
- Dashboard 用户 / ACL；
- 集群元数据。

**不要**删除该目录，否则所有自定义配置丢失。备份时复制整个目录即可。

## 7. 升级

```bash
cd software/gateway/mqtt-broker
docker compose pull
docker compose up -d          # 会优雅重启，保留 data/
```

## 8. 常用 CLI

```bash
# 进入容器
docker exec -it shmpeg-emqx bash

# 查看节点状态
emqx ctl status

# 查看所有客户端
emqx ctl clients list

# 查看订阅
emqx ctl subscriptions list

# 查看 topic 路由
emqx ctl topics list
```

## 9. 故障排查

| 症状                         | 可能原因                            | 解决                                          |
| ---------------------------- | ----------------------------------- | --------------------------------------------- |
| 网关无法连接                 | 端口被防火墙 / iptables 拦截        | `sudo ufw allow 1883`                         |
| Dashboard 登录一直失败       | 持久化目录权限错                    | `sudo chown -R 1000:1000 ./data`              |
| 消息丢失 / 延迟高            | SD 卡 I/O 慢                        | 换 USB SSD；或设置 `synchronous=OFF`          |
| 容器反复重启                 | 内存不足（树莓派 2GB）              | 用 4GB 型号；或改 `BEAM` 参数                 |
