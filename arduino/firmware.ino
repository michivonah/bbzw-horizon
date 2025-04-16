#include <WiFiNINA.h>
#include <Wire.h>
#include "bsec.h"
#include <ArduinoHttpClient.h>
#include <WiFiUdp.h>
#include <NTPClient.h>

// WLAN-Zugangsdaten
#define SSID ""
#define PASSWORT ""

// API-Konfiguration
#define API_HOST ""
#define API_PORT 8080
#define API_ENDPOINT "/sensors/push-data"
#define CLIENT_ID ""
#define API_TOKEN ""

// Sensor & Netzwerk
Bsec iaqSensor;
WiFiClient wifi;
HttpClient client = HttpClient(wifi, API_HOST, API_PORT);

// NTP-Client
WiFiUDP ntpUDP;
const long utcOffsetInSeconds = 0;
NTPClient timeClient(ntpUDP, "pool.ntp.org", utcOffsetInSeconds);

// Sendeintervall
unsigned long sendInterval = 30000;

// Fehlercode per LED ausgeben (Morse-artig)
void errorBlink(int code) {
  while (true) {
    for (int i = 0; i < code; i++) {
      digitalWrite(LED_BUILTIN, HIGH);
      delay(150);
      digitalWrite(LED_BUILTIN, LOW);
      delay(150);
    }
    delay(1000); // Pause zwischen Zyklen
  }
}

// Werte begrenzen
float clampValue(float val) {
  if (val >= 1000.0) return 999.999;
  if (val <= -1000.0) return -999.999;
  return val;
}

// ISO-Zeitstempel generieren
String getTimestamp() {
  timeClient.update();
  unsigned long epochTime = timeClient.getEpochTime();
  int year = 1970;
  unsigned long seconds = epochTime;

  while (true) {
    bool leap = (year % 4 == 0 && (year % 100 != 0 || year % 400 == 0));
    int daysInYear = leap ? 366 : 365;
    if (seconds >= daysInYear * 86400UL) {
      seconds -= daysInYear * 86400UL;
      year++;
    } else {
      break;
    }
  }

  int month = 1;
  const int daysInMonth[] = {31,28,31,30,31,30,31,31,30,31,30,31};
  while (month <= 12) {
    int dim = daysInMonth[month - 1];
    if (month == 2 && (year % 4 == 0 && (year % 100 != 0 || year % 400 == 0))) {
      dim = 29;
    }
    if (seconds >= dim * 86400UL) {
      seconds -= dim * 86400UL;
      month++;
    } else {
      break;
    }
  }

  int day = seconds / 86400UL + 1;
  seconds = seconds % 86400UL;
  int hour = seconds / 3600UL;
  seconds = seconds % 3600UL;
  int minute = seconds / 60UL;
  int second = seconds % 60UL;

  char buf[30];
  sprintf(buf, "%04d-%02d-%02dT%02d:%02d:%02dZ", year, month, day, hour, minute, second);
  return String(buf);
}

// API-Health-Check
bool checkApiHealth() {
  HttpClient healthClient = HttpClient(wifi, API_HOST, API_PORT);
  healthClient.get("/health");
  int statusCode = healthClient.responseStatusCode();
  healthClient.stop();
  return statusCode == 200;
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  // WLAN verbinden mit Timeout
  WiFi.begin(SSID, PASSWORT);
  unsigned long startAttemptTime = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < 20000) {
    delay(500);
  }
  if (WiFi.status() != WL_CONNECTED) {
    errorBlink(1); // Fehlercode 1: WLAN-Fehler
  }

  // API-Healthcheck
  if (!checkApiHealth()) {
    errorBlink(4); // Fehlercode 4: API nicht erreichbar
  }

  Wire.begin();

  // Automatische Sensor-Erkennung
  byte sensorAddress = 0;
  byte possibleAddresses[] = {0x76, 0x77};
  bool sensorFound = false;
  for (int i = 0; i < 2; i++) {
    byte addr = possibleAddresses[i];
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      sensorAddress = addr;
      sensorFound = true;
      break;
    }
  }

  if (!sensorFound) {
    errorBlink(2); // Fehlercode 2: Sensor nicht gefunden
  }

  iaqSensor.begin(sensorAddress, Wire);
  if (iaqSensor.bsecStatus != BSEC_OK) {
    errorBlink(3); // Fehlercode 3: Sensor-Init fehlgeschlagen
  }

  bsec_virtual_sensor_t sensorList[] = {
    BSEC_OUTPUT_IAQ,
    BSEC_OUTPUT_SENSOR_HEAT_COMPENSATED_TEMPERATURE,
    BSEC_OUTPUT_SENSOR_HEAT_COMPENSATED_HUMIDITY,
    BSEC_OUTPUT_RAW_PRESSURE,
    BSEC_OUTPUT_RAW_GAS
  };
  iaqSensor.updateSubscription(sensorList, 5, BSEC_SAMPLE_RATE_LP);

  timeClient.begin();
  while (!timeClient.update()) {
    timeClient.forceUpdate();
  }

  digitalWrite(LED_BUILTIN, HIGH); // Alles bereit – LED dauerhaft an
}

void loop() {
  if (iaqSensor.run()) {
    // Kurzes LED-Blink zur Messanzeige
    digitalWrite(LED_BUILTIN, LOW);
    delay(100);
    digitalWrite(LED_BUILTIN, HIGH);

    float temperature = clampValue(iaqSensor.temperature);
    float humidity = clampValue(iaqSensor.humidity);
    float voc = clampValue(iaqSensor.iaq);
    float gas = clampValue(iaqSensor.gasResistance / 1000.0);
    float pressure = iaqSensor.pressure / 100.0;

    String timestamp = getTimestamp();

    String payload = "{";
    payload += "\"timestamp\": \"" + timestamp + "\",";
    payload += "\"temperature\": " + String(temperature, 3) + ",";
    payload += "\"humidity\": " + String(humidity, 3) + ",";
    payload += "\"pressure\": " + String(pressure, 3) + ",";
    payload += "\"voc\": " + String(voc, 3) + ",";
    payload += "\"gas\": " + String(gas, 3);
    payload += "}";

    String fullPath = String(API_ENDPOINT) + "?client=" + CLIENT_ID;

    client.beginRequest();
    client.post(fullPath);
    client.sendHeader("Content-Type", "application/json");
    client.sendHeader("token", API_TOKEN);
    client.sendHeader("Content-Length", payload.length());
    client.beginBody();
    client.print(payload);
    client.endRequest();

    client.responseStatusCode();
    client.responseBody();
  }

  delay(sendInterval);
}
