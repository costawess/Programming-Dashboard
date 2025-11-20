#include <Arduino.h>

// UART2 pins (must match the wiring from the other device)
#define TXD2 17
#define RXD2 16

HardwareSerial SerialUART(2);

// Helper function: read a line from a Stream until '\n'
bool readLine(Stream &s, String &outLine) {
  if (!s.available()) {
    return false;
  }

  outLine = s.readStringUntil('\n');
  outLine.trim();
  if (outLine.length() == 0) {
    return false;
  }
  return true;
}

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    ; // wait for serial port to connect
  }

  SerialUART.begin(115200, SERIAL_8N1, RXD2, TXD2);

  Serial.println("ESP32 Tic-Tac-Toe bridge");
  Serial.println("Forwarding USB Serial <-> UART2 (lines terminated with \\n)");
}

void loop() {
  String msg;

  // 1) From UART2 to USB Serial (PC)
  if (readLine(SerialUART, msg)) {
    // Only forward the raw message to the PC
    Serial.println(msg);
  }

  // 2) From USB Serial (PC) to UART2
  if (readLine(Serial, msg)) {
    // Only forward the raw message to UART2
    SerialUART.println(msg);
  }
}
