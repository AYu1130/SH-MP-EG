/**
 * ldr.h
 * =====
 *
 * 环境光采样抽象（实现为 **GY-302 / BH1750**，I²C 数字照度，单位 lx）。
 *
 * 硬件（战舰 V4 与板载 24C02 共 I²C 总线）
 * ----------------------------------------
 *   - **PB7** = SDA（与 24C02 SDA 同总线）
 *   - **PB6** = SCL（与 24C02 SCL 同总线）
 *   - GY-302 **VCC/GND** 与 MCU 共地；ADDR 接低时器件地址 **0x23**（与 24C02 0x50 不冲突）
 *
 * 上报字段
 * --------
 *   - ``light``：将 lx **上限裁剪到 4095** 填入 JSON 的 ``l``，与网关 0~4095 约定一致；
 *   - ``is_dark``：lx 低于 ``LIGHT_LUX_DARK_MAX``（默认约 80 lx，可在 build_flags 覆盖）为 true；
 *   - ``analog``：BH1750 读成功为 true。
 */

#ifndef LDR_H
#define LDR_H

#include <Arduino.h>

/** I²C 从机地址（GY-302 ADDR 接 GND 时为 0x23） */
#ifndef BH1750_I2C_ADDR
#define BH1750_I2C_ADDR 0x23
#endif

/** 低于该照度 (lx) 视为偏暗，JSON 中 ``d``=1 */
#ifndef LIGHT_LUX_DARK_MAX
#define LIGHT_LUX_DARK_MAX 80.0f
#endif

struct LdrSample {
  uint16_t light;     // 0~4095：由 lx 裁剪得到，供 JSON 字段 ``l``
  bool     is_dark;   // lx < LIGHT_LUX_DARK_MAX
  bool     analog;    // true = 本次 BH1750 读成功
};

void ldr_init();
LdrSample ldr_read();
uint16_t ldr_read_light();

#endif  // LDR_H
