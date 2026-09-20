# -*- coding: utf-8 -*-
"""
贪吃蛇游戏 (豪华完整版)
功能：莫兰迪配色、动态石头障碍、随机多水果、鼠标+键盘操作、UI高级质感
"""

import pygame
import random
import sys
import os
import math

# ==================== 游戏配置 ====================
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
GRID_SIZE = 20
FPS = 7

# 棋盘偏移量
BOARD_WIDTH = 600
BOARD_HEIGHT = 480
BOARD_X = (WINDOW_WIDTH - BOARD_WIDTH) // 2
BOARD_Y = (WINDOW_HEIGHT - BOARD_HEIGHT) // 2 + 20

# ==================== 莫兰迪配色 ====================
COLOR_BG_TOP = (252, 250, 248)
COLOR_BG_BOTTOM = (235, 230, 225)

COLOR_CARD_BG = (255, 255, 255, 180)
COLOR_SHADOW = (0, 0, 0, 30)
COLOR_TEXT_DARK = (80, 80, 80)
COLOR_TEXT_LIGHT = (150, 150, 150)
COLOR_ACCENT = (180, 140, 140)

COLOR_BOARD_BG = (245, 242, 240)
COLOR_GRID_DOT = (235, 230, 225)
COLOR_SNAKE_HEAD = (120, 160, 130)
COLOR_SNAKE_BODY = (160, 195, 170)
COLOR_SNAKE_SHADOW = (200, 210, 205)
COLOR_SNAKE_CHEEK = (225, 175, 175)

# 水果颜色
COLOR_FOOD_APPLE = (205, 135, 135)
COLOR_FOOD_STRAWBERRY = (190, 120, 120)
COLOR_FOOD_ORANGE = (210, 160, 130)
COLOR_FOOD_LEAF = (150, 175, 145)
COLOR_FOOD_STEM = (130, 120, 110)

# 障碍物颜色
COLOR_OBSTACLE = (170, 165, 160)
COLOR_OBSTACLE_BORDER = (140, 135, 130)

GRID_COLS = BOARD_WIDTH // GRID_SIZE
GRID_ROWS = BOARD_HEIGHT // GRID_SIZE

# 动态障碍物参数
OBSTACLE_COUNT = 6               # 石头数量
OBSTACLE_REFRESH_MS = 3000       # 石头每 3 秒刷新位置

# ==================== 字体加载 ====================
def get_chinese_font(size, bold=False):
    font_paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                font = pygame.font.Font(path, size)
                if bold:
                    font.set_bold(True)
                return font
            except Exception:
                continue
    return pygame.font.SysFont(None, size, bold=bold)

# ==================== 核心渲染工具 ====================
def draw_gradient_bg(surface):
    for y in range(WINDOW_HEIGHT):
        ratio = y / WINDOW_HEIGHT
        r = int(COLOR_BG_TOP[0] * (1 - ratio) + COLOR_BG_BOTTOM[0] * ratio)
        g = int(COLOR_BG_TOP[1] * (1 - ratio) + COLOR_BG_BOTTOM[1] * ratio)
        b = int(COLOR_BG_TOP[2] * (1 - ratio) + COLOR_BG_BOTTOM[2] * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (WINDOW_WIDTH, y))

def draw_shadow(surface, rect, offset=4, radius=12):
    shadow_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surface, COLOR_SHADOW,
                     (0, 0, rect.width, rect.height), border_radius=radius)
    surface.blit(shadow_surface, (rect.x + offset, rect.y + offset))

def draw_panel(surface, rect, radius=15):
    panel_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(panel_surface, COLOR_CARD_BG,
                     (0, 0, rect.width, rect.height), border_radius=radius)
    surface.blit(panel_surface, (rect.x, rect.y))

# ==================== 游戏逻辑 ====================
def generate_obstacles(snake_body, fruits):
    obstacles = set()
    center_col, center_row = GRID_COLS // 2, GRID_ROWS // 2
    fruit_positions = [f[0] for f in fruits]
    
    max_attempts = 100
    attempts = 0
    while len(obstacles) < OBSTACLE_COUNT and attempts < max_attempts:
        attempts += 1
        col = random.randint(1, GRID_COLS - 2)
        row = random.randint(1, GRID_ROWS - 2)
        if abs(col - center_col) < 4 and abs(row - center_row) < 4:
            continue
        if (col, row) in snake_body or (col, row) in fruit_positions:
            continue
        obstacles.add((col, row))
    return obstacles

