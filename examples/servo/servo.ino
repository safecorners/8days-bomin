#include <ArduinoJson.h>
#include <Servo.h>

const int lightPin = A0;
const int servoPin = 9;

Servo myServo;

unsigned long lastSentTime = 0;
const int interval = 1000;

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(50);

  pinMode(lightPin, INPUT);

  myServo.attach(servoPin);

  myServo.write(90);
}

void loop() {
  if (Serial.available() > 0) {
    JsonDocument doc;

    DeserializationError error = deserializeJson(doc, Serial);

    if (!error) {
      if (doc.containsKey("type")) {
        String type = doc["type"];
        if (type == "servo") {
          if (doc.containsKey("angle")) {
            int angle = doc["angle"];
            myServo.write(angle);
          }
        }
      }
    }
  }

  unsigned long currentTime = millis();
  if (currentTime - lastSentTime >= interval) {
    int lightValue = analogRead(lightPin);

    JsonDocument doc;
    doc["type"] = "light";
    doc["value"] = lightValue;

    serializeJson(doc, Serial);
    Serial.println();

    lastSentTime = currentTime;
  }
}
