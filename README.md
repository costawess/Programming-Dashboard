# Embedded Programming Workspace

This repository contains the browser-based simulations, UART/Web Serial experiments, the Python heater simulation, and the older pygame serial project.

## Main Entry Points

- Web menu: `web/heater_sim.html`
- Python simulation: `python/heater_sim_pygame.py`
- Legacy pygame serial app: `legacy/pygame_serial/main.py`

## Structure

- `web/`
  Browser entry point, simulations, shared scripts, assets, and UART experiments.
- `web/simulations/`
  Teaching-oriented simulations for embedded programming topics.
- `web/experiments/`
  Interactive experiments that can also talk to an ESP32 through Web Serial.
- `web/experiments/responses/`
  Per-experiment folders for logs, screenshots, UART captures, or saved responses.
- `web/assets/cards/`
  Menu thumbnails used by `web/heater_sim.html`.
- `python/`
  Python-based local simulation code.
- `legacy/pygame_serial/`
  Original pygame + UART project.

## How To Open

1. Open `web/heater_sim.html` in a desktop browser.
2. Use Chrome or Edge if you need Web Serial.
3. Prefer `localhost` or `https` when using UART/Web Serial pages.
4. Use the menu cards to open each simulation or experiment.

## Simulations

### Gas Water Heater

- File: `web/heater_sim.html`
- Use it to:
  Explore the plant behavior of the heater, setpoints, flow, and temperature response.
- Main interaction:
  Use the UI controls on the page to change heater-related signals and observe the plots.
- UART:
  Not used on this page.

### Robot Sorting Logic Lab

- File: `web/simulations/robot_sorting_lab.html`
- Use it to:
  Practice algorithmic thinking with a robotic arm that must inspect a geometric shape, compare it with the target product, and either let it pass or reject it.
- Main interaction:
  Reorder the logic blocks, choose the target shape and the incoming part, then run the robot one step at a time or as a full cycle.

### Foundations Lab

- File: `web/simulations/course_topics_lab.html?topic=foundations`
- Use it to:
  Show one digital input driving one digital LED output.
- Main interaction:
  Press and hold the button and watch input and LED follow in the timeline.

### Pull-Up / Pull-Down Lab

- File: `web/simulations/pull_resistors_lab.html`
- Use it to:
  Compare resistor-to-VCC and resistor-to-GND wiring.
- Main interaction:
  Switch between pull-up and pull-down, then press the button and watch the GPIO input and LED state.

### Variables Lab

- File: `web/simulations/course_topics_lab.html?topic=variables`
- Use it to:
  Show storing a sensor value in variables and mapping it to PWM.
- Main interaction:
  Change the sensor with the slider or keyboard arrows and observe `sensorValue`, `pwmValue`, brightness, and timeline.

### Variable Types Lab

- File: `web/simulations/variable_types_lab.html`
- Use it to:
  Compare `bool`, signed and unsigned integers, and `float`.
- Main interaction:
  Change the type and value, then inspect byte layout and memory representation.

### Memory Layout Lab

- File: `web/simulations/memory_layout_lab.html`
- Use it to:
  Compare the RAM cost of declaring several variables together.
- Main interaction:
  Load a preset or edit the variable list, then inspect the memory map, byte ownership, total bytes, and generated Arduino declarations.

### ASCII Char Lab

- File: `web/simulations/ascii_char_lab.html`
- Use it to:
  Explain `char`, ASCII codes, printable characters, control codes, and the stored byte.
- Main interaction:
  Change the ASCII value with the slider, number input, character input, quick buttons, or keyboard arrows.

### Number Representation Lab

- File: `web/simulations/number_representation_lab.html`
- Use it to:
  Compare decimal, binary, hexadecimal, bit weights, and signed/unsigned interpretation.
- Main interaction:
  Change the raw value or toggle bits directly and observe the different numeric views.

### Conditionals Lab

