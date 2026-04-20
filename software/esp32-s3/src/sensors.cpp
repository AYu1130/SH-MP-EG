/**
 * sensors.cpp
 * ===========
 *
 * sensors.h 中声明的 DHT11 读取 + 共阴 RGB LED 控制实现。
 */

#include "sensors.h"

#include <DHTesp.h>

// --------------------- 内部状态 ---------------------------------------- //
static DHTesp s_dht;
static float s_last_temp = NAN;
static float s_last_hum  = NAN;
static unsigned long s_last_read_ms = 0;

static LedColor s_led_color = LED_OFF_C;
struct BlinkState {
  bool     active   = false;
  bool     phase_on = false;
  LedColor color    = LED_OFF_C;
  uint16_t on_ms    = 0;
  uint16_t off_ms   = 0;
  uint8_t  remaining = 0;
  unsigned long next_ms = 0;
};
static BlinkState s_blink;

// --------------------- 内部工具 ---------------------------------------- //
static inline void apply_color(const LedColor &c) {
#if LED_ACTIVE_HIGH
  digitalWrite(PIN_LED_R, c.r ? HIGH : LOW);
  digitalWrite(PIN_LED_G, c.g ? HIGH : LOW);
  digitalWrite(PIN_LED_B, c.b ? HIGH : LOW);
#else
  digitalWrite(PIN_LED_R, c.r ? LOW : HIGH);
  digitalWrite(PIN_LED_G, c.g ? LOW : HIGH);
  digitalWrite(PIN_LED_B, c.b ? LOW : HIGH);
#endif
  s_led_color = c;
}

// --------------------- 初始化 ------------------------------------------ //
bool sensors_init() {
  pinMode(PIN_LED_R, OUTPUT);
  pinMode(PIN_LED_G, OUTPUT);
  pinMode(PIN_LED_B, OUTPUT);
  apply_color(LED_OFF_C);

  pinMode(PIN_DHT, INPUT_PULLUP);
#if (DHT_TYPE == 22)
  s_dht.setup(PIN_DHT, DHTesp::DHT22);
#else
  s_dht.setup(PIN_DHT, DHTesp::DHT11);
#endif
  s_last_read_ms = 0;
  return true;
}

// --------------------- DHT 采样 ---------------------------------------- //
SensorPacket sensors_read(const char *node_id) {
  SensorPacket p{};
  p.node_id = node_id;

  const unsigned long now = millis();
  if (s_last_read_ms != 0 && (now - s_last_read_ms) < 2000) {
    p.temperature = isnan(s_last_temp) ? 0.0f : s_last_temp;
    p.humidity    = isnan(s_last_hum)  ? 0.0f : s_last_hum;
    p.battery     = 100;
    p.ts          = now / 1000UL;
    p.ok          = !(isnan(s_last_temp) || isnan(s_last_hum));
    return p;
  }
  s_last_read_ms = now;

  yield();
  TempAndHumidity th = s_dht.getTempAndHumidity();
  const float t = th.temperature;
  const float h = th.humidity;
  const bool readings_finite = !isnan(t) && !isnan(h);
  const bool status_ok = (s_dht.getStatus() == DHTesp::ERROR_NONE);

  if (readings_finite && status_ok) {
    s_last_temp = t;
    s_last_hum  = h;
    p.ok = true;
  } else {
    p.ok = false;
    Serial.printf("[dht] read failed: %s\n", s_dht.getStatusString());
  }

  p.temperature = isnan(s_last_temp) ? 0.0f : s_last_temp;
  p.humidity    = isnan(s_last_hum)  ? 0.0f : s_last_hum;
  p.battery     = 100;
  p.ts          = now / 1000UL;
  return p;
}

// --------------------- LED 控制 ---------------------------------------- //
void led_set(const LedColor &c) {
  s_blink.active = false;
  apply_color(c);
}

bool led_is_on() {
  return s_led_color.r || s_led_color.g || s_led_color.b;
}

void led_blink(const LedColor &c, uint16_t on_ms, uint16_t off_ms, uint8_t count) {
  if (on_ms < 20) on_ms = 20;
  if (off_ms < 20) off_ms = 20;
  s_blink.active   = true;
  s_blink.phase_on = true;
  s_blink.color    = c;
  s_blink.on_ms    = on_ms;
  s_blink.off_ms   = off_ms;
  s_blink.remaining = (count == 0) ? 0xFF : count;
  s_blink.next_ms  = millis() + on_ms;
  apply_color(c);
}

void led_tick() {
  if (!s_blink.active) return;
  unsigned long now = millis();
  if ((long)(now - s_blink.next_ms) < 0) return;

  if (s_blink.phase_on) {
    apply_color(LED_OFF_C);
    s_blink.phase_on = false;
    if (s_blink.remaining != 0xFF) {
      if (--s_blink.remaining == 0) {
        s_blink.active = false;
        return;
      }
    }
    s_blink.next_ms = now + s_blink.off_ms;
  } else {
    apply_color(s_blink.color);
    s_blink.phase_on = true;
    s_blink.next_ms = now + s_blink.on_ms;
  }
}
