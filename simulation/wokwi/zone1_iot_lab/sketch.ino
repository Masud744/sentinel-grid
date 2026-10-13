#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASS = "";

const char* BACKEND_URL = "https://automatically-boolean-easily-russia.trycloudflare.com/api/v1/ingest";
const char* ZONE_API_KEY = "zone-key-iot-lab-001";

#define PIN_FLAME    34
#define PIN_GAS      35
#define PIN_PIR      13
#define PIN_BUZZER   25
#define PIN_LED_RED  26
#define PIN_LED_YEL  27
#define PIN_LED_GRN  14
#define PIN_RELAY    32

unsigned long sequence_id = 0;
WiFiClientSecure secureClient;

// --- retry / failure tracking ---
int consecutiveFailures = 0;
const int MAX_FAILURES_BEFORE_WIFI_RESET = 5;

void setup() {
  Serial.begin(115200);
  delay(500);

  pinMode(PIN_FLAME, INPUT);
  pinMode(PIN_GAS, INPUT);
  pinMode(PIN_PIR, INPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_LED_RED, OUTPUT);
  pinMode(PIN_LED_YEL, OUTPUT);
  pinMode(PIN_LED_GRN, OUTPUT);
  pinMode(PIN_RELAY, OUTPUT);

  digitalWrite(PIN_LED_GRN, HIGH);
  digitalWrite(PIN_LED_YEL, LOW);
  digitalWrite(PIN_LED_RED, LOW);
  digitalWrite(PIN_BUZZER, LOW);
  digitalWrite(PIN_RELAY, LOW);

  connectWiFi();

  secureClient.setInsecure();
}

void connectWiFi() {
  Serial.println("[SCS-RG Zone 1: IoT Lab] Connecting to WiFi...");
  WiFi.disconnect(true);
  delay(200);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  unsigned long startAttempt = millis();
  while (WiFi.status() != WL_CONNECTED) {
    delay(200);
    Serial.print(".");
    // avoid infinite hang if WiFi never connects
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

void loop() {
  // --- WiFi health check ---
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[Zone 1] WiFi dropped, reconnecting...");
    connectWiFi();
  }

  sequence_id++;

  // --- Read raw sensors ---
  int flame_val   = digitalRead(PIN_FLAME) == LOW ? 1 : 0;
  float gas_val   = (float)analogRead(PIN_GAS) * (1000.0 / 4095.0);
  int pir_val     = digitalRead(PIN_PIR);

  // DEBUG: confirm ESP32 itself is seeing sensor changes
  Serial.printf("[DEBUG] flame=%d gas=%.1f pir=%d\n", flame_val, gas_val, pir_val);

  StaticJsonDocument<256> doc;
  doc["sequence_id"] = sequence_id;
  doc["timestamp"] = millis() / 1000;

  JsonObject sensors = doc.createNestedObject("sensors");
  sensors["fire_signal"] = flame_val;
  sensors["gas_level_raw"] = gas_val;
  sensors["water_level_raw"] = 0.0;
  sensors["occupancy_raw"] = pir_val;

  String jsonString;
  serializeJson(doc, jsonString);

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
        Serial.printf("[Zone 1] Sent Seq #%lu | Score: %.1f | State: %s\n",
                      sequence_id, resDoc["risk_score"].as<float>(), resDoc["state"].as<const char*>());
      } else {
        Serial.print("[Zone 1] JSON parse failed: ");
        Serial.println(err.c_str());
        Serial.println(response);
      }
    } else {
      Serial.printf("[Zone 1] HTTP POST Failed, code: %d (%s)\n",
                    httpCode, http.errorToString(httpCode).c_str());
    }

    http.end();
  } else {
    Serial.println("[Zone 1] http.begin() failed — check BACKEND_URL format");
  }

  if (!requestSucceeded) {
    consecutiveFailures++;
    Serial.printf("[Zone 1] consecutiveFailures = %d\n", consecutiveFailures);

    if (consecutiveFailures >= MAX_FAILURES_BEFORE_WIFI_RESET) {
      Serial.println("[Zone 1] Too many failures, resetting WiFi connection...");
      connectWiFi();
      consecutiveFailures = 0;
    }
  }

  // increased delay: reduces request rate, gives the free Cloudflare
  // quick-tunnel more breathing room (main cause of the -1 errors)
  delay(2000);
}
