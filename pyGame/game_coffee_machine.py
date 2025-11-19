import pygame
import serial
import serial.tools.list_ports

# ====== WINDOW CONFIGURATION ======
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
# ==================================

# ====== SERIAL CONFIGURATION ======
BAUD_OPTIONS = [9600, 115200]
# ==================================

# ====== COFFEE MACHINE IMAGE ======
COFFEE_IMAGE_PATH = "pyGame/assets/figures/coffee_machine/coffee_machine_cleaned.png"

# Options to be selected
ESPRESSO_IMAGE_PATH = "pyGame/assets/figures/coffee_machine/espresso.png"
CAPUCCINO_IMAGE_PATH = "pyGame/assets/figures/coffee_machine/capuccino.png"
TOMATO_SOUP_IMAGE_PATH = "pyGame/assets/figures/coffee_machine/tomato_soup.png"
CHOCOLATE_IMAGE_PATH = "pyGame/assets/figures/coffee_machine/chocolate.png"


# background
BACKGROUND_COLOR = (237, 215, 196)  # #edd7c4
# ==================================



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
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=(WINDOW_WIDTH // 2, y))
    screen.blit(surface, rect)


def run_coffee_game(screen):
    """
    Coffee Machine game.

    For now it only shows the cleaned coffee machine image, centered,
    with the same ESP32 / Reset / Menu buttons and connection indicators.

    Returns:
        "menu" -> go back to main menu
        "quit" -> close the whole program
    """
    clock = pygame.time.Clock()
    pygame.display.set_caption("Embedded Programming - Coffee Machine")

    # Fonts
    font_small = pygame.font.SysFont(None, 24)
    font_medium = pygame.font.SysFont(None, 32)

    # Top buttons
    esp32_button_rect = pygame.Rect(20, 20, 120, 40)
    reset_button_rect = pygame.Rect(160, 20, 120, 40)
    menu_button_rect = pygame.Rect(300, 20, 120, 40)

    # Colors
    BTN_BG = (60, 60, 60)
    BTN_BG_HOVER = (90, 90, 90)
    POPUP_BG = (30, 30, 30)
    POPUP_BORDER = (200, 200, 200)
    WHITE = (255, 255, 255)
    YELLOW = (255, 255, 0)

    # Serial / status
    ser = None
    status_message = "Not connected."
    status_color = (255, 0, 0)  # red

    config_open = False
    available_ports = []
    selected_port_index = -1
    baud_index = 0  # 9600 by default

    # Load coffee machine image
    coffee_image = None
    try:
        coffee_image = pygame.image.load(COFFEE_IMAGE_PATH).convert_alpha()
    except Exception as e:
        print(f"Could not load coffee machine image: {e}")
        coffee_image = None

    # Load espresso option image --------------------------------------------------
    espresso_image = None
    try:
        espresso_image = pygame.image.load(ESPRESSO_IMAGE_PATH).convert_alpha()
    except Exception as e:
        print(f"Could not load espresso image: {e}")
        espresso_image = None

    # Load capuccino option image --------------------------------------------------
    capuccino_image = None
    try:
        capuccino_image = pygame.image.load(CAPUCCINO_IMAGE_PATH).convert_alpha()
    except Exception as e:
        print(f"Could not load capuccino image: {e}")
        capuccino_image = None

    # Load chocolate option image --------------------------------------------------
    chocolate_image = None
    try:
        chocolate_image = pygame.image.load(CHOCOLATE_IMAGE_PATH).convert_alpha()
    except Exception as e:
        print(f"Could not load chocolate image: {e}")
        chocolate_image = None

    # Load chocolate option image --------------------------------------------------
    tomato_soup_image = None
    try:
        tomato_soup_image = pygame.image.load(TOMATO_SOUP_IMAGE_PATH).convert_alpha()
    except Exception as e:
        print(f"Could not load tomato_soup image: {e}")
        tomato_soup_image = None

    quit_program = False
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_program = True
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True

            if event.type == pygame.KEYDOWN:
                # Q quits everything
                if event.key == pygame.K_q:
                    quit_program = True
                    running = False
                # ESC goes back to menu
                elif event.key == pygame.K_ESCAPE:
                    running = False

        # ---- Handle mouse clicks ----
        if mouse_clicked and not quit_program:
            if config_open:
                # Pop-up geometry
                popup_width = 400
                popup_height = 300
                popup_rect = pygame.Rect(
                    (WINDOW_WIDTH - popup_width) // 2,
                    (WINDOW_HEIGHT - popup_height) // 2,
                    popup_width,
                    popup_height,
                )

                ports_y = popup_rect.y + 80
                port_btn_w = 90
                port_btn_h = 32
                port_spacing = 10

                port_rects = []
                for i, port in enumerate(available_ports):
                    x = popup_rect.x + 20 + i * (port_btn_w + port_spacing)
                    r = pygame.Rect(x, ports_y, port_btn_w, port_btn_h)
                    port_rects.append(r)

                baud_label_y = ports_y + 60
                baud_buttons_y = baud_label_y + 20
                baud_rects = []
                for i, baud in enumerate(BAUD_OPTIONS):
                    r = pygame.Rect(popup_rect.x + 20 + i * 120, baud_buttons_y, 100, 32)
                    baud_rects.append(r)

                btns_y = baud_buttons_y + 60
                btn_connect_rect = pygame.Rect(popup_rect.x + 30, btns_y, 100, 40)
                btn_disconnect_rect = pygame.Rect(popup_rect.x + 150, btns_y, 120, 40)
                btn_cancel_rect = pygame.Rect(popup_rect.x + popup_width - 130, btns_y, 100, 40)

                # Clicks on ports
                for i, r in enumerate(port_rects):
                    if r.collidepoint(mouse_pos):
                        selected_port_index = i

                # Clicks on baud
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

                # Disconnect
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

            else:
                # Main buttons
                if esp32_button_rect.collidepoint(mouse_pos):
                    available_ports = get_available_ports()
                    selected_port_index = 0 if available_ports else -1
                    config_open = True

                elif reset_button_rect.collidepoint(mouse_pos):
                    # For now reset is only a semantic reset: we could later
                    # clear state (errors, etc). We just reset the status.
                    status_message = "Not connected."
                    status_color = (255, 0, 0)

                elif menu_button_rect.collidepoint(mouse_pos):
                    running = False

        # (Future) serial reading logic could go here if Coffee Machine
        # also reacts to ESP32 commands.

        # ===== DRAW SECTION =====
        screen.fill(BACKGROUND_COLOR)

        # Draw centered coffee machine image
        # Draw centered coffee machine image
        # Draw coffee machine image (scaled and repositioned)
        if coffee_image is not None:
            img = coffee_image

            # 1) SCALE: defina o tamanho aqui (1.0 = 100%, 1.3 = 130%, etc.)
            SCALE = 0.085
            iw, ih = img.get_size()
            new_size = (int(iw * SCALE), int(ih * SCALE))
            img = pygame.transform.smoothscale(img, new_size)

            # 2) POSITION: ajuste aqui a posição na tela
            img_rect = img.get_rect()
            img_rect.centerx = WINDOW_WIDTH // 2   # centralizado horizontalmente
            img_rect.top = 60                     # distância do topo (abaixo dos botões)

            screen.blit(img, img_rect)
        else:
            error_text = font_medium.render("Coffee machine image not found.", True, (150, 0, 0))
            error_rect = error_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            screen.blit(error_text, error_rect)

        # draw espresso option inside the machine "screen"
        if espresso_image is not None and img_rect is not None:
            espresso = espresso_image

            # A) SCALE of the espresso icon (change this freely)
            ESPRESSO_SCALE = 0.02   # 0.25 = 25% of original size
            ew, eh = espresso.get_size()
            new_size = (int(ew * ESPRESSO_SCALE), int(eh * ESPRESSO_SCALE))
            espresso = pygame.transform.smoothscale(espresso, new_size)

            # B) POSITION of the espresso inside the machine
            espresso_rect = espresso.get_rect()

            # Center horizontally on the machine
            espresso_rect.centerx = img_rect.centerx-48

            # Vertical position: adjust the offset to place on the “screen”
            # You can tweak +80 to move up/down
            espresso_rect.top = img_rect.top + 108

            screen.blit(espresso, espresso_rect)

        # draw capuccino option inside the machine "screen"
        if capuccino_image is not None and img_rect is not None:
            capuccino = capuccino_image

            # A) SCALE of the capuccino icon (change this freely)
            CAPUCCINO_SCALE = 0.023   # 0.25 = 25% of original size
            ew, eh = capuccino.get_size()
            new_size = (int(ew * CAPUCCINO_SCALE), int(eh * CAPUCCINO_SCALE))
            capuccino = pygame.transform.smoothscale(capuccino, new_size)

            # B) POSITION of the capuccino inside the machine
            capuccino_rect = capuccino.get_rect()

            # Center horizontally on the machine
            capuccino_rect.centerx = img_rect.centerx+27

            # Vertical position: adjust the offset to place on the “screen”
            # You can tweak +80 to move up/down
            capuccino_rect.top = img_rect.top + 98

            screen.blit(capuccino, capuccino_rect)

        # draw chocolate option inside the machine "screen"
        if chocolate_image is not None and img_rect is not None:
            chocolate = chocolate_image

            # A) SCALE of the chocolate icon (change this freely)
            CHOCOLATE_SCALE = 0.023   # 0.25 = 25% of original size
            ew, eh = chocolate.get_size()
            new_size = (int(ew * CHOCOLATE_SCALE), int(eh * CHOCOLATE_SCALE))
            chocolate = pygame.transform.smoothscale(chocolate, new_size)

            # B) POSITION of the chocolate inside the machine
            chocolate_rect = chocolate.get_rect()

            # Center horizontally on the machine
            chocolate_rect.centerx = img_rect.centerx-48

            # Vertical position: adjust the offset to place on the “screen”
            # You can tweak +80 to move up/down
            chocolate_rect.top = img_rect.top + 180

            screen.blit(chocolate, chocolate_rect)

        # draw tomato_soup option inside the machine "screen"
        if tomato_soup_image is not None and img_rect is not None:
            tomato_soup = tomato_soup_image
            # A) SCALE of the tomato_soup icon (change this freely)
            TOMATO_SOUP_SCALE = 0.023   # 0.25 = 25% of original size
            ew, eh = tomato_soup.get_size()
            new_size = (int(ew * TOMATO_SOUP_SCALE), int(eh * TOMATO_SOUP_SCALE))
            tomato_soup = pygame.transform.smoothscale(tomato_soup, new_size)

            # B) POSITION of the tomato_soup inside the machine
            tomato_soup_rect = tomato_soup.get_rect()

            # Center horizontally on the machine
            tomato_soup_rect.centerx = img_rect.centerx+27

            # Vertical position: adjust the offset to place on the “screen”
            # You can tweak +80 to move up/down
            tomato_soup_rect.top = img_rect.top + 180

            screen.blit(tomato_soup, tomato_soup_rect)
        

        # ===== TOP BUTTONS =====
        # ESP32
        btn_color_esp32 = BTN_BG_HOVER if esp32_button_rect.collidepoint(mouse_pos) and not config_open else BTN_BG
        pygame.draw.rect(screen, btn_color_esp32, esp32_button_rect, border_radius=6)
        pygame.draw.rect(screen, WHITE, esp32_button_rect, 1, border_radius=6)
        txt_esp32 = font_small.render("ESP32", True, WHITE)
        screen.blit(txt_esp32, txt_esp32.get_rect(center=esp32_button_rect.center))

        # Reset
        btn_color_reset = BTN_BG_HOVER if reset_button_rect.collidepoint(mouse_pos) and not config_open else BTN_BG
        pygame.draw.rect(screen, btn_color_reset, reset_button_rect, border_radius=6)
        pygame.draw.rect(screen, WHITE, reset_button_rect, 1, border_radius=6)
        txt_reset = font_small.render("Reset", True, WHITE)
        screen.blit(txt_reset, txt_reset.get_rect(center=reset_button_rect.center))

        # Menu
        btn_color_menu = BTN_BG_HOVER if menu_button_rect.collidepoint(mouse_pos) and not config_open else BTN_BG
        pygame.draw.rect(screen, btn_color_menu, menu_button_rect, border_radius=6)
        pygame.draw.rect(screen, WHITE, menu_button_rect, 1, border_radius=6)
        txt_menu = font_small.render("Menu", True, WHITE)
        screen.blit(txt_menu, txt_menu.get_rect(center=menu_button_rect.center))

        # ===== BOTTOM STATUS (same estilo do maze) =====
        status_surface = font_small.render(status_message, True, status_color)
        screen.blit(status_surface, (20, WINDOW_HEIGHT - 30))

        hint_text = "ESC: Menu  |  Q: Quit  |  Use ESP32 button to configure serial"
        hint_surface = font_small.render(hint_text, True, (0, 0, 0))
        screen.blit(hint_surface, (20, WINDOW_HEIGHT - 55))

        # ===== CONFIG POPUP =====
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
            draw_text_center(
                screen,
                "ESP32 Serial Configuration",
                title_font,
                YELLOW,
                popup_rect.y + 30,
            )

            label_font = pygame.font.SysFont(None, 24)

            # Port label
            port_label = label_font.render("Port:", True, WHITE)
            screen.blit(port_label, (popup_rect.x + 20, popup_rect.y + 55))

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

            baud_label_y = ports_y + 60
            baud_buttons_y = baud_label_y + 20

            baud_label = label_font.render("Baud rate:", True, WHITE)
            screen.blit(baud_label, (popup_rect.x + 20, baud_label_y))

            for i, baud in enumerate(BAUD_OPTIONS):
                r = pygame.Rect(popup_rect.x + 20 + i * 120, baud_buttons_y, 100, 32)
                bg_color = (80, 80, 80) if i == baud_index else (40, 40, 40)
                pygame.draw.rect(screen, bg_color, r, border_radius=6)
                pygame.draw.rect(screen, WHITE, r, 1, border_radius=6)
                t = label_font.render(str(baud), True, WHITE)
                t_rect = t.get_rect(center=r.center)
                screen.blit(t, t_rect)

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

        pygame.display.flip()
        clock.tick(60)

    if ser is not None:
        ser.close()

    print("Coffee game closed.")
    return "quit" if quit_program else "menu"
