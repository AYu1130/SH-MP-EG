# Node-RED 规则引擎

作为应用层的一部分，负责**本地规则触发**和**可视化调试**。

## 功能说明

`flows.json` 已经实现两条示例规则：

| 规则                       | 条件                           | 动作                                     |
| -------------------------- | ------------------------------ | ---------------------------------------- |
| 温度过高 -> 蜂鸣器报警     | Wi-Fi 节点 `temperature > 28`  | 向 `command/wifi/<id>` 发 `buzzer:true`  |
| 光照偏暗 -> 自动点灯       | BLE 节点 `light < 100`         | 向 `command/ble/<id>` 发 `text:"LED:ON"` |

两条规则命中后都通过网关 MQTT 代理下发到 `command` 主题，
由 `mqtt_publisher -> on_command` 回调转换为具体协议动作。

## 部署方式

### 方式 A. 主机直接安装

```bash
sudo npm install -g --unsafe-perm node-red
node-red
```

### 方式 B. Docker

```bash
docker run -d --name shmpeg-nodered \
  --network host \
  -v $PWD/.node-red:/data \
  nodered/node-red:latest
```

### 导入 flows

1. 打开 <http://127.0.0.1:1880>
2. 右上角菜单 -> Import -> 选择本目录下的 `flows.json`
3. Deploy

## 扩展规则建议

- 结合 `node-red-dashboard` 实时展示温湿度曲线；
- 接入 `node-red-contrib-home-assistant-websocket` 进一步上云；
- 使用 `delay` 节点做规则防抖，避免触发洪水；
- 用 `change` 节点对报警加入 cooldown（基于 `flow.context`）。

## 与网关契约

Node-RED **严禁**绕过 `smarthome/v1/command/...` 主题直接写硬件；
这能确保规则引擎随时可替换、迁移到云端或其他平台，而不影响边缘网关。
