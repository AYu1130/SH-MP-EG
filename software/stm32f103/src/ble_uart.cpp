/**
 * ble_uart.cpp —— HM-10 透传封装实现
 *
 * 设计要点
 * --------
 * - 直接用 Arduino_Core_STM32 的 HardwareSerial；USART2 默认管脚为 PA2/PA3；
 * - AT 初始化: 尝试 "AT" / "AT+NAMEXXXX" / "AT+NOTI1"，每条命令有独立超时，
 *   任一条失败都不影响后续；
 * - 接收侧维护一个行缓冲 + 状态解析器，把 "OK+CONN" / "OK+LOST" 剥离出来
 *   更新连接标志位，其余内容作为透传数据暴露给上层。
 */

#include "ble_uart.h"

// Arduino_Core_STM32: 指定 RX / TX 引脚实例化 Serial2
static HardwareSerial BleSerial(PA3 /* RX */, PA2 /* TX */);

static bool s_connected = false;         // 由 OK+CONN / OK+LOST 维护
static String s_rx_line;                 // 透传数据的行缓冲 (\n 分帧)

// --- 小工具：带超时等待一段 AT 应答 --------------------------------------
static String at_wait_reply(uint32_t timeout_ms) {
  String buf;
  uint32_t t0 = millis();
  while (millis() - t0 < timeout_ms) {
    while (BleSerial.available() > 0) {
      char c = static_cast<char>(BleSerial.read());
      buf += c;
      // HM-10 应答一般以 "OK" 开头，短则 2 字节长则几十字节；
      // 看到 OK 后再等 20ms 收剩余尾巴即退出
      if (buf.indexOf("OK") >= 0 && (millis() - t0 > 50)) {
        delay(20);
        while (BleSerial.available() > 0) buf += (char)BleSerial.read();
        return buf;
      }
    }
  }
  return buf;  // 可能为空，表示未响应
}

static bool at_send(const char *cmd, const char *expect_substr,
                   uint32_t timeout_ms = 300) {
  // 清空接收缓冲，避免把上次残留当作本次应答
  while (BleSerial.available() > 0) (void)BleSerial.read();
  BleSerial.print(cmd);  // HM-10 AT 不要求 \r\n
  String r = at_wait_reply(timeout_ms);
  return expect_substr == nullptr || r.indexOf(expect_substr) >= 0;
}

// --- 公开接口 ------------------------------------------------------------
bool ble_init() {
  BleSerial.begin(BLE_UART_BAUD);
  delay(200);  // 等待上电稳定

  // 步骤 1：握手 "AT" -> 期望 "OK"
  bool at_ok = at_send("AT", "OK", 300);

  // 步骤 2：设置广播名（方便被网关的 name_prefixes 过滤命中）
  //   注意：AT+NAME 执行后 HM-10 不会立即更名，需要 AT+RESET
  //   为了避免反复重启浪费时间，只有名字和目标不一致时才改
  if (at_ok) {
    if (at_send("AT+NAME?", "OK+NAME:" BLE_ADV_NAME, 300)) {
      // 名称已经匹配，跳过
    } else {
      String cmd = String("AT+NAME") + BLE_ADV_NAME;
      at_send(cmd.c_str(), "OK+Set", 300);
      // 重启以应用新名字（用户可选）
      at_send("AT+RESET", "OK+RESET", 500);
      delay(700);
      // 重启后重新握手，避免 RESET 期间字节丢失
      at_send("AT", "OK", 300);
    }

    // 步骤 3：开启"连接通知"，让我们能感知 OK+CONN / OK+LOST
    at_send("AT+NOTI1", "OK+Set", 300);
  }

  s_rx_line = "";
  return at_ok;
}

void ble_println(const char *line) {
  if (line == nullptr) return;
  BleSerial.print(line);
  BleSerial.print('\n');
}

void ble_println(const String &line) {
  ble_println(line.c_str());
}

/**
 * 从 BleSerial 连续消费字节：
 *   - 若在缓冲尾端能匹配到 "OK+CONN" / "OK+LOST"，更新 s_connected 并丢弃；
 *   - 其余字节追加到行缓冲，遇到 '\n' 结束一行写入 out_line 并返回 true。
 */
bool ble_try_read_line(String &out_line) {
  while (BleSerial.available() > 0) {
    char c = static_cast<char>(BleSerial.read());

    if (c == '\r') continue;  // 统一去掉 CR
    if (c == '\n') {
      if (s_rx_line.length() == 0) continue;  // 空行跳过
      // 截取"连接状态"通告，不作为业务数据上抛
      if (s_rx_line == "OK+CONN") { s_connected = true;  s_rx_line = ""; continue; }
      if (s_rx_line == "OK+LOST") { s_connected = false; s_rx_line = ""; continue; }
      out_line = s_rx_line;
      s_rx_line = "";
      return true;
    }

    if (s_rx_line.length() < 256) s_rx_line += c;
    else s_rx_line = "";  // 防御：异常长行丢弃

    // HM-10 的 OK+CONN/OK+LOST 不一定带换行，需扫描 suffix
    if (s_rx_line.endsWith("OK+CONN")) {
      s_connected = true;
      s_rx_line.remove(s_rx_line.length() - 7);
    } else if (s_rx_line.endsWith("OK+LOST")) {
      s_connected = false;
      s_rx_line.remove(s_rx_line.length() - 7);
    }
  }
  return false;
}

bool ble_is_connected() {
  return s_connected;
}
