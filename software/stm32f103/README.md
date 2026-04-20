# STM32F103 BLE 终端节点固件

基于 PlatformIO + Arduino_Core_STM32 实现，目标：

- USART2 (PA2=TX, PA3=RX) 对接 HM-10 BLE 模块，作 GATT 0xFFE0/0xFFE1 透传从机；
- **GY-302（BH1750）** I²C：PB7=SDA、PB6=SCL，与板载 24C02 共总线；
- PE0 驱动 **有源蜂鸣器**（高电平鸣响）；
- 本地边缘智能：环境变暗时本地短鸣一次提示；远程命令优先于本地规则。

## 目录结构

```
software/stm32f103/
├── platformio.ini         # 板卡: genericSTM32F103ZE (战舰 V4)
├── include/
│   ├── ble_uart.h         # HM-10 AT 初始化 + 透传 API
│   ├── ldr.h              # GY-302(BH1750) 照度抽象 → JSON 字段 l/d
│   └── buzzer.h           # PE0 有源蜂鸣器（非阻塞 beep）
└── src/
    ├── ble_uart.cpp
    ├── ldr.cpp
    ├── buzzer.cpp
    └── main.cpp           # 主循环: 采样 -> BLE 上报 & 下行命令执行
```

## 硬件接线

| STM32 引脚   | 外设        | 说明                                                   |
| ------------ | ----------- | ------------------------------------------------------ |
| PA2 (USART2_TX) | HM-10 RXD | 3.3V 直连；如果和 5V 板混用，RX 侧串 1kΩ 保护          |
| PA3 (USART2_RX) | HM-10 TXD | 3.3V 直连                                              |
| PB7 / PB6    | GY-302 I²C  | SDA / SCL；与 24C02 同总线；BH1750 地址 0x23（ADDR 接 GND） |
| PE0          | 有源蜂鸣器 IN | 高电平鸣响（带振荡芯片，无需 PWM）                  |
| 3V3 / GND    | 全部模块电源 | HM-10 / GY-302 / 蜂鸣器                            |

> 战舰 V4 板载功能复用提示：
> - **PB6/PB7** 与板载 **24C02** 共 I²C，勿与总线冲突；GY-302 与 EEPROM 地址不同可共存；
> - **PE0 = FSMC_NBL0**，本项目占用为蜂鸣器输出，不要同时挂板载 LCD/FSMC。

## 关键宏 / 配置

| 文件 | 宏 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `ble_uart.h` | `BLE_UART_BAUD` | 9600 | HM-10 出厂默认；若改过自行同步 |
| `ble_uart.h` | `BLE_ADV_NAME`  | `SHMPEG-BLE` | 与网关 `ble_name_prefixes` 对齐 |
| `ldr.h` | `BH1750_I2C_ADDR` | `0x23` | ADDR 接 VCC 的模块常为 `0x5C`，可 build_flags 覆盖 |
| `ldr.h` | `LIGHT_LUX_DARK_MAX` | `80` lx | 低于此照度 JSON 中 `d`=1；可用 `-D LIGHT_LUX_DARK_MAX=50.0f` |
| `buzzer.h` | `BUZZER_PIN` | `PE0` | 有源蜂鸣器信号脚 |
| `buzzer.h` | `BUZZER_ACTIVE_HIGH` | 1 | 0 表示低电平触发模块 |
| `main.cpp` | `DEVICE_ID` | `b01` | 仅文档/日志；上行 JSON 不含 id，MQTT id 靠 BLE 名与网关路由 |
| `main.cpp` | `SAMPLE_INTERVAL_MS` | 1000 | 采样周期 |

## 编译 / 烧录

```powershell
cd software\stm32f103
pio run                         # 编译
pio run --target upload         # 用 ST-Link 烧录
pio device monitor              # 115200 bps 看 USART1 调试输出
```

## 上行 JSON 帧

```json
{"l":1000,"d":0,"seq":12,"send_ns":1713333333123456789}
```

- `l`: 照度 lx **裁剪到 0~4095**（与 BH1750 读数一致，室内多为数百 lx 量级）
- `d`: 1 = 偏暗需要补光，0 = 足够亮
- `seq`: 递增序号，供订阅侧估算丢包
- `send_ns`: 发送端 Unix 纳秒时间戳（需先收到网关 `{"sync_ns":...}` 授时）
- 帧尾 `\n` 分隔。若 JSON >20B，HM-10 会分成多次 notify；网关已支持按换行重组。
- 上行仍不含 `id`，网关用 BLE 设备名/MAC 作为 `device_id`。

## 下行命令 JSON

| 命令示例 | 效果 |
| --- | --- |
| `{"buzzer":true}` / `{"buzzer":false}` | 立即长鸣 / 静音 |
| `{"beep":3}` | 鸣响 3 次（150ms on / 150ms off） |
| `{"beep":{"on":150,"off":150,"n":3}}` | 自定义节奏 |
| `{"auto":true}` | 释放远程接管，恢复"暗->短鸣 1 次"本地规则 |
| `{"sync_ns":1713333333123456789}` | 网关授时，后续上行可生成 `send_ns` |

若命令中含 **`src_seq`**（Node-RED 跨节点联动），执行蜂鸣类命令后会再发一行 **`{"k":<seq>}`**（≤19B，适配 HM-10 单帧）；网关统一模型里为 `payload.k`，供 `cross_node_relay_test.py --stop-at device` 配对端到端时延。`src_seq` 位数过大导致 JSON 超过 19B 时固件会跳过发送。

网关把 `smarthome/v1/command/ble/<device_id>` 下行的 JSON 原样
`write_gatt_char` 到 HM-10，即可直达本节点。

## 本地边缘智能

- 采样到 `is_dark=true` 且未处于远程接管时：本地短鸣 1 次提示；
- 收到任何 `{"buzzer":...}` / `{"beep":...}` 命令进入"远程接管"，
  直到 `{"auto":true}` 或下次重连。

## 故障排查

| 现象 | 可能原因 | 处理 |
| --- | --- | --- |
| `[boot] HM-10 AT NO RESPONSE` | 波特率不对 / 正在被上位机连接中 | 断开手机 BLE；串口用 `AT+BAUD?` 确认 |
| 上位机扫不到设备 | 名字被改成非 `SHMPEG-` 开头 | `AT+NAME?` 查，或改网关 `ble_name_prefixes` |
| 网关日志看到 `raw_hex` 兜底 | JSON 被拆包且网关未更新 | 确认已拉到本项目最新 `ble_receiver.py` |
| 蜂鸣器一直响 / 不响 | 模块触发电平相反 | 改 `BUZZER_ACTIVE_HIGH` 为 0 |
| `l` 恒 0、`d` 恒 1 | I²C 失败 / 地址错 | 查 PB7/PB6、3V3/GND；ADDR 为 0x5C 时改 ``BH1750_I2C_ADDR`` |

## 跨设备性能（可选）

运行网关后会自动在 BLE 连接建立时下发 `sync_ns`。STM32 收到后开始在上行 JSON 中携带 `seq/send_ns`，因此可直接使用：

```bash
python tests/performance/cross_device_perf_subscribe.py --path ble --device-id SHMPEG-BLE --duration 120
```

若日志提示未出现 `send_ns`，请先确认 BLE 已成功连接网关并观察串口是否打印 `[cmd] time sync ns=...`。
