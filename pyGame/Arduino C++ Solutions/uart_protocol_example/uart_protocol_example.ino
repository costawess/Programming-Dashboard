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

  // Read up to newline
  outLine = s.readStringUntil('\n');
  outLine.trim();

  if (outLine.length() == 0) {
    return false;
  }

  return true;
}

void setup() {
  // USB serial (PC side)
  Serial.begin(115200);
  while (!Serial) {
    ; // wait for serial port to connect
  }

  // UART2 (other device side: second ESP / external UART / etc.)
  SerialUART.begin(115200, SERIAL_8N1, RXD2, TXD2);

  Serial.println("ESP32 Tic-Tac-Toe bridge");
  Serial.println("Forwarding lines between USB Serial <-> UART2");
  Serial.println("Protocol example: SYMBOL:SELECTED:X | MOVE:1,2,X");
}

void loop() {
  String msg;

  // 1) From UART2 to USB Serial (PC)
  if (readLine(SerialUART, msg)) {
    // Debug print
    Serial.print("[UART2 -> USB] ");
    Serial.println(msg);

    // Forward exactly the same message to USB Serial
    Serial.print(msg);
    Serial.print('\n');
  }

  // 2) From USB Serial (PC) to UART2
  if (readLine(Serial, msg)) {
    // Debug print
    Serial.print("[USB -> UART2] ");
    Serial.println(msg);

    // Forward exactly the same message to UART2
    SerialUART.print(msg);
    SerialUART.print('\n');
  }
}
