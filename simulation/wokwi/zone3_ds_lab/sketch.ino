/*
 * Smart Campus Safety & Response Grid (SCS-RG)
 * Zone 3: Data Science & AI Lab — ESP32 Sensor Node Firmware
 *
 * Sensors:
 *   - Flame Sensor       → GPIO 34 (Digital, active-LOW)
 *   - Gas Sensor (MQ-2)  → GPIO 35 (Analog, 0–1000 PPM range)
 *   - PIR Motion Sensor   → GPIO 13 (Digital, HIGH = motion)
 *
 * Actuators:
 *   - Buzzer   → GPIO 25
 *   - Red LED  → GPIO 26
 *   - Yellow LED → GPIO 27
 *   - Green LED → GPIO 14
 *   - Relay (power cut) → GPIO 32
 *
 * Wiring notes (diagram.json must match):
 *   ESP32 3V3 → flame VCC, MQ-2 VCC
 *   ESP32 5V  → PIR VCC, relay VCC
 *   ESP32 GND → all component GNDs (flame, mq2, pir, buzzer, led cathodes, relay)
 *   Signal pins as listed above
 *
 * Note: DS Lab uses gas sensor (like IoT Lab) but no water sensor.
 *       water_level_raw is always sent as 0.0 to backend.
 */

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ─── Configuration ───────────────────────────────────────────────
const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASS = "";

// ⚠️ UPDATE THIS URL each time you start a new Cloudflare quick-tunnel
const char* BACKEND_URL = "https://automatically-boolean-easily-russia.trycloudflare.com/api/v1/ingest";
const char* ZONE_API_KEY = "zone-key-ds-lab-001";

// ─── Pin Definitions ─────────────────────────────────────────────
#define PIN_FLAME    34   // Flame sensor digital out
#define PIN_GAS      35   // MQ-2 gas sensor analog out
#define PIN_PIR      13   // PIR motion sensor

#define PIN_BUZZER   25   // Buzzer
#define PIN_LED_RED  26   // Red LED (CRITICAL)
#define PIN_LED_YEL  27   // Yellow LED (WARNING)
#define PIN_LED_GRN  14   // Green LED (SAFE)
#define PIN_RELAY    32   // Relay module (power cut)

// ─── State ───────────────────────────────────────────────────────
unsigned long sequence_id = 0;
WiFiClientSecure secureClient;

int consecutiveFailures = 0;
const int MAX_FAILURES_BEFORE_WIFI_RESET = 5;

// ─── Setup ───────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  delay(500);

  // Sensor pins
  pinMode(PIN_FLAME, INPUT);
  pinMode(PIN_GAS, INPUT);
  pinMode(PIN_PIR, INPUT);

  // Actuator pins
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_LED_RED, OUTPUT);
  pinMode(PIN_LED_YEL, OUTPUT);
  pinMode(PIN_LED_GRN, OUTPUT);
  pinMode(PIN_RELAY, OUTPUT);

  // Default state: SAFE (green on, rest off)
  digitalWrite(PIN_LED_GRN, HIGH);
  digitalWrite(PIN_LED_YEL, LOW);
  digitalWrite(PIN_LED_RED, LOW);
  digitalWrite(PIN_BUZZER, LOW);
  digitalWrite(PIN_RELAY, LOW);

  connectWiFi();

  // Skip TLS certificate verification (Wokwi → Cloudflare quick-tunnel)
  secureClient.setInsecure();
}

