# Embedded Programming Workspace

This workspace contains the browser-based activities, the Python heater simulation, and the legacy pygame + UART project.

## Structure

- `web/`
  - Main HTML entry point and browser-based simulations/experiments.
- `web/experiments/`
  - HTML experiments that can run locally or receive UART input from an ESP32.
- `web/assets/cards/`
  - Menu thumbnails. Replace any file with the same filename to customize the menu image.
- `python/`
  - Python-based local simulation code.
- `assets/branding/`
  - Shared branding assets such as `hanze_logo.png`.
- `assets/references/`
  - Reference images and vector sources used during design/prototyping.
- `legacy/pygame_serial/`
  - Original pygame + UART/ESP32 project, including assets, Arduino sketches, build artifacts, and distribution files.

## Recommended Entry Points

- Web menu: `web/heater_sim.html`
- Python simulation: `python/heater_sim_pygame.py`
- Legacy pygame serial app: `legacy/pygame_serial/main.py`

## Web Activities

### Simulation

- `Gas Water Heater`
  - File: `web/heater_sim.html`
  - Purpose: browser-only process simulation with plant drawing and signal plots.
  - UART: not used on this page.

### Experiments And UART Rules

- `Maze`
  - File: `web/experiments/maze.html`
  - Purpose: move the robot through the maze.
  - UART input expected:
    - `UP`
    - `DOWN`
    - `LEFT`
    - `RIGHT`

- `Tic-Tac-Toe`
  - File: `web/experiments/tic_tac_toe.html`
  - Purpose: local or UART-linked tic-tac-toe, including the sliding mode.
  - UART input/output used:
    - `SYMBOL:SELECTED:X`
    - `SYMBOL:SELECTED:O`
    - `MOVE:<row>,<col>,<symbol>`
    - `REMATCH:REQUEST`
    - `REMATCH:ACCEPT`
    - `MODE:TRADITIONAL`
    - `MODE:SLIDING`

- `Kitchen Timer`
  - File: `web/experiments/kitchen_timer.html`
  - Purpose: show a timer value received from UART against a configurable GUI scale.
  - UART input expected:
    - plain seconds value such as `42`
    - `TIME:42`
    - `SECONDS:42`
    - `VALUE:42`

- `Traffic Lights`
  - File: `web/experiments/traffic_lights.html`
  - Purpose: show one active light and measure how long each color stayed active.
  - UART input expected:
    - `RED`
    - `YELLOW`
    - `GREEN`
    - `AMBER`
  - Notes:
    - `AMBER` is treated as `YELLOW`.
    - When a new valid color arrives, the previous color duration is pushed to history with milliseconds.

- `Intersection Controller`
  - File: `web/experiments/intersection_controller.html`
  - Purpose: simulate the crossing with main street light, side street light, walk lamp, walk button, and side sensor.
  - UART input expected:
    - logical-state commands:
      - `STATE:MAIN_GREEN`
      - `STATE:MAIN_YELLOW`
      - `STATE:SIDE_GREEN`
      - `STATE:WALK`
    - direct actuator commands:
      - `MAIN:RED`
      - `MAIN:YELLOW`
      - `MAIN:GREEN`
      - `SIDE:RED`
      - `SIDE:YELLOW`
      - `SIDE:GREEN`
      - `WALK:ON`
      - `WALK:OFF`
      - `BUTTON:ON`
      - `BUTTON:OFF`
      - `BUTTON:PRESSED`
      - `BUTTON:RELEASED`
      - `SENSOR:ON`
      - `SENSOR:OFF`
      - `SENSOR:ACTIVE`
      - `SENSOR:IDLE`

- `Dual Seven Segment`
  - File: `web/experiments/dual_seven_segment.html`
  - Purpose: mirror the exact segment bits of two 7-segment displays.
  - Bit order expected:
    - `ABCDEFGDP`
  - UART input expected:
    - `LEFT:10111111`
    - `RIGHT:01100000`
    - `D1:10111111`
    - `D2:01100000`
    - `DISPLAY1:10111111`
    - `DISPLAY2:01100000`
    - `DISPLAYS:10111111,01100000`
  - Notes:
    - each frame must contain exactly 8 bits
    - `1` means segment on
    - `0` means segment off

- `Coffee Machine`
  - File: `web/experiments/coffee_machine.html`
  - Purpose: send drink selection and customization options, then mirror the machine states.
  - UART output from browser to ESP32:
    - `SELECTED:ESPRESSO`
    - `SELECTED:CAPUCCINO`
    - `SELECTED:TOMATO_SOUP`
    - `SELECTED:CHOCOLATE`
    - `SUGAR:NO_SUGAR`
    - `SUGAR:LOW`
    - `SUGAR:MEDIUM`
    - `SUGAR:HIGH`
    - `STRENGTH:MILD`
    - `STRENGTH:MEDIUM`
    - `STRENGTH:STRONG`
    - `MILK:YES`
    - `MILK:NO`
    - `s`
  - UART input expected from ESP32:
    - `STATE:CUSTOMIZE`
    - `STATE:PREPARE`
    - `SUGAR:OK`
    - `STRENGTH:OK`
    - `MILK:OK`
    - `READY!`
    - `INSERT COIN`

## Notes

- The original root `heater_sim.html` redirects to the web entry point.
- The HTML pages are currently fixed in dark mode.
- The UART-based experiments rely on the browser Web Serial API, so they should be opened in a compatible desktop browser such as Chrome or Edge, usually from `localhost` or `https`.