- File: `web/simulations/course_topics_lab.html?topic=conditionals`
- Use it to:
  Compare basic logic, nested logic, and numeric comparison.
- Main interaction:
  Switch mode, press logic buttons, or move the comparison sensor/threshold controls.
- Keyboard:
  In comparison mode:
  `Left/Right` changes the sensor.
  `Up/Down` changes the threshold.

### Loops Lab

- File: `web/simulations/course_topics_lab.html?topic=loops`
- Use it to:
  Compare `for`, `while`, and `do while` using LED scanning.
- Main interaction:
  Change loop style, step period, pause/reset the sequence, and watch the LED order and timeline.
- Keyboard:
  `Left/Right` changes the step period.

### ADC Lab

- File: `web/simulations/course_topics_lab.html?topic=adc`
- Use it to:
  Convert an analog voltage to ADC counts and then to PWM.
- Main interaction:
  Change the input voltage and ADC resolution, then observe voltage, ADC raw value, and PWM.
- Keyboard:
  `Left/Right` changes the input voltage.

### Hysteresis Lab

- File: `web/simulations/hysteresis_lab.html`
- Use it to:
  Compare a noisy signal, a single-threshold comparator, and two-threshold hysteresis.
- Main interaction:
  Observe all three graphs and the state diagram while changing the thresholds and signal behavior.

### UART Lab

- File: `web/simulations/course_topics_lab.html?topic=uart`
- Use it to:
  Show frames moving from TX to RX and simple serial acknowledgement logic.
- Main interaction:
  Send UART text and observe TX, RX, and queue signals.

### I2C Lab

- File: `web/simulations/course_topics_lab.html?topic=i2c`
- Use it to:
  Show a master write, address, data byte, and ACK behavior.
- Main interaction:
  Change address/data and observe SDA, SCL, and ACK.

### Functions Lab

- File: `web/simulations/course_topics_lab.html?topic=functions`
- Use it to:
  Demonstrate code reuse with a function called using different parameters.
- Main interaction:
  Trigger calls and observe LED behavior, pending calls, and the highlighted code block.

### Interrupts Lab

- File: `web/simulations/course_topics_lab.html?topic=interrupts`
- Use it to:
  Compare interrupt response against polling.
- Main interaction:
  Trigger events, enable CPU busy mode, and compare IRQ vs polling paths on the timeline.

### Timers Lab

- File: `web/simulations/course_topics_lab.html?topic=timers`
- Use it to:
  Compare `delay()`, `millis()`, and ESP32 hardware timer ISR behavior.
- Main interaction:
  Change timing strategy, pause the blinker, pause the simulation, inject button events, and inspect missed/handled counts.

### State Machines Lab

- File: `web/simulations/course_topics_lab.html?topic=state_machines`
- Use it to:
  Show a traffic-light state machine with pedestrian request logic.
- Main interaction:
  Toggle auto cycle, request pedestrian crossing, step to next state, and inspect the state diagram.

### Arduino To Flowchart

- File: `web/simulations/arduino_flowchart_converter.html`
- Use it to:
  Convert Arduino C++ into a teaching-oriented flowchart.
- Main interaction:
  Paste code and inspect the generated flow representation.

## Experiments

These pages are more application-like and many of them support Web Serial with an ESP32.

### Maze

- File: `web/experiments/maze.html`
- Use it to:
  Move through the maze locally or from UART.
- Keyboard/UI:
  Move the player in the page.
- UART input:
  `UP`
  `DOWN`
  `LEFT`
  `RIGHT`

### Tic-Tac-Toe

- File: `web/experiments/tic_tac_toe.html`
- Use it to:
  Play local or UART-linked tic-tac-toe, including the sliding mode.
- UART input/output:
  `SYMBOL:SELECTED:X`
  `SYMBOL:SELECTED:O`
  `MOVE:<row>,<col>,<symbol>`
  `REMATCH:REQUEST`
  `REMATCH:ACCEPT`
  `MODE:TRADITIONAL`
  `MODE:SLIDING`

