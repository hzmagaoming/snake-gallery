# -*- coding: utf-8 -*-
"""
贪吃蛇小游戏 - pygame 版
运行方式:  python snake.py
操作:
  方向键 / WASD  控制方向
  空格           暂停 / 继续
  1 / 2 / 3      切换速度(低 / 中 / 高)
  回车 / 空格    菜单中开始游戏
  H              菜单中查看玩法规则
  Esc            退出

玩法小创意:
  金苹果   食物会定时变成金色, 吃掉得 30 分(普通食物 10 分)
  道具     场上会定时刷新道具, 蛇头碰到即生效:
            慢 = 减速(移动变慢)   盾 = 护盾(撞到自己不死亡)   穿 = 穿墙(穿过边界到对面)
"""

import random
import sys

import pygame

# ---------- 基本配置 ----------
CELL = 22                 # 每个格子的像素大小
COLS, ROWS = 30, 24       # 棋盘列数、行数
HUD_H = 52                # 顶部信息栏高度
WIDTH = COLS * CELL
HEIGHT = ROWS * CELL + HUD_H
FPS = 60                  # 渲染帧率(固定, 移动速度用计时器控制)

# 三档速度: (名称, 每秒移动的步数)
SPEEDS = [("低", 6), ("中", 10), ("高", 15)]
DEFAULT_SPEED = 1         # 默认选中"中"

# ---------- 配色 ----------
BG         = (22, 25, 38)     # 棋盘底色
BG_ALT     = (28, 31, 46)     # 棋盘格交替色
HUD_BG     = (16, 19, 30)     # 顶栏背景
HUD_LINE   = (44, 50, 68)     # 顶栏与棋盘分隔线
PANEL_BG   = (33, 37, 54)     # 规则/菜单面板背景
SNAKE_HEAD = (92, 227, 172)   # 蛇头(亮绿)
SNAKE_TAIL = (26, 128, 96)    # 蛇尾(深绿)
EYE_WHITE  = (245, 250, 252)
EYE_BLACK  = (18, 26, 34)
FOOD       = (255, 103, 103)  # 普通食物
FOOD_HI    = (255, 196, 148)  # 普通食物高光
GOLD       = (255, 201, 64)   # 金苹果
GOLD_HI    = (255, 240, 168)  # 金苹果高光
TEXT       = (236, 240, 247)
TEXT_DIM   = (158, 168, 186)
ACCENT     = (255, 206, 84)   # 分数/高亮
BTN_BG     = (38, 44, 60)
BTN_HOVER  = (52, 60, 80)
BTN_ACTIVE = (46, 168, 126)
OVERLAY    = (10, 12, 20, 190)

# ---------- 金苹果 ----------
GOLD_CD = 5000            # 普通食物出现多久后变金(毫秒)
GOLD_DURATION = 3000      # 金色持续多久(毫秒)
NORMAL_SCORE = 10
GOLD_SCORE = 30

# ---------- 道具 ----------
POWERUP_INTERVAL = 7000   # 道具刷新间隔(毫秒)
POWERUP_LIFE = 6000       # 道具在场时间(毫秒)
POWERUP_BLINK = 1500      # 道具消失前闪烁的时间(毫秒)
SLOW_FACTOR = 1.8         # 减速: 移动速度除以该系数
EFFECT_DUR = {"slow": 5000, "shield": 6000, "ghost": 8000}
POWERUP_TYPES = ["slow", "shield", "ghost"]
POWERUP_META = {
    "slow":   {"name": "减速", "label": "慢", "color": (96, 165, 250)},
    "shield": {"name": "护盾", "label": "盾", "color": (250, 204, 21)},
    "ghost":  {"name": "穿墙", "label": "穿", "color": (168, 130, 255)},
}

DIR_KEYS = {
    pygame.K_UP: (0, -1), pygame.K_w: (0, -1),
    pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
    pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0),
    pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0),
}
SPEED_KEYS = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2}


def lerp_color(c1, c2, t):
    """在两个颜色之间线性插值"""
    t = max(0.0, min(1.0, t))
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def draw_text(screen, font, text, color, x, y, center=True):
    surface = font.render(text, True, color)
    rect = surface.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surface, rect)
    return rect


def random_free_cell(snake, avoid=()):
    """随机返回一个空格子(不在蛇身上、也不在 avoid 里)"""
    avoid = set(avoid)
    while True:
        pos = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
        if pos not in snake and pos not in avoid:
            return pos