def generate_single_fruit(snake_body, obstacles, existing_fruits):
    fruit_types = ["apple", "strawberry", "orange"]
    for _ in range(100):
        pos = (random.randint(0, GRID_COLS - 1),
               random.randint(0, GRID_ROWS - 1))
        if (pos not in snake_body and 
            pos not in obstacles and 
            pos not in [f[0] for f in existing_fruits]):
            return (pos, random.choice(fruit_types))
    return None

def generate_fruits(snake_body, obstacles):
    fruits = []
    num_fruits = random.randint(1, 3)
    for _ in range(num_fruits):
        fruit = generate_single_fruit(snake_body, obstacles, fruits)
        if fruit:
            fruits.append(fruit)
    return fruits

def draw_board_dots(surface):
    board_rect = pygame.Rect(BOARD_X, BOARD_Y, BOARD_WIDTH, BOARD_HEIGHT)
    pygame.draw.rect(surface, COLOR_BOARD_BG, board_rect, border_radius=15)
    pygame.draw.rect(surface, (220, 215, 210), board_rect, width=2, border_radius=15)
    for x in range(BOARD_X, BOARD_X + BOARD_WIDTH, GRID_SIZE):
        for y in range(BOARD_Y, BOARD_Y + BOARD_HEIGHT, GRID_SIZE):
            pygame.draw.circle(surface, COLOR_GRID_DOT, (x + GRID_SIZE // 2, y + GRID_SIZE // 2), 1)

def draw_obstacles(surface, obstacles):
    for col, row in obstacles:
        cx = BOARD_X + col * GRID_SIZE + GRID_SIZE // 2
        cy = BOARD_Y + row * GRID_SIZE + GRID_SIZE // 2
        pygame.draw.circle(surface, (210, 205, 200), (cx + 2, cy + 2), GRID_SIZE // 2 - 1)
        pygame.draw.circle(surface, COLOR_OBSTACLE, (cx, cy), GRID_SIZE // 2 - 1)
        pygame.draw.circle(surface, COLOR_OBSTACLE_BORDER, (cx - 2, cy - 2), 3)
        pygame.draw.circle(surface, COLOR_OBSTACLE_BORDER, (cx + 3, cy + 2), 2)

def draw_fruit(surface, fruit_pos, fruit_type, time_ticks):
    col, row = fruit_pos
    scale = 1.0 + 0.12 * math.sin(time_ticks / 200.0)
    cx = BOARD_X + col * GRID_SIZE + GRID_SIZE // 2
    cy = BOARD_Y + row * GRID_SIZE + GRID_SIZE // 2
    radius = int((GRID_SIZE // 2 - 2) * scale)

    if fruit_type == "apple":
        pygame.draw.circle(surface, COLOR_SNAKE_SHADOW, (cx + 2, cy + 2), radius)
        pygame.draw.circle(surface, COLOR_FOOD_APPLE, (cx, cy + 1), radius)
        pygame.draw.circle(surface, (235, 190, 190), (cx - 4, cy - 3), max(1, radius // 4))
        pygame.draw.line(surface, COLOR_FOOD_STEM, (cx, cy - radius + 2), (cx + 2, cy - radius - 3), 2)
        leaf_points = [(cx + 2, cy - radius - 1), (cx + 8, cy - radius - 5),
                       (cx + 5, cy - radius - 1), (cx + 10, cy - radius + 1)]
        pygame.draw.polygon(surface, COLOR_FOOD_LEAF, leaf_points)
        
    elif fruit_type == "strawberry":
        pygame.draw.ellipse(surface, COLOR_SNAKE_SHADOW, (cx - radius + 2, cy - radius + 4, radius*2, radius*2 + 2))
        pygame.draw.ellipse(surface, COLOR_FOOD_STRAWBERRY, (cx - radius, cy - radius + 2, radius*2, radius*2 + 2))
        pygame.draw.polygon(surface, COLOR_FOOD_LEAF, [(cx - 5, cy - radius + 2), (cx + 5, cy - radius + 2), (cx, cy - radius - 4)])
        pygame.draw.circle(surface, (255, 230, 230), (cx - 3, cy), 1)
        pygame.draw.circle(surface, (255, 230, 230), (cx + 3, cy + 2), 1)
        pygame.draw.circle(surface, (255, 230, 230), (cx, cy + 4), 1)
        
    elif fruit_type == "orange":
        pygame.draw.circle(surface, COLOR_SNAKE_SHADOW, (cx + 2, cy + 2), radius)
        pygame.draw.circle(surface, COLOR_FOOD_ORANGE, (cx, cy), radius)
        pygame.draw.circle(surface, (240, 200, 170), (cx - 3, cy - 3), max(1, radius // 4))
        pygame.draw.ellipse(surface, COLOR_FOOD_LEAF, (cx - 3, cy - radius - 4, 7, 3))

def draw_snake(surface, snake_body, direction):
    for i in range(len(snake_body) - 1, -1, -1):
        col, row = snake_body[i]
        cx = BOARD_X + col * GRID_SIZE + GRID_SIZE // 2
        cy = BOARD_Y + row * GRID_SIZE + GRID_SIZE // 2

        if i == 0:
            head_rect = pygame.Rect(BOARD_X + col * GRID_SIZE, BOARD_Y + row * GRID_SIZE,
                                    GRID_SIZE, GRID_SIZE)
            draw_shadow(surface, head_rect, offset=2, radius=12)
            pygame.draw.rect(surface, COLOR_SNAKE_HEAD, head_rect, border_radius=12)

            dx, dy = direction
            eye_radius, pupil_radius = 4, 2
            if dx == 1:
                eye1, eye2, cheek = (cx + 5, cy - 5), (cx + 5, cy + 5), (cx + 2, cy + 7)
            elif dx == -1:
                eye1, eye2, cheek = (cx - 5, cy - 5), (cx - 5, cy + 5), (cx - 2, cy + 7)
            elif dy == -1:
                eye1, eye2, cheek = (cx - 5, cy - 5), (cx + 5, cy - 5), (cx + 7, cy - 2)
            else:
                eye1, eye2, cheek = (cx - 5, cy + 5), (cx + 5, cy + 5), (cx + 7, cy + 2)

            pygame.draw.circle(surface, (255, 255, 255), eye1, eye_radius)
            pygame.draw.circle(surface, (255, 255, 255), eye2, eye_radius)
            pygame.draw.circle(surface, (60, 60, 60), eye1, pupil_radius)
            pygame.draw.circle(surface, (60, 60, 60), eye2, pupil_radius)
            pygame.draw.circle(surface, COLOR_SNAKE_CHEEK, cheek, 3)
        else:
            body_rect = pygame.Rect(BOARD_X + col * GRID_SIZE + 1,
                                    BOARD_Y + row * GRID_SIZE + 1,
                                    GRID_SIZE - 2, GRID_SIZE - 2)
            draw_shadow(surface, body_rect, offset=2, radius=8)
            pygame.draw.rect(surface, COLOR_SNAKE_BODY, body_rect, border_radius=8)

# ==================== 界面渲染 ====================
def draw_hud(surface, font, score, high_score):
    hud_rect = pygame.Rect(BOARD_X, BOARD_Y - 60, BOARD_WIDTH, 45)
    draw_shadow(surface, hud_rect, offset=3, radius=10)
    draw_panel(surface, hud_rect, radius=10)

    score_text = font.render(f"当前分数: {score}", True, COLOR_TEXT_DARK)
    high_text = font.render(f"最高分: {high_score}", True, COLOR_TEXT_LIGHT)
    
    surface.blit(score_text, (BOARD_X + 20, BOARD_Y - 50))
    surface.blit(high_text, (BOARD_X + BOARD_WIDTH - 140, BOARD_Y - 50))

def draw_start_screen(surface, font_title, font_btn, font_text, start_btn_rect):
    draw_gradient_bg(surface)
    
    time_ticks = pygame.time.get_ticks()
    
    for i in range(6):
        offset_y = math.sin(time_ticks / 1000.0 + i) * 20
        pygame.draw.circle(surface, (225, 220, 215), 
                           (80 + i * 140, 100 + offset_y), 30 + i * 8)
        pygame.draw.circle(surface, (235, 230, 225), 
                           (120 + i * 130, 450 - offset_y), 25 + i * 5)

    demo_snake = [(10, 5), (9, 5), (8, 5)]
    for i, (col, row) in enumerate(demo_snake):
        cx = BOARD_X + col * GRID_SIZE + GRID_SIZE // 2
        cy = BOARD_Y + row * GRID_SIZE + GRID_SIZE // 2
        if i == 0:
            pygame.draw.rect(surface, COLOR_SNAKE_HEAD, (BOARD_X + col*GRID_SIZE, BOARD_Y + row*GRID_SIZE, GRID_SIZE, GRID_SIZE), border_radius=12)
            pygame.draw.circle(surface, (255,255,255), (cx+5, cy-5), 4)
            pygame.draw.circle(surface, (255,255,255), (cx+5, cy+5), 4)
            pygame.draw.circle(surface, (60,60,60), (cx+5, cy-5), 2)
            pygame.draw.circle(surface, (60,60,60), (cx+5, cy+5), 2)
        else:
            pygame.draw.rect(surface, COLOR_SNAKE_BODY, (BOARD_X + col*GRID_SIZE+1, BOARD_Y + row*GRID_SIZE+1, GRID_SIZE-2, GRID_SIZE-2), border_radius=8)
    
    draw_fruit(surface, (20, 5), "strawberry", time_ticks)
    draw_fruit(surface, (20, 15), "orange", time_ticks)

    card_rect = pygame.Rect(WINDOW_WIDTH // 2 - 250, WINDOW_HEIGHT // 2 - 180, 500, 360)
    draw_shadow(surface, card_rect, offset=6, radius=20)
    draw_panel(surface, card_rect, radius=20)

    title_text = font_title.render("贪吃蛇", True, COLOR_SNAKE_HEAD)
    title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 80))
    surface.blit(title_text, title_rect)

    hints = [
        "↑ ↓ ← →   控制小蛇方向",
        "吃水果变长，不要撞墙、撞石头或撞自己",
    ]
    for i, hint in enumerate(hints):
        hint_text = font_text.render(hint, True, COLOR_TEXT_LIGHT)
        hint_rect = hint_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 10 + i * 35))
        surface.blit(hint_text, hint_rect)

    scale = 1.0 + 0.05 * math.sin(pygame.time.get_ticks() / 200.0)
    draw_btn_rect = pygame.Rect(0, 0, int(200 * scale), int(50 * scale))
    draw_btn_rect.center = start_btn_rect.center
    pygame.draw.rect(surface, COLOR_SNAKE_HEAD, draw_btn_rect, border_radius=25)
    
    start_text = font_btn.render("开 始 游 戏", True, (255, 255, 255))
    start_text_rect = start_text.get_rect(center=draw_btn_rect.center)
    surface.blit(start_text, start_text_rect)

def draw_game_over_screen(surface, font_title, font_btn, font_text, score, high_score, restart_btn_rect, quit_btn_rect):
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    for y in range(WINDOW_HEIGHT):
        alpha = int(180 * (y / WINDOW_HEIGHT))
        pygame.draw.line(overlay, (40, 40, 40, alpha), (0, y), (WINDOW_WIDTH, y))
    surface.blit(overlay, (0, 0))

    card_rect = pygame.Rect(WINDOW_WIDTH // 2 - 200, WINDOW_HEIGHT // 2 - 150, 400, 300)
    draw_shadow(surface, card_rect, offset=8, radius=20)
    draw_panel(surface, card_rect, radius=20)

    over_text = font_title.render("游戏结束", True, COLOR_ACCENT)
    over_rect = over_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 80))
    surface.blit(over_text, over_rect)

    score_label = font_text.render("本局得分", True, COLOR_TEXT_LIGHT)
    score_val = font_title.render(str(score), True, COLOR_SNAKE_HEAD)
    surface.blit(score_label, (WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2 - 10))
    surface.blit(score_val, (WINDOW_WIDTH // 2 + 20, WINDOW_HEIGHT // 2 - 20))

    # 重新开始按钮
    pygame.draw.rect(surface, COLOR_SNAKE_HEAD, restart_btn_rect, border_radius=22)
    restart_text = font_btn.render("再来一局 (R)", True, (255, 255, 255))
    restart_text_rect = restart_text.get_rect(center=restart_btn_rect.center)
    surface.blit(restart_text, restart_text_rect)

    # 退出游戏按钮
    pygame.draw.rect(surface, (200, 190, 190), quit_btn_rect, border_radius=22)
    quit_text = font_btn.render("退出游戏 (Q)", True, (255, 255, 255))
    quit_text_rect = quit_text.get_rect(center=quit_btn_rect.center)
    surface.blit(quit_text, quit_text_rect)

# ==================== 主程序 ====================
def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("可爱贪吃蛇 - 豪华版")
    clock = pygame.time.Clock()

    font_title = get_chinese_font(48, bold=True)
    font_btn = get_chinese_font(22, bold=True)
    font_text = get_chinese_font(20)
    font_hud = get_chinese_font(22, bold=True)

    high_score = 0

    # 统一按钮尺寸和位置
    start_btn_rect = pygame.Rect(0, 0, 200, 50)
    start_btn_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 95)

    restart_btn_rect = pygame.Rect(0, 0, 160, 45)
    restart_btn_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 60)

    quit_btn_rect = pygame.Rect(0, 0, 160, 45)
    quit_btn_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 120)

    def reset_game():
        center_col, center_row = GRID_COLS // 2, GRID_ROWS // 2
        snake = [(center_col, center_row), (center_col - 1, center_row), (center_col - 2, center_row)]
        direction = (1, 0)
        obstacles = generate_obstacles(snake, [])
        fruits = generate_fruits(snake, obstacles)
        return snake, direction, fruits, obstacles, 0

    snake_body, direction, fruits, obstacles, score = reset_game()
    last_obstacle_refresh_time = pygame.time.get_ticks()
    state = "START"
    running = True

    while running:
        time_ticks = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()

        # ---------- 事件处理 ----------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if state == "START":
                    if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        snake_body, direction, fruits, obstacles, score = reset_game()
                        last_obstacle_refresh_time = pygame.time.get_ticks()
                        state = "PLAYING"
                elif state == "PLAYING":
                    if event.key == pygame.K_UP and direction != (0, 1):
                        direction = (0, -1)
                    elif event.key == pygame.K_DOWN and direction != (0, -1):
                        direction = (0, 1)
                    elif event.key == pygame.K_LEFT and direction != (1, 0):
                        direction = (-1, 0)
                    elif event.key == pygame.K_RIGHT and direction != (-1, 0):
                        direction = (1, 0)
                elif state == "GAMEOVER":
                    if event.key == pygame.K_r:
                        snake_body, direction, fruits, obstacles, score = reset_game()
                        last_obstacle_refresh_time = pygame.time.get_ticks()
                        state = "PLAYING"
                    elif event.key == pygame.K_q:
                        running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if state == "START":
                        if start_btn_rect.collidepoint(event.pos):
                            snake_body, direction, fruits, obstacles, score = reset_game()
                            last_obstacle_refresh_time = pygame.time.get_ticks()
                            state = "PLAYING"
                    elif state == "GAMEOVER":
                        if restart_btn_rect.collidepoint(event.pos):
                            snake_body, direction, fruits, obstacles, score = reset_game()
                            last_obstacle_refresh_time = pygame.time.get_ticks()
                            state = "PLAYING"
                        elif quit_btn_rect.collidepoint(event.pos):
                            running = False

        # ---------- 鼠标指针管理 ----------
        if state == "START" and start_btn_rect.collidepoint(mouse_pos):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        elif state == "GAMEOVER" and (restart_btn_rect.collidepoint(mouse_pos) or quit_btn_rect.collidepoint(mouse_pos)):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        # ---------- 逻辑更新 ----------
        if state == "PLAYING":
            if time_ticks - last_obstacle_refresh_time > OBSTACLE_REFRESH_MS:
                obstacles = generate_obstacles(snake_body, fruits)
                last_obstacle_refresh_time = time_ticks

            head_col, head_row = snake_body[0]
            dx, dy = direction
            new_head = (head_col + dx, head_row + dy)

            if (new_head[0] < 0 or new_head[0] >= GRID_COLS or
                    new_head[1] < 0 or new_head[1] >= GRID_ROWS or
                    new_head in snake_body or
                    new_head in obstacles):
                state = "GAMEOVER"
                if score > high_score:
                    high_score = score
            else:
                snake_body.insert(0, new_head)
                eaten_fruit = None
                for fruit in fruits:
                    if new_head == fruit[0]:
                        eaten_fruit = fruit
                        break
                
                if eaten_fruit:
                    score += 1
                    fruits.remove(eaten_fruit)
                    fruits = generate_fruits(snake_body, obstacles)
                else:
                    snake_body.pop()

        # ---------- 画面渲染 ----------
        if state == "START":
            draw_start_screen(screen, font_title, font_btn, font_text, start_btn_rect)
        elif state == "PLAYING":
            draw_gradient_bg(screen)
            draw_board_dots(screen)
            draw_obstacles(screen, obstacles)
            for fruit_pos, fruit_type in fruits:
                draw_fruit(screen, fruit_pos, fruit_type, time_ticks)
            draw_snake(screen, snake_body, direction)
            draw_hud(screen, font_hud, score, high_score)
        elif state == "GAMEOVER":
            draw_gradient_bg(screen)
            draw_board_dots(screen)
            draw_obstacles(screen, obstacles)
            for fruit_pos, fruit_type in fruits:
                draw_fruit(screen, fruit_pos, fruit_type, time_ticks)
            draw_snake(screen, snake_body, direction)
            draw_hud(screen, font_hud, score, high_score)
            draw_game_over_screen(screen, font_title, font_btn, font_text, score, high_score,
                                  restart_btn_rect, quit_btn_rect)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()