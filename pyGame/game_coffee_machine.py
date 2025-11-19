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

# COLORS
green_color = (0, 170, 0)
red_color   = (255, 0, 0)
black_color = (0, 0, 0)
HOVER_OVERLAY_COLOR = (255, 246, 213, 80)



# ====== COFFEE MACHINE IMAGE ======
COFFEE_IMAGE_PATH = "pyGame/assets/figures/coffee_machine/coffee_machine_cleaned.png"

# ====== DRINK OPTIONS (edit only this list to add new options) ======
DRINK_OPTIONS = [
    {
        "name": "espresso",
        "path": "pyGame/assets/figures/coffee_machine/espresso.png",
        "scale": 0.02,
        "dx": -42,
        "dy": 108,
        "command": "SELECTED:ESPRESSO",  # text sent to ESP32
    },
    {
        "name": "capuccino",
        "path": "pyGame/assets/figures/coffee_machine/capuccino.png",
        "scale": 0.023,
        "dx": 31,
        "dy": 98,
        "command": "SELECTED:CAPUCCINO",
    },
    {
        "name": "tomato_soup",
        "path": "pyGame/assets/figures/coffee_machine/tomato_soup.png",
        "scale": 0.02,
        "dx": -42,
        "dy": 180,
        "command": "SELECTED:TOMATO_SOUP",
    },
    {
        "name": "chocolate",
        "path": "pyGame/assets/figures/coffee_machine/chocolate.png",
        "scale": 0.02,
        "dx": 31,
        "dy": 180,
        "command": "SELECTED:CHOCOLATE",
    },
]
# ============================================================

# ====== CUSTOMIZATION STEPS (Sugar, Strength, Milk) ======
CUSTOM_STEPS = [
    {
        "name": "sugar",
        "title": "Sugar level",
        "prefix": "SUGAR:",
        "options": [
            ("No sugar", "NO_SUGAR"),
            ("Low", "LOW"),
            ("Medium", "MEDIUM"),
            ("High", "HIGH"),
        ],
    },
    {
        "name": "strength",
        "title": "Strength level",
        "prefix": "STRENGTH:",
        "options": [
            ("Mild", "MILD"),
            ("Medium", "MEDIUM"),
            ("Strong", "STRONG"),
        ],
    },
    {
        "name": "milk",
        "title": "Milk",
        "prefix": "MILK:",
        "options": [
            ("Yes", "YES"),
            ("No", "NO"),
        ],
    },
]
# =========================================================

# Background
BACKGROUND_COLOR = (237, 215, 196)  # #edd7c4


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


def load_drink_images():
    """
    Load all drink option images defined in DRINK_OPTIONS.
    Returns a list of dicts with the same keys plus 'image'.
    """
    loaded = []
    for opt in DRINK_OPTIONS:
        try:
            img = pygame.image.load(opt["path"]).convert_alpha()
            entry = opt.copy()
            entry["image"] = img
            loaded.append(entry)
        except Exception as e:
            print(f"Could not load drink image '{opt['name']}' from {opt['path']}: {e}")
    return loaded


