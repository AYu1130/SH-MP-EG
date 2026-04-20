/**
 * sensors.h
 * =========
 *
 * ESP32-S3 Wi-Fi 终端节点 —— 传感器与执行器抽象层。
 *
 * 硬件接线（互换执行器后；与 docs/hardware/wiring_guide.md 同步）：
 *   - GPIO 4 : DHT11 DATA（单总线温湿度；裸芯片需外接 10kΩ 上拉）
 *   - GPIO 7 : RGB LED R（共阴模块，高电平点亮）
 *   - GPIO 6 : RGB LED G
 *   - GPIO 5 : RGB LED B
 *
 * 设计原则:
 *   1. 所有与硬件强耦合的逻辑封装在本文件 + sensors.cpp 中；
 *   2. DHT11 采样受 1Hz 硬件限制；读失败时返回上一次有效值并置 ok=false；
 *   3. LED 提供 on_color / off / 非阻塞 blink，便于 main.cpp 联动远程命令。
 */

#ifndef SENSORS_H
#define SENSORS_H

#include <Arduino.h>

// ---------- 硬件引脚（可由 build_flags 覆盖） ---------------------------- //
#ifndef PIN_DHT
#define PIN_DHT 4
#endif

#ifndef PIN_LED_R
#define PIN_LED_R 7
#endif
#ifndef PIN_LED_G
#define PIN_LED_G 6
#endif
#ifndef PIN_LED_B
#define PIN_LED_B 5
#endif

// DHT 芯片类型，11 = DHT11，22 = DHT22
#ifndef DHT_TYPE
#define DHT_TYPE 11
#endif

// 共阴 RGB LED 默认高电平点亮；共阳模块改为 0
#ifndef LED_ACTIVE_HIGH
#define LED_ACTIVE_HIGH 1
#endif

// ---------- 数据结构 ------------------------------------------------------ //
struct SensorPacket {
  const char *node_id;
  float temperature;
  float humidity;
  int   battery;
  unsigned long ts;
  bool  ok;
};

struct LedColor { bool r; bool g; bool b; };

static const LedColor LED_OFF_C    {false, false, false};
static const LedColor LED_RED_C    {true,  false, false};
static const LedColor LED_GREEN_C  {false, true,  false};
static const LedColor LED_BLUE_C   {false, false, true};
static const LedColor LED_YELLOW_C {true,  true,  false};
static const LedColor LED_CYAN_C   {false, true,  true};
static const LedColor LED_MAGENTA_C{true,  false, true};
static const LedColor LED_WHITE_C  {true,  true,  true};

// ---------- 初始化 / 采样 ------------------------------------------------- //
bool sensors_init();
SensorPacket sensors_read(const char *node_id);

// ---------- LED 控制 ----------------------------------------------------- //
/** 立即设置颜色；同时取消进行中的 blink 任务。 */
void led_set(const LedColor &c);
inline void led_off() { led_set(LED_OFF_C); }
bool led_is_on();

/** 非阻塞 blink：on_ms 亮 + off_ms 灭，循环 count 次（0 = 无限）。 */
void led_blink(const LedColor &c, uint16_t on_ms, uint16_t off_ms, uint8_t count);

/** 在 loop() 中周期调用以推进 blink 状态机。 */
void led_tick();

#endif  // SENSORS_H
