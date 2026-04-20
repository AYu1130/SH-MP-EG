# 树莓派部署指南

面向**全新 Raspberry Pi 4B**，从烧录系统到完整运行网关的标准化步骤。
预计耗时 30 ~ 60 分钟。

## 0. 前提准备

- 64GB+ microSD 卡、读卡器；
- 5V 3A USB-C 电源；
- 有线网络（调试更方便）；
- 一台 PC（用于烧录）。

## 1. 烧录系统

1. 下载并安装 [Raspberry Pi Imager](https://www.raspberrypi.com/software/)；
2. 选择 `Raspberry Pi OS (64-bit) Lite`；
3. 高级选项中：
   - 设置主机名 `shmpeg-gw`；
   - 启用 SSH（使用密码登录，或导入公钥）；
   - 预配置 Wi-Fi（可选）；
4. 烧录并把 SD 卡插入树莓派，上电。

## 2. 基础环境

使用 SSH 登录后执行：

```bash
# 更新
sudo apt update && sudo apt -y upgrade

# 基础工具
sudo apt install -y git curl vim python3 python3-venv python3-pip \
                    build-essential libglib2.0-dev bluez \
                    mosquitto-clients tmux htop

# 允许普通用户访问蓝牙（bleak 用到）
sudo usermod -aG bluetooth $USER
```

## 3. 安装 Docker（运行 EMQX）

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# 重新登录使 group 生效
```

## 4. 获取项目代码

```bash
git clone <your-repo> ~/shmpeg
cd ~/shmpeg
```

## 5. 启动 EMQX

```bash
cd software/gateway/mqtt-broker
docker compose up -d
docker compose ps           # 应看到 shmpeg-emqx 为 healthy
```

## 6. 启动网关程序

```bash
cd ~/shmpeg/software/gateway/python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 前台调试
python main.py --log-level INFO
```

确认日志出现：
```
wifi HTTP server listening on ('0.0.0.0', 8080)
wifi TCP server listening on ... 9000
mqtt connected (rc=0)
BleReceiver started: name_prefixes=['SHMPEG-','BT05','HMSoft']
```

## 7. 守护进程化（systemd）

把网关注册为系统服务，保证断电重启后自动运行：

```ini
# /etc/systemd/system/shmpeg-gateway.service
[Unit]
Description=SH-MP-EG Edge Gateway
After=network-online.target docker.service
Wants=network-online.target

[Service]
User=pi
WorkingDirectory=/home/pi/shmpeg/software/gateway/python
Environment=PYTHONUNBUFFERED=1
ExecStart=/home/pi/shmpeg/software/gateway/python/.venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now shmpeg-gateway
sudo journalctl -u shmpeg-gateway -f
```

## 8. 安装 Node-RED（应用层规则）

```bash
bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered)

sudo systemctl enable nodered
sudo systemctl start nodered
# 浏览器打开 http://<pi-ip>:1880 , 导入 software/gateway/node-red/flows.json
```

## 9. 验证

```bash
# 本地自测: 向网关灌入一条模拟数据
curl -X POST http://127.0.0.1:8080/api/v1/telemetry \
     -H 'Content-Type: application/json' \
     -d '{"id":"test-01","t":30,"h":60,"l":50}'

# 订阅消息
mosquitto_sub -h 127.0.0.1 -t 'smarthome/v1/#' -v
```

若同时满足：HTTP 返回 `{"ok":true}` + 订阅端看到 telemetry + 看到 command 触发，
则整条链路已经打通。

## 10. 常见问题

- **EMQX 启动慢**：树莓派首次加载镜像耗时，`docker compose logs -f` 等 20~30s。
- **BLE 找不到设备**：确认 `sudo systemctl status bluetooth` 正常；
  或用 `bluetoothctl scan on` 手动验证。
- **端口被占用**：修改 `config.py` 的 `wifi_http_port` 或删除占用进程。
