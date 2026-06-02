#include <ArduinoJson.h>

unsigned long lastSentTime = 0;
const int interval = 1000;

void setup() {
  Serial.begin(9600);
  Serial.setTimeout(50);

}

void loop() {
  
  unsigned long currentTime = millis();
  if (currentTime - lastSentTime >= interval) {
    int value = analogRead(lightPin);

    JsonDocument doc;

    // TODO:

    serializeJson(doc, Serial);
    Serial.println();

    lastSentTime = currentTime;
  }
}
