import pygame
import serial
import serial.tools.list_ports
import time

# ====== WINDOW CONFIGURATION (same as main.py) ======
WINDOW_WIDTH  = 1000
WINDOW_HEIGHT = 800
# ====================================================

# Scores for X and O
x_score = 0
o_score = 0


GRID_SIZE   = 3
BOARD_SIZE  = 600
BOARD_X     = (WINDOW_WIDTH - BOARD_SIZE) // 2 - 160
BOARD_Y     = (WINDOW_HEIGHT - BOARD_SIZE) // 2
CELL_SIZE   = BOARD_SIZE // GRID_SIZE

# Image paths for X and O symbols
X_IMAGE_PATH = "pyGame/assets/figures/tic-tac-toe/x-symbol.png"
O_IMAGE_PATH = "pyGame/assets/figures/tic-tac-toe/o-symbol.png"


# Serial options
BAUD_OPTIONS = [9600, 115200]

# Colors
BG_COLOR        = (10, 10, 10)
GRID_COLOR      = (200, 200, 200)
X_COLOR         = (200, 50, 50)
O_COLOR         = (50, 150, 220)
TEXT_COLOR      = (255, 255, 255)
BTN_BG          = (60, 60, 60)
BTN_BG_HOVER    = (90, 90, 90)
POPUP_BG        = (30, 30, 30)
POPUP_BORDER    = (200, 200, 200)
STATUS_BG       = (30, 30, 30)
ERROR_COLOR     = (220, 80, 80)
HINT_COLOR      = (200, 200, 200)
HOVER_CELL      = (255, 255, 255, 30)  # transparent white for hovered cell

NUM_MESSAGES_SHOWN = 25

def check_winner(board):
    """
    board: 3x3 list with 'X', 'O' or ''.

    Returns:
      - 'X' or 'O' if there is a winner
      - 'draw' if the board is full and no winner
      - None if game continues
    """
    lines = []

    # Rows
    for r in range(3):
        lines.append(board[r])

    # Columns
    for c in range(3):
        col = [board[r][c] for r in range(3)]
        lines.append(col)

    # Diagonals
    diag1 = [board[i][i] for i in range(3)]
    diag2 = [board[i][2 - i] for i in range(3)]
    lines.append(diag1)
    lines.append(diag2)

    for line in lines:
        if line[0] != "" and line[0] == line[1] == line[2]:
            return line[0]

    full = all(board[r][c] != "" for r in range(3) for c in range(3))
    if full:
        return "draw"

    return None


def get_cell_from_mouse(pos):
    """
    Returns (row, col) if the mouse is anywhere inside the square
    of that cell. The *whole* square is clickable.
    """
    mx, my = pos
    if mx < BOARD_X or mx >= BOARD_X + BOARD_SIZE:
        return None
    if my < BOARD_Y or my >= BOARD_Y + BOARD_SIZE:
        return None

    col = (mx - BOARD_X) // CELL_SIZE
    row = (my - BOARD_Y) // CELL_SIZE
    return (row, col)


