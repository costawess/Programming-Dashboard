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
int state = S_SELECT;
int drink = D_NONE;

// Customization
int  sugarLevel    = 0;   // 0=no sugar, 1=low, 2=medium, 3=high
int  strengthLevel = 0;   // 0=mild, 1=medium, 2=strong
bool withMilk      = false;

// Returns one of D_ESPRESSO, D_CAPPUCCINO, D_TOMATO, D_CHOCOLATE, or D_NONE
int decodeSelectedDrink(const String& line) {
  if (!line.startsWith("SELECTED:")) {
    return D_NONE;
  }

  String name = line.substring(9); // part after "SELECTED:"
  name.trim();
  name.toUpperCase();
  if (name == "ESPRESSO")     return D_ESPRESSO;
  if (name == "CAPPUCCINO")   return D_CAPPUCCINO;
  if (name == "TOMATO_SOUP")  return D_TOMATO;
  if (name == "CHOCOLATE")    return D_CHOCOLATE;
  return D_NONE;
}

int waitForDrinkFromGame() {
  while (true) {
    String line = readLine();          // uses your existing readLine()
    int d = decodeSelectedDrink(line);
    if (d != D_NONE) {
      return d;
    }
    // optional debug
    Serial.print("Ignoring invalid command: ");
    Serial.println(line);
  }
}

// --------- CUSTOMIZATION DECODERS (SUGAR / STRENGTH / MILK) ----------

int decodeSugarLevel(const String &line) {
  if (!line.startsWith("SUGAR:")) return -1;

  String v = line.substring(6);
  v.trim();
  v.toUpperCase();

  if (v == "NO_SUGAR") return 0;
  if (v == "LOW")      return 1;
  if (v == "MEDIUM")   return 2;
  if (v == "HIGH")     return 3;

  return -1;
}

int decodeStrengthLevel(const String &line) {
  if (!line.startsWith("STRENGTH:")) return -1;

  String v = line.substring(9);
  v.trim();
  v.toUpperCase();

  if (v == "MILD")    return 0;
  if (v == "MEDIUM")  return 1;
  if (v == "STRONG")  return 2;

  return -1;
}

int decodeMilk(const String &line) {
  if (!line.startsWith("MILK:")) return -1;

  String v = line.substring(5);
  v.trim();
  v.toUpperCase();

  if (v == "YES") return 1;
  if (v == "NO")  return 0;

  return -1;
}

// Espera até receber um comando SUGAR:... válido
void waitSugarFromGame() {
  while (true) {
    String line = readLine();
    int v = decodeSugarLevel(line);
    if (v >= 0) {
      sugarLevel = v;
      Serial.print("Sugar from game: ");
      Serial.println(line);
      return;
    }
    Serial.print("Ignoring customization cmd (sugar): ");
    Serial.println(line);
  }
}

// Espera até receber um comando STRENGTH:... válido
void waitStrengthFromGame() {
  while (true) {
    String line = readLine();
    int v = decodeStrengthLevel(line);
    if (v >= 0) {
      strengthLevel = v;
      Serial.print("Strength from game: ");
      Serial.println(line);
      return;
    }
    Serial.print("Ignoring customization cmd (strength): ");
    Serial.println(line);
  }
}

// Espera até receber um comando MILK:... válido
void waitMilkFromGame() {
  while (true) {
    String line = readLine();
    int v = decodeMilk(line);
    if (v >= 0) {
      withMilk = (v == 1);
      Serial.print("Milk from game: ");
      Serial.println(line);
      return;
    }
    Serial.print("Ignoring customization cmd (milk): ");
    Serial.println(line);
  }
}


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
      // Serial.println("Waiting drink selection from game (SELECTED:ESPRESSO, ...)");
      
      // 1) Wait until PC/game sends a valid SELECTED:... command
      drink = waitForDrinkFromGame();

      // 2) Turn on the LED for that drink
      indicateSelectedDrink(drink);

      // 3) Decide next state and INFORM the game
      if (drink == D_TOMATO) {
        state = S_PREPARE;
        Serial.println("STATE:PREPARE");    // game can read this and change screen
      } else {
        state = S_CUSTOMIZE;
        Serial.println("STATE:CUSTOMIZE");  // game knows it should go to customize UI
      }
      } break;

    // S_CUSTOMIZE State --------------------------------------
    case S_CUSTOMIZE: {
      // Serial.println("\n-- Customization from game --");
      // Serial.println("Waiting SUGAR:...");
      waitSugarFromGame();        // recebe SUGAR:NO_SUGAR / LOW / MEDIUM / HIGH
      Serial.println("SUGAR:OK");

      waitStrengthFromGame();     // recebe STRENGTH:MILD / MEDIUM / STRONG
      Serial.println("STRENGTH:OK");

      // Serial.println("Waiting MILK:...");
      waitMilkFromGame();         // recebe MILK:YES / NO
      Serial.println("MILK:OK");

      // tudo recebido -> próximo estado
      state = S_PREPARE;
      Serial.println("STATE:PREPARE");   // opcional: informar jogo
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