def run_coffee_game(screen):
    """
    Coffee Machine game.

    Displays the coffee machine and drink options.
    Clicking a drink while ESP32 is connected sends a command over serial.

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

    # Load all drinks once
    drink_images = load_drink_images()

    # State for customization mode
    customize_mode = False   # False = mostrando drinks, True = perguntando Sugar/Strength/Milk
    custom_step = 0          # 0 = Sugar, 1 = Strength, 2 = Milk


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

        # ================= HANDLE MOUSE (buttons and popup) =================
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
                        status_color = green_color if success else red_color
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
                    # Volta para a tela de seleção de drinks
                    customize_mode = False
                    custom_step = 0

                    # Mensagem de status amigável, sem mexer na COM
                    if ser is not None and ser.is_open:
                        status_message = "Ready. Select a drink."
                        status_color = green_color
                    else:
                        status_message = "Not connected. Configure ESP32."
                        status_color = red_color


                elif menu_button_rect.collidepoint(mouse_pos):
                    running = False

        # ====================== DRAW SECTION ======================
        screen.fill(BACKGROUND_COLOR)

        # Draw coffee machine (scaled and repositioned)
        img_rect = None
        if coffee_image is not None:
            img = coffee_image
            MACHINE_SCALE = 0.085
            iw, ih = img.get_size()
            new_size = (int(iw * MACHINE_SCALE), int(ih * MACHINE_SCALE))
            img = pygame.transform.smoothscale(img, new_size)

            img_rect = img.get_rect()
            img_rect.centerx = WINDOW_WIDTH // 2
            img_rect.top = 60
            screen.blit(img, img_rect)
        else:
            error_text = font_medium.render("Coffee machine image not found.", True, (150, 0, 0))
            error_rect = error_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            screen.blit(error_text, error_rect)

        # Draw drink options OR customization options and remember rects
        drink_click_areas = []   # list of (rect, drink_dict)
        custom_click_areas = []  # list of (rect, command_str) for customization

        if img_rect is not None:
            if not customize_mode:
                # === NORMAL MODE: mostrar as imagens das bebidas ===
                for drink in drink_images:
                    base_img = drink["image"]
                    scale = drink["scale"]
                    dx = drink["dx"]
                    dy = drink["dy"]

                    dw, dh = base_img.get_size()
                    new_size = (int(dw * scale), int(dh * scale))
                    img_drink = pygame.transform.smoothscale(base_img, new_size)

                    rect = img_drink.get_rect()
                    rect.centerx = img_rect.centerx + dx
                    rect.top = img_rect.top + dy

                    screen.blit(img_drink, rect)
                    drink_click_areas.append((rect, drink))
            else:
                # === CUSTOMIZATION MODE: Sugar / Strength / Milk ===
                step = CUSTOM_STEPS[custom_step]

                # Título da pergunta (dentro da tela da máquina)
                title_surf = font_medium.render(step["title"], True, black_color)
                title_rect = title_surf.get_rect()
                title_rect.centerx = img_rect.centerx
                title_rect.top = img_rect.top + 80
                screen.blit(title_surf, title_rect)

                # Botões das opções (uma etapa por vez, várias opções)
                option_y = title_rect.bottom + 20
                option_height = 40
                option_width = 220
                spacing_y = 10

                for idx, (label, value) in enumerate(step["options"]):
                    rect = pygame.Rect(0, 0, option_width, option_height)
                    rect.centerx = img_rect.centerx
                    rect.top = option_y + idx * (option_height + spacing_y)

                    bg = BTN_BG_HOVER if rect.collidepoint(mouse_pos) else BTN_BG
                    pygame.draw.rect(screen, bg, rect, border_radius=6)
                    pygame.draw.rect(screen, WHITE, rect, 1, border_radius=6)

                    text_surf = font_small.render(label, True, WHITE)
                    text_rect = text_surf.get_rect(center=rect.center)
                    screen.blit(text_surf, text_rect)

                    cmd = step["prefix"] + value   # ex: "SUGAR:LOW"
                    custom_click_areas.append((rect, cmd))


        # ===== TOP BUTTONS =====
        # --- ESP32 button background depends on connection state ---
        if ser is not None and ser.is_open:
            base_color = green_color      # connected
        else:
            base_color = red_color        # not connected

        # Hover = mesma cor, só um pouco mais clara
        if esp32_button_rect.collidepoint(mouse_pos) and not config_open:
            btn_color_esp32 = tuple(min(c + 40, 255) for c in base_color)
        else:
            btn_color_esp32 = base_color

        pygame.draw.rect(screen, btn_color_esp32, esp32_button_rect, border_radius=6)
        pygame.draw.rect(screen, WHITE, esp32_button_rect, 1, border_radius=6)
        txt_esp32 = font_small.render("ESP32", True, WHITE)
        screen.blit(txt_esp32, txt_esp32.get_rect(center=esp32_button_rect.center))

        # --- Reset button (mantém como estava) ---
        btn_color_reset = BTN_BG_HOVER if reset_button_rect.collidepoint(mouse_pos) and not config_open else BTN_BG
        pygame.draw.rect(screen, btn_color_reset, reset_button_rect, border_radius=6)
        pygame.draw.rect(screen, WHITE, reset_button_rect, 1, border_radius=6)
        txt_reset = font_small.render("Reset", True, WHITE)
        screen.blit(txt_reset, txt_reset.get_rect(center=reset_button_rect.center))

        # --- Menu button (mantém como estava) ---
        btn_color_menu = BTN_BG_HOVER if menu_button_rect.collidepoint(mouse_pos) and not config_open else BTN_BG
        pygame.draw.rect(screen, btn_color_menu, menu_button_rect, border_radius=6)
        pygame.draw.rect(screen, WHITE, menu_button_rect, 1, border_radius=6)
        txt_menu = font_small.render("Menu", True, WHITE)
        screen.blit(txt_menu, txt_menu.get_rect(center=menu_button_rect.center))


        btn_color_reset = BTN_BG_HOVER if reset_button_rect.collidepoint(mouse_pos) and not config_open else BTN_BG
        pygame.draw.rect(screen, btn_color_reset, reset_button_rect, border_radius=6)
        pygame.draw.rect(screen, WHITE, reset_button_rect, 1, border_radius=6)
        txt_reset = font_small.render("Reset", True, WHITE)
        screen.blit(txt_reset, txt_reset.get_rect(center=reset_button_rect.center))

        btn_color_menu = BTN_BG_HOVER if menu_button_rect.collidepoint(mouse_pos) and not config_open else BTN_BG
        pygame.draw.rect(screen, btn_color_menu, menu_button_rect, border_radius=6)
        pygame.draw.rect(screen, WHITE, menu_button_rect, 1, border_radius=6)
        txt_menu = font_small.render("Menu", True, WHITE)
        screen.blit(txt_menu, txt_menu.get_rect(center=menu_button_rect.center))

        # ===== BOTTOM STATUS =====
        status_surface = font_small.render(status_message, True, status_color)
        screen.blit(status_surface, (20, WINDOW_HEIGHT - 30))

        hint_text = "ESC: Menu  |  Q: Quit  |  Click a drink (ESP32 must be connected)"
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
        #
        # ===== HANDLE CLICKS (drinks OR customization) =====
        if mouse_clicked and not quit_program and not config_open:
            if ser is None or not ser.is_open:
                status_message = "Connect ESP32 first."
                status_color = red_color
            else:
                if not customize_mode:
                    # --- MODO NORMAL: clique nas bebidas ---
                    for rect, drink in drink_click_areas:
                        if rect.collidepoint(mouse_pos):
                            cmd = drink["command"]
                            try:
                                ser.write((cmd + "\n").encode("utf-8"))
                                status_message = f"Sent: {cmd}"
                                status_color = green_color
                                print(f"Sent to ESP32 via COM: {cmd}")

                                # Ler respostas do ESP32 (por ex: STATE:CUSTOMIZE)
                                pygame.time.wait(20)
                                while ser.in_waiting > 0:
                                    line = ser.readline().decode(errors="ignore").strip()
                                    if not line:
                                        continue
                                    print(f"Received from ESP32 via COM: {line}")
                                    if line.startswith("STATE:CUSTOMIZE"):
                                        customize_mode = True
                                        custom_step = 0  # começa em Sugar

                            except Exception as e:
                                status_message = f"Error sending command: {e}"
                                status_color = red_color
                                print(f"Error sending command: {e}")
                            break
                else:
                    # --- MODO CUSTOMIZE: clique nas opções (Sugar/Strength/Milk) ---
                    for rect, cmd in custom_click_areas:
                        if rect.collidepoint(mouse_pos):
                            try:
                                # Envia o comando da opção (SUGAR:..., STRENGTH:..., MILK:...)
                                ser.write((cmd + "\n").encode("utf-8"))
                                status_message = f"Sent: {cmd}"
                                status_color = green_color
                                print(f"Sent to ESP32 via COM: {cmd}")

                                # Avança para a próxima etapa de customização
                                custom_step += 1
                                if custom_step >= len(CUSTOM_STEPS):
                                    # Terminou (Sugar, Strength, Milk)
                                    customize_mode = False

                                    # Envia confirmação final
                                    ok_cmd = "CUSTOMIZE:OK"
                                    ser.write((ok_cmd + "\n").encode("utf-8"))
                                    status_message = f"Sent: {ok_cmd}"
                                    status_color = green_color
                                    print(f"Sent to ESP32 via COM: {ok_cmd}")

                            except Exception as e:
                                status_message = f"Error sending command: {e}"
                                status_color = red_color
                                print(f"Error sending command: {e}")
                            break

        pygame.display.flip()
        clock.tick(60)

    if ser is not None:
        ser.close()

    print("Coffee game closed.")
    return "quit" if quit_program else "menu"
