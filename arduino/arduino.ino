#include <ArduinoJson.h>

// 입구와 출구를 분리해서 적외선 센서를 하나씩 둔다.
const int IN_PIN  = 2;   // 1번 = 입구 센서 → 막히면 입장(in)
const int OUT_PIN = 3;   // 2번 = 출구 센서 → 막히면 퇴장(out)

// 직전 루프에서 각 센서가 '막힌 상태'였는지 기억(같은 사람을 여러 번 세지 않기 위해)
bool inWasBlocked  = false;
bool outWasBlocked = false;

// FC-51 같은 디지털 IR 모듈은 무언가에 가려지면 LOW 신호를 낸다.
bool isBlocked(int pin) {
  return digitalRead(pin) == LOW;
}

// Streamlit으로 보낼 출입 이벤트 한 줄을 만든다. event는 "in" 또는 "out".
// (인원을 세거나 누적하는 일은 아두이노가 하지 않고, 집계는 Streamlit에서 한다.)
void sendGate(const char* event) {
  JsonDocument doc;
  doc["type"]  = "gate";
  doc["event"] = event;

  serializeJson(doc, Serial);
  Serial.println();
}

void setup() {
  Serial.begin(115200);

  pinMode(IN_PIN,  INPUT);   // 모듈에 따라 필요하면 INPUT_PULLUP
  pinMode(OUT_PIN, INPUT);
}

void loop() {
  bool inBlocked  = isBlocked(IN_PIN);
  bool outBlocked = isBlocked(OUT_PIN);

  // 비어 있다가 막히는 '그 순간'에만 한 번 보낸다(rising edge).
  // 사람이 센서 앞에 머무는 동안 계속 막혀 있어도 이벤트는 들어올 때 한 번만 나간다.
  if (inBlocked && !inWasBlocked) {
    sendGate("in");
  }
  if (outBlocked && !outWasBlocked) {
    sendGate("out");
  }

  // 다음 루프에서 비교하기 위해 지금 상태를 기억해 둔다.
  inWasBlocked  = inBlocked;
  outWasBlocked = outBlocked;
}