def draw_food(screen, fx, fy, cell, golden=False):
    """画食物: 带光晕和一点高光的果实(金色时为金苹果)"""
    color = GOLD if golden else FOOD
    hi = GOLD_HI if golden else FOOD_HI
    cx = fx * cell + cell // 2
    cy = HUD_H + fy * cell + cell // 2
    r = cell // 2 - 3

    glow = pygame.Surface((cell * 3, cell * 3), pygame.SRCALPHA)
    gc = cell * 3 // 2
    pygame.draw.circle(glow, (*color, 26), (gc, gc), r + 8)
    pygame.draw.circle(glow, (*color, 48), (gc, gc), r + 4)
    screen.blit(glow, (cx - gc, cy - gc))

    pygame.draw.circle(screen, color, (cx, cy), r)
    pygame.draw.circle(screen, hi, (cx - r // 3, cy - r // 3), r // 3)


def draw_powerup(screen, pu, cell, font):
    """画道具: 彩色圆角方块 + 中间一个汉字标签, 快消失时闪烁"""
    if pu is None:
        return
    if pu["remain"] < POWERUP_BLINK and int(pu["remain"] // 150) % 2 == 0:
        return
    meta = POWERUP_META[pu["type"]]
    fx, fy = pu["pos"]
    cx = fx * cell + cell // 2
    cy = HUD_H + fy * cell + cell // 2

    glow = pygame.Surface((cell * 3, cell * 3), pygame.SRCALPHA)
    gc = cell * 3 // 2
    pygame.draw.circle(glow, (*meta["color"], 26), (gc, gc), cell // 2 + 6)
    pygame.draw.circle(glow, (*meta["color"], 48), (gc, gc), cell // 2 + 2)
    screen.blit(glow, (cx - gc, cy - gc))

    rect = pygame.Rect(cx - cell // 2 + 3, cy - cell // 2 + 3, cell - 6, cell - 6)
    pygame.draw.rect(screen, meta["color"], rect, border_radius=8)
    pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=8)
    draw_text(screen, font, meta["label"], (255, 255, 255), cx, cy)


def draw_snake(screen, snake, direction, cell):
    """画蛇: 连续圆润的身体, 头部带眼睛"""
    n = len(snake)
    pts = [(sx * cell + cell // 2, HUD_H + sy * cell + cell // 2) for sx, sy in snake]

    for i in range(n - 1):                       # 身体用粗线连接
        # 穿墙时相邻两段会跨越整张棋盘, 跳过这种连线
        if abs(pts[i][0] - pts[i + 1][0]) > cell or abs(pts[i][1] - pts[i + 1][1]) > cell:
            continue
        color = lerp_color(SNAKE_HEAD, SNAKE_TAIL, i / max(1, n - 1))
        pygame.draw.line(screen, color, pts[i], pts[i + 1], cell - 2)
    for i, p in enumerate(pts):                  # 每个节点画圆, 盖住转折处
        color = lerp_color(SNAKE_HEAD, SNAKE_TAIL, 0 if n == 1 else i / (n - 1))
        pygame.draw.circle(screen, color, p, cell // 2 - 1)

    # 蛇头眼睛
    hx, hy = pts[0]
    dx, dy = direction
    px, py = -dy, dx                            # 垂直方向
    for sign in (-1, 1):
        ex = hx + dx * (cell // 4) + px * sign * (cell // 5)
        ey = hy + dy * (cell // 4) + py * sign * (cell // 5)
        pygame.draw.circle(screen, EYE_WHITE, (ex, ey), 4)
        pygame.draw.circle(screen, EYE_BLACK, (ex + dx, ey + dy), 2)


def draw_hud(screen, fonts, score, speed_index, effects):
    """顶部信息栏: 标题 + 得分 + 当前速度 + 生效中的道具"""
    screen.fill(HUD_BG, (0, 0, WIDTH, HUD_H))
    pygame.draw.line(screen, HUD_LINE, (0, HUD_H - 1), (WIDTH, HUD_H - 1))

    draw_text(screen, fonts["small"], "贪吃蛇", TEXT, 16, HUD_H // 2, center=False)

    speed_surf = fonts["small"].render(f"速度 {SPEEDS[speed_index][0]}", True, TEXT_DIM)
    x = WIDTH - 16
    speed_rect = speed_surf.get_rect(midright=(x, HUD_H // 2))
    screen.blit(speed_surf, speed_rect)

    score_surf = fonts["small"].render(f"得分 {score}", True, ACCENT)
    score_rect = score_surf.get_rect(midright=(speed_rect.left - 20, HUD_H // 2))
    screen.blit(score_surf, score_rect)

    ex = score_rect.left - 16
    for key in POWERUP_TYPES:
        if effects[key] > 0:
            label = f"{POWERUP_META[key]['name']} {effects[key] / 1000:.0f}s"
            surf = fonts["tiny"].render(label, True, POWERUP_META[key]["color"])
            rect = surf.get_rect(midright=(ex, HUD_H // 2))
            screen.blit(surf, rect)
            ex = rect.left - 12


def speed_buttons():
    """菜单里三个速度按钮的矩形"""
    bw, bh, gap = 110, 64, 20
    total = bw * 3 + gap * 2
    x0 = (WIDTH - total) // 2
    y = 190
    return [pygame.Rect(x0 + i * (bw + gap), y, bw, bh) for i in range(3)]


def draw_overlay(screen):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill(OVERLAY)
    screen.blit(overlay, (0, 0))


def draw_menu(screen, fonts, speed_index, mouse_pos):
    """开始菜单: 标题 + 三档速度选择"""
    draw_overlay(screen)
    draw_text(screen, fonts["title"], "贪吃蛇", TEXT, WIDTH // 2, 92)
    draw_text(screen, fonts["small"], "金苹果 · 道具 · 三档速度", TEXT_DIM, WIDTH // 2, 140)

    rects = speed_buttons()
    for i, (name, sps) in enumerate(SPEEDS):
        rect = rects[i]
        hover = rect.collidepoint(mouse_pos)
        active = (i == speed_index)
        color = BTN_ACTIVE if active else (BTN_HOVER if hover else BTN_BG)
        pygame.draw.rect(screen, color, rect, border_radius=14)
        if active:
            pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=14)
        draw_text(screen, fonts["med"], name, (255, 255, 255) if active else TEXT,
                  rect.centerx, rect.centery - 10)
        draw_text(screen, fonts["tiny"], f"{sps} 格/秒", TEXT_DIM,
                  rect.centerx, rect.centery + 16)

    draw_text(screen, fonts["small"], "方向键 / WASD 移动 · 空格暂停 · 1/2/3 切速度",
              TEXT_DIM, WIDTH // 2, 322)
    draw_text(screen, fonts["small"], "金苹果 30 分 · 道具：慢/盾/穿",
              TEXT_DIM, WIDTH // 2, 356)
    draw_text(screen, fonts["small"], "按 H 查看玩法规则 · 回车/空格开始 · Esc 退出",
              TEXT_DIM, WIDTH // 2, HEIGHT - 34)
    return rects


def draw_rules(screen, fonts):
    """玩法规则页: 把规则写进游戏, 发给老师/同学一看就懂"""
    screen.fill(BG)
    draw_text(screen, fonts["title"], "玩法规则", TEXT, WIDTH // 2, 56)

    panel = pygame.Rect(36, 106, WIDTH - 72, 396)
    pygame.draw.rect(screen, PANEL_BG, panel, border_radius=16)

    med = fonts["med"]

    # 主条目: 右对齐金色标题 + 左对齐正文
    rows = [
        ("目标", "控制蛇吃食物，蛇越长、得分越高", TEXT),
        ("移动", "方向键 / WASD 移动 · 空格暂停 · 1/2/3 切速度", TEXT),
        ("食物", "普通食物 10 分；每 5 秒变金，金苹果 30 分", TEXT),
        ("道具", "每 7 秒刷新一个，碰到蛇头即生效", TEXT),
    ]
    y = 130
    for head, body, color in rows:
        label = med.render(head, True, ACCENT)
        screen.blit(label, (112 - label.get_width(), y))
        screen.blit(med.render(body, True, color), (128, y))
        y += 40

    # 道具子项: 用各自道具颜色, 呼应游戏内方块颜色
    subs = [
        ("slow",   "慢 · 减速 —— 移动变慢，持续 5 秒"),
        ("shield", "盾 · 护盾 —— 撞到自己不死亡，持续 6 秒"),
        ("ghost",  "穿 · 穿墙 —— 穿过边界到对面，持续 8 秒"),
    ]
    for key, text in subs:
        color = POWERUP_META[key]["color"]
        screen.blit(med.render("·", True, color), (112, y))
        screen.blit(med.render(text, True, color), (128, y))
        y += 40

    # 结束 / 重开
    tail = [
        ("结束", "撞墙，或撞到自己（无护盾时）即结束", TEXT),
        ("重开", "空格重开 · M 返回菜单 · Esc 退出", TEXT),
    ]
    for head, body, color in tail:
        label = med.render(head, True, ACCENT)
        screen.blit(label, (112 - label.get_width(), y))
        screen.blit(med.render(body, True, color), (128, y))
        y += 40

    draw_text(screen, fonts["small"], "按 H / Esc 返回菜单", TEXT_DIM, WIDTH // 2, HEIGHT - 26)


def reset_game():
    """初始化一局游戏, 返回状态字典"""
    snake = [(COLS // 2 - i, ROWS // 2) for i in range(3)]
    return {
        "snake": snake,
        "direction": (1, 0),
        "next_direction": (1, 0),
        "food": random_free_cell(snake),
        "score": 0,
        "food_gold": False,
        "gold_timer": GOLD_CD,
        "powerup": None,
        "pu_timer": POWERUP_INTERVAL,
        "effects": {"slow": 0, "shield": 0, "ghost": 0},
    }


def move_snake(g):
    """让蛇前进一步; 撞墙或撞到自己时返回 True"""
    g["direction"] = g["next_direction"]
    hx = g["snake"][0][0] + g["direction"][0]
    hy = g["snake"][0][1] + g["direction"][1]

    # 穿墙: 越过边界从对面出来
    if g["effects"]["ghost"] > 0:
        hx %= COLS
        hy %= ROWS
    head = (hx, hy)

    if hx < 0 or hx >= COLS or hy < 0 or hy >= ROWS:
        return True
    # 护盾: 撞到自己不死亡
    if head in g["snake"] and g["effects"]["shield"] <= 0:
        return True

    g["snake"].insert(0, head)
    if head == g["food"]:
        g["score"] += GOLD_SCORE if g["food_gold"] else NORMAL_SCORE
        avoid = {g["powerup"]["pos"]} if g["powerup"] else set()
        g["food"] = random_free_cell(g["snake"], avoid=avoid)
        g["food_gold"] = False
        g["gold_timer"] = GOLD_CD
    else:
        g["snake"].pop()

    # 拾取道具
    pu = g["powerup"]
    if pu and head == pu["pos"]:
        g["effects"][pu["type"]] = EFFECT_DUR[pu["type"]]
        g["powerup"] = None
        g["pu_timer"] = POWERUP_INTERVAL

    return False


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("贪吃蛇 - 空格暂停 / Esc 退出")
    clock = pygame.time.Clock()

    fonts = {
        "small": pygame.font.SysFont("pingfangsc,hiraginosansgb,arial", 16),
        "med":   pygame.font.SysFont("pingfangsc,hiraginosansgb,arial", 20),
        "large": pygame.font.SysFont("pingfangsc,hiraginosansgb,arial", 40),
        "title": pygame.font.SysFont("pingfangsc,hiraginosansgb,arial", 48),
        "tiny":  pygame.font.SysFont("pingfangsc,hiraginosansgb,arial", 14),
    }

    state = "menu"               # menu / playing / paused / over / rules
    speed_index = DEFAULT_SPEED
    g = reset_game()
    move_acc = 0                 # 移动计时器(毫秒)

    while True:
        mouse_pos = pygame.mouse.get_pos()

        # ---------- 事件处理 ----------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if state == "rules":
                    state = "menu"
                else:
                    pygame.quit()
                    sys.exit()

            if state == "menu":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for i, rect in enumerate(speed_buttons()):
                        if rect.collidepoint(event.pos):
                            speed_index = i
                            g = reset_game()
                            move_acc = 0
                            state = "playing"
                elif event.type == pygame.KEYDOWN:
                    if event.key in SPEED_KEYS:
                        speed_index = SPEED_KEYS[event.key]
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        g = reset_game()
                        move_acc = 0
                        state = "playing"
                    elif event.key == pygame.K_LEFT:
                        speed_index = (speed_index - 1) % len(SPEEDS)
                    elif event.key == pygame.K_RIGHT:
                        speed_index = (speed_index + 1) % len(SPEEDS)
                    elif event.key == pygame.K_h:
                        state = "rules"

            elif state == "playing":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        state = "paused"
                    elif event.key in SPEED_KEYS:
                        speed_index = SPEED_KEYS[event.key]
                        move_acc = 0
                    elif event.key in DIR_KEYS:
                        candidate = DIR_KEYS[event.key]
                        if (candidate[0] + g["direction"][0],
                                candidate[1] + g["direction"][1]) != (0, 0):
                            g["next_direction"] = candidate

            elif state == "paused":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        state = "playing"
                    elif event.key in SPEED_KEYS:
                        speed_index = SPEED_KEYS[event.key]

            elif state == "over":
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        g = reset_game()
                        move_acc = 0
                        state = "playing"
                    elif event.key == pygame.K_m:
                        state = "menu"
                    elif event.key in SPEED_KEYS:
                        speed_index = SPEED_KEYS[event.key]

            elif state == "rules":
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_h, pygame.K_BACKSPACE, pygame.K_RETURN):
                        state = "menu"

        # ---------- 计时与移动 ----------
        dt = clock.tick(FPS)
        if state == "playing":
            move_acc += dt

            # 金苹果计时: 普通食物过一段时间变金, 金色持续一会再变回
            g["gold_timer"] -= dt
            if g["gold_timer"] <= 0:
                g["food_gold"] = not g["food_gold"]
                g["gold_timer"] = GOLD_DURATION if g["food_gold"] else GOLD_CD

            # 道具刷新与过期
            g["pu_timer"] -= dt
            if g["powerup"] is None:
                if g["pu_timer"] <= 0:
                    g["powerup"] = {
                        "type": random.choice(POWERUP_TYPES),
                        "pos": random_free_cell(g["snake"], avoid={g["food"]}),
                        "remain": POWERUP_LIFE,
                    }
            else:
                g["powerup"]["remain"] -= dt
                if g["powerup"]["remain"] <= 0:
                    g["powerup"] = None
                    g["pu_timer"] = POWERUP_INTERVAL

            # 生效中的道具倒计时
            for key in g["effects"]:
                if g["effects"][key] > 0:
                    g["effects"][key] = max(0, g["effects"][key] - dt)

            # 蛇的移动(减速效果影响速度)
            sps = SPEEDS[speed_index][1]
            if g["effects"]["slow"] > 0:
                sps /= SLOW_FACTOR
            interval = 1000 / sps
            while move_acc >= interval:
                move_acc -= interval
                if move_snake(g):
                    state = "over"
                    break

        # ---------- 绘制画面 ----------
        screen.fill(BG)
        for row in range(ROWS):                      # 棋盘格背景
            for col in range(COLS):
                if (row + col) % 2 == 0:
                    screen.fill(BG_ALT, (col * CELL, HUD_H + row * CELL, CELL, CELL))

        draw_food(screen, g["food"][0], g["food"][1], CELL, g["food_gold"])
        draw_snake(screen, g["snake"], g["direction"], CELL)
        draw_powerup(screen, g["powerup"], CELL, fonts["tiny"])
        draw_hud(screen, fonts, g["score"], speed_index, g["effects"])

        if state == "menu":
            draw_menu(screen, fonts, speed_index, mouse_pos)
        elif state == "paused":
            draw_overlay(screen)
            draw_text(screen, fonts["large"], "已暂停", TEXT, WIDTH // 2, HEIGHT // 2 - 16)
            draw_text(screen, fonts["small"], "按空格继续", TEXT_DIM, WIDTH // 2, HEIGHT // 2 + 28)
        elif state == "over":
            draw_overlay(screen)
            draw_text(screen, fonts["large"], "游戏结束", TEXT, WIDTH // 2, HEIGHT // 2 - 44)
            draw_text(screen, fonts["med"], f"得分 {g['score']}", ACCENT, WIDTH // 2, HEIGHT // 2)
            draw_text(screen, fonts["small"], "按空格重新开始 · 按 M 返回菜单",
                      TEXT_DIM, WIDTH // 2, HEIGHT // 2 + 44)
        elif state == "rules":
            draw_rules(screen, fonts)

        pygame.display.flip()


if __name__ == "__main__":
    main()
