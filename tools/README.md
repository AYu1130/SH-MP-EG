# tools/

面向开发 / 调试 / 验收的实用脚本集合。所有脚本均为独立可运行入口，
不依赖网关 Python 包（必要时通过 `sys.path` 引用 `software/gateway/python`）。

| 文件                                | 作用                                               |
| ----------------------------------- | -------------------------------------------------- |
| `serial_monitor.py`                 | 简易串口监视/回写工具，替代 PuTTY 便于集成到脚本   |
| `mqtt_bench.py`                     | 本地 MQTT 压测：吞吐率、端到端延迟、丢包率         |
| `generate_test_data.py`             | 向网关 Wi-Fi/HTTP 适配器灌入模拟节点数据           |
| `network_simulator/simulate_break.sh` | 使用 `tc` / `iptables` 模拟网络中断与恢复         |

> 运行 Python 脚本前先 `pip install paho-mqtt requests pyserial`。
