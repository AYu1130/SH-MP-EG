/**
 * ble_uart.h
 * ==========
 *
 * HM-10 BLE 模块的"串口透传"封装。
 *
 * HM-10 特性
 * ----------
 * - BLE 4.0 从机；上电默认广播名 "HMSoft"、波特率 9600 N81；
 * - 作为 GATT 服务的 0xFFE0 / 0xFFE1 (notify + write)：
 *     HM-10 UART RX (PIN 2)  ◀──  写入的字节 (gateway -> node)
 *     HM-10 UART TX (PIN 1)  ──▶  通过 notify 上行 (node -> gateway)
 * - 只有 **断开连接** 时才接受 AT 命令；连接后 UART 透传。
 *
 * 本模块职责
 * ----------
 * 1) 开机时做一次"有条件 AT 初始化"(设置蓝牙广播名、可选调高波特率)，
 *    只要 AT 不响应就跳过，不阻塞业务；
 * 2) 提供 :cpp:func:`ble_println` 发送一行 JSON；
 * 3) 提供 :cpp:func:`ble_try_read_line` 非阻塞读取网关下行 JSON。
 */

#ifndef BLE_UART_H
#define BLE_UART_H

#include <Arduino.h>

#ifndef BLE_UART_BAUD
#define BLE_UART_BAUD 9600  // HM-10 出厂默认，如改过用 AT+BAUD 对齐这里
#endif

/**
 * 期望的 BLE 广播名；首次上电会用 AT+NAME 设置。
 * 网关 config.py 的 ble_name_prefixes 默认包含 "SHMPEG-"，与这里对应。
 * 最长 11 字符（HM-10 硬性限制）。
 */
#ifndef BLE_ADV_NAME
#define BLE_ADV_NAME "SHMPEG-BLE"
#endif

// ------------------------------------------------------------------------ //
/**
 * 初始化 USART2(PA2/PA3) -> HM-10，并尝试下发 AT 命令完成一次性配置。
 *
 * 无论 AT 握手是否成功都返回，便于业务即刻使用 UART 透传；
 * 返回值只用于日志：true 表示至少一条 AT 成功、false 表示模块未应答。
 */
bool ble_init();

/**
 * 发送一行数据 + '\n'，结尾的换行符便于网关侧做分帧。
 * 调用前必须保证总长度 ≤ 约 20 字节，因为 HM-10 单次 BLE
 * notification payload 默认 = 20 字节；更长报文会被拆分到多次 notify，
 * 此时需要网关的 BLE 适配器做行缓冲（本项目已支持）。
 */
void ble_println(const char *line);
void ble_println(const String &line);

/**
 * 非阻塞读取下行命令。以 '\n' 或模块主动 notify 的边界为一帧。
 *
 * - 有完整一行时写入 out_line（不含换行符）返回 true；
 * - 否则立即返回 false。
 *
 * 注意：HM-10 在 **未连接** 状态时收到的 UART 字节会被当作 AT 命令；
 * 我们内部屏蔽了诸如 "OK+CONN" / "OK+LOST" 之类的状态通告，不会误判。
 */
bool ble_try_read_line(String &out_line);

/**
 * 查询模块当前是否正与对端 (gateway) 连接。
 * 实现方式：AT+NOTI=1 开启"连接通知"，并解析透传流里的
 * "OK+CONN" / "OK+LOST" 字符串。
 */
bool ble_is_connected();

#endif  // BLE_UART_H
