import pygame

from game_maze import run_maze_game
# from game2 import run_game2

# ====== WINDOW CONFIGURATION ======
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
# ==================================


def draw_text_center(screen, text, font, color, y):
    """
    Draw text horizontally centered at given y coordinate.
    """
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=(WINDOW_WIDTH // 2, y))
    screen.blit(surface, rect)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Embedded Programming Games")
    clock = pygame.time.Clock()

    font_title = pygame.font.SysFont(None, 60)
    font_btn = pygame.font.SysFont(None, 36)

    # Menu buttons
    btn_width = 300
    btn_height = 60
    btn_spacing = 20

    maze_btn_rect = pygame.Rect(
        (WINDOW_WIDTH - btn_width) // 2,
        200,
        btn_width,
        btn_height,
    )
    game2_btn_rect = pygame.Rect(
        (WINDOW_WIDTH - btn_width) // 2,
        200 + btn_height + btn_spacing,
        btn_width,
        btn_height,
    )
    quit_btn_rect = pygame.Rect(
        (WINDOW_WIDTH - btn_width) // 2,
        200 + 2 * (btn_height + btn_spacing),
        btn_width,
        btn_height,
    )

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        screen.fill((10, 10, 10))

        # Title
        draw_text_center(
            screen,
            "EMBEDDED PROGRAMMING GAMES",
            font_title,
            (255, 255, 255),
            100,
        )

        # Helper to draw a button
        def draw_button(rect, label):
            if rect.collidepoint(mouse_pos):
                bg = (80, 80, 80)
            else:
                bg = (50, 50, 50)
            pygame.draw.rect(screen, bg, rect, border_radius=8)
            pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=8)
            text_surf = font_btn.render(label, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=rect.center)
            screen.blit(text_surf, text_rect)

        draw_button(maze_btn_rect, "Game 1 - Maze (ESP32)")
        draw_button(game2_btn_rect, "Game 2 - Coming soon")
        draw_button(quit_btn_rect, "Quit")

        # Button clicks
        if mouse_clicked:
            if maze_btn_rect.collidepoint(mouse_pos):
                # Run maze game. It returns to the menu when finished.
                run_maze_game(screen)
            elif game2_btn_rect.collidepoint(mouse_pos):
                # Run second game (placeholder for now).
                run_game2(screen)
            elif quit_btn_rect.collidepoint(mouse_pos):
                running = False

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    print("Program closed from menu.")


if __name__ == "__main__":
    main()
