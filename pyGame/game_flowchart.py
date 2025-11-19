import pygame
import sys
import random
import math

pygame.init()

# Window configuration
WIDTH, HEIGHT = 1000, 600
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flowchart Throw Game")

CLOCK = pygame.time.Clock()
FPS = 60

# Scene area (left) and flowchart area (right)
SCENE_WIDTH = 600
FLOW_WIDTH = WIDTH - SCENE_WIDTH

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY_DARK = (40, 40, 40)
GRAY = (80, 80, 80)
GRAY_LIGHT = (150, 150, 150)
BLUE = (70, 130, 180)
GREEN = (0, 180, 0)
RED = (200, 50, 50)
YELLOW = (240, 200, 0)
ORANGE = (255, 140, 0)

FONT_SMALL = pygame.font.SysFont(None, 20)
FONT_MEDIUM = pygame.font.SysFont(None, 28)
FONT_LARGE = pygame.font.SysFont(None, 36)

# Flowchart steps (labels)
FLOW_STEPS = [
    "Start",
    "Input (walk1, walk2)",
    "Decision (até walk1)",
    "Walk1",
    "End decision walk1",
    "Grab",
    "Decision (até walk2)",
    "Walk2",
    "End decision walk2",
    "Throw",
    "Read sensor",
    "If hit: WIN",
    "Else: LOST",
]

# --- Game parameters ---
GROUND_Y = 450
CHAR_WIDTH, CHAR_HEIGHT = 40, 80
BALL_RADIUS = 10
STEP_PIXELS = 10  # pixels per "step" (walk1/walk2 unit)

# States of the high-level state machine
STATE_INPUT = "INPUT"          # user choosing walk1, walk2
STATE_WALK1 = "WALK1"          # executing first walk loop
STATE_GRAB = "GRAB"            # grabbing the ball
STATE_WALK2 = "WALK2"          # second walk loop
STATE_THROW = "THROW"          # ball parabolic throw
STATE_READ_SENSOR = "READ"     # "reading sensor"
STATE_RESULT = "RESULT"        # show win/lost


def draw_flowchart(active_index):
    """
    Draw the flowchart on the right side, highlighting the active step.
    """
    x0 = SCENE_WIDTH + 20
    y0 = 40
    box_width = FLOW_WIDTH - 40
    box_height = 30
    vertical_spacing = 15

    for i, label in enumerate(FLOW_STEPS):
        y = y0 + i * (box_height + vertical_spacing)
        rect = pygame.Rect(x0, y, box_width, box_height)

        if i == active_index:
            color_fill = ORANGE
            color_border = YELLOW
        else:
            color_fill = GRAY_DARK
            color_border = GRAY_LIGHT

        pygame.draw.rect(SCREEN, color_fill, rect, border_radius=6)
        pygame.draw.rect(SCREEN, color_border, rect, 2, border_radius=6)

        text = FONT_SMALL.render(label, True, WHITE)
        text_rect = text.get_rect(center=rect.center)
        SCREEN.blit(text, text_rect)