// ─── WiFi Connection with Timeout ────────────────────────────────
void connectWiFi() {
  Serial.println("[SCS-RG Zone 3: DS Lab] Connecting to WiFi...");
  WiFi.disconnect(true);
  delay(200);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  unsigned long startAttempt = millis();
  while (WiFi.status() != WL_CONNECTED) {
    delay(200);
    Serial.print(".");
    if (millis() - startAttempt > 20000) {
      Serial.println("\n[WiFi] Connection attempt timed out, retrying...");
      WiFi.disconnect(true);
      delay(500);
      WiFi.begin(WIFI_SSID, WIFI_PASS);
      startAttempt = millis();
    }
  }
  Serial.println("\nWiFi Connected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

// ─── Actuator Control ────────────────────────────────────────────
void applyActuation(bool buzzer, String led, bool relay) {
  digitalWrite(PIN_BUZZER, buzzer ? HIGH : LOW);
  digitalWrite(PIN_RELAY, relay ? HIGH : LOW);

  if (led == "RED") {
    digitalWrite(PIN_LED_RED, HIGH);
    digitalWrite(PIN_LED_YEL, LOW);
    digitalWrite(PIN_LED_GRN, LOW);
  } else if (led == "YELLOW") {
    digitalWrite(PIN_LED_RED, LOW);
    digitalWrite(PIN_LED_YEL, HIGH);
    digitalWrite(PIN_LED_GRN, LOW);
  } else {
    digitalWrite(PIN_LED_RED, LOW);
    digitalWrite(PIN_LED_YEL, LOW);
    digitalWrite(PIN_LED_GRN, HIGH);
  }
}

// ─── Main Loop ───────────────────────────────────────────────────
void loop() {
  // WiFi health check
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[Zone 3] WiFi dropped, reconnecting...");
    connectWiFi();
  }

  sequence_id++;

  // ── Read sensors ──
  // Flame: active-LOW (LOW = fire detected → 1)
  int flame_val   = digitalRead(PIN_FLAME) == LOW ? 1 : 0;
  // Gas: MQ-2 analog → scale ADC (0–4095) to 0–1000 PPM
  float gas_val   = (float)analogRead(PIN_GAS) * (1000.0 / 4095.0);
  // PIR: HIGH = motion detected
  int pir_val     = digitalRead(PIN_PIR);

  // Debug output so you can see raw values in serial monitor
  Serial.printf("[DEBUG] flame=%d gas=%.1f ppm pir=%d\n", flame_val, gas_val, pir_val);

  // ── Build JSON payload ──
  StaticJsonDocument<256> doc;
  doc["sequence_id"] = sequence_id;
  doc["timestamp"] = millis() / 1000;

  JsonObject sensors = doc.createNestedObject("sensors");
  sensors["fire_signal"]     = flame_val;
  sensors["gas_level_raw"]   = gas_val;      // DS Lab: gas detection
  sensors["water_level_raw"] = 0.0;          // DS Lab: no water sensor
  sensors["occupancy_raw"]   = pir_val;

  String jsonString;
  serializeJson(doc, jsonString);

  // ── Send to backend via HTTPS ──
  HTTPClient http;
  bool requestSucceeded = false;

  if (http.begin(secureClient, BACKEND_URL)) {
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-Zone-API-Key", ZONE_API_KEY);
    http.setConnectTimeout(10000);
    http.setTimeout(10000);

    int httpCode = http.POST(jsonString);

    if (httpCode == 200) {
      requestSucceeded = true;
      consecutiveFailures = 0;

      String response = http.getString();
      StaticJsonDocument<512> resDoc;
      DeserializationError err = deserializeJson(resDoc, response);

      if (!err) {
        JsonObject actuation = resDoc["actuation"];
        bool buzzer = actuation["buzzer"];
        String led = actuation["led"].as<String>();
        bool relay = actuation["relay_power_cut"];

        applyActuation(buzzer, led, relay);
        Serial.printf("[Zone 3] Sent Seq #%lu | Score: %.1f | State: %s\n",
                      sequence_id, resDoc["risk_score"].as<float>(), resDoc["state"].as<const char*>());
      } else {
        Serial.print("[Zone 3] JSON parse failed: ");
        Serial.println(err.c_str());
        Serial.println(response);
      }
    } else {
      Serial.printf("[Zone 3] HTTP POST Failed, code: %d (%s)\n",
                    httpCode, http.errorToString(httpCode).c_str());
    }

    http.end();
  } else {
    Serial.println("[Zone 3] http.begin() failed — check BACKEND_URL format");
  }

  if (!requestSucceeded) {
    consecutiveFailures++;
    Serial.printf("[Zone 3] consecutiveFailures = %d\n", consecutiveFailures);

    if (consecutiveFailures >= MAX_FAILURES_BEFORE_WIFI_RESET) {
      Serial.println("[Zone 3] Too many failures, resetting WiFi connection...");
      connectWiFi();
      consecutiveFailures = 0;
    }
  }

  // 2s delay: reduces request rate, gives Cloudflare quick-tunnel breathing room
  delay(2000);
}
