/**
 * main.cpp — SH-MP-EG ESP32-S3 Wi-Fi 终端节点
 * ==========================================
 *
 * 功能（互换执行器后）
 * --------------------
 * 1. 采集 DHT11 (GPIO4) 温湿度；
 * 2. 以 **扁平 JSON 行**（网关 ``normalize_wifi`` 入口）经 Wi-Fi + TCP 上报
 *    （默认端口 9000）；含 ``seq``、可选 ``send_ns``（NTP 对时后用于跨设备时延）；
 * 3. 边缘侧本地智能：温度越限本地把 RGB LED (R=GPIO7,G=GPIO6,B=GPIO5) 点红，
 *    退回阈值后熄灭；不依赖云端；
 * 4. 接收下行命令 ``{"led":"red"|"green"|...|"off"}`` /
 *    ``{"blink":{...}}`` / ``{"auto":true}``；远程命令优先于本地规则。
 *    若命令中含 ``src_seq``（Node-RED 跨节点联动），执行后立即经 TCP 回传一行
 *    ``{"id":...,"cmd_ack":<src_seq>,"ts":...}`` 供 ``cross_node_relay_test.py --stop-at device``
 *    统计「真机收到命令 → 网关 → MQTT」端到端时延。
 *
 * 关键配置
 * --------
 *   - WIFI_SSID / WIFI_PASSWORD : 默认对接树莓派热点 ``gateway`` / ``12345678``
 *   - GATEWAY_IP / GATEWAY_PORT : 网关 TCP 监听地址（默认热点下网关 IP）
 *   - SAMPLE_INTERVAL_MS        : 采样 / 上报周期
 *   - TEMP_ALARM_HIGH / LOW     : 本地 LED 报警阈值（带滞回）
 *
 * 调试串口 115200 bps。
 */

#include <Arduino.h>
#include <ArduinoJson.h>
#include <WiFi.h>
#include <time.h>

#include "sensors.h"

// =================================================================== //
// 1. 用户配置区：部署到真实环境时仅需改这里
// =================================================================== //
static const char *WIFI_SSID     = "gateway";
static const char *WIFI_PASSWORD = "12345678";

// 网关地址：与 gateway/python/config.py 中 wifi_tcp_port 对齐。
// 树莓派 NetworkManager 热点 (wlan1) 默认网关多为 10.42.0.1；hostapd 常见 192.168.4.1。
static const char    *GATEWAY_IP   = "10.42.0.1";
static const uint16_t GATEWAY_PORT = 9000;

// 采样 / 上报周期
static const uint32_t SAMPLE_INTERVAL_MS = 5000;

// 本地温度报警阈值（℃），带 1℃ 滞回
static const float TEMP_ALARM_HIGH = 30.0f;
static const float TEMP_ALARM_LOW  = 29.0f;

// TCP 心跳 / 重连参数
static const uint32_t TCP_RECONNECT_MS_MIN = 500;
static const uint32_t TCP_RECONNECT_MS_MAX = 10000;

// =================================================================== //
// 2. 全局状态
// =================================================================== //
static WiFiClient s_tcp;
static String     s_device_id;
static uint32_t   s_last_sample_ms = 0;
static uint32_t   s_next_reconnect_ms = 0;
static uint32_t   s_reconnect_backoff = TCP_RECONNECT_MS_MIN;
static bool       s_alarm_active = false;
static bool       s_remote_override = false;  // 远程命令接管期间不被本地规则反复覆盖
static uint32_t   s_seq = 0;
static bool       s_time_synced = false;
static uint32_t   s_last_ntp_chk_ms = 0;

static String s_rx_line;

// =================================================================== //
// 3. Wi-Fi / TCP 连接管理
// =================================================================== //
static bool wifi_connect(uint32_t timeout_ms = 20000) {
  Serial.printf("[wifi] connecting to \"%s\" ...\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.persistent(false);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  uint32_t t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < timeout_ms) {
    delay(200);
    Serial.print('.');
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    WiFi.setSleep(false);  // 关闭 Modem sleep，降低突发时延
    Serial.printf("[wifi] connected, ip=%s rssi=%d dBm (sleep=off)\n",
                  WiFi.localIP().toString().c_str(), WiFi.RSSI());
    return true;
  }
  Serial.println("[wifi] connect TIMEOUT; will keep retrying in loop");
  return false;
}

