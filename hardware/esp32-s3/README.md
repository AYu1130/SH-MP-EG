# Wi-Fi 节点硬件 (ESP32-S3)

| 项            | 规格                                           |
| ------------- | ---------------------------------------------- |
| 开发板        | ESP32-S3-DevKitC-1（N8R8）                     |
| 主控          | ESP32-S3 (Xtensa LX7 双核, Wi-Fi 4 + BLE 5)    |
| 传感器        | DHT11 模块 — 温湿度 (GPIO4)                    |
| 执行器        | 有源蜂鸣器模块 (GPIO5，高电平鸣响)             |
| 供电          | USB-C 5V / 外部 LDO 3.3V                       |

## 资料归档建议

```
hardware/esp32-s3/
├── README.md
├── schematics/
│   └── wifi_node.kicad_sch
├── datasheets/
│   ├── ESP32-S3-WROOM-1_datasheet.pdf
│   ├── DHT11_datasheet.pdf
│   └── buzzer_active.pdf
└── photos/
```

接线见 [`docs/hardware/wiring_guide.md`](../../docs/hardware/wiring_guide.md#2-wi-fi-节点esp32-s3)。
