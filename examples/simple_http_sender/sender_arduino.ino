/**
 * examples/simple_http_sender/sender_arduino.ino
 * -----------------------------------------------------------------
 * ESP32-S3 示范：用 WiFi + HTTPClient 把温湿度 JSON 发给网关。
 * 仅作为 **网络层** 骨架参考，MCU 代码由感知层同学后续补全。
 */

#include <WiFi.h>
#include <HTTPClient.h>

// ---- 请修改以下常量 ----------------------------------------------------- //
const char* WIFI_SSID = "YOUR_SSID";
const char* WIFI_PASS = "YOUR_PASS";
const char* GW_URL    = "http://192.168.1.10:8080/api/v1/telemetry";
const char* DEVICE_ID = "esp32-s3-node-01";

void setup() {
  Serial.begin(115200);
  Serial.println("connecting wifi ...");
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print('.'); }
  Serial.printf("\nip=%s\n", WiFi.localIP().toString().c_str());
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) { delay(500); return; }

  // 这里仅用随机数演示；真实实现请替换为 DHT22 采样
  float t = 22.0 + (float)random(0, 500) / 100.0;
  float h = 55.0 + (float)random(0, 200) / 100.0;
  int   l = random(100, 700);

  char body[128];
  snprintf(body, sizeof(body),
           "{\"id\":\"%s\",\"t\":%.1f,\"h\":%.1f,\"l\":%d}",
           DEVICE_ID, t, h, l);

  HTTPClient http;
  http.begin(GW_URL);
  http.addHeader("Content-Type", "application/json");
  int code = http.POST((uint8_t*)body, strlen(body));
  Serial.printf("POST %s -> %d\n", body, code);
  http.end();

  delay(5000);  // 5s 间隔
}