static bool tcp_try_connect() {
  if (s_tcp.connected()) return true;
  if (WiFi.status() != WL_CONNECTED) return false;

  uint32_t now = millis();
  if (now < s_next_reconnect_ms) return false;

  Serial.printf("[tcp] connecting %s:%u ...\n", GATEWAY_IP, GATEWAY_PORT);
  if (s_tcp.connect(GATEWAY_IP, GATEWAY_PORT, 3000)) {
    Serial.println("[tcp] connected.");
    s_tcp.setNoDelay(true);
    s_reconnect_backoff = TCP_RECONNECT_MS_MIN;
    s_rx_line = "";
    return true;
  }

  Serial.printf("[tcp] connect failed, retry in %u ms\n", s_reconnect_backoff);
  s_next_reconnect_ms = now + s_reconnect_backoff;
  s_reconnect_backoff = min<uint32_t>(s_reconnect_backoff * 2, TCP_RECONNECT_MS_MAX);
  return false;
}

/** SNTP：联网后自动拉取；成功后才写 ``send_ns``（与树莓派订阅端同一时钟系）。 */
static void ntp_poll() {
  if (WiFi.status() != WL_CONNECTED) return;
  static bool sntp_started = false;
  if (!sntp_started) {
    configTime(8 * 3600, 0, "pool.ntp.org", "cn.pool.ntp.org");
    sntp_started = true;
    Serial.println("[ntp] SNTP requested (GMT+8 offset)");
  }
  if (s_time_synced) return;
  if (millis() - s_last_ntp_chk_ms < 400) return;
  s_last_ntp_chk_ms = millis();
  time_t nowt = time(nullptr);
  if (nowt > 1700000000L) {
    s_time_synced = true;
    Serial.printf("[ntp] wall clock ok, unix=%ld\n", (long)nowt);
  }
}

// =================================================================== //
// 4. 下行命令处理（LED）
// =================================================================== //
static LedColor parse_color_name(const String &name) {
  String s(name); s.toLowerCase();
  if (s == "red")     return LED_RED_C;
  if (s == "green")   return LED_GREEN_C;
  if (s == "blue")    return LED_BLUE_C;
  if (s == "yellow")  return LED_YELLOW_C;
  if (s == "cyan")    return LED_CYAN_C;
  if (s == "magenta") return LED_MAGENTA_C;
  if (s == "white")   return LED_WHITE_C;
  return LED_OFF_C;
}

/** 跨节点 E2E：收到带 src_seq 的 LED 类命令后立刻经 TCP 上行一行 JSON。 */
static void send_cmd_ack_line(int64_t ack_seq) {
  if (!s_tcp.connected() || ack_seq < 0) return;

  JsonDocument doc;
  doc["id"]      = s_device_id;
  doc["cmd_ack"] = ack_seq;
  doc["ts"]      = (long)time(nullptr);

  char buf[160];
  size_t n = serializeJson(doc, buf, sizeof(buf));
  if (n == 0 || n >= sizeof(buf)) {
    Serial.println("[ack] serialize overflow, skip");
    return;
  }
  buf[n] = '\n';
  size_t w = s_tcp.write(reinterpret_cast<const uint8_t *>(buf), n + 1);
  if (w != n + 1) {
    Serial.println("[ack] tcp write failed");
    s_tcp.stop();
    return;
  }
  Serial.printf("[ack] cmd_ack seq=%lld\n", (long long)ack_seq);
}

static void handle_command(const String &line) {
  if (line.length() == 0) return;

  JsonDocument doc;
  DeserializationError err = deserializeJson(doc, line);
  if (err) {
    Serial.printf("[cmd] json parse error: %s | raw=%s\n",
                  err.c_str(), line.c_str());
    return;
  }

  // 网关 ACK：{"ok":true|false}
  if (doc["ok"].is<bool>()) {
    if (!doc["ok"].as<bool>()) Serial.println("[cmd] gateway NACK");
    return;
  }

  int64_t cmd_src_seq = -1;
  if (!doc["src_seq"].isNull()) {
    cmd_src_seq = doc["src_seq"].as<int64_t>();
  }

  if (doc["led"].is<const char *>()) {
    LedColor c = parse_color_name(String((const char *)doc["led"]));
    led_set(c);
    s_remote_override = true;
    Serial.printf("[cmd] led=%s\n", (const char *)doc["led"]);
    send_cmd_ack_line(cmd_src_seq);
    return;
  }

  if (doc["blink"].is<JsonObject>()) {
    JsonObject b = doc["blink"];
    LedColor c = parse_color_name(String((const char *)(b["color"] | "red")));
    uint16_t on  = b["on"]  | 200;
    uint16_t off = b["off"] | 200;
    uint8_t  n   = b["n"]   | 3;
    led_blink(c, on, off, n);
    s_remote_override = true;
    Serial.println("[cmd] led blink");
    send_cmd_ack_line(cmd_src_seq);
    return;
  }

  if (doc["auto"].is<bool>() && doc["auto"].as<bool>()) {
    s_remote_override = false;
    led_off();
    Serial.println("[cmd] release to local auto");
    return;
  }
}

