/**
 * main.cpp —— SH-MP-EG STM32F103 BLE 终端节点
 * ===========================================
 *
 * 硬件资源（互换执行器后；见 docs/hardware/wiring_guide.md）
 * --------------------------------------------------------
 *   USART2 (PA2=TX, PA3=RX)  <->  HM-10 BLE 模块 (UART 透传, 9600 N81)
 *   PB7 / PB6 (I²C)          <-   GY-302(BH1750) SDA/SCL，与板载 24C02 共总线
 *   PE0                      ->   有源蜂鸣器 IN（高电平鸣响）
 *   USART1 (PA9 / PA10)      ->   CH340 USB 虚拟串口，115200 bps，仅做调试
 *
 * 数据流（互换后）
 * ----------------
 *   STM32 -> HM-10 UART(TX) -> GATT 0xFFE1 notify -> 网关 BLE 适配器 ->
 *     data_converter.normalize_ble -> MQTT smarthome/v1/telemetry/ble/<id>
 *
 *   Node-RED / 上位机 -> smarthome/v1/command/ble/<id> ->
 *     网关 on_command -> BleReceiver.write -> GATT 0xFFE1 write ->
 *       HM-10 UART(RX) -> STM32 -> handle_command() -> 蜂鸣器
 *
 * 上行 JSON 帧（HM-10 单次 notify ≤19B；末尾 '\\n' 由 ble_println 加）：
 *   仅 l、d；l 为 lx 裁剪到 0~4095；例：{"l":320,"d":0}
 *
 * 下行命令 JSON：
 *   {"buzzer": true|false}             // 立即开/关
 *   {"beep": 3}                        // 鸣响 N 次
 *   {"beep": {"on":150,"off":150,"n":3}} // 自定义节奏
 *   {"auto": true}                     // 释放远程接管，恢复本地规则
 *
 * 跨节点 E2E：若命令含 ``src_seq``，执行蜂鸣类命令后经 BLE 再发一行 ``{"k":<seq>}``
 * （≤19B 适配 HM-10 单帧），统一模型里 ``payload.k`` 即对端脚本配对用的 ack。
 *
 * 本地边缘智能
 * -------------
 * 即便未与网关连接，环境转暗时本地短鸣 1 次提示；远程命令优先（s_remote_override）。
 */

#include <Arduino.h>
#include <ArduinoJson.h>

#include "ble_uart.h"
#include "buzzer.h"
#include "ldr.h"

static HardwareSerial SerialDbg(PA10, PA9);

// ============================ 用户配置 ==================================
static const char *DEVICE_ID = "b01";
static const uint32_t SAMPLE_INTERVAL_MS = 1000;

// ============================ 全局状态 ==================================
static uint32_t s_last_sample = 0;
static uint32_t s_seq = 0;
static bool     s_remote_override = false;
static bool     s_last_dark = false;

// ==================== 1. 上行：编码 + 发送 ==============================
static void publish_telemetry(const LdrSample &s) {
  JsonDocument doc;
  doc["l"] = s.light;
  doc["d"] = s.is_dark ? 1 : 0;

  char buf[48];
  size_t n = serializeJson(doc, buf, sizeof(buf));
  if (n == 0 || n >= sizeof(buf)) return;
  buf[n] = '\0';
  if (n > 19) {
    SerialDbg.println("[tx] WARN json>19B");
  }

  SerialDbg.print("[tx] ");
  SerialDbg.print(buf);
  SerialDbg.print(" json_bytes=");
  SerialDbg.println((int)n);

  ble_println(buf);
  s_seq++;
}

/** HM-10 单帧宜 ≤19B；仅用短键 ``k`` 回传 Node-RED 的 ``src_seq``。 */
static void send_ble_cmd_ack(long ack_seq) {
  if (ack_seq < 0L || !ble_is_connected()) return;
  char buf[24];
  int n = snprintf(buf, sizeof(buf), "{\"k\":%ld}", ack_seq);
  if (n <= 0 || n >= (int)sizeof(buf)) return;
  if (n > 19) {
    SerialDbg.println("[ack] src_seq too large for HM-10 19B frame");
    return;
  }
  SerialDbg.print("[ack] ");
  SerialDbg.println(buf);
  ble_println(buf);
}