### Kitchen Timer

- File: `web/experiments/kitchen_timer.html`
- Use it to:
  Show a timer value coming from UART against a configurable scale.
- UART input:
  plain numeric value such as `42`
  `TIME:42`
  `SECONDS:42`
  `VALUE:42`

### Traffic Lights

- File: `web/experiments/traffic_lights.html`
- Use it to:
  Monitor one active lamp and store timing history for each completed state.
- UART input:
  `RED`
  `YELLOW`
  `GREEN`
  `AMBER`
- Notes:
  `AMBER` is treated as `YELLOW`.

### Intersection Controller

- File: `web/experiments/intersection_controller.html`
- Use it to:
  Control a junction with main street light, side street light, walk lamp, walk button, and side sensor.
- GUI:
  Click state cards to force `MAIN_GREEN`, `MAIN_YELLOW`, `SIDE_GREEN`, or `WALK`.
- UART input:
  `STATE:MAIN_GREEN`
  `STATE:MAIN_YELLOW`
  `STATE:SIDE_GREEN`
  `STATE:WALK`
  `MAIN:RED`
  `MAIN:YELLOW`
  `MAIN:GREEN`
  `SIDE:RED`
  `SIDE:YELLOW`
  `SIDE:GREEN`
  `WALK:ON`
  `WALK:OFF`
  `BUTTON:ON`
  `BUTTON:OFF`
  `BUTTON:PRESSED`
  `BUTTON:RELEASED`
  `SENSOR:ON`
  `SENSOR:OFF`
  `SENSOR:ACTIVE`
  `SENSOR:IDLE`

### Dual Seven Segment

- File: `web/experiments/dual_seven_segment.html`
- Use it to:
  Mirror the exact segment bits of two 7-segment displays.
- UART input:
  `LEFT:10111111`
  `RIGHT:01100000`
  `D1:10111111`
  `D2:01100000`
  `DISPLAY1:10111111`
  `DISPLAY2:01100000`
  `DISPLAYS:10111111,01100000`
  `DISPLAYS:10111111,01100000,10111111,01100000`
- Notes:
  Bit order is `ABCDEFGDP`.
  Each frame must contain exactly 8 bits.

### Coffee Machine

- File: `web/experiments/coffee_machine.html`
- Use it to:
  Send drink options from the browser and mirror machine states from the ESP32.
- UART output from browser:
  `SELECTED:ESPRESSO`
  `SELECTED:CAPUCCINO`
  `SELECTED:TOMATO_SOUP`
  `SELECTED:CHOCOLATE`
  `SUGAR:NO_SUGAR`
  `SUGAR:LOW`
  `SUGAR:MEDIUM`
  `SUGAR:HIGH`
  `STRENGTH:MILD`
  `STRENGTH:MEDIUM`
  `STRENGTH:STRONG`
  `MILK:YES`
  `MILK:NO`
  `s`
- UART input from ESP32:
  `STATE:CUSTOMIZE`
  `STATE:PREPARE`
  `SUGAR:OK`
  `STRENGTH:OK`
  `MILK:OK`
  `READY!`
  `INSERT COIN`

## Shared Interaction Notes

- Several simulations support keyboard shortcuts for sliders or comparison controls.
- Many code panels include `Copy code`.
- Some timelines include `Pause timeline` so the graph can be frozen for analysis.
- In the course-topic lab, the highlighted Arduino line follows the currently active part of the simulation.

## Responses Folder

- Base folder: `web/experiments/responses/`
- Use it to store:
  UART captures
  screenshots
  test notes
  exported logs
  experiment-specific answers

## Notes

- The root `heater_sim.html` redirects to the web entry point.
- The HTML pages are intentionally dark-themed.
- Web Serial experiments should be opened in a compatible desktop browser such as Chrome or Edge.
