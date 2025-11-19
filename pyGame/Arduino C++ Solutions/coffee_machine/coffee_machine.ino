// Hanze Coffee Machine
// Drinks: Espresso, Cappuccino, Tomato Soup

// LED pins
int LEDs[] = {23, 22, 21, 4};  // espresso, cappuccino, tomato soup, ready

// States
const int S_IDLE        = 0;
const int S_SELECT      = 1;
const int S_CUSTOMIZE   = 2;
const int S_PREPARE     = 3;
const int S_DONE        = 4;

// Drinks
int D_NONE        = 0;
int D_ESPRESSO    = 1;
int D_CAPPUCCINO  = 2;
int D_TOMATO      = 3;
int D_CHOCOLATE   = 4;

// Start
int state = S_IDLE;
int drink = D_NONE;

// Customization
int  sugarLevel    = 0;   // 0=no sugar, 1=low, 2=medium, 3=high
int  strengthLevel = 0;   // 0=mild, 1=medium, 2=strong
bool withMilk      = false;

// function to read User Serial input (reads keyboard)
String readLine() {
  while (!Serial.available()) { delay(5); }
  String s = Serial.readStringUntil('\n');
  s.trim();
  return s;
}

// function to read int values constrained by low (lo) and high (hi)
int readIntInRange(int lo, int hi) {
  while (true) {
    String s = readLine();
    long v = s.toInt(); // returns 0 if not numeric

    // if the lenght is not 0 (empty) and value!=0 
    if (s.length() > 0 && (v != 0 || s == "0")) {
      // check range
      if (v >= lo && v <= hi) return v;
    }
    Serial.println("Invalid input. Please input the value within range.");
  }
}

// function to read yes or no
bool readYesNo() {
  while (true) {
    String s = readLine();
    s.toLowerCase();
    if (s == "y" || s == "yes") return true;
    if (s == "n" || s == "no")  return false;
    Serial.println("Please answer with 'y' or 'n'.");
  }
}

// LEDs control
void allDrinkLEDsOff() {
  for (int iLED = 0; iLED<3; iLED++){
      digitalWrite(LEDs[iLED], LOW);
  }
}

// set the led high for the selected drink
void indicateSelectedDrink(int  d) {
  allDrinkLEDsOff();
  if (d == D_ESPRESSO)   digitalWrite(LEDs[0], HIGH);
  else if (d == D_CAPPUCCINO) digitalWrite(LEDs[1], HIGH);
  else if (d == D_TOMATO)     digitalWrite(LEDs[2], HIGH);
}

// when the drink is ready, blink the corresponding led
// TODO: (future implementation) use timer here
void blinkDrinkLED(int  d, int times, int onMs, int offMs) {
  // int pin = (d == D_ESPRESSO) ? LED1 : (d == D_CAPPUCCINO ? LED2 : LED3);
  for (int i = 0; i < times; ++i) {
    digitalWrite(LEDs[d], HIGH);
    delay(onMs);
    digitalWrite(LEDs[d], LOW);
    delay(offMs);
  }
  // leave it ON after blinking
  digitalWrite(LEDs[d], HIGH);
}

// Setup
void setup() {
  Serial.begin(115200);

  // define leds as output
  for (int iLED=0;iLED<4;iLED++){
    pinMode(LEDs[iLED], OUTPUT);
  }
  
  // leds off
  allDrinkLEDsOff();
  digitalWrite(LEDs[3], LOW);

  Serial.println("Hanze Coffee Machine");
  Serial.println("Available: 1) Espresso  2) Cappuccino  3) Tomato Soup");
}

// Loop
void loop() {
  switch (state) {

    // S_IDLE State --------------------------------------
    case S_IDLE: {
      // Ready LED ON in idle
      digitalWrite(LEDs[3], HIGH);
      Serial.println("\nInsert coin (type 's')...");
      String s = readLine();

      // check if it is correct
      if (s.equalsIgnoreCase("s")) {
        // Set idle LED to low
        digitalWrite(LEDs[3], LOW);
        
        // next state
        state = S_SELECT;
      } else {
        Serial.println("Type 's' to proceed.");
      }
    } break;

    // S_SELECT State --------------------------------------
    case S_SELECT: {
      // choose a drink
      Serial.print("Select drink: 1=Espresso, 2=Cappuccino, 3=Tomato Soup");
      drink = readIntInRange(1, 3);

      // led for the drink
      indicateSelectedDrink(drink);

      // tomato soups doesnt require custom.
      if (drink == D_TOMATO) {  
        state = S_PREPARE;
      } else {
        state = S_CUSTOMIZE;
      }
    } break;

    // S_CUSTOMIZE State --------------------------------------
    case S_CUSTOMIZE: {
      Serial.println("\n-- Customization :p --");

      // sugar
      Serial.println("Sugar level (0=no sugar, 1=low, 2=medium, 3=high)");
      sugarLevel    = readIntInRange(0, 3);

      // strength
      Serial.println("Strength level (0=mild, 1=medium, 2=strong)");
      strengthLevel = readIntInRange(0, 2);
      
      // msg
      Serial.print("Add milk? [y/n]: ");
      withMilk      = readYesNo();
      
      // next state
      state = S_PREPARE;
    } break;

    // S_CHECK_CUP State --------------------------------------
    // EXERCISE

    // S_PREPARE State --------------------------------------
    case S_PREPARE: {
      // preparation time
      Serial.print("\nPreparing ");
      if (drink == D_ESPRESSO)        Serial.print("Espresso");
      else if (drink == D_CAPPUCCINO) Serial.print("Cappuccino");
      else if (drink == D_TOMATO)     Serial.print("Tomato Soup");
      Serial.println("...");

      if (drink != D_TOMATO) {
        Serial.print("Sugar: ");    Serial.println(sugarLevel);
        Serial.print("Strength: "); Serial.println(strengthLevel);
        Serial.print("Milk: ");     Serial.println(withMilk ? "Yes" : "No");
      }

      // Blink selected drink LED
      Serial.printf("Blink LED %d\n", LEDs[drink-1]);
      blinkDrinkLED(drink-1, 3, 300, 200);

      // brew time
      delay(2000);

      // Indicate ready
      digitalWrite(LEDs[3], HIGH);
      Serial.println("Ready! Please take your cup.");

      // next state
      state = S_DONE;
    } break;

    // S_DONE State --------------------------------------
    case S_DONE: {
      // LED ON for a moment
      delay(1500);
      digitalWrite(LEDs[3], LOW);
      allDrinkLEDsOff();

      // replace custom values to default
      drink = D_NONE;
      sugarLevel = 0;
      strengthLevel = 0;
      withMilk = false;

      // Go back to idle
      state = S_IDLE;
    } break;
  }
}
