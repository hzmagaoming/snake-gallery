import random
import sys
import math
from collections import deque

import pygame


WIDTH = 960
HEIGHT = 760
CELL_SIZE = 24
BOARD_WIDTH = 720
BOARD_HEIGHT = 576
BOARD_LEFT = (WIDTH - BOARD_WIDTH) // 2
BOARD_TOP = 120
COLS = BOARD_WIDTH // CELL_SIZE
ROWS = BOARD_HEIGHT // CELL_SIZE
FOODS_PER_LEVEL = 5

BACKGROUND = (239, 235, 226)
BACKGROUND_TOP = (191, 207, 205)
BACKGROUND_BOTTOM = (232, 218, 201)
PANEL = (244, 240, 231)
PANEL_LIGHT = (181, 166, 151)
GRID = (218, 214, 204)
TEXT = (67, 72, 70)
MUTED = (128, 127, 119)
GREEN = (143, 166, 148)
GREEN_DARK = (91, 116, 104)
RED = (174, 116, 108)
RED_LIGHT = (199, 149, 132)
YELLOW = (190, 165, 119)
CHEEK = (202, 137, 130)
CREAM = (232, 211, 174)
SNAKE_STAGE_COLORS = [
    ((91, 116, 104), (143, 166, 148), (187, 196, 169)),
    ((104, 127, 137), (153, 172, 177), (193, 202, 196)),
    ((146, 119, 93), (181, 151, 116), (211, 185, 145)),
    ((116, 116, 130), (153, 153, 166), (194, 188, 181)),
    ((150, 103, 105), (183, 132, 128), (211, 164, 145)),
    ((89, 126, 119), (137, 168, 153), (181, 196, 169)),
    ((160, 138, 90), (192, 169, 116), (218, 195, 146)),
    ((105, 124, 139), (145, 160, 174), (187, 198, 199)),
    ((104, 137, 101), (151, 174, 124), (190, 199, 155)),
    ((151, 107, 132), (184, 137, 157), (211, 169, 177)),
]
OBSTACLE_THEMES = [
    ((116, 139, 119), (158, 173, 143), (198, 201, 169)),
    ((112, 135, 143), (153, 174, 177), (194, 202, 193)),
    ((157, 130, 102), (186, 157, 120), (211, 186, 146)),
    ((130, 128, 139), (161, 159, 166), (199, 190, 173)),
    ((157, 108, 107), (187, 139, 128), (211, 170, 143)),
    ((105, 141, 132), (145, 173, 147), (190, 195, 162)),
]
FOOD_THEMES = [
    ((238, 91, 105), (255, 173, 142)),
    ((242, 151, 48), (255, 213, 100)),
    ((154, 91, 203), (213, 169, 245)),
    ((46, 177, 190), (151, 235, 226)),
    ((239, 185, 44), (255, 231, 120)),
    ((232, 91, 157), (255, 176, 210)),
]

DIRECTIONS = {
    pygame.K_UP: (0, -1),
    pygame.K_w: (0, -1),
    pygame.K_DOWN: (0, 1),
    pygame.K_s: (0, 1),
    pygame.K_LEFT: (-1, 0),
    pygame.K_a: (-1, 0),
    pygame.K_RIGHT: (1, 0),
    pygame.K_d: (1, 0),
}

BASE_MOVE_SPEED = 1.8
SPEED_INCREASE_PER_LEVEL = 0.18
SEGMENT_SPACING = CELL_SIZE * 0.82