def run_tictactoe_game(screen):
    """
    Tic-Tac-Toe game with two players over a serial connection.

    Protocol:
      - Symbol selection:
          SYMBOL:SELECTED:X
          SYMBOL:SELECTED:O
        * Depois de clicar, envia SYMBOL:SELECTED:<SYMBOL> 10x/s
          até receber o símbolo do oponente.

      - Moves:
          MOVE:row,col,symbol   (ex: MOVE:1,2,X)

      - Rematch:
          REMATCH:REQUEST
          REMATCH:ACCEPT
    """
    pygame.display.set_caption("Embedded Programming - Tic-Tac-Toe")
    clock = pygame.time.Clock()

    font_title = pygame.font.SysFont(None, 60)
    font_big   = pygame.font.SysFont(None, 80)
    font_mid   = pygame.font.SysFont(None, 40)
    font_small = pygame.font.SysFont(None, 24)

    # --- Load X/O images and scale to fit a cell ---
    try:
        x_image_raw = pygame.image.load(X_IMAGE_PATH).convert_alpha()
        o_image_raw = pygame.image.load(O_IMAGE_PATH).convert_alpha()
    except Exception as e:
        print("Error loading X/O images:", e)
        x_image_raw = None
        o_image_raw = None

    # factor < 1.0 so there is some margin inside the cell
    scale_factor = 0.7
    target_size = int(CELL_SIZE * scale_factor)

    if x_image_raw:
        x_image = pygame.transform.smoothscale(
            x_image_raw, (target_size, target_size)
        )
    else:
        x_image = None

    if o_image_raw:
        o_image = pygame.transform.smoothscale(
            o_image_raw, (target_size, target_size)
        )
    else:
        o_image = None


    # ---- SERIAL STATE ------------------------------------------------
    ports = list(serial.tools.list_ports.comports())
    selected_port_index = 0 if ports else -1
    selected_baud_index = 1 if len(BAUD_OPTIONS) > 1 else 0
    serial_error = ""
    ser = None

    # For non-blocking line-oriented reading
    rx_buffer = ""

    def refresh_ports():
        nonlocal ports, selected_port_index
        ports = list(serial.tools.list_ports.comports())
        selected_port_index = 0 if ports else -1

    def network_send(message: str):
        """Send a message line over serial if connected."""
        nonlocal ser
        msg = message.strip() + "\n"
        add_log(f"(TX): {message}")
        if ser and ser.is_open:
            try:
                ser.write(msg.encode("utf-8", errors="ignore"))
            except Exception as e:
                print(f"[SERIAL SEND ERROR] {e}")
        else:
            print(f"[OUT (no serial)] {message}")

    def network_poll():
        """
        Non-blocking read of all complete lines currently available on serial.
        Returns a list of messages (str, stripped).
        """
        nonlocal ser, rx_buffer
        messages = []
        if not ser or not ser.is_open:
            return messages

        try:
            waiting = ser.in_waiting
            if waiting:
                data = ser.read(waiting)
                try:
                    chunk = data.decode("utf-8", errors="ignore")
                except Exception:
                    chunk = ""
                if chunk:
                    rx_buffer += chunk

            while "\n" in rx_buffer:
                line, rx_buffer = rx_buffer.split("\n", 1)
                line = line.strip()
                if line:
                    messages.append(line)
                    add_log(f"(RX): {line}")
        except Exception as e:
            print(f"[SERIAL READ ERROR] {e}")

        return messages

    # ---- GAME STATE --------------------------------------------------
    board = [["" for _ in range(3)] for _ in range(3)]

    my_symbol = None
    opponent_symbol = None
    current_turn = "X"
    game_state = "serial_setup"  # 'serial_setup','select_symbol','waiting','playing','finished'
    winner = None
    quit_program = False

    status_message = "Select serial port and baud rate."

    # Serial / protocol message log (like the coffee game)
    msg_log = []  # list of strings

    def add_log(message: str):
        """Append a message to the log and keep only the last N."""
        msg_log.append(message)
        if len(msg_log) > NUM_MESSAGES_SHOWN:
            msg_log.pop(0)


    # X/O selection broadcast control
    broadcasting_symbol = False
    last_broadcast_time = 0.0
    BROADCAST_INTERVAL = 0.1  # 10 times per second

    # Rematch control
    rematch_request_sent = False
    rematch_request_received = False

    def reset_round():
        """Start a new round with same symbols."""
        nonlocal board, winner, current_turn, game_state
        nonlocal rematch_request_sent, rematch_request_received
        nonlocal status_message
        nonlocal msg_log   # <--- adiciona isto

        board = [["" for _ in range(3)] for _ in range(3)]
        winner = None
        current_turn = "X"
        game_state = "playing"
        rematch_request_sent = False
        rematch_request_received = False
        status_message = f"You are {my_symbol}. X starts."

        # limpa o painel de mensagens
        msg_log.clear()


    # UI elements

    # Serial setup buttons
    refresh_btn_rect = pygame.Rect(700, 180, 150, 40)
    connect_btn_rect = pygame.Rect(700, 240, 150, 40)

    # Symbol selection buttons
    btn_width = 140
    btn_height = 60
    btn_spacing = 40
    x_btn_rect = pygame.Rect(
        (WINDOW_WIDTH - 2 * btn_width - btn_spacing) // 2,
        260,
        btn_width,
        btn_height,
    )
    o_btn_rect = pygame.Rect(
        x_btn_rect.right + btn_spacing,
        260,
        btn_width,
        btn_height,
    )

    button_width  = 280
    button_height = 50
    button_spacing = 20

    back_btn_rect = pygame.Rect(
        (WINDOW_WIDTH // 2) - button_width - button_spacing // 2,
        520,
        button_width,
        button_height,
    )
    rematch_btn_rect = pygame.Rect(
        (WINDOW_WIDTH // 2) + button_spacing // 2,
        520,
        button_width,
        button_height,
    )

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False

        # === Precompute rects for COM and baud buttons (used in click + draw) ===
        port_rects = []
        baud_rects = []
        if game_state == "serial_setup":
            # small COM buttons
            base_x_port = 110
            base_y_port = 170
            w_port = 80
            h_port = 32
            spacing_port = 10
            for i, _ in enumerate(ports):
                r = pygame.Rect(
                    base_x_port,
                    base_y_port + i * (h_port + spacing_port),
                    w_port,
                    h_port,
                )
                port_rects.append(r)

            # small baud buttons
            base_x_baud = 380
            base_y_baud = 170
            w_baud = 80
            h_baud = 32
            spacing_baud = 10
            for i, _ in enumerate(BAUD_OPTIONS):
                r = pygame.Rect(
                    base_x_baud,
                    base_y_baud + i * (h_baud + spacing_baud),
                    w_baud,
                    h_baud,
                )
                baud_rects.append(r)

        # ------------------------------------------------------------
        # EVENTS
        # ------------------------------------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_program = True
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    quit_program = True
                    running = False
                elif event.key == pygame.K_ESCAPE:
                    running = False

        # ------------------------------------------------------------
        # SERIAL MESSAGES
        # ------------------------------------------------------------
        messages = network_poll()
        for msg in messages:
            if msg.startswith("SYMBOL:SELECTED:"):
                remote_symbol = msg.split(":")[-1].upper()

                if my_symbol is None:
                    opponent_symbol = remote_symbol
                    my_symbol = "O" if remote_symbol == "X" else "X"
                    status_message = f"You are {my_symbol}. X starts."
                    game_state = "playing"
                    network_send(f"SYMBOL:SELECTED:{my_symbol}")
                else:
                    opponent_symbol = remote_symbol
                    if game_state in ("waiting", "select_symbol"):
                        game_state = "playing"
                        status_message = f"You are {my_symbol}. X starts."

                broadcasting_symbol = False

            elif msg.startswith("MOVE:"):
                try:
                    payload = msg[5:]
                    parts = payload.split(",")
                    row = int(parts[0])
                    col = int(parts[1])
                    sym = parts[2].upper() if len(parts) > 2 else None
                except Exception:
                    continue

                if 0 <= row < 3 and 0 <= col < 3 and board[row][col] == "" and game_state == "playing":
                    if sym is None and opponent_symbol is not None:
                        sym = opponent_symbol

                    if sym is not None:
                        board[row][col] = sym
                        current_turn = "O" if current_turn == "X" else "X"
                        result = check_winner(board)
                        if result is not None:
                            game_state = "finished"
                            winner = result
                            if winner == "draw":
                                status_message = "Draw! No winner."
                            else:
                                status_message = f"Player {winner} wins!"

            elif msg == "REMATCH:REQUEST":
                rematch_request_received = True
                status_message = "Opponent wants a rematch."

            elif msg == "REMATCH:ACCEPT":
                reset_round()

        # ------------------------------------------------------------
        # SYMBOL BROADCAST (10x/s while waiting)
        # ------------------------------------------------------------
        now = time.time()
        if broadcasting_symbol and my_symbol is not None and ser and ser.is_open:
            if now - last_broadcast_time >= BROADCAST_INTERVAL:
                network_send(f"SYMBOL:SELECTED:{my_symbol}")
                last_broadcast_time = now

        # ------------------------------------------------------------
        # MOUSE CLICKS
        # ------------------------------------------------------------
        if mouse_clicked:
            if game_state == "serial_setup":
                # Select COM
                for idx, r in enumerate(port_rects):
                    if r.collidepoint(mouse_pos):
                        selected_port_index = idx
                        break

                # Select baud
                for idx, r in enumerate(baud_rects):
                    if r.collidepoint(mouse_pos):
                        selected_baud_index = idx
                        break

                # Refresh / Connect
                if refresh_btn_rect.collidepoint(mouse_pos):
                    refresh_ports()
                    serial_error = ""
                    status_message = "Ports refreshed."

                if connect_btn_rect.collidepoint(mouse_pos):
                    serial_error = ""
                    if selected_port_index < 0 or selected_port_index >= len(ports):
                        serial_error = "No port selected."
                        status_message = "Select a valid port."
                    else:
                        port = ports[selected_port_index].device
                        baud = BAUD_OPTIONS[selected_baud_index]
                        try:
                            if ser and ser.is_open:
                                ser.close()
                            ser = serial.Serial(port, baudrate=baud, timeout=0)
                            status_message = f"Connected to {port} @ {baud}."
                            game_state = "select_symbol"
                        except Exception as e:
                            serial_error = f"Error: {e}"
                            status_message = "Failed to open port."

            elif game_state == "select_symbol":
                if x_btn_rect.collidepoint(mouse_pos):
                    my_symbol = "X"
                    status_message = "You chose X. Waiting opponent..."
                    game_state = "waiting"
                    broadcasting_symbol = True
                    last_broadcast_time = 0.0

                elif o_btn_rect.collidepoint(mouse_pos):
                    my_symbol = "O"
                    status_message = "You chose O. Waiting opponent..."
                    game_state = "waiting"
                    broadcasting_symbol = True
                    last_broadcast_time = 0.0

            elif game_state == "playing":
                cell = get_cell_from_mouse(mouse_pos)
                if cell is not None and my_symbol is not None:
                    row, col = cell
                    if current_turn == my_symbol and board[row][col] == "":
                        board[row][col] = my_symbol
                        network_send(f"MOVE:{row},{col},{my_symbol}")
                        current_turn = "O" if current_turn == "X" else "X"
                        result = check_winner(board)
                        if result is not None:
                            game_state = "finished"
                            winner = result
                            if winner == "draw":
                                status_message = "Draw! No winner."
                            else:
                                status_message = f"Player {winner} wins!"

            elif game_state == "finished":
                if back_btn_rect.collidepoint(mouse_pos):
                    running = False
                elif rematch_btn_rect.collidepoint(mouse_pos):
                    if not rematch_request_sent and not rematch_request_received:
                        rematch_request_sent = True
                        network_send("REMATCH:REQUEST")
                        status_message = "Rematch request sent. Waiting opponent."
                    elif rematch_request_received:
                        network_send("REMATCH:ACCEPT")
                        reset_round()

        # ------------------------------------------------------------
        # DRAW
        # ------------------------------------------------------------
        screen.fill(BG_COLOR)

        if game_state == "serial_setup":
            title_text = "Tic-Tac-Toe - Serial Setup"
            title_surf = font_title.render(title_text, True, TEXT_COLOR)
            title_rect = title_surf.get_rect(center=(WINDOW_WIDTH // 2, 80))
        else:
            title_text = "Tic-Tac-Toe"
            title_surf = font_title.render(title_text, True, TEXT_COLOR)
            title_rect = title_surf.get_rect(center=(BOARD_X+BOARD_SIZE//2, 80))
        screen.blit(title_surf, title_rect)

        # ---------------- SERIAL SETUP SCREEN -----------------------
        if game_state == "serial_setup":
            # Labels
            ports_label = font_mid.render("Serial port", True, TEXT_COLOR)
            baud_label  = font_mid.render("Baud rate", True, TEXT_COLOR)
            screen.blit(ports_label, (80, 130))
            screen.blit(baud_label,  (350, 130))

            # COM buttons
            if not ports:
                no_port_surf = font_small.render("No ports found.", True, HINT_COLOR)
                screen.blit(no_port_surf, (80, 175))
            else:
                for i, p in enumerate(ports):
                    rect = port_rects[i]
                    if i == selected_port_index:
                        bg = BTN_BG_HOVER
                    else:
                        bg = BTN_BG
                    pygame.draw.rect(screen, bg, rect, border_radius=6)
                    pygame.draw.rect(screen, TEXT_COLOR, rect, 2, border_radius=6)

                    label = p.device  # only "COM3", "COM15", etc.
                    txt = font_small.render(label, True, TEXT_COLOR)
                    txt_rect = txt.get_rect(center=rect.center)
                    screen.blit(txt, txt_rect)

            # Baud buttons
            for i, b in enumerate(BAUD_OPTIONS):
                rect = baud_rects[i]
                if i == selected_baud_index:
                    bg = BTN_BG_HOVER
                else:
                    bg = BTN_BG
                pygame.draw.rect(screen, bg, rect, border_radius=6)
                pygame.draw.rect(screen, TEXT_COLOR, rect, 2, border_radius=6)

                label = f"{b}"
                txt = font_small.render(label, True, TEXT_COLOR)
                txt_rect = txt.get_rect(center=rect.center)
                screen.blit(txt, txt_rect)

            # Refresh / Connect buttons
            def draw_button(rect, label):
                if rect.collidepoint(mouse_pos):
                    bg = BTN_BG_HOVER
                else:
                    bg = BTN_BG
                pygame.draw.rect(screen, bg, rect, border_radius=8)
                pygame.draw.rect(screen, TEXT_COLOR, rect, 2, border_radius=8)
                txt_surf = font_mid.render(label, True, TEXT_COLOR)
                txt_rect = txt_surf.get_rect(center=rect.center)
                screen.blit(txt_surf, txt_rect)

            draw_button(refresh_btn_rect, "Refresh")
            draw_button(connect_btn_rect, "Connect")

            if serial_error:
                err_surf = font_small.render(serial_error, True, ERROR_COLOR)
                screen.blit(err_surf, (80, 340))

            # Short UART explanation at bottom
            info_lines = [
                "UART2 on ESP32: TX = GPIO17, RX = GPIO16.",
                "Connect TX(17) -> RX of other board, RX(16) <- TX, and share GND.",
            ]
            y_info = WINDOW_HEIGHT - 130
            for line in info_lines:
                info_surf = font_small.render(line, True, HINT_COLOR)
                screen.blit(info_surf, (80, y_info))
                y_info += 22

        # ---------------- GAME SCREENS ------------------------------
        else:
            # Draw board frame
            pygame.draw.rect(
                screen,
                GRID_COLOR,
                (BOARD_X, BOARD_Y, BOARD_SIZE, BOARD_SIZE),
                width=2,
            )

            # Grid lines
            for i in range(1, GRID_SIZE):
                x = BOARD_X + i * CELL_SIZE
                pygame.draw.line(
                    screen,
                    GRID_COLOR,
                    (x, BOARD_Y),
                    (x, BOARD_Y + BOARD_SIZE),
                    2,
                )
                y = BOARD_Y + i * CELL_SIZE
                pygame.draw.line(
                    screen,
                    GRID_COLOR,
                    (BOARD_X, y),
                    (BOARD_X + BOARD_SIZE, y),
                    2,
                )

            # Hover highlight (whole square) – only if it is my turn
            hover_cell = get_cell_from_mouse(mouse_pos)
            if (
                game_state == "playing"
                and my_symbol is not None
                and current_turn == my_symbol   # só quando é minha vez
                and hover_cell is not None
            ):
                hr, hc = hover_cell
                if board[hr][hc] == "":
                    hx = BOARD_X + hc * CELL_SIZE
                    hy = BOARD_Y + hr * CELL_SIZE
                    hover_surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                    hover_surface.fill(HOVER_CELL)
                    screen.blit(hover_surface, (hx, hy))

            # Draw X and O using images
            for r in range(3):
                for c in range(3):
                    symbol = board[r][c]
                    if symbol == "":
                        continue

                    cx = BOARD_X + c * CELL_SIZE + CELL_SIZE // 2
                    cy = BOARD_Y + r * CELL_SIZE + CELL_SIZE // 2

                    if symbol == "X" and x_image is not None:
                        img_rect = x_image.get_rect(center=(cx, cy))
                        screen.blit(x_image, img_rect)
                    elif symbol == "O" and o_image is not None:
                        img_rect = o_image.get_rect(center=(cx, cy))
                        screen.blit(o_image, img_rect)



            # Symbol selection / info area
            if game_state == "select_symbol":
                def draw_btn(rect, label):
                    if rect.collidepoint(mouse_pos):
                        bg = BTN_BG_HOVER
                    else:
                        bg = BTN_BG
                    pygame.draw.rect(screen, bg, rect, border_radius=8)
                    pygame.draw.rect(screen, TEXT_COLOR, rect, 2, border_radius=8)
                    txt = font_mid.render(label, True, TEXT_COLOR)
                    txt_rect = txt.get_rect(center=rect.center)
                    screen.blit(txt, txt_rect)

                info_surf = font_mid.render("Choose your symbol", True, TEXT_COLOR)
                info_rect = info_surf.get_rect(center=(WINDOW_WIDTH // 2, 210))
                screen.blit(info_surf, info_rect)

                draw_btn(x_btn_rect, "Be X")
                draw_btn(o_btn_rect, "Be O")

            elif game_state == "waiting":
                waiting_text = "Waiting opponent to connect..."
                wt_surf = font_mid.render(waiting_text, True, TEXT_COLOR)
                wt_rect = wt_surf.get_rect(center=(WINDOW_WIDTH // 2, 220))
                screen.blit(wt_surf, wt_rect)

            elif game_state == "finished":
                popup_width  = 700
                popup_height = 260
                popup_rect = pygame.Rect(
                    (WINDOW_WIDTH - popup_width) // 2,
                    (WINDOW_HEIGHT - popup_height) // 2,
                    popup_width,
                    popup_height,
                )

                # Depois de criar popup_rect...
                button_width  = 240
                button_height = 50
                button_spacing = 20

                # y dos botões: um pouco abaixo do fundo do popup
                buttons_y = popup_rect.bottom + 10

                back_btn_rect = pygame.Rect(
                    (WINDOW_WIDTH // 2) - button_width - button_spacing // 2,
                    buttons_y,
                    button_width,
                    button_height,
                )
                rematch_btn_rect = pygame.Rect(
                    (WINDOW_WIDTH // 2) + button_spacing // 2,
                    buttons_y,
                    button_width,
                    button_height,
                )

                overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                screen.blit(overlay, (0, 0))

                pygame.draw.rect(screen, POPUP_BG, popup_rect, border_radius=10)
                pygame.draw.rect(screen, POPUP_BORDER, popup_rect, 2, border_radius=10)

                if winner == "draw":
                    result_text = "Draw!"
                else:
                    result_text = f"{winner} wins!"

                res_surf = font_big.render(result_text, True, TEXT_COLOR)
                res_rect = res_surf.get_rect(center=(popup_rect.centerx, popup_rect.y + 70))
                screen.blit(res_surf, res_rect)

                def draw_popup_button(rect, label):
                    if rect.collidepoint(mouse_pos):
                        bg = BTN_BG_HOVER
                    else:
                        bg = BTN_BG
                    pygame.draw.rect(screen, bg, rect, border_radius=8)
                    pygame.draw.rect(screen, TEXT_COLOR, rect, 2, border_radius=8)
                    lbl_surf = font_mid.render(label, True, TEXT_COLOR)
                    lbl_rect = lbl_surf.get_rect(center=rect.center)
                    screen.blit(lbl_surf, lbl_rect)

                draw_popup_button(back_btn_rect, "Back to menu")

                if rematch_request_received:
                    rematch_label = "Accept challenge?"
                elif rematch_request_sent:
                    rematch_label = "Waiting..."
                else:
                    rematch_label = "Play again?"

                draw_popup_button(rematch_btn_rect, rematch_label)

        # ===== RIGHT-SIDE MESSAGE PANEL (like coffee game) =====
        if game_state not in ("serial_setup", "finished"):
            panel_width = 320
            panel_height = 620
            panel_x = WINDOW_WIDTH - panel_width - 20
            panel_y = (WINDOW_HEIGHT - panel_height) // 2

            panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)

            # Semi-transparent background
            panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
            panel_surface.fill((240, 240, 240, 180))  # light grey with alpha
            screen.blit(panel_surface, (panel_x, panel_y))

            # Border
            border_color = (140, 140, 140)
            pygame.draw.rect(screen, border_color, panel_rect, 2, border_radius=8)

            # Title above the panel (white)
            title_surf = font_small.render("Serial / game messages:", True, TEXT_COLOR)
            # ou: title_surf = font_small.render("Serial / game messages:", True, (255, 255, 255))
            title_rect = title_surf.get_rect()
            title_rect.topleft = (panel_x + 10, panel_y - title_rect.height - 5)
            screen.blit(title_surf, title_rect)


            # Messages inside
            line_y = panel_y + 10
            line_spacing = 18
            for msg in msg_log:
                msg_surf = font_small.render(msg, True, (0, 0, 0))
                screen.blit(msg_surf, (panel_x + 10, line_y))
                line_y += line_spacing


        # Status bar
        status_rect = pygame.Rect(0, WINDOW_HEIGHT - 40, WINDOW_WIDTH, 40)
        pygame.draw.rect(screen, STATUS_BG, status_rect)

        if game_state == "playing" and my_symbol is not None:
            # Mensagem de turno na barra de baixo
            if current_turn == my_symbol:
                turn_text = f"Your turn ({my_symbol})"
                # Piscar em verde de leve
                blink_on = (time.time() * 2.0) % 1.0 < 0.5   # ~2 Hz
                if blink_on:
                    color = (0, 220, 0)
                else:
                    color = (90, 200, 90)
            else:
                turn_text = "Opponent's turn"
                color = TEXT_COLOR  # branco

            status_surf = font_small.render(turn_text, True, color)
        else:
            # Fora do jogo (setup, waiting, finished) mostra status_message normal
            status_surf = font_small.render(status_message, True, TEXT_COLOR)

        screen.blit(status_surf, (20, WINDOW_HEIGHT - 30))

        # Hint
        hint_text = "ESC: back to menu   |   Q: quit program"
        hint_surf = font_small.render(hint_text, True, HINT_COLOR)
        screen.blit(hint_surf, (20, WINDOW_HEIGHT - 60))

        pygame.display.flip()
        clock.tick(60)

    # Close serial when leaving game
    if ser and ser.is_open:
        try:
            ser.close()
        except Exception:
            pass

    print("Tic-Tac-Toe game closed.")
    return "quit" if quit_program else "menu"
