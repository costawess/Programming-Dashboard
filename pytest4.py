import serial
import serial.tools.list_ports
import pygame

# ====== WINDOW CONFIGURATION ======
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
# ==================================

# ====== MAZE CONFIGURATION ======
# 0 = free cell, 1 = wall
# Start = top-left (0,0), Goal = bottom-right (cols-1, rows-1)
MAZE = [
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    [1, 1, 0, 1, 1, 0, 1, 1, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 0, 1, 0],
    [0, 1, 0, 0, 0, 0, 1, 0, 0, 0],
    [0, 1, 0, 1, 1, 0, 1, 1, 1, 0],
    [0, 0, 0, 1, 0, 0, 0, 0, 1, 0],
    [1, 1, 0, 1, 0, 1, 1, 0, 0, 0],
]
MAZE_ROWS = len(MAZE)
MAZE_COLS = len(MAZE[0])

# Maze drawing area (centered)
MAZE_WIDTH = 600
MAZE_HEIGHT = 480
MAZE_X_OFFSET = (WINDOW_WIDTH - MAZE_WIDTH) // 2
MAZE_Y_OFFSET = 60

CELL_W = MAZE_WIDTH // MAZE_COLS
CELL_H = MAZE_HEIGHT // MAZE_ROWS

BALL_RADIUS = min(CELL_W, CELL_H) // 3
# ==================================

# ====== SERIAL CONFIGURATION ======
BAUD_OPTIONS = [9600, 115200]
# ==================================

# ====== WIN IMAGE CONFIGURATION ======
WIN_IMAGE_PATH = "assets/figures/win/gold-winner.gif"
# ======================================


def try_open_serial(port_name, baudrate):
    """
    Try to open a serial port.
    Returns (ser, success, message).
    """
    if not port_name:
        return None, False, "No port selected."

    try:
        ser = serial.Serial(port_name, baudrate, timeout=0.05)
        msg = f"Connected to {port_name} at {baudrate} baud."
        return ser, True, msg
    except serial.SerialException as e:
        return None, False, f"Error opening {port_name}: {e}"


def get_available_ports():
    """
    Return a list of available serial port device names (e.g. ['COM3', 'COM4']).
    """
    return [p.device for p in serial.tools.list_ports.comports()]