/** 非阻塞读 TCP，按 '\n' 拆帧。 */
static void tcp_poll_rx() {
  while (s_tcp.connected() && s_tcp.available() > 0) {
    char c = static_cast<char>(s_tcp.read());
    if (c == '\n') {
      handle_command(s_rx_line);
      s_rx_line = "";
    } else if (c != '\r') {
      if (s_rx_line.length() < 512) s_rx_line += c;
      else s_rx_line = "";
    }
  }
}

// =================================================================== //
// 5. 上行遥测
// =================================================================== //
static void send_telemetry(const SensorPacket &p) {
  JsonDocument doc;
  doc["id"]      = s_device_id;
  doc["seq"]     = (uint32_t)s_seq;
  doc["t"]       = p.temperature;
  doc["h"]       = p.humidity;
  doc["battery"] = p.battery;
  doc["alarm"]   = s_alarm_active;
  doc["rssi"]    = WiFi.RSSI();
  doc["ts"]      = (long)time(nullptr);

  if (s_time_synced) {
    struct timespec ts;
    if (clock_gettime(CLOCK_REALTIME, &ts) == 0) {
      int64_t ns = (int64_t)ts.tv_sec * 1000000000LL + ts.tv_nsec;
      doc["send_ns"] = ns;
    }
  }

  char buf[384];
  size_t n = serializeJson(doc, buf, sizeof(buf));
  if (n == 0 || n >= sizeof(buf)) {
    Serial.println("[tx] serialize overflow, skip");
    return;
  }
  buf[n] = '\n';

  size_t written = s_tcp.write(reinterpret_cast<const uint8_t *>(buf), n + 1);
  if (written != n + 1) {
    Serial.println("[tx] partial write, drop TCP to reconnect");
    s_tcp.stop();
    return;
  }
  Serial.printf("[tx] seq=%lu t=%.1fC h=%.1f%% ok=%d bytes=%u send_ns=%s\n",
                (unsigned long)s_seq, p.temperature, p.humidity, p.ok, (unsigned)n + 1,
                s_time_synced ? "yes" : "pending-ntp");
  s_seq++;
}

// =================================================================== //
// 6. 本地阈值报警 -> RGB LED 红色
// =================================================================== //
static void update_local_alarm(float temperature, bool sensor_ok) {
  if (!sensor_ok) return;
  if (s_remote_override) return;  // 远程命令接管期间不覆盖

  if (!s_alarm_active && temperature > TEMP_ALARM_HIGH) {
    s_alarm_active = true;
    Serial.printf("[alarm] ENTER (t=%.1f > %.1f) -> LED RED\n",
                  temperature, TEMP_ALARM_HIGH);
    led_set(LED_RED_C);
  } else if (s_alarm_active && temperature < TEMP_ALARM_LOW) {
    s_alarm_active = false;
    Serial.printf("[alarm] LEAVE (t=%.1f < %.1f) -> LED OFF\n",
                  temperature, TEMP_ALARM_LOW);
    led_off();
  }
}

// =================================================================== //
// 7. setup / loop
// =================================================================== //
void setup() {
  Serial.begin(115200);
  delay(300);
  Serial.println();
  Serial.println("================================================");
  Serial.println(" SH-MP-EG ESP32-S3 Wi-Fi telemetry node boot    ");
  Serial.println("================================================");

  uint8_t mac[6];
  WiFi.macAddress(mac);
  char buf[24];
  snprintf(buf, sizeof(buf), "esp32-s3-%02x%02x%02x", mac[3], mac[4], mac[5]);
  s_device_id = buf;
  Serial.printf("[boot] device_id=%s\n", s_device_id.c_str());

  sensors_init();
  Serial.printf("[boot] DHT on GPIO%d, RGB LED R=GPIO%d G=GPIO%d B=GPIO%d\n",
                PIN_DHT, PIN_LED_R, PIN_LED_G, PIN_LED_B);
  delay(2000);

  // 上电自检：蓝色闪 2 下
  led_blink(LED_BLUE_C, 100, 100, 2);

  wifi_connect();
}

void loop() {
  led_tick();

  if (WiFi.status() != WL_CONNECTED) {
    static uint32_t t_last_warn = 0;
    if (millis() - t_last_warn > 5000) {
      Serial.println("[wifi] disconnected, waiting auto-reconnect ...");
      t_last_warn = millis();
    }
    delay(200);
    return;
  }

  if (!s_tcp.connected()) {
    tcp_try_connect();
  }

  tcp_poll_rx();
  ntp_poll();

  if (millis() - s_last_sample_ms >= SAMPLE_INTERVAL_MS) {
    s_last_sample_ms = millis();
    SensorPacket p = sensors_read(s_device_id.c_str());

    update_local_alarm(p.temperature, p.ok);

    if (s_tcp.connected()) {
      send_telemetry(p);
    }
  }

  delay(10);
}
