const int DISPLAY_COUNT = 4;
unsigned long lastFrameMs = 0;
int counterValue = 0;

uint8_t encodeDigit(uint8_t digit) {
  static const uint8_t LUT[10] = {
    0b11111100, // 0
    0b01100000, // 1
    0b11011010, // 2
    0b11110010, // 3
    0b01100110, // 4
    0b10110110, // 5
    0b10111110, // 6
    0b11100000, // 7
    0b11111110, // 8
    0b11110110  // 9
  };
  return LUT[digit % 10];
}

String bits8(uint8_t value) {
  String out;
  for (int bit = 7; bit >= 0; --bit) out += ((value >> bit) & 0x01) ? '1' : '0';
  return out;
}

void sendDisplays(int value) {
  int digits[4] = {0, 0, 0, 0};
  int temp = value;
  for (int i = DISPLAY_COUNT - 1; i >= 0; --i) {
    digits[i] = temp % 10;
    temp /= 10;
  }

  String line = "DISPLAYS:";
  for (int i = 0; i < DISPLAY_COUNT; ++i) {
    if (i) line += ",";
    line += bits8(encodeDigit(digits[i]));
  }
  Serial.println(line);
}

void setup() {
  Serial.begin(115200);
  delay(250);
  sendDisplays(counterValue);
}

void loop() {
  if (millis() - lastFrameMs < 500) return;
  lastFrameMs = millis();
  sendDisplays(counterValue);
  counterValue = (counterValue + 1) % 10000;
}
