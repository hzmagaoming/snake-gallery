# -*- coding: utf-8 -*-
"""
贪吃蛇 · 主题版 v15（Anaconda 直接运行）
==========================================================
主题：
  · 音符蛇：五线谱纸上的音符
  · 花园蛇：草地上吃六种花
  · 甜品蛇：马卡龙色甜品店，吃甜品点亮茶匙（首页卡片梦幻粉彩）
  · 星星蛇：夜空连星座

操作：
  菜单：← → ↑ ↓ 切换主题，空格/回车开始，ESC 退出
  游戏中：方向键/WASD 控制，鼠标点击跟随
         空格暂停，R 重开，ESC 或点"返回首页"回到菜单
==========================================================
"""

import math
import random
import time
import tkinter as tk
import tkinter.font as tkfont
from collections import deque

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageTk

try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass


# ==================== 全局参数 ====================
SS = 2

W, H = 1040, 700
MARGIN = 16

SNAKE_SPEED    = 160
TURN_SPEED     = math.radians(720)
INIT_BODY_LEN  = 170
GROW_PER_FOOD  = 26
BODY_THICKNESS = 24
FOOD_SCORE     = 10
FOOD_RADIUS    = 14

CONSTELLATION_SIZE = 5

ACCENT        = "#FFC766"
ACCENT_GLOW   = (255, 199, 102)
ACCENT_TEXT   = "#FFF3D6"
QUIT_COLOR    = "#FFA575"
QUIT_COLOR_BG = (60, 32, 20)
TEXT          = "#E8E8F0"
TEXT_DIM      = "#7A7A96"
CARD_BG       = (20, 20, 36)
CARD_EDGE     = (44, 44, 72)

FLOWER_COLORS = [
    (255, 120, 160), (255, 190, 90), (200, 130, 230),
    (255, 230, 120), (130, 200, 240), (255, 160, 200),
]

FLOWER_VARIANTS = [
    {"name": "rose",         "petal": (222, 78, 100),  "petal2": (172, 40, 62),  "center": (255, 218, 200)},
    {"name": "sakura",       "petal": (255, 182, 200), "petal2": (240, 138, 165),"center": (255, 230, 235)},
    {"name": "peach",        "petal": (255, 155, 175), "petal2": (235, 115, 140),"center": (255, 220, 200)},
    {"name": "chinese_rose", "petal": (235, 100, 140), "petal2": (200, 65, 105), "center": (255, 215, 220)},
    {"name": "lily",         "petal": (255, 250, 240), "petal2": (240, 225, 200),"center": (255, 210, 120)},
    {"name": "daisy",        "petal": (255, 255, 250), "petal2": (240, 240, 235),"center": (255, 210, 80)},
]

DESSERTS = [
    {"name": "草莓蛋糕",     "kind": "cake",     "color": (255, 130, 160), "accent": (255, 205, 220)},
    {"name": "巧克力甜甜圈", "kind": "donut",    "color": (168, 102, 68),  "accent": (240, 200, 160)},
    {"name": "抹茶马卡龙",   "kind": "macaron",  "color": (132, 198, 122), "accent": (228, 245, 210)},
    {"name": "蓝莓冰淇淋",   "kind": "icecream", "color": (150, 165, 232), "accent": (222, 228, 252)},
    {"name": "芒果布丁",     "kind": "pudding",  "color": (255, 192, 82),  "accent": (255, 233, 178)},
    {"name": "葡萄果冻",     "kind": "jelly",    "color": (190, 140, 220), "accent": (235, 215, 248)},
]

THEME_NAMES = ["音符蛇", "花园蛇", "甜品蛇", "星星蛇"]

THEME_ART = {
    "音符蛇": {
        "c_head": "#FFFFFF", "c1": "#FCFCFC", "c2": "#EEEEEE", "c3": "#C8C8C8",
        "hint":   "#5A4A6A",
        "hud_bg": (252, 248, 238),
        "hud_outline": (150, 130, 180),
    },
    "花园蛇": {
        "c_head": "#CCF2E2", "c1": "#A8E8CC", "c2": "#7CD2AC", "c3": "#4FB08E",
        "hint":   "#266A58",
        "hud_bg": (250, 255, 252),
        "hud_outline": (130, 200, 175),
    },
    "甜品蛇": {
        "c_head": "#FFFFFF", "c1": "#FFFDF9", "c2": "#FFF3E4", "c3": "#F3DCC0",
        "hint":   "#8A5A3A",
        "hud_bg": (255, 252, 246),
        "hud_outline": (225, 190, 150),
    },
    "星星蛇": {
        "c_head": "#F0F5FF", "c1": "#D8E4FF", "c2": "#A8BCE8", "c3": "#7088B8",
        "hint":   "#C8D8F8",
        "hud_bg": (28, 38, 68),
        "hud_outline": (100, 130, 200),
    },
}