// ==================== 2. 下行：解析并执行命令 ===========================
static void handle_command(const String &line) {
  if (line.length() == 0) return;
  SerialDbg.print("[rx] ");
  SerialDbg.println(line);

  JsonDocument doc;
  DeserializationError err = deserializeJson(doc, line);
  if (err) {
    SerialDbg.print("[cmd] json parse error: ");
    SerialDbg.println(err.c_str());
    return;
  }

  long cmd_src_seq = -1L;
  if (!doc["src_seq"].isNull()) {
    cmd_src_seq = doc["src_seq"].as<long>();
  }

  if (doc["buzzer"].is<bool>()) {
    bool on = doc["buzzer"].as<bool>();
    s_remote_override = true;
    if (on) buzzer_on();
    else    buzzer_off();
    SerialDbg.print("[cmd] buzzer=");
    SerialDbg.println(on ? "ON" : "OFF");
    send_ble_cmd_ack(cmd_src_seq);
    return;
  }

  if (doc["beep"].is<JsonObject>()) {
    JsonObject b = doc["beep"];
    uint16_t on  = b["on"]  | 150;
    uint16_t off = b["off"] | 150;
    uint8_t  n   = b["n"]   | 3;
    s_remote_override = true;
    buzzer_beep(on, off, n);
    SerialDbg.println("[cmd] beep custom");
    send_ble_cmd_ack(cmd_src_seq);
    return;
  }
  if (doc["beep"].is<int>()) {
    int n = doc["beep"].as<int>();
    s_remote_override = true;
    if (n > 0) {
      buzzer_beep(150, 150, static_cast<uint8_t>(n));
      SerialDbg.print("[cmd] beep x");
      SerialDbg.println(n);
    } else {
      buzzer_off();
      SerialDbg.println("[cmd] buzzer off (beep<=0)");
    }
    send_ble_cmd_ack(cmd_src_seq);
    return;
  }

  if (doc["auto"].is<bool>() && doc["auto"].as<bool>()) {
    s_remote_override = false;
    buzzer_off();
    SerialDbg.println("[cmd] release to local auto");
    return;
  }
}

// ==================== 3. 本地边缘智能：暗 -> 短鸣提示 ===================
static void update_local_rule(const LdrSample &s) {
  if (s_remote_override) return;

  if (s.is_dark && !s_last_dark) {
    buzzer_beep(120, 120, 1);
    SerialDbg.println("[rule] dark -> short beep");
  }
  s_last_dark = s.is_dark;
}

// ==================== 4. setup / loop ==================================
void setup() {
  SerialDbg.begin(115200);
  delay(300);
  SerialDbg.println();
  SerialDbg.println("================================================");
  SerialDbg.println(" SH-MP-EG STM32F103 BLE node boot");
  SerialDbg.println("================================================");

  buzzer_init();
  ldr_init();

  buzzer_beep(80, 80, 2);  // 上电短鸣 2 次提示

  SerialDbg.println("[boot] initializing HM-10 ...");
  bool at_ok = ble_init();
  SerialDbg.print("[boot] HM-10 AT ");
  SerialDbg.println(at_ok ? "OK" : "NO RESPONSE");

  SerialDbg.print("[boot] device_id=");  SerialDbg.println(DEVICE_ID);
  SerialDbg.println("[boot] Light=GY-302 I2C PB7/SDA PB6/SCL  Buzzer=PE0");
}

void loop() {
  buzzer_tick();

  String line;
  while (ble_try_read_line(line)) {
    handle_command(line);
  }

  uint32_t now = millis();
  if (now - s_last_sample >= SAMPLE_INTERVAL_MS) {
    s_last_sample = now;
    LdrSample s = ldr_read();

    update_local_rule(s);

    if (ble_is_connected()) {
      publish_telemetry(s);
    } else {
      static uint32_t t_last_hint = 0;
      if (now - t_last_hint > 5000) {
        SerialDbg.println("[ble] not connected (waiting central) ...");
        t_last_hint = now;
      }
      SerialDbg.print("[sample] light=");
      SerialDbg.print(s.light);
      SerialDbg.print(" dark=");
      SerialDbg.println(s.is_dark ? "1" : "0");
    }
  }

  delay(5);
}
