/**
 * buzzer.cpp —— STM32F103 PE0 有源蜂鸣器，非阻塞控制。
 */

#include "buzzer.h"

struct BuzzerState {
  bool     active   = false;
  bool     phase_on = false;
  uint16_t on_ms    = 0;
  uint16_t off_ms   = 0;
  uint8_t  remaining = 0;     // 0xFF -> 无限
  uint32_t next_ms  = 0;
};
static BuzzerState s_buzzer;
static bool s_level = false;

static inline void buzzer_write(bool on) {
  s_level = on;
#if BUZZER_ACTIVE_HIGH
  digitalWrite(BUZZER_PIN, on ? HIGH : LOW);
#else
  digitalWrite(BUZZER_PIN, on ? LOW : HIGH);
#endif
}

void buzzer_init() {
  pinMode(BUZZER_PIN, OUTPUT);
  buzzer_write(false);
}

void buzzer_on() {
  s_buzzer.active = false;
  buzzer_write(true);
}

void buzzer_off() {
  s_buzzer.active = false;
  buzzer_write(false);
}

bool buzzer_is_on() {
  return s_level;
}

void buzzer_beep(uint16_t on_ms, uint16_t off_ms, uint8_t count) {
  if (on_ms < 20) on_ms = 20;
  if (off_ms < 20) off_ms = 20;
  s_buzzer.on_ms     = on_ms;
  s_buzzer.off_ms    = off_ms;
  s_buzzer.remaining = (count == 0) ? 0xFF : count;
  s_buzzer.phase_on  = true;
  s_buzzer.active    = true;
  s_buzzer.next_ms   = millis() + on_ms;
  buzzer_write(true);
}

void buzzer_tick() {
  if (!s_buzzer.active) return;
  uint32_t now = millis();
  if ((int32_t)(now - s_buzzer.next_ms) < 0) return;

  if (s_buzzer.phase_on) {
    buzzer_write(false);
    s_buzzer.phase_on = false;
    if (s_buzzer.remaining != 0xFF) {
      if (--s_buzzer.remaining == 0) {
        s_buzzer.active = false;
        return;
      }
    }
    s_buzzer.next_ms = now + s_buzzer.off_ms;
  } else {
    buzzer_write(true);
    s_buzzer.phase_on = true;
    s_buzzer.next_ms = now + s_buzzer.on_ms;
  }
}
