const uint8_t BTN_UP = 18;
const uint8_t BTN_RIGHT = 19;
const uint8_t BTN_DOWN = 21;
const uint8_t BTN_LEFT = 22;

bool lastUp = HIGH;
bool lastRight = HIGH;
bool lastDown = HIGH;
bool lastLeft = HIGH;

void setup() {
  Serial.begin(115200);
  pinMode(BTN_UP, INPUT_PULLUP);
  pinMode(BTN_RIGHT, INPUT_PULLUP);
  pinMode(BTN_DOWN, INPUT_PULLUP);
  pinMode(BTN_LEFT, INPUT_PULLUP);
}

void sendOnPress(uint8_t pin, bool& lastState, const char* command) {
  bool current = digitalRead(pin);
  if (lastState == HIGH && current == LOW) {
    Serial.println(command);
  }
  lastState = current;
}

void loop() {
  sendOnPress(BTN_UP, lastUp, "UP");
  sendOnPress(BTN_RIGHT, lastRight, "RIGHT");
  sendOnPress(BTN_DOWN, lastDown, "DOWN");
  sendOnPress(BTN_LEFT, lastLeft, "LEFT");
}
