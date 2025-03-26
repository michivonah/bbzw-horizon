#include <WiFiNINA.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME680.h>

#define SSID ""
#define PASSWORT ""
#define API_HOST ""  // Deine API-Domain
#define API_ENDPOINT "/sensor-data/"  // API-Endpunkt
#define API_PORT 8080  // Falls HTTPS, dann 443
#define CLIENT_ID "1.54"  // Eindeutige ID für den Arduino
#define API_TOKEN "test2"  // Setze hier dein API-Token

Adafruit_BME680 bme;
WiFiClient client;

void setup() {
    Serial.begin(115200);
    while (!Serial);

    if (WiFi.status() == WL_NO_MODULE) {
        Serial.println("WiFi-Modul nicht gefunden!");
        while (1);
    }

    WiFi.begin(SSID, PASSWORT);
    Serial.print("Verbinde mit WLAN...");
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWLAN verbunden!");

    if (!bme.begin()) {
        Serial.println("BME680 nicht gefunden!");
        while (1);
    }

    bme.setTemperatureOversampling(BME680_OS_8X);
    bme.setHumidityOversampling(BME680_OS_2X);
    bme.setPressureOversampling(BME680_OS_4X);
    bme.setIIRFilterSize(BME680_FILTER_SIZE_3);
    bme.setGasHeater(320, 150);
}

void loop() {
    if (!bme.performReading()) {
        Serial.println("Fehler beim Auslesen des BME680!");
        return;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("Sende Daten an API...");

        String jsonPayload = "{";
        jsonPayload += "\"token\": \"" + String(API_TOKEN) + "\",";
        jsonPayload += "\"clientid\": \"" + String(CLIENT_ID) + "\",";
        jsonPayload += "\"temperature\": " + String(bme.temperature) + ",";
        jsonPayload += "\"humidity\": " + String(bme.humidity) + ",";
        jsonPayload += "\"pressure\": " + String(bme.pressure / 100.0) + ",";
        jsonPayload += "\"voc\": " + String(0.0) + ","; // Falls VOC nicht gemessen wird
        jsonPayload += "\"gas\": " + String(bme.gas_resistance / 1000.0);
        jsonPayload += "}";

        if (client.connect(API_HOST, API_PORT)) {  // Falls HTTPS genutzt wird, dann WiFiSSLClient
            client.println("POST " + String(API_ENDPOINT) + " HTTP/1.1");
            client.println("Host: " + String(API_HOST));
            client.println("Content-Type: application/json");
            client.print("Content-Length: ");
            client.println(jsonPayload.length());
            client.println();
            client.println(jsonPayload);

            unsigned long timeout = millis() + 5000; // Wartezeit für die Antwort
            while (client.available() == 0) {
                if (millis() > timeout) {
                    Serial.println("Timeout bei API-Antwort!");
                    client.stop();
                    return;
                }
            }

            while (client.available()) {
                String response = client.readString();
                Serial.println("API Antwort: " + response);
            }
        } else {
            Serial.println("Fehler beim Verbinden mit API!");
        }

        client.stop();
    } else {
        Serial.println("WLAN nicht verbunden!");
    }

    delay(5000);
}
