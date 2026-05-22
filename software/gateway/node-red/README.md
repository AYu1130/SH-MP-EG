# Node-RED 规则引擎

作为应用层的一部分，负责**本地规则触发**和**可视化调试**。

## 功能说明

`flows.json` 包含两个 Tab：

### Tab 1: SH-MP-EG Cross-Node Rules（跨节点联动规则）

| 规则                       | 条件                           | 动作                                     |
| -------------------------- | ------------------------------ | ---------------------------------------- |
| 温度过高 -> 蜂鸣器报警     | Wi-Fi 节点 `temperature > 28`  | 向 `command/ble/<id>` 发 `beep:3`       |
| 光照偏暗 -> 自动点灯       | BLE 节点 `light < 70`          | 向 `command/wifi/<id>` 发 `led:yellow`  |
| 光照恢复 -> 释放远程接管   | BLE 节点 `light > 130`         | 向 `command/wifi/<id>` 发 `auto:true`   |

### Tab 2: Dashboard（仪表盘）

通过 `node-red-dashboard` 节点实现传感器数据实时可视化：
- **温度仪表盘**（ui_gauge）— 范围 -10~50°C，分色段显示
- **湿度仪表盘**（ui_gauge）— 范围 0~100%
- **光照仪表盘**（ui_gauge）— 范围 0~1000 lux
- **温度/湿度/光照历史曲线**（ui_chart）— 保留最近 1 小时数据
- **LED 状态指示**（ui_text）— 显示当前 LED 颜色
- **蜂鸣器状态指示**（ui_text）— 显示 ON/OFF
- **报警状态指示**（ui_text）— 显示 ACTIVE/INACTIVE

仪表盘访问地址：`http://<网关IP>:1880/ui`

## 部署方式

### 前置条件：安装 node-red-dashboard

```bash
cd ~/.node-red
npm install node-red-dashboard
```

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
