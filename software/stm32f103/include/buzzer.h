/**
 * buzzer.h
 * ========
 *
 * STM32F103 BLE 节点的有源蜂鸣器抽象层。
 *
 * 硬件接线：
 *   PE0 -> 有源蜂鸣器 IN（高电平鸣响；模块自带振荡）
 *   GND -> 蜂鸣器 GND
 *
 * 与 ESP32 上 sensors.h::buzzer_xxx 系列保持相同的非阻塞 API 命名，
 * 便于与文档/规则引擎概念一致。
 */

#ifndef BUZZER_H
#define BUZZER_H

#include <Arduino.h>

#ifndef BUZZER_PIN
#define BUZZER_PIN PE0
#endif

#ifndef BUZZER_ACTIVE_HIGH
#define BUZZER_ACTIVE_HIGH 1
#endif

void buzzer_init();

void buzzer_on();
void buzzer_off();
bool buzzer_is_on();

/**
 * 非阻塞 beep：on_ms 鸣响 + off_ms 间歇，重复 count 次（0 = 无限）。
 * 必须在 loop() 中周期调用 buzzer_tick() 才会推进。
 */
void buzzer_beep(uint16_t on_ms, uint16_t off_ms, uint8_t count);
void buzzer_tick();

#endif  // BUZZER_H