def draw_scene(char_x, has_ball, ball_pos, show_hoop=True):
    """
    Draw the scene (left half): ground, character, ball, hoop.
    """
    # Background
    pygame.draw.rect(SCREEN, BLACK, (0, 0, SCENE_WIDTH, HEIGHT))

    # Ground
    pygame.draw.line(SCREEN, GRAY_LIGHT, (0, GROUND_Y + CHAR_HEIGHT // 2), (SCENE_WIDTH, GROUND_Y + CHAR_HEIGHT // 2), 2)

    # Character (simple rectangle and head)
    char_y = GROUND_Y - CHAR_HEIGHT
    pygame.draw.rect(SCREEN, BLUE, (char_x, char_y, CHAR_WIDTH, CHAR_HEIGHT))
    head_radius = 12
    pygame.draw.circle(SCREEN, WHITE, (char_x + CHAR_WIDTH // 2, char_y - head_radius), head_radius)

    # Ball: either in hand or on ground
    if has_ball:
        # Ball in hand (slightly in front of character)
        ball_x = char_x + CHAR_WIDTH
        ball_y = char_y + CHAR_HEIGHT // 2
    else:
        ball_x, ball_y = ball_pos

    pygame.draw.circle(SCREEN, ORANGE, (int(ball_x), int(ball_y)), BALL_RADIUS)

    # Hoop (right side of scene)
    if show_hoop:
        hoop_x = SCENE_WIDTH - 80
        hoop_y = GROUND_Y - 150
        hoop_width = 40
        hoop_height = 10
        pygame.draw.rect(SCREEN, RED, (hoop_x, hoop_y, hoop_width, hoop_height), 3)
        # small backboard
        pygame.draw.rect(SCREEN, GRAY_LIGHT, (hoop_x + hoop_width // 2 - 10, hoop_y - 40, 20, 40))


def compute_ball_trajectory_points(start_pos, end_pos, num_frames=60, arc_height=150):
    """
    Precompute parabolic trajectory points between start_pos and end_pos.
    start_pos, end_pos: (x, y)
    Returns a list of points (x, y).
    """
    sx, sy = start_pos
    ex, ey = end_pos

    points = []
    for i in range(num_frames):
        t = i / (num_frames - 1)
        # horizontal interpolation
        x = sx + (ex - sx) * t
        # vertical: parabola with apex above the midpoint
        mid_x = (sx + ex) / 2
        apex_y = min(sy, ey) - arc_height
        # parametric parabola using quadratic blend
        # y(t) = (1 - t)^2 * sy + 2(1 - t)t*apex_y + t^2 * ey
        y = (1 - t) * (1 - t) * sy + 2 * (1 - t) * t * apex_y + t * t * ey
        points.append((x, y))

    return points


def main():
    # Initial values
    walk1 = 5   # user-adjustable
    walk2 = 5   # user-adjustable

    # Character starting x
    start_x = 80

    # Variables that will be recomputed whenever INPUT is done
    char_x = start_x
    has_ball = False
    ball_on_ground_pos = (0, 0)  # will be set after INPUT
    ball_traj_points = []
    ball_traj_index = 0

    # Counters for walks
    steps1_done = 0
    steps2_done = 0

    # Result logic
    last_hit = False

    # Flow state
    state = STATE_INPUT
    active_flow_index = 0

    running = True
    while running:
        dt = CLOCK.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Key events
            if event.type == pygame.KEYDOWN:
                if state == STATE_INPUT:
                    # Adjust walk1/walk2
                    if event.key == pygame.K_a:   # decrease walk1
                        walk1 = max(0, walk1 - 1)
                    elif event.key == pygame.K_z: # increase walk1
                        walk1 += 1
                    elif event.key == pygame.K_k: # decrease walk2
                        walk2 = max(0, walk2 - 1)
                    elif event.key == pygame.K_m: # increase walk2
                        walk2 += 1
                    elif event.key == pygame.K_RETURN:
                        # Prepare scene based on walk1/walk2
                        char_x = start_x
                        has_ball = False
                        steps1_done = 0
                        steps2_done = 0

                        # Place ball on ground where walk1 will end
                        ball_x = start_x + walk1 * STEP_PIXELS + CHAR_WIDTH
                        ball_y = GROUND_Y - BALL_RADIUS
                        ball_on_ground_pos = (ball_x, ball_y)

                        # Character final position after walk2 (for aiming)
                        final_char_x = start_x + (walk1 + walk2) * STEP_PIXELS

                        # Hoop position
                        hoop_x = SCENE_WIDTH - 60
                        hoop_y = GROUND_Y - 150

                        # Precompute trajectory from character hand to hoop
                        hand_x = final_char_x + CHAR_WIDTH
                        hand_y = GROUND_Y - CHAR_HEIGHT // 2
                        ball_traj_points = compute_ball_trajectory_points(
                            (hand_x, hand_y),
                            (hoop_x, hoop_y + 10),
                            num_frames=60,
                            arc_height=150
                        )
                        ball_traj_index = 0

                        state = STATE_WALK1
                        active_flow_index = 2  # Decision (até walk1)

                elif state == STATE_RESULT:
                    if event.key == pygame.K_SPACE:
                        # back to input
                        state = STATE_INPUT
                        active_flow_index = 1

        # --- State machine logic (per frame) ---
        if state == STATE_INPUT:
            active_flow_index = 1  # Input
            # nothing else, waits for ENTER

        elif state == STATE_WALK1:
            # We are in the "Decision (até walk1)" / "Walk1" loop
            if steps1_done < walk1:
                # Highlight decision/walk
                active_flow_index = 2  # Decision
                # Move character a bit
                char_x += STEP_PIXELS
                steps1_done += 1
                # Show "Walk1" as well
                # (we keep 2 or 3 depending on taste; here we alternate logically)
                active_flow_index = 3
            else:
                # End decision walk1
                active_flow_index = 4
                # Snap ball to character position and grab it
                has_ball = True
                state = STATE_GRAB

        elif state == STATE_GRAB:
            # Grab step
            active_flow_index = 5
            # Short pause? For simplicity, go immediately to WALK2
            steps2_done = 0
            state = STATE_WALK2
            active_flow_index = 6  # Decision (até walk2)

        elif state == STATE_WALK2:
            if steps2_done < walk2:
                active_flow_index = 6  # Decision (até walk2)
                char_x += STEP_PIXELS
                steps2_done += 1
                active_flow_index = 7  # Walk2
            else:
                active_flow_index = 8  # End decision walk2
                state = STATE_THROW
                active_flow_index = 9

        elif state == STATE_THROW:
            active_flow_index = 9  # Throw
            # During throw, character is stationary, ball moves along trajectory
            if ball_traj_index < len(ball_traj_points):
                ball_pos = ball_traj_points[ball_traj_index]
                ball_traj_index += 1
            else:
                # After the throw animation finishes
                state = STATE_READ_SENSOR
                active_flow_index = 10

        elif state == STATE_READ_SENSOR:
            active_flow_index = 10  # Read sensor
            # For demo purposes, randomly decide hit or miss
            last_hit = random.choice([True, False])
            state = STATE_RESULT
            # Choose which branch of flowchart to highlight
            active_flow_index = 11 if last_hit else 12

        elif state == STATE_RESULT:
            # Just show result, waiting for SPACE
            pass

        # --- Drawing ---
        SCREEN.fill(BLACK)

        # ----- Left side: scene -----
        if state in (STATE_INPUT,):
            # During input, character is at start, ball placed for illustration
            char_x_draw = start_x
            has_ball_draw = False
            ball_x = start_x + walk1 * STEP_PIXELS + CHAR_WIDTH
            ball_y = GROUND_Y - BALL_RADIUS
            ball_pos_draw = (ball_x, ball_y)
            draw_scene(char_x_draw, has_ball_draw, ball_pos_draw)
        elif state in (STATE_WALK1, STATE_GRAB, STATE_WALK2):
            # Before throw, ball is either on ground or in hand
            if has_ball:
                ball_pos_draw = ball_on_ground_pos  # not used when has_ball=True
            else:
                ball_pos_draw = ball_on_ground_pos
            draw_scene(char_x, has_ball, ball_pos_draw)
        elif state in (STATE_THROW, STATE_READ_SENSOR, STATE_RESULT):
            # During/after throw, ball follows last known trajectory position
            if ball_traj_points:
                idx = min(ball_traj_index - 1, len(ball_traj_points) - 1)
                if idx < 0:
                    idx = 0
                ball_pos_draw = ball_traj_points[idx]
            else:
                ball_pos_draw = ball_on_ground_pos
            draw_scene(char_x, False, ball_pos_draw)

        # Additional text in scene area (instructions)
        if state == STATE_INPUT:
            info1 = FONT_SMALL.render("INPUT MODE: adjust walk1/walk2, press ENTER to start", True, WHITE)
            info2 = FONT_SMALL.render("A/Z = walk1 -, +   |   K/M = walk2 -, +", True, WHITE)
            SCREEN.blit(info1, (20, 20))
            SCREEN.blit(info2, (20, 40))

        walk_info = FONT_SMALL.render(f"walk1 = {walk1}  |  walk2 = {walk2}", True, WHITE)
        SCREEN.blit(walk_info, (20, 70))

        if state == STATE_RESULT:
            msg = "WIN!" if last_hit else "LOST!"
            color = GREEN if last_hit else RED
            result_text = FONT_LARGE.render(msg, True, color)
            result_rect = result_text.get_rect(center=(SCENE_WIDTH // 2, 100))
            SCREEN.blit(result_text, result_rect)

            hint = FONT_SMALL.render("Press SPACE to go back to INPUT", True, WHITE)
            SCREEN.blit(hint, (SCENE_WIDTH // 2 - 120, 130))

        # ----- Right side: flowchart -----
        draw_flowchart(active_flow_index)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
