# BLE 节点硬件 (战舰 V4 / STM32F103ZET6 + HM-10)

| 项            | 规格                                                           |
| ------------- | -------------------------------------------------------------- |
| 开发板        | 正点原子 战舰 V4 (STM32F103ZET6, 512KB Flash / 64KB SRAM)      |
| BLE 模组      | HM-10 (CC2541, UART 透传 9600 N81, GATT FFE0/FFE1)             |
| 传感器        | GY-302(BH1750) I²C，PB7/PB6，与 24C02 共总线                   |
| 执行器        | 5050 共阴 3色 RGB LED 模块，PE0 R / PE1 G / PE2 B，高电平亮    |
| 供电          | 板载 5V USB -> 3.3V LDO；外设全部共 3.3V                       |
| 烧录          | ST-Link V2 (SWD)；也可板载 CH340 + DTR/RTS 一键下载            |

## 资料归档建议

```
hardware/stm32f103/
├── README.md
├── schematics/
│   └── ble_node.kicad_sch
├── datasheets/
│   ├── STM32F103ZET6_datasheet.pdf
│   ├── 战舰V4_硬件参考手册.pdf
│   ├── HM-10_AT命令.pdf
│   ├── 光敏电阻模块.pdf
│   └── 3色LED模块RGB.pdf
└── photos/
```

## 初次通电检查清单

1. VCC / GND 无短路；
2. STM32 板载 BOOT0 = 0、NRST 复位一次；
3. ST-Link 能识别 MCU：`st-info --probe`；
4. HM-10 上电后蓝灯慢闪（未连接）；
5. PC 蓝牙能扫描到设备名（`HMSoft` 或自定义前缀）。

接线见 [`docs/hardware/wiring_guide.md`](../../docs/hardware/wiring_guide.md#3-ble-节点stm32f103--hm-10)。
