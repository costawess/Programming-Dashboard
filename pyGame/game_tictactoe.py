import pygame
import serial
import serial.tools.list_ports
import time

# ====== WINDOW CONFIGURATION (same as main.py) ======
WINDOW_WIDTH  = 1000
WINDOW_HEIGHT = 800
# ====================================================

GRID_SIZE   = 3
BOARD_SIZE  = 600
BOARD_X     = (WINDOW_WIDTH - BOARD_SIZE) // 2
BOARD_Y     = (WINDOW_HEIGHT - BOARD_SIZE) // 2
CELL_SIZE   = BOARD_SIZE // GRID_SIZE

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

    # Draw?
    full = all(board[r][c] != "" for r in range(3) for c in range(3))
    if full:
        return "draw"

    return None


def get_cell_from_mouse(pos):
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

        Regra extra:
          * Quando o usuário clicar em um símbolo, ele envia
            SYMBOL:SELECTED:<SIMBOLO> 10x por segundo até o outro responder.

      - Moves:
          MOVE:row,col,symbol   (ex: MOVE:1,2,X)

    Fluxo de entrada no jogo:
      1) Tela de seleção de porta COM + baud.
      2) Depois de conectar:
         - Se chegar SYMBOL:SELECTED:... antes do jogador clicar em algo,
           esse jogador NÃO vê tela de seleção.
           Ele recebe diretamente "You are O/X" (símbolo oposto) e o jogo começa.
         - Se ele clicar primeiro, começa a transmitir o SYMBOL:SELECTED:<...>
           10x por segundo até o outro mandar o seu SYMBOL:SELECTED.
    """
    pygame.display.set_caption("Embedded Programming - Tic-Tac-Toe")
    clock = pygame.time.Clock()

    font_title = pygame.font.SysFont(None, 60)
    font_big   = pygame.font.SysFont(None, 80)
    font_mid   = pygame.font.SysFont(None, 40)
    font_small = pygame.font.SysFont(None, 24)

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
        if ser and ser.is_open:
            try:
                ser.write(msg.encode("utf-8", errors="ignore"))
            except Exception as e:
                # Just print to console; status bar also will indicate issues if needed.
                print(f"[SERIAL SEND ERROR] {e}")
        else:
            # For debug when not connected
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
            # Read all available bytes
            waiting = ser.in_waiting
            if waiting:
                data = ser.read(waiting)
                try:
                    chunk = data.decode("utf-8", errors="ignore")
                except Exception:
                    chunk = ""
                if chunk:
                    rx_buffer += chunk

            # Extract full lines
            while "\n" in rx_buffer:
                line, rx_buffer = rx_buffer.split("\n", 1)
                line = line.strip()
                if line:
                    messages.append(line)
        except Exception as e:
            print(f"[SERIAL READ ERROR] {e}")

        return messages

    # ---- GAME STATE --------------------------------------------------
    board = [["" for _ in range(3)] for _ in range(3)]

    my_symbol = None          # 'X' or 'O'
    opponent_symbol = None    # 'X' or 'O'
    current_turn = "X"        # X always starts
    game_state = "serial_setup"  # 'serial_setup','select_symbol','waiting','playing','finished'
    winner = None             # 'X', 'O', 'draw' or None
    quit_program = False

    status_message = "Select serial port and baud rate."

    # X/O selection broadcast control
    broadcasting_symbol = False
    last_broadcast_time = 0.0
    BROADCAST_INTERVAL = 0.1  # 10 times per second

    # UI elements

    # Serial setup buttons
    port_list_rect = pygame.Rect(80, 170, 380, 360)
    baud_list_rect = pygame.Rect(540, 170, 200, 140)
    refresh_btn_rect = pygame.Rect(540, 340, 200, 50)
    connect_btn_rect = pygame.Rect(540, 410, 200, 50)

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

    # Button for "Back to menu" on finished screen
    back_btn_rect = pygame.Rect(
        (WINDOW_WIDTH - 200) // 2,
        520,
        200,
        50,
    )

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False

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
                    # ESC always returns to menu from inside the game
                    running = False

        # ------------------------------------------------------------
        # SERIAL MESSAGES (only after connect)
        # ------------------------------------------------------------
        messages = network_poll()
        for msg in messages:
            # Example: SYMBOL:SELECTED:X
            if msg.startswith("SYMBOL:SELECTED:"):
                remote_symbol = msg.split(":")[-1].upper()
                # If we do not have a symbol yet: auto-assign opposite
                if my_symbol is None:
                    opponent_symbol = remote_symbol
                    my_symbol = "O" if remote_symbol == "X" else "X"
                    status_message = f"You are {my_symbol}. X starts."
                    game_state = "playing"
                    broadcasting_symbol = False  # we never started, but ensure disabled

                    # Send our symbol back once (now that we know)
                    network_send(f"SYMBOL:SELECTED:{my_symbol}")

                else:
                    # We already chose something, this is the confirmation from other side
                    opponent_symbol = remote_symbol
                    status_message = f"You are {my_symbol}. X starts."
                    if game_state in ("waiting", "select_symbol"):
                        game_state = "playing"
                # Stop broadcasting once we see the other side
                broadcasting_symbol = False

            # Example: MOVE:row,col,symbol
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

        # ------------------------------------------------------------
        # SYMBOL BROADCAST (10x per second while waiting the other)
        # ------------------------------------------------------------
        now = time.time()
        if broadcasting_symbol and my_symbol is not None and ser and ser.is_open:
            if now - last_broadcast_time >= BROADCAST_INTERVAL:
                network_send(f"SYMBOL:SELECTED:{my_symbol}")
                last_broadcast_time = now

        # ------------------------------------------------------------
        # MOUSE CLICKS (LOCAL ACTIONS)
        # ------------------------------------------------------------
        if mouse_clicked:
            # --- SERIAL SETUP SCREEN ---
            if game_state == "serial_setup":
                # Click inside port list
                if port_list_rect.collidepoint(mouse_pos):
                    # Determine which line was clicked
                    x, y = mouse_pos
                    relative_y = y - port_list_rect.y
                    line_height = 30
                    index = relative_y // line_height
                    if 0 <= index < len(ports):
                        selected_port_index = index

                # Click inside baud list
                elif baud_list_rect.collidepoint(mouse_pos):
                    x, y = mouse_pos
                    relative_y = y - baud_list_rect.y
                    line_height = 30
                    index = relative_y // line_height
                    if 0 <= index < len(BAUD_OPTIONS):
                        selected_baud_index = index

                # Refresh ports
                if refresh_btn_rect.collidepoint(mouse_pos):
                    refresh_ports()
                    serial_error = ""
                    status_message = "Ports refreshed."

                # Connect
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

            # --- SYMBOL SELECTION ---
            elif game_state == "select_symbol":
                if x_btn_rect.collidepoint(mouse_pos):
                    my_symbol = "X"
                    status_message = "You chose X. Waiting opponent..."
                    game_state = "waiting"
                    # Start broadcasting X 10x/s
                    broadcasting_symbol = True
                    last_broadcast_time = 0.0

                elif o_btn_rect.collidepoint(mouse_pos):
                    my_symbol = "O"
                    status_message = "You chose O. Waiting opponent..."
                    game_state = "waiting"
                    # Start broadcasting O 10x/s
                    broadcasting_symbol = True
                    last_broadcast_time = 0.0

            # --- PLAYING: LOCAL MOVE ---
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

            # --- FINISHED: BACK TO MENU ---
            elif game_state == "finished":
                if back_btn_rect.collidepoint(mouse_pos):
                    running = False

        # ------------------------------------------------------------
        # DRAW
        # ------------------------------------------------------------
        screen.fill(BG_COLOR)

        # Title
        if game_state == "serial_setup":
            title_text = "Tic-Tac-Toe - Serial Setup"
        else:
            title_text = "Tic-Tac-Toe (2 Players)"
        title_surf = font_title.render(title_text, True, TEXT_COLOR)
        title_rect = title_surf.get_rect(center=(WINDOW_WIDTH // 2, 80))
        screen.blit(title_surf, title_rect)

        # ---------------- SERIAL SETUP SCREEN -----------------------
        if game_state == "serial_setup":
            # PORT LIST
            pygame.draw.rect(screen, (40, 40, 40), port_list_rect, border_radius=8)
            pygame.draw.rect(screen, TEXT_COLOR, port_list_rect, 2, border_radius=8)
            port_title = font_mid.render("Serial Ports", True, TEXT_COLOR)
            screen.blit(port_title, (port_list_rect.x, port_list_rect.y - 35))

            line_y = port_list_rect.y + 5
            line_height = 30
            if not ports:
                no_port_surf = font_small.render("No ports found.", True, HINT_COLOR)
                screen.blit(no_port_surf, (port_list_rect.x + 10, line_y))
            else:
                for i, p in enumerate(ports):
                    if i == selected_port_index:
                        bg_rect = pygame.Rect(
                            port_list_rect.x + 2,
                            line_y - 2,
                            port_list_rect.width - 4,
                            line_height,
                        )
                        pygame.draw.rect(screen, (90, 90, 90), bg_rect, border_radius=4)

                    label = f"{p.device}  -  {p.description}"
                    port_surf = font_small.render(label, True, TEXT_COLOR)
                    screen.blit(port_surf, (port_list_rect.x + 8, line_y))
                    line_y += line_height

            # BAUD LIST
            pygame.draw.rect(screen, (40, 40, 40), baud_list_rect, border_radius=8)
            pygame.draw.rect(screen, TEXT_COLOR, baud_list_rect, 2, border_radius=8)
            baud_title = font_mid.render("Baud rate", True, TEXT_COLOR)
            screen.blit(baud_title, (baud_list_rect.x, baud_list_rect.y - 35))

            line_y = baud_list_rect.y + 5
            for i, b in enumerate(BAUD_OPTIONS):
                if i == selected_baud_index:
                    bg_rect = pygame.Rect(
                        baud_list_rect.x + 2,
                        line_y - 2,
                        baud_list_rect.width - 4,
                        30,
                    )
                    pygame.draw.rect(screen, (90, 90, 90), bg_rect, border_radius=4)
                lbl = f"{b} bps"
                baud_surf = font_small.render(lbl, True, TEXT_COLOR)
                screen.blit(baud_surf, (baud_list_rect.x + 8, line_y))
                line_y += 30

            # Buttons: Refresh / Connect
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
                screen.blit(err_surf, (80, 550))

        # ---------------- GAME SCREENS ------------------------------
        else:
            # Draw board
            pygame.draw.rect(
                screen,
                GRID_COLOR,
                (BOARD_X, BOARD_Y, BOARD_SIZE, BOARD_SIZE),
                width=2,
            )

            # Grid lines
            for i in range(1, GRID_SIZE):
                # Vertical
                x = BOARD_X + i * CELL_SIZE
                pygame.draw.line(
                    screen,
                    GRID_COLOR,
                    (x, BOARD_Y),
                    (x, BOARD_Y + BOARD_SIZE),
                    2,
                )
                # Horizontal
                y = BOARD_Y + i * CELL_SIZE
                pygame.draw.line(
                    screen,
                    GRID_COLOR,
                    (BOARD_X, y),
                    (BOARD_X + BOARD_SIZE, y),
                    2,
                )

            # Draw X and O on board
            for r in range(3):
                for c in range(3):
                    symbol = board[r][c]
                    if symbol == "":
                        continue

                    cx = BOARD_X + c * CELL_SIZE + CELL_SIZE // 2
                    cy = BOARD_Y + r * CELL_SIZE + CELL_SIZE // 2

                    if symbol == "X":
                        offset = CELL_SIZE // 3
                        pygame.draw.line(
                            screen,
                            X_COLOR,
                            (cx - offset, cy - offset),
                            (cx + offset, cy + offset),
                            6,
                        )
                        pygame.draw.line(
                            screen,
                            X_COLOR,
                            (cx + offset, cy - offset),
                            (cx - offset, cy + offset),
                            6,
                        )
                    elif symbol == "O":
                        radius = CELL_SIZE // 3
                        pygame.draw.circle(
                            screen,
                            O_COLOR,
                            (cx, cy),
                            radius,
                            6,
                        )

            # Symbol selection / info area
            if game_state == "select_symbol":
                # Draw selection buttons
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

            elif game_state == "playing":
                # Show whose turn
                if my_symbol is not None:
                    if current_turn == my_symbol:
                        turn_text = f"Your turn ({my_symbol})"
                    else:
                        turn_text = "Opponent's turn"
                else:
                    turn_text = "Playing..."

                tt_surf = font_mid.render(turn_text, True, TEXT_COLOR)
                tt_rect = tt_surf.get_rect(center=(WINDOW_WIDTH // 2, 220))
                screen.blit(tt_surf, tt_rect)

            elif game_state == "finished":
                # Popup with result
                popup_width  = 500
                popup_height = 260
                popup_rect = pygame.Rect(
                    (WINDOW_WIDTH - popup_width) // 2,
                    (WINDOW_HEIGHT - popup_height) // 2,
                    popup_width,
                    popup_height,
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

                # Button: back to menu
                if back_btn_rect.collidepoint(mouse_pos):
                    bg = BTN_BG_HOVER
                else:
                    bg = BTN_BG
                pygame.draw.rect(screen, bg, back_btn_rect, border_radius=8)
                pygame.draw.rect(screen, TEXT_COLOR, back_btn_rect, 2, border_radius=8)
                back_txt = font_mid.render("Back to menu", True, TEXT_COLOR)
                back_txt_rect = back_txt.get_rect(center=back_btn_rect.center)
                screen.blit(back_txt, back_txt_rect)

        # Status bar at bottom
        status_rect = pygame.Rect(0, WINDOW_HEIGHT - 40, WINDOW_WIDTH, 40)
        pygame.draw.rect(screen, STATUS_BG, status_rect)
        status_surf = font_small.render(status_message, True, TEXT_COLOR)
        screen.blit(status_surf, (20, WINDOW_HEIGHT - 30))

        # Hint at bottom-left
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
