#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 14 15:32:41 2026

@author: lllhaoran
"""

# -*- coding: utf-8 -*-
"""
贪吃蛇 · 霓虹版  Neon Snake
基于 tkinter，Anaconda 自带，无需安装任何第三方库。

运行：保存为 snake.py，Spyder 按 F5，或命令行 python snake.py
操作：方向键 / WASD 移动    P 暂停    空格 重开    ESC 退出
"""

import tkinter as tk
import tkinter.font as tkfont
import random
import math
import time
import os
import json

# ==================== 尺寸 ====================
CELL = 24
COLS, ROWS = 26, 24
HUD_H = 56
WIDTH = COLS * CELL
HEIGHT = HUD_H + ROWS * CELL

BASE_STEP = 0.125
FAST_STEP = 0.062
SLOW_STEP = 0.20
MIN_STEP = 0.062

# ==================== 配色 ====================
BG       = "#080b14"
BG2      = "#0c1220"
GRID     = "#0f1626"
HUD_BG   = "#0a0f1c"
BORDER   = "#1c2a44"
SHADOW   = "#04060c"

HEAD_C   = "#8dffc0"
BODY_TOP = "#3ce08c"
BODY_END = "#0a5c3c"

WALL_C   = "#1e2a42"
WALL_E   = "#2f4166"
WALL_HI  = "#3b5482"

TEXT     = "#eaf2ff"
DIM      = "#5b6b8c"
GOLD     = "#ffd23f"

FOODS = {
    "normal": {"color": "#ff4757", "hi": "#ff8a94", "score": 10, "grow": 1, "weight": 60, "life": None},
    "gold":   {"color": "#ffd23f", "hi": "#fff3b0", "score": 50, "grow": 2, "weight": 12, "life": 9.0},
    "slow":   {"color": "#38bdf8", "hi": "#a5e8ff", "score": 15, "grow": 1, "weight": 9,  "life": 11.0},
    "fast":   {"color": "#a78bfa", "hi": "#ddd0ff", "score": 15, "grow": 1, "weight": 9,  "life": 11.0},
    "shield": {"color": "#2dd4bf", "hi": "#a0fff0", "score": 15, "grow": 1, "weight": 8,  "life": 12.0},
}

UP, DOWN, LEFT, RIGHT = (0, -1), (0, 1), (-1, 0), (1, 0)

CJK = ("Microsoft YaHei", "微软雅黑", "PingFang SC", "Heiti SC",
       "Noto Sans CJK SC", "WenQuanYi Micro Hei", "SimHei")
MONO = ("Consolas", "JetBrains Mono", "DejaVu Sans Mono", "Menlo",
        "Monaco", "Courier New")

try:
    _BASE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _BASE = os.path.expanduser("~")
HS_FILE = os.path.join(_BASE, "neon_snake_hs.json")


# ==================== 工具 ====================
def hex2rgb(h):
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgb2hex(r, g, b):
    return "#%02x%02x%02x" % (max(0, min(255, int(r))),
                              max(0, min(255, int(g))),
                              max(0, min(255, int(b))))


def lerp_color(c1, c2, t):
    r1, g1, b1 = hex2rgb(c1)
    r2, g2, b2 = hex2rgb(c2)
    return rgb2hex(r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t)


def blend(fg, bg, a):
    r1, g1, b1 = hex2rgb(fg)
    r2, g2, b2 = hex2rgb(bg)
    return rgb2hex(r1 * a + r2 * (1 - a),
                   g1 * a + g2 * (1 - a),
                   b1 * a + b2 * (1 - a))


def make_font(families, size, bold=False):
    fams = set(tkfont.families())
    weight = "bold" if bold else "normal"
    for f in families:
        if f in fams:
            return tkfont.Font(family=f, size=size, weight=weight)
    return tkfont.Font(size=size, weight=weight)


def round_rect(canvas, x1, y1, x2, y2, r, **kw):
    pts = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kw)


# ==================== 粒子 ====================
class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size")

    def __init__(self, x, y, color, spread=3.5, size=4.0, life_range=(0.35, 0.95)):
        a = random.uniform(0, math.tau)
        s = random.uniform(0.4, spread)
        self.x = x
        self.y = y
        self.vx = math.cos(a) * s
        self.vy = math.sin(a) * s
        self.max_life = self.life = random.uniform(*life_range)
        self.color = color
        self.size = random.uniform(1.8, size)


# ==================== 游戏 ====================
class NeonSnake:
    def __init__(self, root):
        self.root = root
        root.title("霓虹贪吃蛇 · Neon Snake")
        root.resizable(False, False)
        root.configure(bg=BG)
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT,
                                bg=BG, highlightthickness=0)
        self.canvas.pack()
        root.bind("<Key>", self.on_key)
        self.canvas.focus_set()
        root.focus_force()

        # 字体
        self.f_tiny  = make_font(CJK, 9)
        self.f_small = make_font(CJK, 11)
        self.f_mid   = make_font(CJK, 13)
        self.f_num   = make_font(MONO, 20, True)
        self.f_num2  = make_font(MONO, 14, True)
        self.f_big   = make_font(CJK, 18, True)
        self.f_huge  = make_font(CJK, 40, True)
        self.f_sub   = make_font(CJK, 14)

        self.high_score = self.load_hs()
        self.reset()
        self.last_time = time.time()
        self.loop()

    # ---------------- 存档 ----------------
    def load_hs(self):
        try:
            with open(HS_FILE, "r", encoding="utf-8") as f:
                return int(json.load(f).get("high", 0))
        except Exception:
            return 0

    def save_hs(self):
        try:
            with open(HS_FILE, "w", encoding="utf-8") as f:
                json.dump({"high": int(self.high_score)}, f)
        except Exception:
            pass

    # ---------------- 初始化 ----------------
    def reset(self):
        cx, cy = COLS // 2, ROWS // 2
        self.snake = [(cx - i, cy) for i in range(4)]
        self.vis_snake = [[float(x), float(y)] for x, y in self.snake]
        self.direction = RIGHT
        self.next_dir = RIGHT
        self.grow_pending = 0
        self.score = 0
        self.game_over = False
        self.paused = False
        self.walls = set()
        self.particles = []
        self.slow_t = 0.0
        self.fast_t = 0.0
        self.shield_t = 0.0
        self.move_acc = 0.0
        self.time = 0.0
        self.shake = 0.0
        self.banner = ""
        self.banner_t = 0.0
        self.death_cause = ""
        self.walls_milestone = 0
        self.food = None
        self.food_type = "normal"
        self.food_life = None
        self.head_pulse = 0.0

        for _ in range(8):
            self.add_wall()
        self.spawn_food()

    # ---------------- 障碍物 ----------------
    def add_wall(self):
        if len(self.walls) >= 60:
            return
        hx, hy = self.snake[0]
        for _ in range(400):
            x = random.randint(0, COLS - 1)
            y = random.randint(0, ROWS - 1)
            if (x, y) in self.walls or (x, y) in self.snake:
                continue
            if abs(x - hx) + abs(y - hy) < 8:
                continue
            if self.food and (x, y) == self.food:
                continue
            near = sum(1 for d in (UP, DOWN, LEFT, RIGHT)
                       if (x + d[0], y + d[1]) in self.walls)
            if near >= 2:
                continue
            self.walls.add((x, y))
            return

    # ---------------- 食物 ----------------
    def spawn_food(self):
        occupied = set(self.snake) | self.walls
        empty = [(x, y) for x in range(COLS) for y in range(ROWS)
                 if (x, y) not in occupied]
        if not empty:
            self.food = None
            return
        names, weights = [], []
        for k, v in FOODS.items():
            if k == "gold" and self.score < 30:
                continue
            if k == "shield" and self.score < 60:
                continue
            names.append(k)
            weights.append(v["weight"])
        kind = random.choices(names, weights=weights, k=1)[0]
        self.food_type = kind
        self.food = random.choice(empty)
        self.food_life = FOODS[kind]["life"]

    # ---------------- 键盘 ----------------
    def on_key(self, event):
        k = event.keysym
        if k == "Escape":
            self.save_hs()
            self.root.destroy()
            return
        if self.game_over:
            if k in ("space", "Return"):
                self.reset()
            return
        if k in ("p", "P"):
            self.paused = not self.paused
            return
        if self.paused:
            return
        if k in ("Up", "w", "W"):
            self.turn(UP)
        elif k in ("Down", "s", "S"):
            self.turn(DOWN)
        elif k in ("Left", "a", "A"):
            self.turn(LEFT)
        elif k in ("Right", "d", "D"):
            self.turn(RIGHT)

    def turn(self, nd):
        if (nd[0] + self.next_dir[0], nd[1] + self.next_dir[1]) != (0, 0):
            self.next_dir = nd

    # ---------------- 主循环 ----------------
    def loop(self):
        now = time.time()
        dt = now - self.last_time
        self.last_time = now
        if dt > 0.1:
            dt = 0.1
        self.tick(dt)
        self.draw()
        self.root.after(16, self.loop)

    def tick(self, dt):
        self.time += dt

        # 粒子
        alive = []
        for p in self.particles:
            p.x += p.vx
            p.y += p.vy
            p.vy += 0.18
            p.vx *= 0.95
            p.vy *= 0.95
            p.life -= dt
            if p.life > 0:
                alive.append(p)
        self.particles = alive if len(alive) < 400 else alive[:400]

        # 视觉位置平滑
        self.update_vis(dt)

        # 屏幕抖动
        if self.shake > 0:
            self.shake = max(0.0, self.shake - dt * 42)
        if self.banner_t > 0:
            self.banner_t = max(0.0, self.banner_t - dt)

        if self.game_over or self.paused:
            return

        # 倒计时
        if self.slow_t > 0:
            self.slow_t = max(0.0, self.slow_t - dt)
        if self.fast_t > 0:
            self.fast_t = max(0.0, self.fast_t - dt)
        if self.shield_t > 0:
            self.shield_t = max(0.0, self.shield_t - dt)

        if self.food_life is not None and self.food is not None:
            self.food_life -= dt
            if self.food_life <= 0:
                self.spawn_food()

        # 蛇头脉冲
        self.head_pulse = (self.head_pulse + dt * 3.2) % (math.tau)

        # 移动节奏
        self.move_acc += dt
        interval = self.step_interval()
        guard = 0
        while self.move_acc >= interval and not self.game_over:
            self.move_acc -= interval
            self.step()
            interval = self.step_interval()
            guard += 1
            if guard > 4:
                self.move_acc = 0.0
                break

    def update_vis(self, dt):
        n = len(self.snake)
        vs = self.vis_snake
        while len(vs) < n:
            if vs:
                vs.append([vs[-1][0], vs[-1][1]])
            else:
                vs.append([float(self.snake[0][0]), float(self.snake[0][1])])
        if len(vs) > n:
            del vs[n:]

        s = min(1.0, dt * 26.0)
        for i in range(n):
            tx, ty = self.snake[i]
            v = vs[i]
            v[0] += (tx - v[0]) * s
            v[1] += (ty - v[1]) * s

    def step_interval(self):
        if self.fast_t > 0:
            return FAST_STEP
        if self.slow_t > 0:
            return SLOW_STEP
        base = BASE_STEP - min(0.05, self.score * 0.0007)
        return max(MIN_STEP, base)

    # ---------------- 单步 ----------------
    def step(self):
        self.direction = self.next_dir
        hx, hy = self.snake[0]
        dx, dy = self.direction
        nx, ny = hx + dx, hy + dy
        shielded = self.shield_t > 0

        if not (0 <= nx < COLS and 0 <= ny < ROWS):
            if shielded:
                nx %= COLS
                ny %= ROWS
                self.burst(hx, hy, "#2dd4bf", 12)
            else:
                self.die("撞到墙壁了")
                return

        if (nx, ny) in self.walls:
            if shielded:
                self.walls.discard((nx, ny))
                self.burst(nx, ny, WALL_HI, 16, 4.5)
                self.shake = 7
                self.banner, self.banner_t = "破墙 +5", 0.9
                self.score += 5
            else:
                self.die("撞到障碍物了")
                return

        new_head = (nx, ny)

        if new_head in self.snake[:-1] and not shielded:
            self.die("咬到自己了")
            return

        self.snake.insert(0, new_head)
        # 视觉上新增一节从蛇头位置出现
        self.vis_snake.insert(0, [float(hx), float(hy)])

        if self.food is not None and new_head == self.food:
            self.grow_pending += FOODS[self.food_type]["grow"]
            self.on_eat()
            self.spawn_food()

        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            self.snake.pop()
            # 视觉上尾巴也一起收缩
            if len(self.vis_snake) > len(self.snake):
                self.vis_snake.pop()

    # ---------------- 吃 ----------------
    def on_eat(self):
        info = FOODS[self.food_type]
        gained = info["score"]
        if self.fast_t > 0:
            gained *= 2
        self.score += gained

        fx, fy = self.food
        self.burst(fx, fy, info["color"], 22)
        self.burst(fx, fy, info["hi"], 8, 2.5)

        kind = self.food_type
        if kind == "slow":
            self.slow_t, self.fast_t = 5.0, 0.0
            self.banner, self.banner_t = "缓速 5 秒", 1.2
        elif kind == "fast":
            self.fast_t, self.slow_t = 5.0, 0.0
            self.banner, self.banner_t = "狂暴 · 双倍得分", 1.2
        elif kind == "shield":
            self.shield_t = 6.0
            self.banner, self.banner_t = "护盾 6 秒", 1.2
        elif kind == "gold":
            self.banner, self.banner_t = "金苹果 +%d" % gained, 1.0
            self.shake = 5
        else:
            self.banner, self.banner_t = "+%d" % gained, 0.5

        if self.score // 50 > self.walls_milestone:
            self.walls_milestone = self.score // 50
            for _ in range(2):
                self.add_wall()
            self.banner, self.banner_t = "障碍增加！", 1.2

        if self.score > self.high_score:
            self.high_score = self.score
            self.save_hs()

    def die(self, cause):
        self.game_over = True
        self.death_cause = cause
        hx, hy = self.snake[0]
        self.burst(hx, hy, "#ff4757", 55, 7.5, (0.5, 1.4))
        self.burst(hx, hy, "#ffb0b8", 20, 4.5)
        self.shake = 18
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_hs()

    def burst(self, gx, gy, color, n, spread=3.5, life_range=(0.35, 0.95)):
        px = gx * CELL + CELL / 2
        py = HUD_H + gy * CELL + CELL / 2
        for _ in range(n):
            self.particles.append(Particle(px, py, color, spread, 4.5, life_range))

    # ==================== 渲染 ====================
    def draw(self):
        c = self.canvas
        c.delete("all")

        ox = oy = 0.0
        if self.shake > 0.1:
            ox = random.uniform(-1, 1) * self.shake * 0.35
            oy = random.uniform(-1, 1) * self.shake * 0.35

        # 背景
        c.create_rectangle(0, 0, WIDTH, HEIGHT, fill=BG, outline="")

        # 网格（仅在游戏区域）
        for x in range(COLS + 1):
            px = x * CELL + ox
            c.create_line(px, HUD_H, px, HEIGHT, fill=GRID)
        for y in range(ROWS + 1):
            py = HUD_H + y * CELL + oy
            c.create_line(0, py, WIDTH, py, fill=GRID)

        self.draw_walls(c, ox, oy)
        self.draw_food(c, ox, oy)
        self.draw_snake(c, ox, oy)
        self.draw_particles(c, ox, oy)
        self.draw_hud(c)
        self.draw_overlay(c)

    # ---------------- 障碍物 ----------------
    def draw_walls(self, c, ox, oy):
        for (x, y) in self.walls:
            px = x * CELL + ox
            py = HUD_H + y * CELL + oy
            # 阴影
            c.create_rectangle(px + 3, py + 4, px + CELL - 1, py + CELL + 1,
                               fill=SHADOW, outline="")
            # 主体
            c.create_rectangle(px + 2, py + 2, px + CELL - 2, py + CELL - 2,
                               fill=WALL_C, outline=WALL_E, width=1)
            # 顶部高光
            c.create_line(px + 4, py + 3, px + CELL - 4, py + 3,
                          fill=WALL_HI, width=1)

    # ---------------- 食物 ----------------
    def draw_food(self, c, ox, oy):
        if self.food is None:
            return
        info = FOODS[self.food_type]
        col = info["color"]
        hi = info["hi"]

        fx, fy = self.food
        cx = fx * CELL + CELL / 2 + ox
        cy = HUD_H + fy * CELL + CELL / 2 + oy

        pulse = 0.5 + 0.5 * math.sin(self.time * 5.5)
        r = CELL * 0.26 * (0.9 + 0.2 * pulse)

        # 多层光晕
        for i, alpha in enumerate((0.06, 0.10, 0.16)):
            gr = r + (3 - i) * 5.0
            c.create_oval(cx - gr, cy - gr, cx + gr, cy + gr,
                          fill=blend(col, BG, alpha), outline="")

        # 本体
        c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=col, outline="")

        # 高光
        hl_r = r * 0.40
        hx_ = cx - r * 0.30
        hy_ = cy - r * 0.36
        c.create_oval(hx_ - hl_r, hy_ - hl_r, hx_ + hl_r, hy_ + hl_r,
                      fill=blend("#ffffff", hi, 0.55), outline="")

        # 倒计时弧
        if self.food_life is not None and info["life"]:
            frac = max(0.0, self.food_life / info["life"])
            if frac > 0.02:
                ext = r + 7.5
                c.create_arc(cx - ext, cy - ext, cx + ext, cy + ext,
                             start=90, extent=-359.9 * frac,
                             style="arc", outline=col, width=2)

    # ---------------- 蛇 ----------------
    def draw_snake(self, c, ox, oy):
        vs = self.vis_snake
        n = len(vs)
        if n == 0:
            return

        # 计算节点
        nodes = []
        for i in range(n):
            gx, gy = vs[i]
            cx = gx * CELL + CELL / 2 + ox
            cy = HUD_H + gy * CELL + CELL / 2 + oy
            t = i / max(1, n - 1)
            r = CELL * 0.53 * (1.0 - 0.32 * t)
            nodes.append((cx, cy, r, t))

        # 外发光（描边）
        for (cx, cy, r, t) in nodes:
            rr = r + 2.4
            c.create_oval(cx - rr, cy - rr, cx + rr, cy + rr,
                          fill=SHADOW, outline="")

        # 身体渐变
        for i, (cx, cy, r, t) in enumerate(nodes):
            if i == 0:
                # 蛇头稍亮
                col = HEAD_C
            else:
                col = lerp_color(BODY_TOP, BODY_END, t ** 1.15)
            c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=col, outline="")

        # 护盾
        if self.shield_t > 0:
            hx, hy, hr, _ = nodes[0]
            gr = hr + 6 + math.sin(self.time * 9) * 2
            c.create_oval(hx - gr, hy - gr, hx + gr, hy + gr,
                          outline="#2dd4bf", width=2)
            c.create_oval(hx - gr - 3, hy - gr - 3, hx + gr + 3, hy + gr + 3,
                          outline=blend("#2dd4bf", BG, 0.35), width=1)

        # 蛇头细节
        hx, hy, hr, _ = nodes[0]
        dx, dy = self.direction
        pxv, pyv = -dy, dx

        # 眼睛
        eye_fwd = hr * 0.34
        eye_side = hr * 0.42
        eye_r = hr * 0.27
        for sgn in (1, -1):
            ex = hx + dx * eye_fwd + pxv * eye_side * sgn
            ey = hy + dy * eye_fwd + pyv * eye_side * sgn
            # 眼白
            c.create_oval(ex - eye_r, ey - eye_r, ex + eye_r, ey + eye_r,
                          fill="#ffffff", outline="")
            # 瞳孔（朝向前进方向）
            pr = eye_r * 0.58
            ppx = ex + dx * eye_r * 0.24
            ppy = ey + dy * eye_r * 0.24
            c.create_oval(ppx - pr, ppy - pr, ppx + pr, ppy + pr,
                          fill="#06121a", outline="")
            # 瞳孔高光
            gl_r = pr * 0.42
            c.create_oval(ppx - pr * 0.55 - gl_r,
                          ppy - pr * 0.55 - gl_r,
                          ppx - pr * 0.55 + gl_r,
                          ppy - pr * 0.55 + gl_r,
                          fill="#ffffff", outline="")

        # 舌头（脉冲）
        tongue = math.sin(self.head_pulse * 2) * 0.5 + 0.5
        if tongue > 0.7:
            tl = hr * 0.55 * (tongue - 0.7) / 0.3
            tx1 = hx + dx * hr
            ty1 = hy + dy * hr
            tx2 = hx + dx * (hr + tl)
            ty2 = hy + dy * (hr + tl)
            c.create_line(tx1, ty1, tx2, ty2, fill="#ff5f7a", width=2,
                          capstyle="round")

    # ---------------- 粒子 ----------------
    def draw_particles(self, c, ox, oy):
        for p in self.particles:
            a = p.life / p.max_life
            r = p.size * a
            if r < 0.35:
                continue
            col = blend(p.color, BG, min(1.0, a * 1.2))
            c.create_oval(p.x - r + ox, p.y - r + oy,
                          p.x + r + ox, p.y + r + oy,
                          fill=col, outline="")

    # ---------------- HUD ----------------
    def draw_hud(self, c):
        c.create_rectangle(0, 0, WIDTH, HUD_H, fill=HUD_BG, outline="")
        c.create_line(0, HUD_H, WIDTH, HUD_H, fill=BORDER, width=1)

        # 左侧：得分
        c.create_text(18, 10, anchor="nw", text="得分",
                      fill=DIM, font=self.f_tiny)
        c.create_text(18, 24, anchor="nw", text=str(self.score),
                      fill=TEXT, font=self.f_num)

        # 中间：最高分
        c.create_text(WIDTH // 2, 10, anchor="n", text="最高分",
                      fill=DIM, font=self.f_tiny)
        c.create_text(WIDTH // 2, 24, anchor="n", text=str(self.high_score),
                      fill=GOLD, font=self.f_num)

        # 右侧：状态条
        items = []
        if self.shield_t > 0:
            items.append(("护盾", self.shield_t / 6.0, "#2dd4bf"))
        if self.fast_t > 0:
            items.append(("狂暴", self.fast_t / 5.0, "#a78bfa"))
        if self.slow_t > 0:
            items.append(("缓速", self.slow_t / 5.0, "#38bdf8"))

        bx = WIDTH - 16
        for name, frac, col in reversed(items):
            w = 64
            # 背景条
            round_rect(c, bx - w, 14, bx, 24, 4,
                       fill="#141d31", outline="")
            # 进度
            pw = max(2, w * frac)
            round_rect(c, bx - w, 14, bx - w + pw, 24, 4,
                       fill=col, outline="")
            # 文字
            c.create_text(bx - w / 2, 36, text=name, fill=col,
                          font=self.f_tiny)
            bx -= w + 10

        # 中央横幅提示
        if self.banner_t > 0 and not self.game_over:
            a = min(1.0, self.banner_t / 0.4)
            col = blend(GOLD, BG, a)
            c.create_text(WIDTH // 2, HUD_H + 34, text=self.banner,
                          fill=col, font=self.f_big)

    # ---------------- 覆盖层 ----------------
    def draw_overlay(self, c):
        if not (self.paused or self.game_over):
            return

        # 半透明遮罩（用点阵模拟）
        c.create_rectangle(0, HUD_H, WIDTH, HEIGHT,
                           fill="#000000", stipple="gray50", outline="")

        if self.paused:
            c.create_text(WIDTH // 2, HEIGHT // 2 - 20, text="已暂停",
                          fill=HEAD_C, font=self.f_huge)
            c.create_text(WIDTH // 2, HEIGHT // 2 + 34,
                          text="按 P 继续游戏 · ESC 退出",
                          fill=DIM, font=self.f_mid)
            return

        # 游戏结束
        cy0 = HEIGHT // 2 - 90
        c.create_text(WIDTH // 2, cy0, text="游戏结束",
                      fill="#ff4757", font=self.f_huge)
        c.create_text(WIDTH // 2, cy0 + 52, text=self.death_cause,
                      fill=DIM, font=self.f_sub)

        c.create_text(WIDTH // 2, cy0 + 100,
                      text="本局得分", fill=DIM, font=self.f_tiny)
        c.create_text(WIDTH // 2, cy0 + 128, text=str(self.score),
                      fill=TEXT, font=self.f_big)

        c.create_text(WIDTH // 2, cy0 + 168,
                      text="历史最高  %d" % self.high_score,
                      fill=GOLD, font=self.f_mid)

        c.create_text(WIDTH // 2, cy0 + 220,
                      text="按 空格 重新开始 · ESC 退出",
                      fill=DIM, font=self.f_small)


if __name__ == "__main__":
    root = tk.Tk()
    NeonSnake(root)
    root.mainloop()