/**
 * ldr.cpp —— GY-302 (BH1750) I²C 照度采样
 *
 * 与战舰 V4 板载 24C02 共用 PB6/PB7；仅访问地址 0x23，不操作 EEPROM。
 */

#include "ldr.h"

#include <Wire.h>

// 战舰 V4：PB7=SDA, PB6=SCL（与 24C02 同总线）
static TwoWire s_bus(PB7, PB6);

static bool s_bh_ok = false;

static bool bh1750_write(uint8_t cmd) {
  s_bus.beginTransmission(BH1750_I2C_ADDR);
  s_bus.write(cmd);
  return s_bus.endTransmission() == 0;
}

/** 连续高分辨率模式；之后每 ~120ms 更新一次测量值（见 BH1750 datasheet） */
static constexpr uint8_t kModeContinuousHr = 0x10;
static constexpr uint8_t kPowerOn         = 0x01;

void ldr_init() {
  s_bus.begin();
  s_bh_ok = false;
  if (!bh1750_write(kPowerOn)) return;
  delay(2);
  if (!bh1750_write(kModeContinuousHr)) return;
  delay(130);  // 首帧测量时间
  s_bh_ok = true;
}

LdrSample ldr_read() {
  LdrSample s{};
  s.analog = false;

  if (!s_bh_ok) {
    s.light   = 0;
    s.is_dark = true;
    return s;
  }

  const uint8_t n = s_bus.requestFrom(static_cast<uint8_t>(BH1750_I2C_ADDR), static_cast<uint8_t>(2));
  if (n != 2) {
    s.light   = 0;
    s.is_dark = true;
    return s;
  }

  const uint16_t raw = (static_cast<uint16_t>(s_bus.read()) << 8) | static_cast<uint8_t>(s_bus.read());
  const float     lux = raw / 1.2f;

  s.analog = true;
  if (lux <= 0.0f) {
    s.light = 0;
  } else if (lux >= 4095.0f) {
    s.light = 4095;
  } else {
    s.light = static_cast<uint16_t>(lux + 0.5f);
  }
  s.is_dark = (lux < LIGHT_LUX_DARK_MAX);
  return s;
}

uint16_t ldr_read_light() {
  return ldr_read().light;
}
