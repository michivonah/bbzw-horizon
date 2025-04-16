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

// Werte begrenzen (nur für sensible Werte wie Temp, Feuchte, VOC, Gas)
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

void setup() {
  Serial.begin(115200);
  while (!Serial);

  WiFi.begin(SSID, PASSWORT);
  Serial.print("Verbinde mit WLAN...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWLAN verbunden!");

  Wire.begin();

  // Automatische Adresserkennung
  bool sensorFound = false;
  byte sensorAddress;
  byte possibleAddresses[] = {0x76, 0x77};
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
    Serial.println("Kein BME680 gefunden!");
    while (1);
  }

  Serial.print("BME680 gefunden bei I2C-Adresse 0x");
  Serial.println(sensorAddress, HEX);
  iaqSensor.begin(sensorAddress, Wire);

  if (iaqSensor.bsecStatus != BSEC_OK) {
    Serial.print("BSEC Status Fehler: ");
    Serial.println(iaqSensor.bsecStatus);
    while (1);
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
}

void loop() {
  if (iaqSensor.run()) {
    float temperature = clampValue(iaqSensor.temperature);
    float humidity = clampValue(iaqSensor.humidity);
    float voc = clampValue(iaqSensor.iaq);
    float gas = clampValue(iaqSensor.gasResistance / 1000.0);
    float pressure = iaqSensor.pressure / 100.0; // <-- Kein Clamping hier!

    String timestamp = getTimestamp();

    // Debug-Ausgabe
    Serial.println("Messwerte:");
    Serial.println("Temp: " + String(temperature));
    Serial.println("Feuchte: " + String(humidity));
    Serial.println("Druck: " + String(pressure));
    Serial.println("VOC/IAQ: " + String(voc));
    Serial.println("Gas: " + String(gas));
    Serial.println("Zeit: " + timestamp);

    // JSON erstellen
    String payload = "{";
    payload += "\"timestamp\": \"" + timestamp + "\",";
    payload += "\"temperature\": " + String(temperature, 3) + ",";
    payload += "\"humidity\": " + String(humidity, 3) + ",";
    payload += "\"pressure\": " + String(pressure, 3) + ","; // unverfälscht
    payload += "\"voc\": " + String(voc, 3) + ",";
    payload += "\"gas\": " + String(gas, 3);
    payload += "}";

    String fullPath = String(API_ENDPOINT) + "?client=" + CLIENT_ID;

    Serial.println("Sende an API:");
    Serial.println(payload);

    client.beginRequest();
    client.post(fullPath);
    client.sendHeader("Content-Type", "application/json");
    client.sendHeader("token", API_TOKEN);
    client.sendHeader("Content-Length", payload.length());
    client.beginBody();
    client.print(payload);
    client.endRequest();

    int statusCode = client.responseStatusCode();
    String response = client.responseBody();

    Serial.print("Status: ");
    Serial.println(statusCode);
    Serial.print("Antwort: ");
    Serial.println(response);
  } else {
    Serial.println("Noch keine gültigen Daten von BSEC.");
  }

  delay(sendInterval);
}