# ==================== 工具 ====================
def _hex(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _lerp(c1, c2, t):
    if t <= 0: return c1
    if t >= 1: return c2
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def _resample(name):
    if hasattr(Image, "Resampling"):
        return getattr(Image.Resampling, name)
    return getattr(Image, name)


def _draw_star_shape(d, cx, cy, r, color, rot=0.0, points=5):
    inner = r * 0.42
    pts = []
    for i in range(points * 2):
        ang = -math.pi / 2 + i * math.pi / points + rot
        rr = r if i % 2 == 0 else inner
        pts.append((cx + math.cos(ang) * rr,
                    cy + math.sin(ang) * rr))
    d.polygon(pts, fill=color)


def _draw_drop_shape(d, cx, cy, r, color):
    d.ellipse([cx - r * 0.72, cy - r * 0.72,
               cx + r * 0.72, cy + r * 0.72], fill=color)
    d.polygon([
        (cx - r * 0.58, cy + r * 0.30),
        (cx + r * 0.58, cy + r * 0.30),
        (cx, cy + r * 1.35),
    ], fill=color)


# ==================== 蛇 ====================
class Snake:
    def __init__(self, x, y, angle):
        self.x, self.y = x, y
        self.angle = angle
        self.speed = SNAKE_SPEED
        self.max_path_len = INIT_BODY_LEN

        dx, dy = math.cos(angle), math.sin(angle)
        pts, total = [], 0.0
        while total < INIT_BODY_LEN:
            pts.append((x - dx * total, y - dy * total))
            total += 3.0
        self.path = deque(pts)
        self.total_path_len = total

    def rotate_towards(self, target, dt):
        diff = (target - self.angle + math.pi) % (2 * math.pi) - math.pi
        step = TURN_SPEED * dt
        if abs(diff) <= step:
            self.angle = target
        else:
            self.angle += math.copysign(step, diff)

    def move(self, dt):
        dx = math.cos(self.angle) * self.speed * dt
        dy = math.sin(self.angle) * self.speed * dt
        self.x += dx
        self.y += dy

        self.path.appendleft((self.x, self.y))
        self.total_path_len += math.hypot(dx, dy)

        while (self.total_path_len > self.max_path_len + 22
               and len(self.path) > 1):
            old = self.path.pop()
            new_old = self.path[-1]
            self.total_path_len -= math.hypot(old[0] - new_old[0],
                                              old[1] - new_old[1])

    def body_points(self, spacing=2):
        pts = [(self.x, self.y)]
        path = list(self.path)
        if len(path) < 2:
            return pts
        next_t, acc = spacing, 0.0
        for i in range(len(path) - 1):
            p0, p1 = path[i], path[i + 1]
            seg = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
            if seg <= 0:
                continue
            end = acc + seg
            while next_t <= end:
                t = (next_t - acc) / seg
                pts.append((p0[0] + (p1[0] - p0[0]) * t,
                            p0[1] + (p1[1] - p0[1]) * t))
                next_t += spacing
                if len(pts) > 2200:
                    return pts
            acc = end
        return pts

    def hits_self(self):
        head_r = BODY_THICKNESS * 0.30
        skip = BODY_THICKNESS * 2.8
        acc = 0.0
        path = list(self.path)
        for i in range(len(path) - 1):
            p0, p1 = path[i], path[i + 1]
            acc += math.hypot(p1[0] - p0[0], p1[1] - p0[1])
            if acc < skip:
                continue
            if math.hypot(p1[0] - self.x, p1[1] - self.y) < head_r:
                return True
        return False


# ==================== 游戏 ====================
class Game:
    def __init__(self, root):
        self.root = root
        self.root.title("贪吃蛇 · 主题版")
        self.root.configure(bg="#0A0A14")
        self.root.resizable(False, False)

        self.state = "menu"
        self.selected_idx = 0
        self.theme_name = THEME_NAMES[0]

        self.score = 0
        self.target_angle = 0.0
        self.last_tick = time.perf_counter()
        self.photo = None

        self.follow_mouse = False
        self.mouse_x = 0
        self.mouse_y = 0

        self.particles = []

        self.constellation_points = []
        self.constellations = []
        self.extra_stars = []

        self.spoons_lit = [False] * len(DESSERTS)

        self.card_bounds = []
        self.start_btn_bounds = None
        self.menu_quit_btn_bounds = None
        self.restart_btn_bounds = None
        self.quit_btn_bounds = None
        self.over_restart_btn_bounds = None

        self._pick_font()
        self._build_ui()
        self._new_snake()
        self._build_bg()

        self.root.bind("<KeyPress>", self.on_press)
        self.root.bind("<Button-1>", self.on_click)
        self.root.bind("<Motion>", self.on_motion)
        self.root.focus_force()

        self.tick()

    # ---------- 字体 ----------
    def _pick_font(self):
        families = set(tkfont.families(self.root))
        for c in ("Microsoft YaHei UI", "微软雅黑", "PingFang SC",
                  "Hiragino Sans GB", "Noto Sans CJK SC",
                  "Source Han Sans SC", "WenQuanYi Micro Hei"):
            if c in families:
                self.family = c
                return
        self.family = "TkDefaultFont"

    def _font(self, size, bold=False):
        for name in (("msyhbd.ttc" if bold else "msyh.ttc"),
                     "msyhbd.ttc", "msyh.ttc",
                     "simhei.ttf", "PingFang.ttc",
                     "arial.ttf"):
            try:
                return ImageFont.truetype(name, size)
            except Exception:
                continue
        return ImageFont.load_default()

    # ---------- UI ----------
    def _build_ui(self):
        wrap = tk.Frame(self.root, bg="#0A0A14")
        wrap.pack(padx=14, pady=14)
        frame = tk.Frame(wrap, bg="#2A2A48")
        frame.pack()
        self.canvas = tk.Canvas(frame, width=W, height=H,
                                highlightthickness=0, bd=0, bg="#0B0B16")
        self.canvas.pack(padx=2, pady=2)
        self.img_id = self.canvas.create_image(0, 0, anchor="nw")
        self.render_buf = Image.new("RGBA", (W * SS, H * SS))

    # ---------- 背景 ----------
    def _build_bg(self):
        Wb, Hb = W * SS, H * SS
        theme = self.theme_name

        if theme == "音符蛇":
            img = Image.new("RGBA", (Wb, Hb), (250, 246, 235, 255))
            d = ImageDraw.Draw(img)
            line_col = (85, 82, 92, 130)
            line_gap = 12 * SS
            group_gap = 110 * SS
            y = 40 * SS
            while y + 4 * line_gap < Hb:
                for i in range(5):
                    ly = y + i * line_gap
                    d.line([(24 * SS, ly), (Wb - 24 * SS, ly)],
                           fill=line_col, width=max(1, SS))
                cx = 46 * SS
                cy = y + 2 * line_gap
                d.ellipse([cx - 5 * SS, cy - 10 * SS,
                           cx + 5 * SS, cy + 10 * SS],
                          outline=(90, 80, 100, 110), width=SS)
                y += 5 * line_gap + group_gap
            for _ in range(20):
                x = random.randint(int(40 * SS), int(Wb - 40 * SS))
                y_g = random.randint(int(40 * SS), int(Hb - 40 * SS))
                r = random.randint(2 * SS, 4 * SS)
                d.ellipse([x - r, y_g - r * 0.7, x + r, y_g + r * 0.7],
                          fill=(90, 80, 100, 60))
            for i in range(90 * SS):
                a = int(45 * (1 - i / (90 * SS)) ** 1.6)
                if a <= 0:
                    continue
                d.rectangle([i, i, Wb - 1 - i, Hb - 1 - i],
                            outline=(0, 0, 0, a), width=1)
            self.bg_big = img

        elif theme == "花园蛇":
            img = Image.new("RGBA", (Wb, Hb), (242, 234, 218, 255))
            d = ImageDraw.Draw(img)

            for i in range(Hb):
                t = i / Hb
                col = (int(246 - 8 * t), int(238 - 8 * t), int(224 - 8 * t), 255)
                d.line([(0, i), (Wb, i)], fill=col, width=1)

            random.seed(7)
            for _ in range(900):
                x = random.randint(0, Wb)
                y = random.randint(0, Hb)
                r = random.randint(1 * SS, 3 * SS)
                sh = random.randint(-14, 6)
                d.ellipse([x - r, y - r, x + r, y + r],
                          fill=(242 + sh, 234 + sh, 218 + sh, 140))

            for _ in range(80):
                x = random.randint(0, Wb)
                y = random.randint(0, Hb)
                r = random.randint(2 * SS, 5 * SS)
                d.ellipse([x - r, y - r, x + r, y + r],
                          fill=(226, 218, 200, 130))

            def draw_grass(x, y, length, color, width=SS):
                for _ in range(random.randint(2, 4)):
                    lean = random.randint(-4, 4) * SS
                    l = length + random.randint(-4 * SS, 4 * SS)
                    d.line([(x, y), (x + lean, y - l)],
                           fill=color, width=width)

            grass_col = (110, 205, 175, 230)
            grass_col2 = (86, 188, 158, 220)

            for _ in range(100):
                x = random.randint(0, Wb)
                y = random.randint(8 * SS, 30 * SS)
                draw_grass(x, y, random.randint(10 * SS, 20 * SS), grass_col)
            for _ in range(100):
                x = random.randint(0, Wb)
                y = Hb - random.randint(8 * SS, 30 * SS)
                draw_grass(x, y, -random.randint(-20 * SS, -10 * SS), grass_col)
            for _ in range(55):
                x = random.randint(8 * SS, 30 * SS)
                y = random.randint(0, Hb)
                d.line([(x, y), (x + random.randint(8 * SS, 16 * SS),
                                 y + random.randint(-6 * SS, 6 * SS))],
                       fill=grass_col2, width=SS)
            for _ in range(55):
                x = Wb - random.randint(8 * SS, 30 * SS)
                y = random.randint(0, Hb)
                d.line([(x, y), (x - random.randint(8 * SS, 16 * SS),
                                 y + random.randint(-6 * SS, 6 * SS))],
                       fill=grass_col2, width=SS)

            corners = [(0, 0), (Wb, 0), (0, Hb), (Wb, Hb)]
            for ccx, ccy in corners:
                for _ in range(38):
                    x = ccx + random.randint(-80 * SS, 80 * SS)
                    y = ccy + random.randint(-80 * SS, 80 * SS)
                    draw_grass(x, y, random.randint(10 * SS, 24 * SS),
                               grass_col2)

            for i in range(60 * SS):
                a = int(22 * (1 - i / (60 * SS)) ** 1.6)
                if a <= 0:
                    continue
                d.rectangle([i, i, Wb - 1 - i, Hb - 1 - i],
                            outline=(0, 0, 0, a), width=1)
            self.bg_big = img

        elif theme == "甜品蛇":
            img = Image.new("RGBA", (Wb, Hb), (255, 244, 248, 255))
            d = ImageDraw.Draw(img)

            for i in range(Hb):
                t = i / Hb
                r = int(255 - 8 * t)
                g = int(240 + 12 * t)
                b = int(246 + 6 * t)
                d.line([(0, i), (Wb, i)], fill=(r, g, b, 255), width=1)

            random.seed(1073)
            blob_layer = Image.new("RGBA", (Wb, Hb), (0, 0, 0, 0))
            bd = ImageDraw.Draw(blob_layer)
            blob_cols = [
                (255, 200, 220, 90),
                (200, 230, 255, 85),
                (215, 250, 220, 80),
                (255, 235, 200, 85),
                (235, 210, 255, 80),
            ]
            for _ in range(9):
                bx = random.randint(int(-60 * SS), int(Wb + 60 * SS))
                by = random.randint(int(-60 * SS), int(Hb + 60 * SS))
                br = random.randint(110 * SS, 230 * SS)
                col = random.choice(blob_cols)
                bd.ellipse([bx - br, by - br, bx + br, by + br], fill=col)
            blob_layer = blob_layer.filter(
                ImageFilter.GaussianBlur(radius=32 * SS))
            img.alpha_composite(blob_layer)
            d = ImageDraw.Draw(img)

            step = 42 * SS
            r1 = 2.0 * SS
            r2 = 1.3 * SS
            for gy in range(0, Hb + step, step):
                for gx in range(0, Wb + step, step):
                    d.ellipse([gx - r1, gy - r1, gx + r1, gy + r1],
                              fill=(255, 195, 215, 120))
                    ox = gx + step // 2
                    oy = gy + step // 2
                    if ox < Wb and oy < Hb:
                        d.ellipse([ox - r2, oy - r2, ox + r2, oy + r2],
                                  fill=(185, 215, 240, 110))

            for _ in range(34):
                sx = random.randint(0, Wb)
                sy = random.randint(0, Hb)
                sr = random.randint(2 * SS, 5 * SS)
                a = random.randint(120, 200)
                d.line([(sx - sr, sy), (sx + sr, sy)],
                       fill=(255, 255, 255, a), width=1)
                d.line([(sx, sy - sr), (sx, sy + sr)],
                       fill=(255, 255, 255, a), width=1)

            for i in range(70 * SS):
                a = int(20 * (1 - i / (70 * SS)) ** 1.8)
                if a <= 0:
                    continue
                d.rectangle([i, i, Wb - 1 - i, Hb - 1 - i],
                            outline=(180, 140, 160, a), width=1)

            self.bg_big = img

        else:  # 星星蛇
            img = Image.new("RGBA", (Wb, Hb), (8, 12, 32, 255))
            d = ImageDraw.Draw(img)
            for i in range(Hb):
                t = i / Hb
                col = (int(6 + 14 * t), int(10 + 12 * t), int(28 + 20 * t), 255)
                d.line([(0, i), (Wb, i)], fill=col, width=1)
            random.seed(99)
            for _ in range(180):
                x = random.randint(0, Wb)
                y = random.randint(0, Hb)
                sz = random.choice([1 * SS, 1 * SS, 2 * SS, 2 * SS, 3 * SS])
                a = random.randint(110, 230)
                d.ellipse([x - sz, y - sz, x + sz, y + sz],
                          fill=(255, 255, 255, a))
                if sz >= 3 * SS:
                    d.ellipse([x - sz * 2, y - sz * 2,
                               x + sz * 2, y + sz * 2],
                              fill=(200, 220, 255, 40))
            for cons in self.constellations:
                if len(cons) < 2:
                    continue
                cpts = [(x * SS, y * SS) for x, y in cons]
                for i in range(len(cpts) - 1):
                    d.line([cpts[i], cpts[i + 1]],
                           fill=(160, 195, 255, 90), width=2 * SS)
                for (px, py) in cpts:
                    for k in range(10, 0, -1):
                        a = int(120 * (1 - k / 10))
                        if a <= 0:
                            continue
                        rr = k * SS
                        d.ellipse([px - rr, py - rr, px + rr, py + rr],
                                  fill=(200, 220, 255, a))
                    d.ellipse([px - 4 * SS, py - 4 * SS,
                               px + 4 * SS, py + 4 * SS],
                              fill=(255, 255, 255, 255))
            for (x, y) in self.extra_stars:
                px, py = x * SS, y * SS
                for k in range(8, 0, -1):
                    a = int(110 * (1 - k / 8))
                    if a <= 0:
                        continue
                    rr = k * SS
                    d.ellipse([px - rr, py - rr, px + rr, py + rr],
                              fill=(255, 235, 180, a))
                d.ellipse([px - 3 * SS, py - 3 * SS,
                           px + 3 * SS, py + 3 * SS],
                          fill=(255, 250, 220, 255))
            self.bg_big = img

    # ---------- 新游戏 ----------
    def _new_snake(self):
        self.snake = Snake(W / 2 - 100, H / 2, 0)
        self.target_angle = 0.0
        self.follow_mouse = False
        self.score = 0
        self.particles = []
        self.constellation_points = []
        self.spoons_lit = [False] * len(DESSERTS)
        self.food = self._place_food()
        self.last_tick = time.perf_counter()

    def _place_food(self):
        theme = self.theme_name
        if theme == "音符蛇":
            kinds = ["quarter", "eighth", "beamed"]
        elif theme == "花园蛇":
            kinds = ["flower", "grass"]
        elif theme == "甜品蛇":
            kinds = ["dessert"]
        else:
            kinds = ["star"]

        m = 70
        for _ in range(160):
            fx = random.uniform(m, W - m)
            fy = random.uniform(m, H - m)
            ok = True
            for px, py in self.snake.path:
                if math.hypot(px - fx, py - fy) < 90:
                    ok = False
                    break
            if ok:
                d = {"x": fx, "y": fy, "kind": random.choice(kinds)}
                if theme == "甜品蛇":
                    d["variant"] = random.randint(0, len(DESSERTS) - 1)
                elif theme == "花园蛇" and d["kind"] == "flower":
                    d["variant"] = random.randint(0, len(FLOWER_VARIANTS) - 1)
                return d

        d = {"x": random.uniform(m, W - m),
             "y": random.uniform(m, H - m),
             "kind": random.choice(kinds)}
        if theme == "甜品蛇":
            d["variant"] = random.randint(0, len(DESSERTS) - 1)
        elif theme == "花园蛇" and d["kind"] == "flower":
            d["variant"] = random.randint(0, len(FLOWER_VARIANTS) - 1)
        return d

    # ---------- 输入 ----------
    def on_press(self, e):
        k = e.keysym

        if self.state == "menu":
            n = len(THEME_NAMES)
            if k in ("Left", "a", "A"):
                self.selected_idx = (self.selected_idx - 1) % n
                self.theme_name = THEME_NAMES[self.selected_idx]
                self._build_bg()
            elif k in ("Right", "d", "D"):
                self.selected_idx = (self.selected_idx + 1) % n
                self.theme_name = THEME_NAMES[self.selected_idx]
                self._build_bg()
            elif k in ("Up", "w", "W"):
                self.selected_idx = (self.selected_idx - 2) % n
                self.theme_name = THEME_NAMES[self.selected_idx]
                self._build_bg()
            elif k in ("Down", "s", "S"):
                self.selected_idx = (self.selected_idx + 2) % n
                self.theme_name = THEME_NAMES[self.selected_idx]
                self._build_bg()
            elif k in ("space", "Return", "KP_Enter"):
                self._start_game()
            elif k == "Escape":
                self.root.destroy()
            return

        if k == "Escape":
            self._back_to_menu()
            return
        if k in ("r", "R"):
            self._start_game()
            return

        if k == "space":
            if self.state == "over":
                self._start_game()
            elif self.state == "playing":
                self.state = "paused"
            elif self.state == "paused":
                self.state = "playing"
                self.last_tick = time.perf_counter()
            return

        if self.state != "playing":
            return

        moved = False
        if k in ("Up", "w", "W"):
            self.target_angle = -math.pi / 2; moved = True
        elif k in ("Down", "s", "S"):
            self.target_angle = math.pi / 2; moved = True
        elif k in ("Left", "a", "A"):
            self.target_angle = math.pi; moved = True
        elif k in ("Right", "d", "D"):
            self.target_angle = 0.0; moved = True
        if moved:
            self.follow_mouse = False

    def on_motion(self, e):
        self.mouse_x = e.x
        self.mouse_y = e.y

    def on_click(self, e):
        x, y = e.x, e.y

        if self.state == "menu":
            for i, (x0, y0, x1, y1) in enumerate(self.card_bounds):
                if x0 <= x <= x1 and y0 <= y <= y1:
                    self.selected_idx = i
                    self.theme_name = THEME_NAMES[i]
                    self._build_bg()
                    return
            if self.start_btn_bounds:
                x0, y0, x1, y1 = self.start_btn_bounds
                if x0 <= x <= x1 and y0 <= y <= y1:
                    self._start_game()
                    return
            if self.menu_quit_btn_bounds:
                x0, y0, x1, y1 = self.menu_quit_btn_bounds
                if x0 <= x <= x1 and y0 <= y <= y1:
                    self.root.destroy()
                    return
            return

        if self.state == "over":
            if self.over_restart_btn_bounds:
                x0, y0, x1, y1 = self.over_restart_btn_bounds
                if x0 <= x <= x1 and y0 <= y <= y1:
                    self._start_game()
                    return

        if self.state in ("playing", "paused", "over"):
            if self.restart_btn_bounds:
                x0, y0, x1, y1 = self.restart_btn_bounds
                if x0 <= x <= x1 and y0 <= y <= y1:
                    self._start_game()
                    return
            if self.quit_btn_bounds:
                x0, y0, x1, y1 = self.quit_btn_bounds
                if x0 <= x <= x1 and y0 <= y <= y1:
                    self._back_to_menu()
                    return

        if self.state == "playing":
            self.mouse_x = x
            self.mouse_y = y
            dx = x - self.snake.x
            dy = y - self.snake.y
            if dx * dx + dy * dy > 64:
                self.target_angle = math.atan2(dy, dx)
                self.follow_mouse = True

    def _start_game(self):
        self.theme_name = THEME_NAMES[self.selected_idx]
        self.state = "playing"
        self.constellation_points = []
        self.constellations = []
        self.extra_stars = []
        self._build_bg()
        self._new_snake()

    def _back_to_menu(self):
        """退出当前场景，回到首页菜单。"""
        self.state = "menu"
        self.follow_mouse = False
        self.particles = []
        self.theme_name = THEME_NAMES[self.selected_idx]
        self._build_bg()

    # ---------- 更新 ----------
    def _update(self, dt):
        if self.state != "playing":
            self._update_particles(dt)
            return

        if self.follow_mouse:
            dx = self.mouse_x - self.snake.x
            dy = self.mouse_y - self.snake.y
            if dx * dx + dy * dy > 36:
                self.target_angle = math.atan2(dy, dx)

        self.snake.rotate_towards(self.target_angle, dt)
        self.snake.move(dt)
        self._update_particles(dt)

        if (self.snake.x < MARGIN or self.snake.x > W - MARGIN or
                self.snake.y < MARGIN or self.snake.y > H - MARGIN):
            self.state = "over"
            return

        if self.snake.hits_self():
            self.state = "over"
            return

        if self.food:
            fx, fy = self.food["x"], self.food["y"]
            if math.hypot(fx - self.snake.x, fy - self.snake.y) < 28:
                self.snake.max_path_len += GROW_PER_FOOD
                self._spawn_effect(fx, fy)

                if self.theme_name == "甜品蛇":
                    variant = self.food.get("variant", 0)
                    self.spoons_lit[variant] = True
                    self.score += FOOD_SCORE
                elif self.theme_name == "星星蛇":
                    self.score += FOOD_SCORE
                    self.constellation_points.append((fx, fy))
                    if len(self.constellation_points) >= CONSTELLATION_SIZE:
                        self.constellations.append(list(self.constellation_points))
                        self.constellation_points = []
                        self.extra_stars.append(
                            (random.uniform(60, W - 60),
                             random.uniform(60, H - 60)))
                        self._build_bg()
                else:
                    self.score += FOOD_SCORE

                self.food = self._place_food()

    def _update_particles(self, dt):
        alive = []
        for p in self.particles:
            p["life"] -= dt
            if p["life"] <= 0:
                continue
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt

            if p["type"] == "note":
                p["vy"] *= 0.985
                p["vx"] *= 0.985
            elif p["type"] == "petal":
                p["vy"] += 90 * dt
                p["vx"] *= 0.98
                p["rot"] += p["rot_speed"] * dt
                p["vx"] += math.sin(p["life"] * 6) * 22 * dt
            elif p["type"] == "star":
                p["vx"] *= 0.96
                p["vy"] *= 0.96
                p["rot"] += p["rot_speed"] * dt
            elif p["type"] == "sprinkle":
                p["vy"] += 260 * dt
                p["vx"] *= 0.99
                p["rot"] += p["rot_speed"] * dt

            alive.append(p)
        self.particles = alive

    def _spawn_effect(self, x, y):
        theme = self.theme_name

        if theme == "音符蛇":
            for i in range(8):
                ang = random.uniform(-math.pi * 0.85, -math.pi * 0.15)
                sp = random.uniform(50, 110)
                self.particles.append({
                    "type": "note",
                    "x": x, "y": y,
                    "vx": math.cos(ang) * sp,
                    "vy": math.sin(ang) * sp,
                    "life": 1.6, "max_life": 1.6,
                    "kind": random.choice(["quarter", "eighth", "beamed"]),
                    "size": random.uniform(0.7, 1.2),
                })

        elif theme == "花园蛇":
            for i in range(11):
                ang = random.uniform(0, 2 * math.pi)
                sp = random.uniform(60, 150)
                self.particles.append({
                    "type": "petal",
                    "x": x, "y": y,
                    "vx": math.cos(ang) * sp,
                    "vy": math.sin(ang) * sp - 40,
                    "life": 1.7, "max_life": 1.7,
                    "color": random.choice(FLOWER_COLORS),
                    "size": random.uniform(4, 7) * SS,
                    "rot": random.uniform(0, 2 * math.pi),
                    "rot_speed": random.uniform(-4, 4),
                })
            for i in range(6):
                ang = random.uniform(0, 2 * math.pi)
                sp = random.uniform(80, 180)
                self.particles.append({
                    "type": "petal",
                    "x": x, "y": y,
                    "vx": math.cos(ang) * sp,
                    "vy": math.sin(ang) * sp - 60,
                    "life": 1.3, "max_life": 1.3,
                    "color": (110, 200, 160),
                    "size": random.uniform(3, 5) * SS,
                    "rot": random.uniform(0, 2 * math.pi),
                    "rot_speed": random.uniform(-6, 6),
                })

        elif theme == "甜品蛇":
            for i in range(16):
                ang = random.uniform(0, 2 * math.pi)
                sp = random.uniform(60, 180)
                self.particles.append({
                    "type": "sprinkle",
                    "x": x, "y": y,
                    "vx": math.cos(ang) * sp,
                    "vy": math.sin(ang) * sp - 50,
                    "life": 1.4, "max_life": 1.4,
                    "size": random.uniform(3, 6) * SS,
                    "rot": random.uniform(0, math.pi),
                    "rot_speed": random.uniform(-9, 9),
                    "color": random.choice([
                        (255, 130, 160), (255, 200, 90), (140, 200, 240),
                        (185, 150, 230), (140, 210, 160), (255, 170, 120),
                    ]),
                })

        else:  # 星星蛇
            for i in range(12):
                ang = random.uniform(0, 2 * math.pi)
                sp = random.uniform(60, 160)
                self.particles.append({
                    "type": "star",
                    "x": x, "y": y,
                    "vx": math.cos(ang) * sp,
                    "vy": math.sin(ang) * sp,
                    "life": 1.5, "max_life": 1.5,
                    "size": random.uniform(4, 9) * SS,
                    "rot": random.uniform(0, math.pi),
                    "rot_speed": random.uniform(-3, 3),
                    "color": random.choice([
                        (255, 245, 200), (255, 220, 150),
                        (220, 235, 255), (255, 255, 230),
                    ]),
                })

    # ---------- 渲染 ----------
    def _render(self):
        if self.state == "menu":
            img = self._render_menu()
        else:
            img = self._render_game()
        self.photo = ImageTk.PhotoImage(img)
        self.canvas.itemconfig(self.img_id, image=self.photo)

    # ---------- 菜单 ----------
    def _render_menu(self):
        Wb, Hb = W * SS, H * SS
        img = Image.new("RGBA", (Wb, Hb), (11, 11, 22, 255))
        d = ImageDraw.Draw(img)

        cell = 60 * SS
        for x in range(0, Wb, cell):
            d.line([(x, 0), (x, Hb)], fill=(17, 17, 34, 255), width=SS)
        for y in range(0, Hb, cell):
            d.line([(0, y), (Wb, y)], fill=(17, 17, 34, 255), width=SS)

        cx = Wb / 2
        title = "贪 吃 蛇"
        title_font = self._font(56 * SS, bold=True)
        for k in range(10, 0, -1):
            a = int(70 * (1 - k / 10))
            if a <= 0:
                continue
            d.text((cx, 56 * SS), title, fill=ACCENT_GLOW + (a,),
                   anchor="mm", font=title_font)
        d.text((cx, 56 * SS), title, fill=ACCENT, anchor="mm",
               font=title_font)
        d.text((cx, 96 * SS), "选择你的主题",
               fill=TEXT_DIM, anchor="mm", font=self._font(15 * SS))

        cols = 2
        card_w, card_h = 360, 220
        gap = 34
        gw = cols * card_w + (cols - 1) * gap
        gh = 2 * card_h + gap
        sx = (Wb - gw * SS) / 2
        sy = 130 * SS

        self.card_bounds = []

        for i, name in enumerate(THEME_NAMES):
            col = i % cols
            row = i // cols
            x = sx + col * (card_w + gap) * SS
            y = sy + row * (card_h + gap) * SS
            cw, ch = card_w * SS, card_h * SS
            self.card_bounds.append((x / SS, y / SS,
                                     (x + cw) / SS, (y + ch) / SS))

            selected = (i == self.selected_idx)
            if selected:
                for k in range(8 * SS, 0, -SS):
                    a = int(95 * (1 - k / (8 * SS)))
                    if a <= 0:
                        continue
                    d.rounded_rectangle(
                        [x - k, y - k, x + cw + k, y + ch + k],
                        radius=(22 + k // SS) * SS,
                        outline=ACCENT_GLOW + (a,), width=SS)
                edge, edge_w = ACCENT, 3 * SS
            else:
                edge, edge_w = CARD_EDGE, 2 * SS

            d.rounded_rectangle([x, y, x + cw, y + ch],
                                radius=22 * SS, fill=CARD_BG,
                                outline=edge, width=edge_w)

            # ★ 传入 img（Image 对象），让甜品蛇预览能在内部用 alpha_composite
            self._draw_theme_preview(img, x, y, cw, ch, name)

            # 重新创建 d，因为 preview 内部可能就地修改了 img
            d = ImageDraw.Draw(img)

            d.text((x + cw / 2, y + ch - 26 * SS), name,
                   fill=(255, 255, 255) if selected else TEXT_DIM,
                   anchor="mm",
                   font=self._font(19 * SS, bold=selected))

        d = ImageDraw.Draw(img)

        by_base = sy + gh * SS + 30 * SS
        btn_h = 54

        start_w = 240
        start_x0 = (Wb - start_w * SS) / 2
        start_y0 = by_base
        start_x1 = start_x0 + start_w * SS
        start_y1 = start_y0 + btn_h * SS
        self.start_btn_bounds = (start_x0 / SS, start_y0 / SS,
                                 start_x1 / SS, start_y1 / SS)

        for k in range(9 * SS, 0, -SS):
            a = int(95 * (1 - k / (9 * SS)))
            if a <= 0:
                continue
            d.rounded_rectangle(
                [start_x0 - k, start_y0 - k, start_x1 + k, start_y1 + k],
                radius=(16 + k // SS) * SS,
                outline=ACCENT_GLOW + (a,), width=SS)

        d.rounded_rectangle([start_x0, start_y0, start_x1, start_y1],
                            radius=16 * SS, fill=(64, 46, 20, 255),
                            outline=ACCENT, width=2 * SS)
        d.text(((start_x0 + start_x1) / 2, (start_y0 + start_y1) / 2),
               "开 始 游 戏", fill=ACCENT_TEXT, anchor="mm",
               font=self._font(21 * SS, bold=True))

        quit_w = 120
        quit_h = 54
        quit_x0 = start_x1 + 24 * SS
        quit_y0 = start_y0
        quit_x1 = quit_x0 + quit_w * SS
        quit_y1 = quit_y0 + quit_h * SS
        self.menu_quit_btn_bounds = (quit_x0 / SS, quit_y0 / SS,
                                     quit_x1 / SS, quit_y1 / SS)

        self._draw_hud_button(
            d, quit_x0, quit_y0, quit_x1, quit_y1,
            "退 出", "quit", size=18)

        d.text((cx, start_y1 + 24 * SS),
               "← → ↑ ↓  切换主题      空格 / 回车  开始      ESC  退出",
               fill=TEXT_DIM, anchor="mm", font=self._font(13 * SS))

        return img.resize((W, H), _resample("LANCZOS"))

    def _draw_hud_button(self, d, x0, y0, x1, y1, label, style="restart", size=14):
        if style == "restart":
            fill = (233, 246, 243)
            outline = (120, 185, 165)
            text_col = (30, 90, 72)
        else:
            fill = (252, 238, 238)
            outline = (222, 162, 162)
            text_col = (150, 60, 60)

        d.rounded_rectangle([x0 + 1, y0 + 2, x1 + 1, y1 + 2],
                            radius=11, fill=(0, 0, 0, 40))
        d.rounded_rectangle([x0, y0, x1, y1], radius=11,
                            fill=fill, outline=outline, width=1)
        d.line([(x0 + 6, y0 + 1), (x1 - 6, y0 + 1)],
               fill=(255, 255, 255, 180), width=1)
        d.text(((x0 + x1) / 2, (y0 + y1) / 2), label,
               fill=text_col, anchor="mm",
               font=self._font(size, bold=True))

    def _draw_theme_preview(self, img, x, y, cw, ch, name):
        """在 img（Image 对象）上绘制主题缩略图。
        甜品蛇分支使用独立图层 + alpha_composite，避免半透明像素透出深色背景形成黑圈。"""
        d = ImageDraw.Draw(img)
        art = THEME_ART[name]
        pad = 14 * SS
        px0, py0 = x + pad, y + pad
        px1, py1 = x + cw - pad, y + ch - pad - 36 * SS

        if name == "音符蛇":
            d.rounded_rectangle([px0, py0, px1, py1],
                                radius=14 * SS, fill=(250, 246, 235, 255))
            lg = 6 * SS
            y0 = py0 + 14 * SS
            for grp in range(2):
                for i in range(5):
                    ly = y0 + (i * lg) + grp * (5 * lg + 18 * SS)
                    if ly > py1 - 6 * SS:
                        continue
                    d.line([(px0 + 10 * SS, ly), (px1 - 10 * SS, ly)],
                           fill=(85, 82, 92, 130), width=SS)
            self._draw_note(d, (px1 + px0) / 2 - 46 * SS,
                            (py1 + py0) / 2 + 8 * SS,
                            "eighth", (30, 30, 35, 255),
                            size=FOOD_RADIUS * SS * 0.7)

        elif name == "花园蛇":
            d.rounded_rectangle([px0, py0, px1, py1],
                                radius=14 * SS, fill=(242, 234, 218, 255))
            random.seed(3)
            for _ in range(80):
                rx = random.randint(int(px0), int(px1))
                ry = random.randint(int(py0), int(py1))
                r = random.randint(SS, 2 * SS)
                sh = random.randint(-10, 5)
                d.ellipse([rx - r, ry - r, rx + r, ry + r],
                          fill=(242 + sh, 234 + sh, 218 + sh, 160))
            for _ in range(22):
                rx = random.randint(int(px0), int(px1))
                ry = py0 + random.randint(2 * SS, 12 * SS)
                l = random.randint(6 * SS, 12 * SS)
                d.line([(rx, ry + l), (rx + random.randint(-3, 3) * SS, ry)],
                       fill=(110, 205, 175, 230), width=SS)
            for _ in range(18):
                rx = random.randint(int(px0), int(px1))
                ry = py1 - random.randint(2 * SS, 12 * SS)
                l = random.randint(6 * SS, 12 * SS)
                d.line([(rx, ry - l), (rx + random.randint(-3, 3) * SS, ry)],
                       fill=(110, 205, 175, 230), width=SS)
            self._draw_flower_rose(
                d, px1 - 40 * SS, py1 - 40 * SS,
                FOOD_RADIUS * SS * 0.85, FLOWER_VARIANTS[0])

        elif name == "甜品蛇":
            # ★ 梦幻粉彩卡片：用独立图层分层合成，彻底避免半透明破洞
            cw_ = px1 - px0
            ch_ = py1 - py0

            # --- 第 1 层：卡片本体（不透明背景 + 渐变）---
            card = Image.new("RGBA", img.size, (0, 0, 0, 0))
            cd = ImageDraw.Draw(card)
            cd.rounded_rectangle([px0, py0, px1, py1],
                                 radius=14 * SS, fill=(255, 246, 250, 255))

            # 三段式梦幻粉彩渐变：淡粉 → 薰衣草 → 薄荷
            hgt = int(ch_)
            for i in range(hgt):
                t = i / max(1, hgt)
                if t < 0.42:
                    tt = t / 0.42
                    r = int(255 - 10 * tt)
                    g = int(220 + 18 * tt)
                    b = int(238 + 8 * tt)
                elif t < 0.72:
                    tt = (t - 0.42) / 0.30
                    r = int(245 - 8 * tt)
                    g = int(238 + 8 * tt)
                    b = int(246 + 4 * tt)
                else:
                    tt = (t - 0.72) / 0.28
                    r = int(237 - 6 * tt)
                    g = int(246 - 4 * tt)
                    b = int(250 - 10 * tt)
                cd.line([(px0, py0 + i), (px1, py0 + i)],
                        fill=(r, g, b, 255), width=1)

            # --- 第 2 层：柔光光斑 + 十字闪光 ---
            eff = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ed = ImageDraw.Draw(eff)

            random.seed(int(px0) * 31 + int(py0) * 17)
            blobs = [
                (0.18, 0.22, 62 * SS, (255, 200, 225)),
                (0.82, 0.26, 55 * SS, (205, 225, 255)),
                (0.26, 0.80, 52 * SS, (255, 235, 205)),
                (0.76, 0.74, 58 * SS, (215, 245, 225)),
                (0.50, 0.42, 72 * SS, (240, 215, 250)),
            ]
            for fx, fy, br, bc in blobs:
                bx = px0 + fx * cw_
                by = py0 + fy * ch_
                for k in range(12, 0, -1):
                    tk = k / 12
                    a = int(26 * (1 - tk))
                    if a <= 0:
                        continue
                    rr = br * (0.30 + tk * 0.90)
                    ed.ellipse([bx - rr, by - rr, bx + rr, by + rr],
                               fill=bc + (a,))

            for _ in range(28):
                sx = px0 + random.uniform(6 * SS, cw_ - 6 * SS)
                sy = py0 + random.uniform(6 * SS, ch_ - 6 * SS)
                sr = random.uniform(1.2 * SS, 2.8 * SS)
                a = random.randint(170, 230)
                ed.line([(sx - sr, sy), (sx + sr, sy)],
                        fill=(255, 255, 255, a), width=1)
                ed.line([(sx, sy - sr), (sx, sy + sr)],
                        fill=(255, 255, 255, a), width=1)
                ed.ellipse([sx - sr * 0.40, sy - sr * 0.40,
                            sx + sr * 0.40, sy + sr * 0.40],
                           fill=(255, 255, 255, a))

            card.alpha_composite(eff)

            # --- 第 3 层：甜品 + 茶匙 ---
            det = Image.new("RGBA", img.size, (0, 0, 0, 0))
            dd = ImageDraw.Draw(det)

            spoon_size = FOOD_RADIUS * SS * 0.72
            self._draw_spoon(dd, px1 - 58 * SS, py0 + 34 * SS,
                             spoon_size, DESSERTS[2], False)
            self._draw_spoon(dd, px1 - 30 * SS, py0 + 34 * SS,
                             spoon_size, DESSERTS[0], True)

            dessert_y = py1 - 26 * SS
            n_des = 4
            span = 40 * SS
            margin_x = (cw_ - n_des * span) / 2
            order = [1, 0, 3, 2]
            for i, idx in enumerate(order):
                dx = px0 + margin_x + (i + 0.5) * span
                self._draw_dessert(dd, dx, dessert_y,
                                   FOOD_RADIUS * SS * 0.65, idx)

            card.alpha_composite(det)

            # --- 圆角裁切 + 合成到主图 ---
            mask_img = Image.new("L", img.size, 0)
            ImageDraw.Draw(mask_img).rounded_rectangle(
                [px0, py0, px1, py1], radius=14 * SS, fill=255)
            card.putalpha(ImageChops.multiply(card.getchannel("A"),
                                              mask_img))
            img.alpha_composite(card)
            # ★ 重新创建 d，因为 img 已被就地修改
            d = ImageDraw.Draw(img)

        else:  # 星星蛇
            d.rounded_rectangle([px0, py0, px1, py1],
                                radius=14 * SS, fill=(10, 14, 34, 255))
            random.seed(21)
            for _ in range(35):
                sx_ = random.randint(int(px0 + 8 * SS), int(px1 - 8 * SS))
                sy_ = random.randint(int(py0 + 8 * SS), int(py1 - 8 * SS))
                ss = random.choice([SS, SS, 2 * SS, 2 * SS, 3 * SS])
                aa = random.randint(140, 240)
                d.ellipse([sx_ - ss, sy_ - ss, sx_ + ss, sy_ + ss],
                          fill=(255, 255, 255, aa))
            stx = (px1 + px0) / 2 + 46 * SS
            sty = (py1 + py0) / 2 + 8 * SS
            # 星形光晕（沿星角扩散，避免圆盘底色）
            for k in range(5, 0, -1):
                a = int(120 * (1 - k / 5))
                if a <= 0:
                    continue
                _draw_star_shape(d, stx, sty,
                                 (FOOD_RADIUS + k * 2) * SS,
                                 (255, 240, 180, a))
            _draw_star_shape(d, stx, sty, FOOD_RADIUS * SS * 1.16,
                             (220, 145, 35, 255))
            _draw_star_shape(d, stx, sty, FOOD_RADIUS * SS * 1.02,
                             (255, 195, 70, 255))
            _draw_star_shape(d, stx, sty, FOOD_RADIUS * SS * 0.60,
                             (255, 255, 248, 255))

        # ★ 每个卡片中央的小蛇（四个主题共用）
        scx = (px1 + px0) / 2
        scy = (py1 + py0) / 2 - 10 * SS
        width = (px1 - px0) * 0.58
        n = 54
        thick = 13 * SS
        c_head = _hex(art["c_head"])
        c1 = _hex(art["c1"]); c2 = _hex(art["c2"]); c3 = _hex(art["c3"])

        pts = []
        for i in range(n):
            t = i / (n - 1)
            px = scx + (t - 0.5) * width
            py = scy + math.sin(t * math.pi * 2.0) * 9 * SS
            pts.append((px, py))

        r = thick / 2
        d.line(pts, fill=c2 + (255,), width=int(thick), joint="curve")
        tx, ty = pts[-1]
        d.ellipse([tx - r, ty - r, tx + r, ty + r], fill=c2 + (255,))
        for i in range(n):
            t = i / (n - 1)
            if t < 0.45:
                col = _lerp(c1, c2, t / 0.45)
            else:
                col = _lerp(c2, c3, (t - 0.45) / 0.55)
            x_, y_ = pts[i]
            d.ellipse([x_ - r, y_ - r, x_ + r, y_ + r], fill=col + (255,))
        d.ellipse([tx - r, ty - r, tx + r, ty + r], fill=c3 + (255,))

        hx, hy = pts[-1]
        hr = 11 * SS
        d.ellipse([hx - hr, hy - hr, hx + hr, hy + hr],
                  fill=c_head + (255,))

        pupil_col = (50, 60, 80)
        for sy_sign in (-4, 4):
            ew = 3 * SS
            d.ellipse([hx - 1 * SS - ew, hy + sy_sign * SS - ew,
                       hx - 1 * SS + ew, hy + sy_sign * SS + ew],
                      fill=(255, 255, 255, 255))
            pr = 2 * SS
            cx_p = hx + 0.5 * SS
            cy_p = hy + sy_sign * SS
            d.ellipse([cx_p - pr, cy_p - pr, cx_p + pr, cy_p + pr],
                      fill=pupil_col + (255,))
            d.ellipse([cx_p - pr * 0.7, cy_p - pr * 0.9,
                       cx_p - pr * 0.1, cy_p - pr * 0.3],
                      fill=(255, 255, 255, 240))

    # ---------- 游戏渲染 ----------
    def _render_game(self):
        self.render_buf.paste(self.bg_big)
        d = ImageDraw.Draw(self.render_buf)
        art = THEME_ART[self.theme_name]

        if self.theme_name == "星星蛇" and self.constellation_points:
            pts_ = [(px * SS, py * SS) for px, py in self.constellation_points]
            if len(pts_) >= 2:
                for i in range(len(pts_) - 1):
                    d.line([pts_[i], pts_[i + 1]],
                           fill=(180, 210, 255, 100), width=2 * SS)
            for (px, py) in pts_:
                for k in range(8, 0, -1):
                    a = int(140 * (1 - k / 8))
                    if a <= 0:
                        continue
                    rr = k * SS
                    d.ellipse([px - rr, py - rr, px + rr, py + rr],
                              fill=(220, 235, 255, a))
                d.ellipse([px - 4 * SS, py - 4 * SS,
                           px + 4 * SS, py + 4 * SS],
                          fill=(255, 255, 255, 255))

        if self.food:
            self._draw_food(d, self.food)

        pts = self.snake.body_points(spacing=2)
        if len(pts) >= 2:
            self._draw_body(d, pts, art)

        self._draw_head(d, self.snake.x * SS, self.snake.y * SS,
                        self.snake.angle, art)

        self._draw_particles(d)

        border_col = (100, 100, 130, 200)
        if self.theme_name == "星星蛇":
            border_col = (80, 110, 180, 200)
        elif self.theme_name == "甜品蛇":
            border_col = (230, 180, 200, 220)
        elif self.theme_name == "花园蛇":
            border_col = (170, 215, 195, 200)
        m = MARGIN * SS
        d.rectangle([m, m, W * SS - m, H * SS - m],
                    outline=border_col, width=2 * SS)

        img = self.render_buf.resize((W, H), _resample("LANCZOS"))
        if img.mode == "RGBA":
            flat = Image.new("RGB", (W, H), (255, 255, 255))
            flat.paste(img, (0, 0), img)
            img = flat

        d1 = ImageDraw.Draw(img)
        self._draw_hud(d1)

        if self.state == "paused":
            black = Image.new("RGB", (W, H), (0, 0, 0))
            img = Image.blend(img, black, 0.5)
            d1 = ImageDraw.Draw(img)
            d1.text((W / 2, H / 2 - 16), "已暂停", fill=ACCENT,
                    anchor="mm", font=self._font(54, bold=True))
            d1.text((W / 2, H / 2 + 46), "按空格继续",
                    fill="#B8B8CC", anchor="mm", font=self._font(19))

        if self.state == "over":
            black = Image.new("RGB", (W, H), (0, 0, 0))
            img = Image.blend(img, black, 0.62)
            d1 = ImageDraw.Draw(img)

            d1.text((W / 2, H / 2 - 130), "游戏结束",
                    fill=ACCENT, anchor="mm",
                    font=self._font(58, bold=True))
            d1.text((W / 2, H / 2 - 40),
                    f"得分  {self.score}",
                    fill="#FFFFFF", anchor="mm", font=self._font(30))

            btn_w, btn_h = 260, 62
            bx0 = (W - btn_w) / 2
            by0 = H / 2 + 30
            bx1 = bx0 + btn_w
            by1 = by0 + btn_h
            self.over_restart_btn_bounds = (bx0, by0, bx1, by1)

            self._draw_hud_button(
                d1, bx0, by0, bx1, by1, "重 新 开 始", "restart", size=24)

            d1.text((W / 2, by1 + 40),
                    "点击按钮  ·  或按 空格 / R  重新开始",
                    fill="#B8B8CC", anchor="mm",
                    font=self._font(16))

        return img

    # ---------- 蛇身 ----------
    def _draw_body(self, d, pts, art):
        n = BODY_THICKNESS * SS
        total = len(pts)
        c1 = _hex(art["c1"]); c2 = _hex(art["c2"]); c3 = _hex(art["c3"])

        def col_at(t):
            if t < 0.45:
                return _lerp(c1, c2, t / 0.45)
            return _lerp(c2, c3, (t - 0.45) / 0.55)

        bpts = [(p[0] * SS, p[1] * SS) for p in pts]
        r = n / 2

        if self.theme_name == "星星蛇":
            for layer, alpha in [(5, 30), (4, 45), (3, 60)]:
                glow_r = r + layer * SS
                for i in range(0, total, 2):
                    x, y = bpts[i]
                    d.ellipse([x - glow_r, y - glow_r, x + glow_r, y + glow_r],
                              fill=(180, 210, 255, alpha))

        if self.theme_name == "甜品蛇":
            shadow_r = r + 1.6 * SS
            for i in range(0, total, 2):
                x, y = bpts[i]
                d.ellipse([x - shadow_r, y - shadow_r,
                           x + shadow_r, y + shadow_r],
                          fill=(200, 170, 178, 65))

        d.line(bpts, fill=c2 + (255,), width=int(n), joint="curve")
        tx, ty = bpts[-1]
        d.ellipse([tx - r, ty - r, tx + r, ty + r], fill=c2 + (255,))

        for i in range(total):
            t = i / max(1, total - 1)
            color = col_at(t) + (255,)
            x, y = bpts[i]
            d.ellipse([x - r, y - r, x + r, y + r], fill=color)

        d.ellipse([tx - r, ty - r, tx + r, ty + r], fill=c3 + (255,))

    # ---------- 蛇头 ----------
    def _draw_head(self, d, cx, cy, angle, art):
        ca, sa = math.cos(angle), math.sin(angle)
        r = BODY_THICKNESS * 0.72 * SS
        c_head = _hex(art["c_head"])

        if self.theme_name == "星星蛇":
            for k in range(8, 0, -1):
                a = int(50 * (1 - k / 8))
                if a <= 0:
                    continue
                rr = r + k * SS
                d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                          fill=(180, 210, 255, a))
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c_head + (255,))
        elif self.theme_name == "甜品蛇":
            for k in range(6, 0, -1):
                a = int(40 * (1 - k / 6))
                if a <= 0:
                    continue
                rr = r + k * SS
                d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                          fill=(255, 250, 240, a))
            d.ellipse([cx - r, cy - r, cx + r, cy + r],
                      fill=c_head + (255,))
        else:
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c_head + (255,))

        eye_side = r * 0.46
        eye_fwd = r * 0.30
        eye_r = r * 0.30
        pupil_color = (50, 60, 80)
        if self.theme_name == "甜品蛇":
            pupil_color = (110, 70, 50)

        for side in (-1, 1):
            px = -sa * side
            py = ca * side
            ex = cx + ca * eye_fwd + px * eye_side
            ey = cy + sa * eye_fwd + py * eye_side

            d.ellipse([ex - eye_r, ey - eye_r * 1.05,
                       ex + eye_r, ey + eye_r * 1.05],
                      fill=(255, 255, 255, 255))

            pr = eye_r * 0.62
            ppx = ex + ca * eye_r * 0.18
            ppy = ey + sa * eye_r * 0.18
            d.ellipse([ppx - pr, ppy - pr, ppx + pr, ppy + pr],
                      fill=pupil_color + (255,))

            hr = pr * 0.50
            gx = ppx - pr * 0.40
            gy = ppy - pr * 0.50
            d.ellipse([gx - hr, gy - hr, gx + hr, gy + hr],
                      fill=(255, 255, 255, 250))
            hr2 = pr * 0.22
            gx2 = ppx + pr * 0.40
            gy2 = ppy + pr * 0.40
            d.ellipse([gx2 - hr2, gy2 - hr2, gx2 + hr2, gy2 + hr2],
                      fill=(255, 255, 255, 220))

    # ---------- 食物 ----------
    def _draw_food(self, d, food):
        fx, fy = food["x"] * SS, food["y"] * SS
        kind = food["kind"]
        theme = self.theme_name

        if theme == "音符蛇":
            self._draw_note(d, fx, fy, kind, (30, 30, 35, 255),
                            size=FOOD_RADIUS * SS)
        elif theme == "花园蛇":
            if kind == "flower":
                self._draw_flower(d, fx, fy, food.get("variant", 0))
            else:
                self._draw_grass_bundle(d, fx, fy)
        elif theme == "甜品蛇":
            self._draw_dessert(d, fx, fy, FOOD_RADIUS * SS,
                               food.get("variant", 0))
        else:
            self._draw_star_food(d, fx, fy)

    def _draw_note(self, d, cx, cy, kind, color, size=14 * SS):
        head_w = size * 1.25
        head_h = size * 0.9

        def draw_head(hx, hy):
            d.ellipse([hx - head_w / 2, hy - head_h / 2,
                       hx + head_w / 2, hy + head_h / 2], fill=color)

        if kind == "quarter":
            draw_head(cx, cy)
            stem_x = cx + head_w / 2 - 2 * SS
            d.rectangle([stem_x, cy - size * 1.7,
                         stem_x + 3 * SS, cy], fill=color)
        elif kind == "eighth":
            draw_head(cx, cy)
            stem_x = cx + head_w / 2 - 2 * SS
            d.rectangle([stem_x, cy - size * 1.7,
                         stem_x + 3 * SS, cy], fill=color)
            tail_pts = []
            for t in [i / 8 for i in range(9)]:
                x = stem_x + 3 * SS + t * size * 0.8
                y = cy - size * 1.7 + math.sin(t * math.pi * 0.8) * size * 0.55
                tail_pts.append((x, y))
            tail_pts.append((stem_x + 3 * SS, cy - size * 1.7 + size * 0.35))
            d.polygon(tail_pts, fill=color)
        else:
            off = size * 1.0
            draw_head(cx - off, cy)
            draw_head(cx + off, cy)
            s1x = cx - off + head_w / 2 - 2 * SS
            s2x = cx + off + head_w / 2 - 2 * SS
            d.rectangle([s1x, cy - size * 1.7, s1x + 3 * SS, cy], fill=color)
            d.rectangle([s2x, cy - size * 1.7, s2x + 3 * SS, cy], fill=color)
            d.rectangle([s1x, cy - size * 1.7,
                         s2x + 3 * SS, cy - size * 1.7 + size * 0.4],
                        fill=color)

    # ==================== 甜品绘制 ====================
    def _draw_dessert(self, d, cx, cy, r, idx):
        idx = idx % len(DESSERTS)
        info = DESSERTS[idx]
        kind = info["kind"]
        if kind == "cake":
            self._draw_dessert_cake(d, cx, cy, r, info)
        elif kind == "donut":
            self._draw_dessert_donut(d, cx, cy, r, info)
        elif kind == "macaron":
            self._draw_dessert_macaron(d, cx, cy, r, info)
        elif kind == "icecream":
            self._draw_dessert_icecream(d, cx, cy, r, info)
        elif kind == "pudding":
            self._draw_dessert_pudding(d, cx, cy, r, info)
        else:
            self._draw_dessert_jelly(d, cx, cy, r, info)

    def _draw_dessert_cake(self, d, cx, cy, r, info):
        w = r * 1.7
        h = r * 1.55
        d.ellipse([cx - w * 0.52, cy + h * 0.48,
                   cx + w * 0.52, cy + h * 0.66],
                  fill=(190, 160, 128, 90))
        d.rounded_rectangle([cx - w / 2, cy - h * 0.05,
                             cx + w / 2, cy + h * 0.48],
                            radius=r * 0.18,
                            fill=(252, 236, 208, 255))
        d.rectangle([cx - w / 2, cy + h * 0.16,
                     cx + w / 2, cy + h * 0.27],
                    fill=(255, 190, 200, 255))
        d.rounded_rectangle([cx - w / 2, cy - h * 0.42,
                             cx + w / 2, cy - h * 0.02],
                            radius=r * 0.20,
                            fill=info["color"] + (255,))
        wave_n = 5
        for i in range(wave_n):
            t = (i + 0.5) / wave_n
            wx = cx - w / 2 + w * t
            d.ellipse([wx - r * 0.14, cy - h * 0.06,
                       wx + r * 0.14, cy + h * 0.06],
                      fill=info["color"] + (255,))
        sx = cx
        sy = cy - h * 0.52
        d.ellipse([sx - r * 0.26, sy - r * 0.26,
                   sx + r * 0.26, sy + r * 0.30],
                  fill=(232, 62, 82, 255))
        d.polygon([
            (sx - r * 0.22, sy - r * 0.24),
            (sx, sy - r * 0.42),
            (sx + r * 0.22, sy - r * 0.24),
            (sx, sy - r * 0.16),
        ], fill=(96, 176, 96, 255))
        d.ellipse([sx - r * 0.16, sy - r * 0.14,
                   sx - r * 0.04, sy - r * 0.02],
                  fill=(255, 255, 255, 200))

    def _draw_dessert_donut(self, d, cx, cy, r, info):
        d.ellipse([cx - r, cy - r, cx + r, cy + r],
                  fill=(226, 186, 140, 255))
        d.ellipse([cx - r * 0.94, cy - r * 0.94,
                   cx + r * 0.94, cy + r * 0.94],
                  fill=info["color"] + (255,))
        d.ellipse([cx - r * 0.36, cy - r * 0.36,
                   cx + r * 0.36, cy + r * 0.36],
                  fill=(238, 224, 206, 255))
        sp_colors = [(255, 255, 255), (255, 214, 130), (255, 150, 180),
                     (140, 220, 200), (200, 170, 255)]
        random.seed(int(cx * 7 + cy * 13) & 0x7fffffff)
        for i in range(14):
            ang = random.uniform(0, 2 * math.pi)
            rr = r * random.uniform(0.48, 0.85)
            px = cx + math.cos(ang) * rr
            py = cy + math.sin(ang) * rr
            rot = random.uniform(0, math.pi)
            col = random.choice(sp_colors)
            self._draw_sprinkle(d, px, py, r * 0.22, rot, col + (255,))
        d.ellipse([cx - r * 0.72, cy - r * 0.78,
                   cx - r * 0.30, cy - r * 0.50],
                  fill=(255, 255, 255, 70))

    def _draw_dessert_macaron(self, d, cx, cy, r, info):
        w = r * 1.7
        h = r * 0.62
        d.ellipse([cx - w / 2, cy + h * 0.10,
                   cx + w / 2, cy + h * 1.75],
                  fill=info["color"] + (255,))
        d.rounded_rectangle([cx - w * 0.44, cy - h * 0.30,
                             cx + w * 0.44, cy + h * 0.62],
                            radius=h * 0.35,
                            fill=info["accent"] + (255,))
        d.ellipse([cx - w / 2, cy - h * 1.75,
                   cx + w / 2, cy + h * 0.30],
                  fill=info["color"] + (255,))
        for i in range(9):
            t = i / 8
            px = cx - w * 0.45 + w * 0.90 * t
            py = cy + h * 0.14
            d.ellipse([px - r * 0.07, py - r * 0.05,
                       px + r * 0.07, py + r * 0.05],
                      fill=tuple(max(0, c - 25) for c in info["color"]) + (200,))
        d.ellipse([cx - w * 0.28, cy - h * 1.30,
                   cx - w * 0.05, cy - h * 0.90],
                  fill=(255, 255, 255, 130))

    def _draw_dessert_icecream(self, d, cx, cy, r, info):
        d.polygon([
            (cx - r * 0.58, cy + r * 0.10),
            (cx + r * 0.58, cy + r * 0.10),
            (cx, cy + r * 1.25),
        ], fill=(226, 176, 116, 255))
        for i in range(4):
            t = (i + 1) / 5
            yy = cy + r * 0.10 + (r * 1.15) * t
            hw = r * 0.58 * (1 - t)
            d.line([(cx - hw, yy), (cx + hw, yy)],
                   fill=(198, 148, 92, 220), width=max(1, SS))
        for i in range(-2, 3):
            d.line([(cx + i * r * 0.22, cy + r * 0.10),
                    (cx + i * r * 0.08, cy + r * 1.20)],
                   fill=(198, 148, 92, 160), width=max(1, SS))
        d.ellipse([cx - r * 0.88, cy - r * 1.18,
                   cx + r * 0.88, cy + r * 0.32],
                  fill=info["color"] + (255,))
        d.ellipse([cx - r * 0.62, cy - r * 1.60,
                   cx + r * 0.62, cy - r * 0.55],
                  fill=info["accent"] + (255,))
        for i, (ox, oy) in enumerate([(-0.5, -1.3), (0.45, -1.15),
                                      (0.0, -1.55), (-0.15, -0.95)]):
            px = cx + ox * r
            py = cy + oy * r
            d.ellipse([px - r * 0.14, py - r * 0.14,
                       px + r * 0.14, py + r * 0.14],
                      fill=(86, 96, 176, 255))
            d.ellipse([px - r * 0.07, py - r * 0.09,
                       px - r * 0.01, py - r * 0.03],
                      fill=(210, 220, 255, 220))
        d.ellipse([cx - r * 0.55, cy - r * 1.05,
                   cx - r * 0.22, cy - r * 0.70],
                  fill=(255, 255, 255, 150))

    def _draw_dessert_pudding(self, d, cx, cy, r, info):
        d.ellipse([cx - r * 0.92, cy + r * 0.70,
                   cx + r * 0.92, cy + r * 1.02],
                  fill=(190, 160, 120, 90))
        d.polygon([
            (cx - r * 0.62, cy - r * 0.62),
            (cx + r * 0.62, cy - r * 0.62),
            (cx + r * 0.86, cy + r * 0.82),
            (cx - r * 0.86, cy + r * 0.82),
        ], fill=info["color"] + (255,))
        d.polygon([
            (cx - r * 0.62, cy - r * 0.62),
            (cx + r * 0.62, cy - r * 0.62),
            (cx + r * 0.48, cy - r * 0.28),
            (cx - r * 0.48, cy - r * 0.28),
        ], fill=(196, 118, 50, 255))
        d.polygon([
            (cx - r * 0.30, cy - r * 0.30),
            (cx - r * 0.18, cy - r * 0.30),
            (cx - r * 0.22, cy + r * 0.16),
            (cx - r * 0.30, cy + r * 0.10),
        ], fill=(196, 118, 50, 220))
        d.polygon([
            (cx + r * 0.14, cy - r * 0.30),
            (cx + r * 0.26, cy - r * 0.30),
            (cx + r * 0.30, cy + r * 0.30),
            (cx + r * 0.18, cy + r * 0.24),
        ], fill=(196, 118, 50, 220))
        d.ellipse([cx - r * 0.48, cy - r * 0.18,
                   cx - r * 0.22, cy + r * 0.14],
                  fill=(255, 255, 255, 90))

    def _draw_dessert_jelly(self, d, cx, cy, r, info):
        d.ellipse([cx - r * 0.92, cy + r * 0.60,
                   cx + r * 0.92, cy + r * 0.95],
                  fill=(216, 200, 226, 200))
        d.rounded_rectangle([cx - r * 0.84, cy - r * 0.72,
                             cx + r * 0.84, cy + r * 0.80],
                            radius=r * 0.30,
                            fill=info["color"] + (215,))
        d.rounded_rectangle([cx - r * 0.66, cy - r * 0.54,
                             cx + r * 0.54, cy + r * 0.30],
                            radius=r * 0.24,
                            fill=info["accent"] + (120,))
        for ox, oy in [(-0.35, 0.20), (0.0, -0.05), (0.35, 0.22),
                       (-0.15, 0.45), (0.20, 0.48)]:
            px = cx + ox * r
            py = cy + oy * r
            d.ellipse([px - r * 0.16, py - r * 0.16,
                       px + r * 0.16, py + r * 0.16],
                      fill=(140, 84, 176, 220))
        d.ellipse([cx - r * 0.48, cy - r * 0.58,
                   cx - r * 0.12, cy - r * 0.32],
                  fill=(255, 255, 255, 170))

    # ==================== 茶匙 ====================
    def _draw_spoon(self, d, cx, cy, size, dessert, lit):
        head_rx = size * 0.52
        head_ry = size * 0.68
        head_cy = cy - size * 0.42

        handle_w = size * 0.20
        handle_top = head_cy
        handle_bottom = cy + size * 0.92

        if lit:
            head_fill = dessert["color"] + (255,)
            head_edge = tuple(max(0, c - 55) for c in dessert["color"]) + (255,)
            handle_fill = (240, 236, 230, 255)
            handle_edge = (190, 182, 172, 255)
        else:
            head_fill = (218, 212, 206, 255)
            head_edge = (172, 166, 160, 255)
            handle_fill = (218, 212, 206, 255)
            handle_edge = (172, 166, 160, 255)

        d.rounded_rectangle(
            [cx - handle_w / 2, handle_top,
             cx + handle_w / 2, handle_bottom],
            radius=handle_w / 2,
            fill=handle_fill, outline=handle_edge,
            width=max(1, SS // 2))
        d.ellipse([cx - head_rx, head_cy - head_ry,
                   cx + head_rx, head_cy + head_ry],
                  fill=head_fill, outline=head_edge,
                  width=max(1, SS // 2))

        if lit:
            self._draw_spoon_pattern(d, cx, head_cy, head_rx, dessert)
            d.ellipse([cx - head_rx * 0.62, head_cy - head_ry * 0.62,
                       cx - head_rx * 0.12, head_cy - head_ry * 0.20],
                      fill=(255, 255, 255, 180))

    def _draw_spoon_pattern(self, d, cx, cy, r, dessert):
        col = (255, 255, 255, 235)
        kind = dessert["kind"]

        if kind == "cake":
            d.polygon([
                (cx, cy - r * 0.55),
                (cx + r * 0.55, cy + r * 0.40),
                (cx - r * 0.55, cy + r * 0.40),
            ], fill=col)
        elif kind == "donut":
            d.ellipse([cx - r * 0.55, cy - r * 0.55,
                       cx + r * 0.55, cy + r * 0.55],
                      outline=col, width=max(1, SS))
        elif kind == "macaron":
            d.ellipse([cx - r * 0.62, cy - r * 0.28,
                       cx + r * 0.62, cy + r * 0.28],
                      fill=col)
        elif kind == "icecream":
            _draw_star_shape(d, cx, cy, r * 0.62, col)
        elif kind == "pudding":
            d.polygon([
                (cx - r * 0.45, cy - r * 0.40),
                (cx + r * 0.45, cy - r * 0.40),
                (cx + r * 0.58, cy + r * 0.42),
                (cx - r * 0.58, cy + r * 0.42),
            ], fill=col)
        else:  # jelly
            d.polygon([
                (cx, cy - r * 0.60),
                (cx + r * 0.52, cy),
                (cx, cy + r * 0.60),
                (cx - r * 0.52, cy),
            ], fill=col)

    # ==================== 花园蛇花朵 ====================
    def _draw_flower(self, d, cx, cy, variant_idx):
        v = FLOWER_VARIANTS[variant_idx % len(FLOWER_VARIANTS)]
        name = v["name"]
        if name == "rose":
            self._draw_flower_rose(d, cx, cy, FOOD_RADIUS * SS, v)
        elif name == "sakura":
            self._draw_flower_sakura(d, cx, cy, FOOD_RADIUS * SS, v)
        elif name == "peach":
            self._draw_flower_peach(d, cx, cy, FOOD_RADIUS * SS, v)
        elif name == "chinese_rose":
            self._draw_flower_chinese_rose(d, cx, cy, FOOD_RADIUS * SS, v)
        elif name == "lily":
            self._draw_flower_lily(d, cx, cy, FOOD_RADIUS * SS, v)
        else:
            self._draw_flower_daisy(d, cx, cy, FOOD_RADIUS * SS, v)

    def _draw_flower_rose(self, d, cx, cy, r, v):
        for i in range(5):
            ang = i * 2 * math.pi / 5 + 0.2
            px = cx + math.cos(ang) * r * 0.62
            py = cy + math.sin(ang) * r * 0.62
            d.ellipse([px - r * 0.58, py - r * 0.58,
                       px + r * 0.58, py + r * 0.58],
                      fill=v["petal2"] + (255,))
        for i in range(4):
            ang = i * 2 * math.pi / 4 + 0.5
            px = cx + math.cos(ang) * r * 0.40
            py = cy + math.sin(ang) * r * 0.40
            d.ellipse([px - r * 0.48, py - r * 0.48,
                       px + r * 0.48, py + r * 0.48],
                      fill=v["petal"] + (255,))
        d.ellipse([cx - r * 0.32, cy - r * 0.32,
                   cx + r * 0.32, cy + r * 0.32],
                  fill=v["petal"] + (255,))
        d.ellipse([cx - r * 0.15, cy - r * 0.15,
                   cx + r * 0.15, cy + r * 0.15],
                  fill=v["center"] + (255,))

    def _draw_flower_sakura(self, d, cx, cy, r, v):
        for i in range(5):
            ang = i * 2 * math.pi / 5 - math.pi / 2
            px = cx + math.cos(ang) * r * 0.52
            py = cy + math.sin(ang) * r * 0.52
            d.ellipse([px - r * 0.56, py - r * 0.56,
                       px + r * 0.56, py + r * 0.56],
                      fill=v["petal"] + (255,))
            tip_x = cx + math.cos(ang) * r * 1.05
            tip_y = cy + math.sin(ang) * r * 1.05
            perp_x = -math.sin(ang)
            perp_y = math.cos(ang)
            d.polygon([
                (tip_x + perp_x * r * 0.16, tip_y + perp_y * r * 0.16),
                (tip_x - perp_x * r * 0.16, tip_y - perp_y * r * 0.16),
                (tip_x - math.cos(ang) * r * 0.22,
                 tip_y - math.sin(ang) * r * 0.22),
            ], fill=(252, 245, 250, 255))
        d.ellipse([cx - r * 0.28, cy - r * 0.28,
                   cx + r * 0.28, cy + r * 0.28],
                  fill=v["center"] + (255,))
        for i in range(5):
            ang = i * 2 * math.pi / 5
            px = cx + math.cos(ang) * r * 0.16
            py = cy + math.sin(ang) * r * 0.16
            d.ellipse([px - r * 0.055, py - r * 0.055,
                       px + r * 0.055, py + r * 0.055],
                      fill=(255, 170, 195, 255))

    def _draw_flower_peach(self, d, cx, cy, r, v):
        for i in range(5):
            ang = i * 2 * math.pi / 5 - math.pi / 2
            px = cx + math.cos(ang) * r * 0.50
            py = cy + math.sin(ang) * r * 0.50
            d.ellipse([px - r * 0.55, py - r * 0.55,
                       px + r * 0.55, py + r * 0.55],
                      fill=v["petal"] + (255,))
        d.ellipse([cx - r * 0.32, cy - r * 0.32,
                   cx + r * 0.32, cy + r * 0.32],
                  fill=v["petal2"] + (255,))
        for i in range(6):
            ang = i * 2 * math.pi / 6 + 0.3
            px = cx + math.cos(ang) * r * 0.22
            py = cy + math.sin(ang) * r * 0.22
            d.ellipse([px - r * 0.075, py - r * 0.075,
                       px + r * 0.075, py + r * 0.075],
                      fill=(255, 218, 150, 255))

    def _draw_flower_chinese_rose(self, d, cx, cy, r, v):
        for i in range(6):
            ang = i * 2 * math.pi / 6
            px = cx + math.cos(ang) * r * 0.66
            py = cy + math.sin(ang) * r * 0.66
            d.ellipse([px - r * 0.50, py - r * 0.50,
                       px + r * 0.50, py + r * 0.50],
                      fill=v["petal2"] + (255,))
        for i in range(5):
            ang = i * 2 * math.pi / 5 + 0.3
            px = cx + math.cos(ang) * r * 0.44
            py = cy + math.sin(ang) * r * 0.44
            d.ellipse([px - r * 0.44, py - r * 0.44,
                       px + r * 0.44, py + r * 0.44],
                      fill=v["petal"] + (255,))
        for i in range(4):
            ang = i * 2 * math.pi / 4 + 0.6
            px = cx + math.cos(ang) * r * 0.26
            py = cy + math.sin(ang) * r * 0.26
            d.ellipse([px - r * 0.34, py - r * 0.34,
                       px + r * 0.34, py + r * 0.34],
                      fill=v["petal"] + (255,))
        d.ellipse([cx - r * 0.17, cy - r * 0.17,
                   cx + r * 0.17, cy + r * 0.17],
                  fill=v["center"] + (255,))

    def _draw_flower_lily(self, d, cx, cy, r, v):
        for i in range(6):
            ang = i * 2 * math.pi / 6 - math.pi / 2
            tip_x = cx + math.cos(ang) * r * 1.05
            tip_y = cy + math.sin(ang) * r * 1.05
            perp_x = -math.sin(ang) * r * 0.30
            perp_y = math.cos(ang) * r * 0.30
            base_x = cx + math.cos(ang) * r * 0.14
            base_y = cy + math.sin(ang) * r * 0.14
            d.polygon([
                (base_x + perp_x, base_y + perp_y),
                (tip_x, tip_y),
                (base_x - perp_x, base_y - perp_y),
            ], fill=v["petal"] + (255,))
        d.ellipse([cx - r * 0.26, cy - r * 0.26,
                   cx + r * 0.26, cy + r * 0.26],
                  fill=v["center"] + (255,))
        for i in range(5):
            ang = i * 2 * math.pi / 5 + 0.4
            ex = cx + math.cos(ang) * r * 0.55
            ey = cy + math.sin(ang) * r * 0.55
            d.line([(cx, cy), (ex, ey)],
                   fill=(200, 160, 90, 255), width=max(1, SS))
            d.ellipse([ex - r * 0.06, ey - r * 0.06,
                       ex + r * 0.06, ey + r * 0.06],
                      fill=(160, 110, 50, 255))

    def _draw_flower_daisy(self, d, cx, cy, r, v):
        n = 12
        for i in range(n):
            ang = i * 2 * math.pi / n
            tip_x = cx + math.cos(ang) * r * 1.08
            tip_y = cy + math.sin(ang) * r * 1.08
            base_x = cx + math.cos(ang) * r * 0.14
            base_y = cy + math.sin(ang) * r * 0.14
            perp_x = -math.sin(ang) * r * 0.13
            perp_y = math.cos(ang) * r * 0.13
            d.polygon([
                (base_x + perp_x, base_y + perp_y),
                (tip_x + perp_x * 0.4, tip_y + perp_y * 0.4),
                (tip_x, tip_y),
                (tip_x - perp_x * 0.4, tip_y - perp_y * 0.4),
                (base_x - perp_x, base_y - perp_y),
            ], fill=v["petal"] + (255,))
        d.ellipse([cx - r * 0.36, cy - r * 0.36,
                   cx + r * 0.36, cy + r * 0.36],
                  fill=v["center"] + (255,))
        for i in range(5):
            ang = i * 2 * math.pi / 5 + 0.3
            px = cx + math.cos(ang) * r * 0.16
            py = cy + math.sin(ang) * r * 0.16
            d.ellipse([px - r * 0.05, py - r * 0.05,
                       px + r * 0.05, py + r * 0.05],
                      fill=(220, 160, 40, 255))

    def _draw_grass_bundle(self, d, cx, cy):
        r = FOOD_RADIUS * SS
        base_x = cx
        base_y = cy + r * 0.75

        leaves = [
            (-0.75, -1.55, 0.18, (96, 195, 165)),
            (-0.38, -1.95, 0.16, (110, 215, 180)),
            (-0.05, -2.10, 0.18, (120, 225, 190)),
            (0.30, -1.85, 0.16, (110, 215, 180)),
            (0.68, -1.50, 0.18, (96, 195, 165)),
        ]

        for dx, dy, w, col in leaves:
            tip_x = base_x + dx * r
            tip_y = base_y + dy * r
            mid_x = base_x + dx * r * 0.35
            mid_y = base_y + dy * r * 0.55
            bw = r * w

            left_pts = []
            right_pts = []
            n_seg = 10
            for k in range(n_seg + 1):
                t = k / n_seg
                bx = (1 - t) ** 2 * base_x + 2 * (1 - t) * t * mid_x + t ** 2 * tip_x
                by = (1 - t) ** 2 * base_y + 2 * (1 - t) * t * mid_y + t ** 2 * tip_y
                wt = bw * (1 - t) ** 0.6
                tx = 2 * (1 - t) * (mid_x - base_x) + 2 * t * (tip_x - mid_x)
                ty = 2 * (1 - t) * (mid_y - base_y) + 2 * t * (tip_y - mid_y)
                L = math.hypot(tx, ty) or 1
                nx = -ty / L
                ny = tx / L
                left_pts.append((bx - nx * wt, by - ny * wt))
                right_pts.append((bx + nx * wt, by + ny * wt))

            poly = left_pts + list(reversed(right_pts))
            d.polygon(poly, fill=col + (255,))

        d.ellipse([base_x - r * 0.32, base_y - r * 0.18,
                   base_x + r * 0.32, base_y + r * 0.22],
                  fill=(140, 205, 175, 255))

    def _draw_star_food(self, d, cx, cy):
        r = FOOD_RADIUS * SS

        # 星形光晕：沿星角向外扩散（不用圆形，避免星星背后出现圆盘底色）
        for k in range(5, 0, -1):
            t = k / 5
            a = int(48 * (1 - t) ** 1.8)
            if a <= 0:
                continue
            _draw_star_shape(d, cx, cy, r * (1.22 + 0.78 * t),
                             (255, 210, 120, a))

        # 星形本体：深金描边 → 亮金 → 浅金 → 奶白，五个角轮廓清晰
        _draw_star_shape(d, cx, cy, r * 1.16, (220, 145, 35, 255))
        _draw_star_shape(d, cx, cy, r * 1.02, (255, 195, 70, 255))
        _draw_star_shape(d, cx, cy, r * 0.68, (255, 236, 160, 255))
        _draw_star_shape(d, cx, cy, r * 0.36, (255, 255, 248, 255))

    # ---------- 粒子 ----------
    def _draw_particles(self, d):
        for p in self.particles:
            x, y = p["x"] * SS, p["y"] * SS
            t = max(0.0, min(1.0, p["life"] / p["max_life"]))

            if p["type"] == "note":
                color = (30, 30, 35, int(255 * t))
                size = FOOD_RADIUS * SS * p["size"]
                self._draw_note(d, x, y, p["kind"], color, size)

            elif p["type"] == "petal":
                color = p["color"] + (int(240 * t),)
                self._draw_petal(d, x, y, p["size"], p["rot"], color)

            elif p["type"] == "star":
                color = p["color"] + (int(255 * t),)
                for k in range(5, 0, -1):
                    a = int(90 * (1 - k / 5) * t)
                    if a <= 0:
                        continue
                    _draw_star_shape(d, x, y, p["size"] * (1 + k * 0.4),
                                     (255, 240, 180, a), p["rot"])
                _draw_star_shape(d, x, y, p["size"], color, p["rot"])

            elif p["type"] == "sprinkle":
                color = p["color"] + (int(255 * t),)
                self._draw_sprinkle(d, x, y, p["size"], p["rot"], color)

    def _draw_sprinkle(self, d, cx, cy, size, rot, color):
        w, h = size, size * 0.42
        ca, sa = math.cos(rot), math.sin(rot)
        pts = []
        for dx, dy in [(-w / 2, -h / 2), (w / 2, -h / 2),
                       (w / 2, h / 2), (-w / 2, h / 2)]:
            pts.append((cx + dx * ca - dy * sa, cy + dx * sa + dy * ca))
        d.polygon(pts, fill=color)

    def _draw_petal(self, d, cx, cy, size, rot, color):
        n = 14
        pts = []
        for i in range(n):
            a = i / n * 2 * math.pi
            px = math.cos(a) * size
            py = math.sin(a) * size * 0.55
            rx = px * math.cos(rot) - py * math.sin(rot)
            ry = px * math.sin(rot) + py * math.cos(rot)
            pts.append((cx + rx, cy + ry))
        d.polygon(pts, fill=color)

    # ---------- HUD ----------
    def _draw_hud(self, d):
        art = THEME_ART[self.theme_name]
        hint_col = _hex(art["hint"])
        panel = art["hud_bg"]
        outl = art["hud_outline"]

        box = [MARGIN + 14, MARGIN + 14, MARGIN + 200, MARGIN + 92]
        d.rounded_rectangle(box, radius=14, fill=panel,
                            outline=outl, width=1)
        d.text((box[0] + 22, box[1] + 14), "得分",
               fill=hint_col, font=self._font(14))
        d.text((box[0] + 22, box[1] + 34), str(self.score),
               fill=hint_col, font=self._font(34, bold=True))

        if self.theme_name == "星星蛇":
            progress = len(self.constellation_points)
            total_done = len(self.constellations)
            box2 = [MARGIN + 14, MARGIN + 100, MARGIN + 200, MARGIN + 154]
            d.rounded_rectangle(box2, radius=14, fill=panel,
                                outline=outl, width=1)
            d.text((box2[0] + 22, box2[1] + 10), "星座进度",
                   fill=hint_col, font=self._font(12))
            d.text((box2[0] + 22, box2[1] + 28),
                   f"{progress}/{CONSTELLATION_SIZE}    已完成 {total_done}",
                   fill=hint_col, font=self._font(16, bold=True))

        if self.theme_name == "甜品蛇":
            box2 = [MARGIN + 14, MARGIN + 100,
                    MARGIN + 14 + 264, MARGIN + 100 + 76]
            d.rounded_rectangle(box2, radius=14, fill=panel,
                                outline=outl, width=1)
            d.text((box2[0] + 18, box2[1] + 8), "甜品茶匙",
                   fill=hint_col, font=self._font(12))

            spoon_y = box2[1] + 50
            sx = box2[0] + 30
            for i, ds in enumerate(DESSERTS):
                self._draw_spoon(d, sx + i * 40, spoon_y, 16,
                                 ds, self.spoons_lit[i])

        btn_w = 130
        bx1 = W - MARGIN - 14
        bx0 = bx1 - btn_w

        y0 = MARGIN + 14
        y1 = y0 + 40
        d.rounded_rectangle([bx0, y0, bx1, y1], radius=12,
                            fill=panel, outline=outl, width=1)
        d.text(((bx0 + bx1) / 2, (y0 + y1) / 2), self.theme_name,
               fill=hint_col, anchor="mm",
               font=self._font(16, bold=True))

        y0 = MARGIN + 62
        y1 = y0 + 38
        self.restart_btn_bounds = (bx0, y0, bx1, y1)
        self._draw_hud_button(
            d, bx0, y0, bx1, y1, "重 新 开 始 (R)", "restart", size=14)

        y0 = MARGIN + 108
        y1 = y0 + 38
        self.quit_btn_bounds = (bx0, y0, bx1, y1)
        self._draw_hud_button(
            d, bx0, y0, bx1, y1, "返 回 首 页", "quit", size=14)

        if self.follow_mouse:
            status = "鼠标跟随中"
        else:
            status = "方向键 / WASD 控制"

        hint_y = H - MARGIN - 22
        panel_w = 880
        px0 = (W - panel_w) / 2
        d.rounded_rectangle([px0, hint_y - 14,
                             px0 + panel_w, hint_y + 16],
                            radius=12, fill=panel,
                            outline=outl, width=1)

        d.text((W / 2 - 250, hint_y), status,
               fill=hint_col, anchor="mm",
               font=self._font(14, bold=True))

        if self.theme_name == "甜品蛇":
            hint2 = "点击跟随  ·  空格暂停  ·  R重开  ·  吃甜品点亮茶匙  ·  ESC返回首页"
        else:
            hint2 = "点击跟随  ·  空格暂停  ·  R重开  ·  ESC返回首页"
        d.text((W / 2 + 130, hint_y), hint2,
               fill=hint_col, anchor="mm",
               font=self._font(13))

    # ---------- 主循环 ----------
    def tick(self):
        now = time.perf_counter()
        dt = now - self.last_tick
        self.last_tick = now
        if dt > 0.06:
            dt = 0.06
        self._update(dt)
        self._render()
        self.root.after(16, self.tick)


# ==================== 启动 ====================
def main():
    root = tk.Tk()
    Game(root)
    root.mainloop()


if __name__ == "__main__":
    main()