def cell_of(position):
    """Convert a pixel position or grid cell to the nearest board cell."""
    if position is None:
        return None
    if (
        isinstance(position[0], int)
        and isinstance(position[1], int)
        and 0 <= position[0] < COLS
        and 0 <= position[1] < ROWS
    ):
        return position
    return (
        int((position[0] - BOARD_LEFT) // CELL_SIZE),
        int((position[1] - BOARD_TOP) // CELL_SIZE),
    )


def snake_cells(snake):
    return {cell_of(segment) for segment in snake}


def hits_snake_body(position, snake):
    distance_from_head = 0
    for index in range(1, len(snake)):
        distance_from_head += math.hypot(
            snake[index - 1][0] - snake[index][0],
            snake[index - 1][1] - snake[index][1],
        )
        if distance_from_head < CELL_SIZE * 1.25:
            continue
        if math.hypot(position[0] - snake[index][0], position[1] - snake[index][1]) < CELL_SIZE * 0.45:
            return True
    return False


def level_move_speed(level):
    return min(BASE_MOVE_SPEED + (level - 1) * SPEED_INCREASE_PER_LEVEL, 3.2)


def level_target_length(level):
    return SEGMENT_SPACING + (FOODS_PER_LEVEL + level - 1) * CELL_SIZE


def reachable_cells(start, blocked):
    if start is None or start in blocked:
        return set()

    reachable = {start}
    pending = deque([start])
    while pending:
        x, y = pending.popleft()
        for offset_x, offset_y in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbor = (x + offset_x, y + offset_y)
            if (
                0 <= neighbor[0] < COLS
                and 0 <= neighbor[1] < ROWS
                and neighbor not in blocked
                and neighbor not in reachable
            ):
                reachable.add(neighbor)
                pending.append(neighbor)
    return reachable


def make_food(snake, blocked=None):
    blocked = blocked or set()
    head_cell = cell_of(snake[0]) if snake else None
    occupied = snake_cells(snake)
    reachable = reachable_cells(head_cell, blocked)
    available = [
        (x, y)
        for y in range(ROWS)
        for x in range(COLS)
        if (x, y) in reachable and (x, y) not in occupied
    ]
    return random.choice(available) if available else None


def make_poison(snake, food, blocked=None):
    if len(snake) == 0 or food is None:
        return None
    blocked = blocked or set()
    occupied = snake_cells(snake)
    reachable = reachable_cells(cell_of(snake[0]), blocked)
    available = [
        (x, y)
        for y in range(ROWS)
        for x in range(COLS)
        if (x, y) in reachable and (x, y) not in occupied and (x, y) != food
    ]
    return random.choice(available) if available else None


def make_spiral(level):
    walls = set()
    left, top = 2, 2
    right, bottom = COLS - 3, ROWS - 3
    ring = 0

    while left <= right and top <= bottom:
        for x in range(left, right + 1):
            walls.add((x, top))
            walls.add((x, bottom))
        for y in range(top, bottom + 1):
            walls.add((left, y))
            walls.add((right, y))

        if ring % 2 == 0:
            walls.discard((left, top + 2))
            walls.discard((right, bottom - 2))
        else:
            walls.discard((right, top + 2))
            walls.discard((left, bottom - 2))
        left += 3
        top += 3
        right -= 3
        bottom -= 3
        ring += 1

    center_x, center_y = COLS // 2, ROWS // 2
    walls.difference_update(
        (x, y)
        for x in range(center_x - 2, center_x + 3)
        for y in range(center_y - 2, center_y + 3)
    )
    # Give the snake a generous landing area and a clear first lane.
    walls.difference_update(
        (x, y)
        for x in range(center_x - 5, center_x + 9)
        for y in range(center_y - 3, center_y + 4)
    )
    return walls


def make_maze(level):
    if level >= 4:
        return make_spiral(level)

    walls = set()
    vertical_spacing = max(4, 13 - min(level, 9))
    horizontal_spacing = max(5, 15 - min(level, 10))

    for x in range(4, COLS - 3, vertical_spacing):
        gap_y = 3 + ((x * 3 + level * 2) % (ROWS - 6))
        for y in range(2, ROWS - 2):
            if abs(y - gap_y) > 1:
                walls.add((x, y))

    if level >= 3:
        for y in range(5, ROWS - 3, horizontal_spacing):
            gap_x = 3 + ((y * 2 + level * 3) % (COLS - 6))
            for x in range(2, COLS - 2):
                if abs(x - gap_x) > 1:
                    walls.add((x, y))

    # Keep the starting lane open so every level begins fairly.
    start_x, start_y = COLS // 2, ROWS // 2
    walls.difference_update(
        (x, y)
        for x in range(start_x - 3, start_x + 4)
        for y in range(start_y - 2, start_y + 3)
    )
    return walls


def draw_text(surface, text, font, color, position, center=False):
    image = font.render(text, True, color)
    rect = image.get_rect()
    if center:
        rect.center = position
    else:
        rect.topleft = position
    surface.blit(image, rect)


def draw_background(surface):
    for y in range(HEIGHT):
        blend = y / max(1, HEIGHT - 1)
        color = tuple(
            int(BACKGROUND_TOP[index] * (1 - blend) + BACKGROUND_BOTTOM[index] * blend)
            for index in range(3)
        )
        pygame.draw.line(surface, color, (0, y), (WIDTH, y))

    haze = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(haze, (255, 255, 255, 38), (120, 105), 120)
    pygame.draw.circle(haze, (255, 255, 255, 32), (850, 170), 155)
    pygame.draw.circle(haze, (255, 255, 255, 28), (480, 625), 190)
    surface.blit(haze, (0, 0))

    frame_color = (119, 157, 151)
    pygame.draw.arc(surface, frame_color, (32, -130, 896, 410), 3.35, 6.08, 4)
    pygame.draw.arc(surface, (151, 183, 169), (74, -95, 812, 340), 3.35, 6.08, 2)
    pygame.draw.line(surface, (151, 183, 169), (72, 0), (72, 220), 2)
    pygame.draw.line(surface, (151, 183, 169), (888, 0), (888, 220), 2)

    vine_color = (84, 157, 118)
    for points in [
        [(22, 380), (39, 345), (31, 308), (51, 273), (45, 232)],
        [(938, 425), (919, 385), (930, 348), (908, 312), (917, 270)],
    ]:
        pygame.draw.lines(surface, vine_color, False, points, 3)
        for leaf_x, leaf_y, angle in [
            (34, 330, -1),
            (42, 278, 1),
            (923, 373, 1),
            (914, 315, -1),
        ]:
            leaf = [
                (leaf_x, leaf_y),
                (leaf_x + 12 * angle, leaf_y - 8),
                (leaf_x + 15 * angle, leaf_y + 4),
            ]
            pygame.draw.polygon(surface, GREEN_DARK, leaf)

    for flower_x, flower_y, flower_color in [
        (52, 540, RED),
        (903, 555, (180, 151, 232)),
        (84, 140, YELLOW),
        (870, 128, RED_LIGHT),
    ]:
        for petal_offset in [(-7, 0), (7, 0), (0, -7), (0, 7)]:
            pygame.draw.circle(
                surface,
                flower_color,
                (flower_x + petal_offset[0], flower_y + petal_offset[1]),
                6,
            )
        pygame.draw.circle(surface, CREAM, (flower_x, flower_y), 4)


def draw_food(surface, food, score, level):
    food_x = BOARD_LEFT + food[0] * CELL_SIZE + CELL_SIZE // 2
    food_y = BOARD_TOP + food[1] * CELL_SIZE + CELL_SIZE // 2 + 2
    food_color, food_highlight = FOOD_THEMES[(level - 1) % len(FOOD_THEMES)]

    stage = (score // 5) % 4
    if stage == 0:
        pygame.draw.ellipse(surface, food_highlight, (food_x - 9, food_y - 8, 18, 18))
        pygame.draw.ellipse(surface, food_color, (food_x - 8, food_y - 10, 16, 18))
        pygame.draw.ellipse(surface, (255, 238, 211), (food_x - 5, food_y - 8, 7, 6))
        pygame.draw.line(surface, GREEN_DARK, (food_x + 1, food_y - 9), (food_x + 3, food_y - 15), 2)
        pygame.draw.ellipse(surface, GREEN, (food_x + 2, food_y - 16, 8, 5))
    elif stage == 1:
        pygame.draw.circle(surface, food_color, (food_x, food_y), 9)
        pygame.draw.arc(surface, food_highlight, (food_x - 6, food_y - 7, 8, 9), 1.8, 4.8, 2)
        pygame.draw.line(surface, GREEN_DARK, (food_x, food_y - 8), (food_x + 2, food_y - 14), 2)
        pygame.draw.ellipse(surface, GREEN, (food_x + 2, food_y - 15, 8, 5))
    elif stage == 2:
        pygame.draw.polygon(
            surface,
            food_color,
            [(food_x - 9, food_y - 5), (food_x + 9, food_y - 5), (food_x, food_y + 10)],
        )
        for seed_x, seed_y in [(-4, -2), (1, 0), (5, -3), (0, 5)]:
            pygame.draw.ellipse(surface, CREAM, (food_x + seed_x, food_y + seed_y, 2, 4))
        pygame.draw.polygon(
            surface,
            GREEN,
            [(food_x - 8, food_y - 5), (food_x, food_y - 12), (food_x + 8, food_y - 5)],
        )
    else:
        pygame.draw.ellipse(surface, food_color, (food_x - 9, food_y - 8, 18, 18))
        pygame.draw.ellipse(surface, food_highlight, (food_x - 5, food_y - 7, 7, 6))
        pygame.draw.circle(surface, YELLOW, (food_x, food_y - 11), 2)
        pygame.draw.circle(surface, YELLOW, (food_x, food_y + 11), 2)

    face_y = food_y + 2
    pygame.draw.circle(surface, TEXT, (food_x - 3, face_y), 1)
    pygame.draw.circle(surface, TEXT, (food_x + 3, face_y), 1)
    pygame.draw.arc(surface, TEXT, (food_x - 3, face_y, 6, 5), 3.4, 6.0, 1)


def draw_poison(surface, poison):
    poison_x = BOARD_LEFT + poison[0] * CELL_SIZE + CELL_SIZE // 2
    poison_y = BOARD_TOP + poison[1] * CELL_SIZE + CELL_SIZE // 2

    pygame.draw.circle(surface, (239, 215, 91), (poison_x, poison_y), 12, 2)
    pygame.draw.rect(surface, (69, 48, 91), (poison_x - 7, poison_y - 6, 14, 14), border_radius=4)
    pygame.draw.rect(surface, (117, 78, 143), (poison_x - 5, poison_y - 10, 10, 5), border_radius=2)
    pygame.draw.line(surface, (255, 231, 94), (poison_x - 4, poison_y - 3), (poison_x + 4, poison_y + 5), 2)
    pygame.draw.line(surface, (255, 231, 94), (poison_x + 4, poison_y - 3), (poison_x - 4, poison_y + 5), 2)


def draw_obstacle(surface, wall_x, wall_y, level):
    left = BOARD_LEFT + wall_x * CELL_SIZE + 2
    top = BOARD_TOP + wall_y * CELL_SIZE + 2
    outer, inner, highlight = OBSTACLE_THEMES[(level - 1) % len(OBSTACLE_THEMES)]
    wall_rect = pygame.Rect(left, top, CELL_SIZE - 4, CELL_SIZE - 4)
    shape = (wall_x * 7 + wall_y * 11 + level) % 4

    if shape == 0:
        pygame.draw.rect(surface, outer, wall_rect, border_radius=5)
        pygame.draw.rect(surface, inner, wall_rect.inflate(-5, -5), border_radius=3)
        pygame.draw.line(surface, highlight, (left + 5, top + 5), (left + 14, top + 5), 2)
    elif shape == 1:
        points = [(left + 2, top + 7), (left + 8, top + 2), (left + 19, top + 4),
                  (left + 20, top + 16), (left + 13, top + 20), (left + 3, top + 17)]
        pygame.draw.polygon(surface, outer, points)
        pygame.draw.polygon(surface, inner, [(x, y + 2) for x, y in points[1:5]])
        pygame.draw.line(surface, highlight, points[0], points[2], 2)
    elif shape == 2:
        pygame.draw.ellipse(surface, outer, wall_rect)
        pygame.draw.ellipse(surface, inner, wall_rect.inflate(-5, -5))
        pygame.draw.circle(surface, highlight, (left + 8, top + 7), 2)
    else:
        points = [(left + 6, top + 2), (left + 18, top + 2), (left + 21, top + 11),
                  (left + 14, top + 20), (left + 4, top + 17), (left + 2, top + 8)]
        pygame.draw.polygon(surface, outer, points)
        pygame.draw.polygon(surface, inner, [(x, y + 2) for x, y in points[1:5]])
        pygame.draw.line(surface, highlight, (left + 7, top + 5), (left + 16, top + 5), 2)


def draw_board(surface, snake, food, poison, score, maze, level):
    board_rect = pygame.Rect(BOARD_LEFT, BOARD_TOP, BOARD_WIDTH, BOARD_HEIGHT)
    pygame.draw.rect(surface, (242, 241, 224), board_rect, border_radius=12)
    pygame.draw.rect(surface, (112, 137, 123), board_rect, 3, border_radius=12)

    for wall_x, wall_y in maze:
        draw_obstacle(surface, wall_x, wall_y, level)

    for stone_x, stone_y in [
        (BOARD_LEFT + 110, BOARD_TOP + 90),
        (BOARD_LEFT + 275, BOARD_TOP + 130),
        (BOARD_LEFT + 610, BOARD_TOP + 440),
        (BOARD_LEFT + 670, BOARD_TOP + 320),
    ]:
        pygame.draw.ellipse(surface, (193, 218, 190), (stone_x - 10, stone_y - 6, 20, 12))

    if food is not None:
        draw_food(surface, food, score, level)

    if poison is not None:
        draw_poison(surface, poison)

    growth_level = score // 5
    stage = min(growth_level, len(SNAKE_STAGE_COLORS) - 1)
    body_color, head_color, highlight_color = SNAKE_STAGE_COLORS[stage]
    snake_centers = [
        (int(x), int(y))
        for x, y in snake
    ]

    for index in range(len(snake_centers) - 1, 0, -1):
        body_width = min(23, max(13, 19 + min(growth_level, 3) - index // 4))
        pygame.draw.line(surface, body_color, snake_centers[index], snake_centers[index - 1], body_width)
        pygame.draw.circle(surface, body_color, snake_centers[index], body_width // 2)
        if index % 2 == 0:
            pygame.draw.circle(surface, highlight_color, snake_centers[index], max(3, body_width // 5))

    for index, (center_x, center_y) in enumerate(snake_centers[1:], start=1):
        pygame.draw.ellipse(
            surface,
            highlight_color,
            (center_x - 6, center_y - 7, 5, 4),
        )

    head_x, head_y = snake_centers[0]
    head_size = min(28, 22 + growth_level)
    head_radius = head_size // 2
    head_rect = pygame.Rect(head_x - head_radius, head_y - head_radius, head_size, head_size)
    pygame.draw.ellipse(surface, body_color, head_rect.inflate(4, 4))
    pygame.draw.ellipse(surface, head_color, head_rect)
    pygame.draw.polygon(
        surface,
        head_color,
        [(head_x - head_radius + 4, head_y - 7),
         (head_x - head_radius + 2, head_y - head_radius - 5),
         (head_x - 1, head_y - head_radius + 1)],
    )
    eye_x = head_x + head_radius // 2
    eye_offset = max(4, head_radius // 2)
    pygame.draw.circle(surface, (255, 255, 252), (eye_x, head_y - eye_offset), 4)
    pygame.draw.circle(surface, (255, 255, 252), (eye_x, head_y + eye_offset), 4)
    pygame.draw.circle(surface, TEXT, (eye_x, head_y - eye_offset), 2)
    pygame.draw.circle(surface, TEXT, (eye_x, head_y + eye_offset), 2)
    pygame.draw.circle(surface, (255, 255, 255), (eye_x - 1, head_y - eye_offset - 1), 1)
    pygame.draw.circle(surface, (255, 255, 255), (eye_x - 1, head_y + eye_offset - 1), 1)
    pygame.draw.circle(surface, CHEEK, (head_x - 4, head_y + head_radius // 2), 2)
    pygame.draw.circle(surface, CHEEK, (head_x + head_radius - 1, head_y + head_radius // 2), 2)
    pygame.draw.arc(
        surface,
        TEXT,
        (head_x - 3, head_y, 10, 7),
        3.5,
        5.9,
        1,
    )

    draw_text(surface, f"LEVEL {level}   SCORE  {score:03d}", pygame.font.Font(None, 28), TEXT, (BOARD_LEFT, 88))


def new_game(score=0, level=1):
    center = (COLS // 2, ROWS // 2)
    head = (
        BOARD_LEFT + center[0] * CELL_SIZE + CELL_SIZE // 2,
        BOARD_TOP + center[1] * CELL_SIZE + CELL_SIZE // 2,
    )
    snake = [head]
    direction = (1, 0)
    maze = make_maze(level)
    food = make_food(snake, maze)
    poison = None
    return snake, direction, direction, food, poison, score, maze


def draw_start_screen(screen, title_font, font, small_font):
    draw_background(screen)
    draw_text(screen, "SNAKE", title_font, GREEN_DARK, (WIDTH // 2, 175), center=True)
    draw_text(screen, "A tiny game of timing and appetite", font, MUTED, (WIDTH // 2, 235), center=True)

    card = pygame.Rect(WIDTH // 2 - 210, 290, 420, 170)
    pygame.draw.rect(screen, PANEL, card, border_radius=14)
    pygame.draw.rect(screen, PANEL_LIGHT, card, 2, border_radius=14)
    draw_text(screen, "PRESS SPACE TO START", font, GREEN_DARK, (WIDTH // 2, 337), center=True)
    draw_text(screen, "Arrow keys or WASD to move", small_font, MUTED, (WIDTH // 2, 382), center=True)
    draw_text(screen, "P to pause  ·  ESC to quit", small_font, MUTED, (WIDTH // 2, 416), center=True)


def draw_game_over(screen, title_font, font, small_font, score, high_score):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((7, 10, 17, 190))
    screen.blit(overlay, (0, 0))
    draw_text(screen, "GAME OVER", title_font, RED, (WIDTH // 2, 240), center=True)
    draw_text(screen, f"Score  {score:03d}    Best  {high_score:03d}", font, TEXT, (WIDTH // 2, 305), center=True)
    draw_text(screen, "PRESS SPACE TO PLAY AGAIN", font, YELLOW, (WIDTH // 2, 390), center=True)
    draw_text(screen, "Press ESC to quit", small_font, MUTED, (WIDTH // 2, 435), center=True)


def draw_pause(screen, font):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((7, 10, 17, 155))
    screen.blit(overlay, (0, 0))
    draw_text(screen, "PAUSED", font, TEXT, (WIDTH // 2, HEIGHT // 2 - 20), center=True)
    draw_text(screen, "Press P to continue", pygame.font.Font(None, 28), MUTED, (WIDTH // 2, HEIGHT // 2 + 25), center=True)


def draw_level_clear(screen, title_font, font, small_font, level):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((7, 10, 17, 175))
    screen.blit(overlay, (0, 0))
    draw_text(screen, "LEVEL CLEAR!", title_font, YELLOW, (WIDTH // 2, 240), center=True)
    draw_text(screen, f"Level {level} complete", font, TEXT, (WIDTH // 2, 305), center=True)
    draw_text(screen, "PRESS SPACE OR ENTER FOR THE NEXT LEVEL", font, GREEN, (WIDTH // 2, 390), center=True)
    draw_text(screen, "Press ESC to quit", small_font, MUTED, (WIDTH // 2, 435), center=True)


def main():
    pygame.init()
    pygame.display.set_caption("Snake | Sweet Garden")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    title_font = pygame.font.Font(None, 86)
    font = pygame.font.Font(None, 34)
    small_font = pygame.font.Font(None, 24)

    state = "start"
    snake, direction, next_direction, food, poison, score, maze = new_game()
    level = 1
    high_score = 0
    desired_length = SEGMENT_SPACING
    running = True

    while running:
        elapsed = clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif state == "start" and event.key == pygame.K_SPACE:
                    snake, direction, next_direction, food, poison, score, maze = new_game()
                    desired_length = SEGMENT_SPACING
                    state = "playing"
                elif state == "game_over" and event.key == pygame.K_SPACE:
                    snake, direction, next_direction, food, poison, score, maze = new_game()
                    desired_length = SEGMENT_SPACING
                    level = 1
                    state = "playing"
                elif state == "level_clear" and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    snake, direction, next_direction, food, poison, score, maze = new_game(score, level)
                    desired_length = SEGMENT_SPACING
                    state = "playing"
                elif state == "playing" and event.key == pygame.K_p:
                    state = "paused"
                elif state == "paused" and event.key == pygame.K_p:
                    state = "playing"
                elif state == "playing" and event.key in DIRECTIONS:
                    candidate = DIRECTIONS[event.key]
                    if candidate != (-direction[0], -direction[1]):
                        next_direction = candidate

        if state == "playing":
            direction = next_direction
            head_x, head_y = snake[0]
            movement = level_move_speed(level) * elapsed / (1000 / 60)
            new_head = (
                head_x + direction[0] * movement,
                head_y + direction[1] * movement,
            )
            head_cell = cell_of(new_head)
            hit_wall = not (
                BOARD_LEFT <= new_head[0] < BOARD_LEFT + BOARD_WIDTH
                and BOARD_TOP <= new_head[1] < BOARD_TOP + BOARD_HEIGHT
            )
            hit_maze = head_cell in maze
            hit_self = hits_snake_body(new_head, snake)
            hit_poison = poison is not None and head_cell == poison

            if hit_wall or hit_maze or hit_self or hit_poison:
                high_score = max(high_score, score)
                state = "game_over"
            else:
                snake.insert(0, new_head)
                while len(snake) > 2:
                    path_length = sum(
                        math.hypot(
                            snake[index - 1][0] - snake[index][0],
                            snake[index - 1][1] - snake[index][1],
                        )
                        for index in range(1, len(snake))
                    )
                    if path_length <= desired_length:
                        break
                    snake.pop()

                if head_cell == food:
                    score += 1
                    desired_length += CELL_SIZE
                    if desired_length >= level_target_length(level):
                        level += 1
                        state = "level_clear"
                    elif score >= 20 and poison is None:
                        food = make_food(snake, maze)
                        poison = make_poison(snake, food, maze)
                    if state == "playing":
                        food = make_food(snake, maze | ({poison} if poison else set()))

        if state == "start":
            draw_start_screen(screen, title_font, font, small_font)
        else:
            draw_background(screen)
            draw_text(screen, "SWEET GARDEN", title_font, TEXT, (WIDTH // 2, 42), center=True)
            draw_board(screen, snake, food, poison, score, maze, level)
            draw_text(screen, "P pause", small_font, MUTED, (BOARD_LEFT + BOARD_WIDTH - 90, 93))
            if state == "paused":
                draw_pause(screen, font)
            elif state == "level_clear":
                draw_level_clear(screen, title_font, font, small_font, level)
            elif state == "game_over":
                draw_game_over(screen, title_font, font, small_font, score, high_score)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