def draw_text_center(screen, text, font, color, y):
    """
    Draw text horizontally centered at given y coordinate.
    """
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=(WINDOW_WIDTH // 2, y))
    screen.blit(surface, rect)


def cell_to_pixel(cx, cy):
    """
    Convert maze cell coordinates (cx, cy) to pixel center (x, y).
    """
    x = MAZE_X_OFFSET + cx * CELL_W + CELL_W // 2
    y = MAZE_Y_OFFSET + cy * CELL_H + CELL_H // 2
    return x, y


def process_command(cmd, robot_cell):
    """
    Process a movement command with absolute directions.

    cmd: "UP", "DOWN", "LEFT", "RIGHT"
    robot_cell: (cx, cy)

    Returns: (new_cell, collision, moved, new_direction)
      - collision = True if robot hit wall or left maze
      - moved = True if actually moved into a new cell
      - new_direction = 0=up,1=right,2=down,3=left (used only to draw arrow)
    """
    cx, cy = robot_cell
    collision = False
    moved = False

    dx, dy = 0, 0
    new_direction = 0

    if cmd == "UP":
        dx, dy = 0, -1
        new_direction = 0
    elif cmd == "RIGHT":
        dx, dy = 1, 0
        new_direction = 1
    elif cmd == "DOWN":
        dx, dy = 0, 1
        new_direction = 2
    elif cmd == "LEFT":
        dx, dy = -1, 0
        new_direction = 3

    nx = cx + dx
    ny = cy + dy

    # Check maze limits
    if nx < 0 or nx >= MAZE_COLS or ny < 0 or ny >= MAZE_ROWS:
        collision = True
    else:
        # Check wall
        if MAZE[ny][nx] == 1:
            collision = True
        else:
            cx, cy = nx, ny
            moved = True

    return (cx, cy), collision, moved, new_direction


def init_game():
    """
    Return initial game state for a new attempt.
    """
    robot_cell = (0, 0)  # start cell
    direction = 1        # facing right initially for arrow
    score = 0
    game_over = False
    return robot_cell, direction, score, game_over


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Embedded Programming Maze - Serial Robot")
    clock = pygame.time.Clock()

    # Load win image (static)
    try:
        win_image = pygame.image.load(WIN_IMAGE_PATH).convert_alpha()
    except Exception as e:
        print(f"Could not load win image: {e}")
        win_image = None

    # ===== INTRO SCREEN (1 second) =====
    intro_font = pygame.font.SysFont(None, 60)
    screen.fill((0, 0, 0))
    draw_text_center(screen, "EMBEDDED PROGRAMMING 2026", intro_font, (255, 255, 255), WINDOW_HEIGHT // 2)
    pygame.display.flip()
    pygame.time.delay(1000)  # 1 second
    # ===================================

    # Initial game state (not started yet)
    robot_cell, direction, score, game_over = init_game()
    game_started = False
    won = False  # win state

    # Serial port initially not connected
    ser = None

    # Status message (success or error)
    status_message = "Not connected."
    status_color = (255, 0, 0)  # red for not connected

    # GUI fonts and elements
    font_small = pygame.font.SysFont(None, 24)
    font_medium = pygame.font.SysFont(None, 32)
    font_large = pygame.font.SysFont(None, 40)

    # Buttons on main screen
    esp32_button_rect = pygame.Rect(20, 20, 120, 40)
    start_button_rect = pygame.Rect(160, 20, 120, 40)
    reset_button_rect = pygame.Rect(300, 20, 120, 40)

    # Popup (configuration window) state
    config_open = False
    available_ports = []
    selected_port_index = -1  # -1 indicates no selection
    baud_index = 0            # Index in BAUD_OPTIONS, default 0 -> 9600

    # Colors
    BTN_BG = (60, 60, 60)
    BTN_BG_HOVER = (90, 90, 90)
    POPUP_BG = (30, 30, 30)
    POPUP_BORDER = (200, 200, 200)
    INPUT_BG = (20, 20, 20)
    WHITE = (255, 255, 255)
    YELLOW = (255, 255, 0)
    GREY = (80, 80, 80)
    WALL_COLOR = (40, 40, 40)
    FREE_COLOR = (10, 10, 10)
    START_COLOR = (0, 100, 0)
    GOAL_COLOR = (100, 0, 0)

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Mouse clicks
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True

            # Keyboard handling
            if event.type == pygame.KEYDOWN:
                # ENTER on GAME OVER -> same as clicking "I wanna try again"
                if game_over and not config_open and event.key == pygame.K_RETURN:
                    robot_cell, direction, score, game_over = init_game()
                    won = False
                    game_started = True

                # Keyboard controls for testing without serial (only if not over/won)
                elif (
                    not config_open
                    and not game_over
                    and not won
                    and game_started
                ):
                    cmd = None
                    if event.key == pygame.K_UP:
                        cmd = "UP"
                    elif event.key == pygame.K_DOWN:
                        cmd = "DOWN"
                    elif event.key == pygame.K_LEFT:
                        cmd = "LEFT"
                    elif event.key == pygame.K_RIGHT:
                        cmd = "RIGHT"

                    if cmd is not None:
                        robot_cell, collision, moved, new_dir = process_command(cmd, robot_cell)
                        direction = new_dir
                        if collision:
                            game_over = True
                        elif moved:
                            score += 1
                            # Check for win condition
                            if robot_cell == (MAZE_COLS - 1, MAZE_ROWS - 1):
                                won = True
                                game_started = False

        # --- Handle mouse clicks on buttons / popup / game over / win ---
        if mouse_clicked:
            if config_open:
                # CONFIG POPUP geometry
                popup_width = 400
                popup_height = 300
                popup_rect = pygame.Rect(
                    (WINDOW_WIDTH - popup_width) // 2,
                    (WINDOW_HEIGHT - popup_height) // 2,
                    popup_width,
                    popup_height,
                )

                label_font = pygame.font.SysFont(None, 24)

                # ---- PORT BUTTONS (horizontal) ----
                ports_y = popup_rect.y + 80
                port_btn_w = 90
                port_btn_h = 32
                port_spacing = 10

                port_rects = []
                for i, port in enumerate(available_ports):
                    x = popup_rect.x + 20 + i * (port_btn_w + port_spacing)
                    r = pygame.Rect(x, ports_y, port_btn_w, port_btn_h)
                    port_rects.append(r)

                # ---- BAUD BUTTONS (horizontal) ----
                baud_label_y = ports_y + 60
                baud_buttons_y = baud_label_y + 20
                baud_rects = []
                for i, baud in enumerate(BAUD_OPTIONS):
                    r = pygame.Rect(popup_rect.x + 20 + i * 120, baud_buttons_y, 100, 32)
                    baud_rects.append(r)

                # Buttons "Connect", "Disconnect", "Cancel"
                btns_y = baud_buttons_y + 60
                btn_connect_rect = pygame.Rect(popup_rect.x + 30, btns_y, 100, 40)
                btn_disconnect_rect = pygame.Rect(popup_rect.x + 150, btns_y, 120, 40)
                btn_cancel_rect = pygame.Rect(popup_rect.x + popup_width - 130, btns_y, 100, 40)

                # Handle clicks on ports
                for i, r in enumerate(port_rects):
                    if r.collidepoint(mouse_pos):
                        selected_port_index = i

                # Handle clicks on bauds
                for i, r in enumerate(baud_rects):
                    if r.collidepoint(mouse_pos):
                        baud_index = i

                # Connect
                if btn_connect_rect.collidepoint(mouse_pos):
                    if not available_ports:
                        status_message = "No COM ports available."
                        status_color = (255, 0, 0)
                    else:
                        port_name = available_ports[selected_port_index] if selected_port_index >= 0 else None
                        baudrate = BAUD_OPTIONS[baud_index]

                        if ser is not None:
                            ser.close()
                            ser = None

                        ser_new, success, msg = try_open_serial(port_name, baudrate)
                        status_message = msg
                        status_color = (0, 255, 0) if success else (255, 0, 0)

                        if success:
                            ser = ser_new
                            config_open = False

                # Disconnect only if currently connected
                if ser is not None and btn_disconnect_rect.collidepoint(mouse_pos):
                    try:
                        port_name = ser.port
                    except Exception:
                        port_name = "COM"
                    ser.close()
                    ser = None
                    status_message = f"Disconnected from {port_name}."
                    status_color = (255, 0, 0)

                # Cancel
                if btn_cancel_rect.collidepoint(mouse_pos):
                    config_open = False

            elif game_over:
                # GAME OVER POPUP
                go_width = 400
                go_height = 220
                go_rect = pygame.Rect(
                    (WINDOW_WIDTH - go_width) // 2,
                    (WINDOW_HEIGHT - go_height) // 2,
                    go_width,
                    go_height,
                )
                try_again_rect = pygame.Rect(go_rect.x + 100, go_rect.y + 140, 200, 40)

                if try_again_rect.collidepoint(mouse_pos):
                    robot_cell, direction, score, game_over = init_game()
                    won = False
                    game_started = True

            elif won:
                # WIN POPUP
                win_width = 500
                win_height = 350
                win_rect = pygame.Rect(
                    (WINDOW_WIDTH - win_width) // 2,
                    (WINDOW_HEIGHT - win_height) // 2,
                    win_width,
                    win_height,
                )
                play_again_rect = pygame.Rect(win_rect.x + 150, win_rect.y + win_height - 70, 200, 40)

                if play_again_rect.collidepoint(mouse_pos):
                    robot_cell, direction, score, game_over = init_game()
                    won = False
                    game_started = True

            else:
                # MAIN SCREEN buttons
                if esp32_button_rect.collidepoint(mouse_pos):
                    # Refresh COM list whenever opening the popup
                    available_ports = get_available_ports()
                    selected_port_index = 0 if available_ports else -1
                    config_open = True

                elif start_button_rect.collidepoint(mouse_pos):
                    robot_cell, direction, score, game_over = init_game()
                    won = False
                    game_started = True

                elif reset_button_rect.collidepoint(mouse_pos):
                    robot_cell, direction, score, game_over = init_game()
                    won = False
                    game_started = False

        # ----- Read serial data if connected, game started and not over/won -----
        if (
            not game_over
            and not config_open
            and not won
            and game_started
            and ser is not None
            and ser.in_waiting > 0
        ):
            try:
                line = ser.readline().decode(errors="ignore").strip()
            except Exception:
                line = ""
            if line:
                cmd = line.upper()
                if cmd in ("UP", "DOWN", "LEFT", "RIGHT"):
                    print(f"Serial command: {cmd}")
                    robot_cell, collision, moved, new_dir = process_command(cmd, robot_cell)
                    direction = new_dir
                    if collision:
                        print("Collision detected! GAME OVER.")
                        game_over = True
                    elif moved:
                        score += 1
                        if robot_cell == (MAZE_COLS - 1, MAZE_ROWS - 1):
                            won = True
                            game_started = False
                else:
                    print(f"Unknown command: {line!r}")

        # ===== DRAW SECTION =====
        screen.fill((0, 0, 0))  # background

        # Draw maze
        for r in range(MAZE_ROWS):
            for c in range(MAZE_COLS):
                cell_val = MAZE[r][c]
                cell_rect = pygame.Rect(
                    MAZE_X_OFFSET + c * CELL_W,
                    MAZE_Y_OFFSET + r * CELL_H,
                    CELL_W,
                    CELL_H,
                )

                if (c, r) == (0, 0):
                    color = START_COLOR
                elif (c, r) == (MAZE_COLS - 1, MAZE_ROWS - 1):
                    color = GOAL_COLOR
                else:
                    color = WALL_COLOR if cell_val == 1 else FREE_COLOR

                pygame.draw.rect(screen, color, cell_rect)
                pygame.draw.rect(screen, GREY, cell_rect, 1)  # grid lines

        # Draw robot
        rx, ry = cell_to_pixel(*robot_cell)
        pygame.draw.circle(screen, WHITE, (rx, ry), BALL_RADIUS)

        # Draw direction indicator
        dir_dx, dir_dy = 0, 0
        if direction == 0:   # up
            dir_dx, dir_dy = 0, -BALL_RADIUS
        elif direction == 1: # right
            dir_dx, dir_dy = BALL_RADIUS, 0
        elif direction == 2: # down
            dir_dx, dir_dy = 0, BALL_RADIUS
        elif direction == 3: # left
            dir_dx, dir_dy = -BALL_RADIUS, 0
        pygame.draw.line(screen, YELLOW, (rx, ry), (rx + dir_dx, ry + dir_dy), 3)

        # Score (top-right)
        score_text = font_medium.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (WINDOW_WIDTH - 150, 20))

        # Status message at bottom
        status_surface = font_small.render(status_message, True, status_color)
        screen.blit(status_surface, (20, WINDOW_HEIGHT - 30))

        # Hint
        hint_text = font_small.render("Commands: UP, DOWN, LEFT, RIGHT (serial or arrows)", True, WHITE)
        screen.blit(hint_text, (20, WINDOW_HEIGHT - 55))

        # "ESP32" button
        if esp32_button_rect.collidepoint(mouse_pos) and not config_open and not game_over and not won:
            btn_color_esp32 = BTN_BG_HOVER
        else:
            btn_color_esp32 = BTN_BG
        pygame.draw.rect(screen, btn_color_esp32, esp32_button_rect, border_radius=6)
        pygame.draw.rect(screen, WHITE, esp32_button_rect, 1, border_radius=6)
        txt_esp32 = font_small.render("ESP32", True, WHITE)
        txt_esp32_rect = txt_esp32.get_rect(center=esp32_button_rect.center)
        screen.blit(txt_esp32, txt_esp32_rect)

        # "Start" button
        if start_button_rect.collidepoint(mouse_pos) and not config_open and not game_over and not won:
            btn_color_start = BTN_BG_HOVER
        else:
            btn_color_start = BTN_BG
        pygame.draw.rect(screen, btn_color_start, start_button_rect, border_radius=6)
        pygame.draw.rect(screen, WHITE, start_button_rect, 1, border_radius=6)
        txt_start = font_small.render("Start", True, WHITE)
        txt_start_rect = txt_start.get_rect(center=start_button_rect.center)
        screen.blit(txt_start, txt_start_rect)

        # "Reset" button
        if reset_button_rect.collidepoint(mouse_pos) and not config_open and not game_over and not won:
            btn_color_reset = BTN_BG_HOVER
        else:
            btn_color_reset = BTN_BG
        pygame.draw.rect(screen, btn_color_reset, reset_button_rect, border_radius=6)
        pygame.draw.rect(screen, WHITE, reset_button_rect, 1, border_radius=6)
        txt_reset = font_small.render("Reset", True, WHITE)
        txt_reset_rect = txt_reset.get_rect(center=reset_button_rect.center)
        screen.blit(txt_reset, txt_reset_rect)

        # CONFIG POPUP
        if config_open:
            popup_width = 400
            popup_height = 300
            popup_rect = pygame.Rect(
                (WINDOW_WIDTH - popup_width) // 2,
                (WINDOW_HEIGHT - popup_height) // 2,
                popup_width,
                popup_height,
            )

            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))

            pygame.draw.rect(screen, POPUP_BG, popup_rect, border_radius=10)
            pygame.draw.rect(screen, POPUP_BORDER, popup_rect, 2, border_radius=10)

            title_font = pygame.font.SysFont(None, 28)
            draw_text_center(screen, "ESP32 Serial Configuration", title_font, YELLOW, popup_rect.y + 30)

            label_font = pygame.font.SysFont(None, 24)

            # Port label
            port_label = label_font.render("Port:", True, WHITE)
            screen.blit(port_label, (popup_rect.x + 20, popup_rect.y + 55))

            # PORT BUTTONS (horizontal)
            ports_y = popup_rect.y + 80
            port_btn_w = 90
            port_btn_h = 32
            port_spacing = 10

            if not available_ports:
                no_ports_text = label_font.render("No COM ports found.", True, WHITE)
                screen.blit(no_ports_text, (popup_rect.x + 20, ports_y))
            else:
                for i, port in enumerate(available_ports):
                    x = popup_rect.x + 20 + i * (port_btn_w + port_spacing)
                    r = pygame.Rect(x, ports_y, port_btn_w, port_btn_h)
                    bg_color = (80, 80, 80) if i == selected_port_index else (40, 40, 40)
                    pygame.draw.rect(screen, bg_color, r, border_radius=6)
                    pygame.draw.rect(screen, WHITE, r, 1, border_radius=6)
                    t = label_font.render(port, True, WHITE)
                    t_rect = t.get_rect(center=r.center)
                    screen.blit(t, t_rect)

            # Baud options
            baud_label_y = ports_y + 60
            baud_buttons_y = baud_label_y + 20

            baud_label = label_font.render("Baud rate:", True, WHITE)
            screen.blit(baud_label, (popup_rect.x + 20, baud_label_y))

            baud_rects_draw = []
            for i, baud in enumerate(BAUD_OPTIONS):
                r = pygame.Rect(popup_rect.x + 20 + i * 120, baud_buttons_y, 100, 32)
                baud_rects_draw.append(r)
                bg_color = (80, 80, 80) if i == baud_index else (40, 40, 40)
                pygame.draw.rect(screen, bg_color, r, border_radius=6)
                pygame.draw.rect(screen, WHITE, r, 1, border_radius=6)
                t = label_font.render(str(baud), True, WHITE)
                t_rect = t.get_rect(center=r.center)
                screen.blit(t, t_rect)

            # Buttons "Connect", "Disconnect", "Cancel"
            btns_y = baud_buttons_y + 60
            btn_connect_rect = pygame.Rect(popup_rect.x + 30, btns_y, 100, 40)
            btn_disconnect_rect = pygame.Rect(popup_rect.x + 150, btns_y, 120, 40)
            btn_cancel_rect = pygame.Rect(popup_rect.x + popup_width - 130, btns_y, 100, 40)

            pygame.draw.rect(screen, BTN_BG, btn_connect_rect, border_radius=6)
            pygame.draw.rect(screen, WHITE, btn_connect_rect, 1, border_radius=6)
            c_txt = label_font.render("Connect", True, WHITE)
            c_txt_rect = c_txt.get_rect(center=btn_connect_rect.center)
            screen.blit(c_txt, c_txt_rect)

            if ser is not None:
                pygame.draw.rect(screen, BTN_BG, btn_disconnect_rect, border_radius=6)
                pygame.draw.rect(screen, WHITE, btn_disconnect_rect, 1, border_radius=6)
                d_txt = label_font.render("Disconnect", True, WHITE)
                d_txt_rect = d_txt.get_rect(center=btn_disconnect_rect.center)
                screen.blit(d_txt, d_txt_rect)

            pygame.draw.rect(screen, BTN_BG, btn_cancel_rect, border_radius=6)
            pygame.draw.rect(screen, WHITE, btn_cancel_rect, 1, border_radius=6)
            x_txt = label_font.render("Cancel", True, WHITE)
            x_txt_rect = x_txt.get_rect(center=btn_cancel_rect.center)
            screen.blit(x_txt, x_txt_rect)

        # WIN POPUP
        if won:
            win_width = 500
            win_height = 350
            win_rect = pygame.Rect(
                (WINDOW_WIDTH - win_width) // 2,
                (WINDOW_HEIGHT - win_height) // 2,
                win_width,
                win_height,
            )

            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            pygame.draw.rect(screen, POPUP_BG, win_rect, border_radius=10)
            pygame.draw.rect(screen, POPUP_BORDER, win_rect, 2, border_radius=10)

            if win_image is not None:
                max_w, max_h = 350, 200
                img = win_image
                iw, ih = img.get_size()
                scale = min(max_w / iw, max_h / ih, 1.0)
                new_size = (int(iw * scale), int(ih * scale))
                img_scaled = pygame.transform.smoothscale(img, new_size)
                img_rect = img_scaled.get_rect(center=(win_rect.centerx, win_rect.y + 120))
                screen.blit(img_scaled, img_rect)
            else:
                fallback = font_large.render("YOU WIN!", True, YELLOW)
                fallback_rect = fallback.get_rect(center=(win_rect.centerx, win_rect.y + 120))
                screen.blit(fallback, fallback_rect)

            score_text_win = font_large.render(f"Score: {score}", True, WHITE)
            score_rect_win = score_text_win.get_rect(center=(win_rect.centerx, win_rect.y + 200))
            screen.blit(score_text_win, score_rect_win)

            play_again_rect = pygame.Rect(win_rect.x + 150, win_rect.y + win_height - 70, 200, 40)
            pygame.draw.rect(screen, BTN_BG, play_again_rect, border_radius=6)
            pygame.draw.rect(screen, WHITE, play_again_rect, 1, border_radius=6)
            pa_txt = font_medium.render("Play Again?", True, WHITE)
            pa_txt_rect = pa_txt.get_rect(center=play_again_rect.center)
            screen.blit(pa_txt, pa_txt_rect)

        # GAME OVER POPUP
        if game_over:
            go_width = 400
            go_height = 220
            go_rect = pygame.Rect(
                (WINDOW_WIDTH - go_width) // 2,
                (WINDOW_HEIGHT - go_height) // 2,
                go_width,
                go_height,
            )

            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            pygame.draw.rect(screen, POPUP_BG, go_rect, border_radius=10)
            pygame.draw.rect(screen, POPUP_BORDER, go_rect, 2, border_radius=10)

            title = font_large.render("GAME OVER (Try again ;))", True, YELLOW)
            title_rect = title.get_rect(center=(go_rect.centerx, go_rect.y + 50))
            screen.blit(title, title_rect)

            score_text_go = font_large.render(f"Score: {score}", True, WHITE)
            score_rect_go = score_text_go.get_rect(center=(go_rect.centerx, go_rect.y + 100))
            screen.blit(score_text_go, score_rect_go)

            try_again_rect = pygame.Rect(go_rect.x + 100, go_rect.y + 140, 200, 40)
            pygame.draw.rect(screen, BTN_BG, try_again_rect, border_radius=6)
            pygame.draw.rect(screen, WHITE, try_again_rect, 1, border_radius=6)
            ta_txt = font_medium.render("I wanna try again", True, WHITE)
            ta_txt_rect = ta_txt.get_rect(center=try_again_rect.center)
            screen.blit(ta_txt, ta_txt_rect)

        pygame.display.flip()
        clock.tick(60)

    if ser is not None:
        ser.close()
    pygame.quit()
    print("Program closed.")


if __name__ == "__main__":
    main()