// Maze Controller (solution)
// Wesley Costa (2025)

// Define the (start) button pin number
int button35 = 35;
int button34 = 34;

// Functions to control the game: UP, DOWN, LEFT, RIGHT
// this can be optimized, but just wanted to explore what could be used here:
// so far: input/output, functions, flux control (loop and conditionals), 
// libraries (would also be nice to show as an example).
void start(int iter){
  Serial.print("START"); // TODO: not being used yet! Even in the pyGame
}
void down(int iter){
  for(int i=0; i<iter; i++){
    Serial.println("DOWN"); delay(200);
  }
}
void right(int iter){
  for(int i=0; i<iter; i++){
    Serial.println("RIGHT"); delay(200);
  }
}
void left(int iter){
  for(int i=0; i<iter; i++){
    Serial.println("LEFT"); delay(200);
  }
}
void up(int iter){
  for(int i=0; i<iter; i++){
    Serial.println("UP"); delay(200);
  }
}

// Setup: serial and pin configs
void setup() {
  Serial.begin(115200);
  
  // Define Buttons
  pinMode(button35, INPUT);
  pinMode(button34, INPUT);
}

// Finally, this is the Maze controller! :)
void loop() {
  int state35 = digitalRead(button35);
  int state34 = digitalRead(button34);

  if(state35 == HIGH){
    right(2);
    down(2);
    right(5);
    down(2);
    right(2);
    down(3);
  }

  if(state34 == HIGH){
    right(2);
    down(2);
    left(2);
    down(4);
    right(2);
    up(2);
    right(3);
    down(2);
    right(2);
    down(1);
    right(2);
  }
}
