# -*- coding: utf-8 -*-
"""贪吃蛇小游戏（莫兰迪配色 · 浅灰底）- 基于 tkinter 标准库，无需第三方依赖。

玩法：蛇自动前进，方向键 / WASD 只改变方向，空格暂停。
      - 吃到食物 +10 分；每 50 分速度加快，并新增一个障碍块
      - 撞到障碍物（石块）、撞墙、咬到自己 都会游戏结束
      - 右上角「退出」或 Esc 退出；底部「－ / ＋」或 +/- 键缩放游戏框
      - 按回车重新开始，棋盘上的障碍物会重新随机生成
"""

import random
import tkinter as tk
from tkinter import messagebox

CELL = 20            # 每格像素大小（缩放基准）
COLS, ROWS = 30, 20
WIDTH, HEIGHT = COLS * CELL, ROWS * CELL

OBSTACLE_GROUPS = 4  # 开局障碍物簇数量（每簇 2~5 格）
SAFE_RADIUS = 3      # 出生点周围的安全半径（格），该范围内不生成障碍物
START_LEN = 3        # 初始蛇长

BASE_SPEED = 220     # 初始移动间隔（毫秒），越小越快
SPEED_STEP = 12      # 每升一级加快的毫秒数
MIN_SPEED = 90       # 速度下限
LEVEL_SCORE = 50     # 每多少分升一级（提速 + 新增一个障碍块）

ZOOM_MIN, ZOOM_MAX, ZOOM_STEP = 0.6, 2.0, 0.2   # 游戏框缩放范围

# ---------------- 莫兰迪色板（低饱和、带灰调） ----------------
COLOR_BG = "#e9e6e2"          # 浅灰底（棋盘主色）
COLOR_BG_ALT = "#f2f0ed"      # 棋盘交替格
COLOR_CARD = "#f6f4f1"        # 弹层卡片
COLOR_CARD_EDGE = "#d8d3cd"

# 小蛇：灰绿鼠尾草色
COLOR_SNAKE = "#b4c8a6"        # 蛇身
COLOR_SNAKE_EDGE = "#9ab088"   # 蛇身描边
COLOR_SNAKE_BELLY = "#dbe5d0"  # 蛇腹高光
COLOR_SHADOW = "#d5d0ca"       # 蛇身投影
COLOR_HEAD = "#a9c096"         # 蛇头
COLOR_HEAD_EDGE = "#8ea87c"
COLOR_TONGUE = "#cd9a9a"       # 藕荷粉舌头
COLOR_CHEEK = "#e3b8b8"        # 腮红
COLOR_EYE = "#fbfaf8"
COLOR_PUPIL = "#5b5a57"

# 障碍物：暖灰石块
COLOR_ROCK = "#cfc8c1"
COLOR_ROCK_EDGE = "#b2aaa2"
COLOR_ROCK_LIGHT = "#e2ddd6"

# 食物
COLOR_APPLE = "#c08a84"        # 灰调红
COLOR_APPLE_DARK = "#a17069"
COLOR_APPLE_HL = "#dcb3ad"
COLOR_STEM = "#9c8b78"
COLOR_LEAF = "#a9b896"

COLOR_CUP = "#c9b79b"
COLOR_CUP_EDGE = "#ab9a80"
COLOR_CREAM = "#e8c8cb"
COLOR_CHERRY = "#b98a85"
COLOR_SPRINKLE = "#efe3cf"

COLOR_WATER = "#a8bcc9"
COLOR_WATER_EDGE = "#8ba4b3"
COLOR_WATER_HL = "#dde7ed"

COLOR_GRASS = "#a7b892"
COLOR_GRASS_DARK = "#8b9c78"

COLOR_TEXT = "#5f5b56"
COLOR_HINT = "#9a948d"

# 方向键 / WASD -> 方向向量
KEY_DIRS = {
    "up": (0, -1), "w": (0, -1),
    "down": (0, 1), "s": (0, 1),
    "left": (-1, 0), "a": (-1, 0),
    "right": (1, 0), "d": (1, 0),
}


# ---------- 食物样式：模块级绘制函数（canvas, 中心x, 中心y, 半径, 格子底色） ----------
def draw_apple(cv, cx, cy, r, bg):
    """苹果"""
    cv.create_line(cx, cy - r * 0.75, cx + 2, cy - r * 1.5,
                   fill=COLOR_STEM, width=2, capstyle="round")
    cv.create_oval(cx + 2, cy - r * 1.75, cx + r * 1.05, cy - r * 0.95,
                   fill=COLOR_LEAF, outline="")
    cv.create_oval(cx - r, cy - r * 0.9, cx + r, cy + r * 1.1,
                   fill=COLOR_APPLE, outline=COLOR_APPLE_DARK, width=1)
    # 顶部凹陷：用格子底色盖出果蒂凹口
    cv.create_oval(cx - r * 0.38, cy - r * 1.18, cx + r * 0.38, cy - r * 0.62,
                   fill=bg, outline="")
    cv.create_oval(cx - r * 0.55, cy - r * 0.5, cx - r * 0.2, cy - r * 0.1,
                   fill=COLOR_APPLE_HL, outline="")


def draw_cupcake(cv, cx, cy, r, bg):
    """小蛋糕"""
    cv.create_polygon(cx - r * 0.72, cy + r * 0.1,
                      cx + r * 0.72, cy + r * 0.1,
                      cx + r * 0.5, cy + r,
                      cx - r * 0.5, cy + r,
                      fill=COLOR_CUP, outline=COLOR_CUP_EDGE)
    for ox, oy in ((-0.45, 0.0), (0.0, -0.3), (0.45, 0.0)):
        bx, by = cx + r * ox, cy + r * oy - r * 0.05
        br = r * 0.5
        cv.create_oval(bx - br, by - br, bx + br, by + br,
                       fill=COLOR_CREAM, outline="")
    cr = r * 0.22
    cv.create_oval(cx - cr, cy - r * 0.95 - cr,
                   cx + cr, cy - r * 0.95 + cr,
                   fill=COLOR_CHERRY, outline="")
    for ox, oy in ((-0.35, -0.1), (0.15, -0.35), (0.4, 0.1)):
        px, py = cx + r * ox, cy + r * oy
        cv.create_rectangle(px, py, px + 2.5, py + 2.5,
                            fill=COLOR_SPRINKLE, outline="")


def draw_waterdrop(cv, cx, cy, r, bg):
    """水滴"""
    cv.create_polygon(cx, cy - r * 1.15,
                      cx + r * 0.9, cy + r * 0.15,
                      cx, cy + r * 0.95,
                      cx - r * 0.9, cy + r * 0.15,
                      fill=COLOR_WATER, outline=COLOR_WATER_EDGE,
                      smooth=True, splinesteps=24)
    cv.create_oval(cx - r * 0.45, cy - r * 0.1, cx - r * 0.12, cy + r * 0.35,
                   fill=COLOR_WATER_HL, outline="")


def draw_grass(cv, cx, cy, r, bg):
    """小草"""
    cv.create_oval(cx - r * 0.8, cy + r * 0.55, cx + r * 0.8, cy + r * 1.0,
                   fill=COLOR_GRASS_DARK, outline="")
    for dx, dy, bend in ((-0.45, -0.55, -0.6), (0.0, -1.0, 0.0),
                         (0.45, -0.6, 0.6)):
        cv.create_line(cx, cy + r * 0.7,
                       cx + r * dx * 0.4, cy + r * 0.1,
                       cx + r * dx + r * bend * 0.8, cy + r * dy,
                       fill=COLOR_GRASS, width=4, smooth=True,
                       capstyle="round", splinesteps=12)


class SnakeGame:
    def __init__(self, root):
        self.root = root
        self.root.title("贪吃蛇")
        self.root.configure(bg=COLOR_BG)

        self.zoom = 1.0             # 游戏框缩放系数
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT,
                                bg=COLOR_BG, highlightthickness=0)
        self.canvas.pack()
        self._apply_zoom()

        # 底部信息栏：得分 + 缩放按钮
        self.score_var = tk.StringVar(value="得分: 0")
        hud = tk.Frame(root, bg=COLOR_BG)
        tk.Label(hud, textvariable=self.score_var, fg=COLOR_TEXT,
                 bg=COLOR_BG, font=("Microsoft YaHei", 11)
                 ).pack(side="left", padx=14, pady=4)
        for text, delta in (("－", -ZOOM_STEP), ("＋", ZOOM_STEP)):
            tk.Button(hud, text=text, width=3,
                      command=lambda d=delta: self.change_zoom(d),
                      font=("Microsoft YaHei", 10),
                      bg=COLOR_CARD, fg=COLOR_TEXT,
                      activebackground=COLOR_CARD_EDGE,
                      relief="flat", bd=0, cursor="hand2"
                      ).pack(side="right", padx=4, pady=3)
        hud.pack(fill="x")

        # 蛇自动移动，按键只负责改变方向
        self.root.bind("<Key>", self.on_key)

        self.state = "menu"         # menu（开始界面）-> playing -> over
        self.reset()

        # 「开吃！」按钮：开始界面时悬浮在画布中央，进入游戏后隐藏
        self.btn_start = tk.Button(
            self.canvas, text="开吃！", command=self.start_game,
            font=("Microsoft YaHei", 16, "bold"),
            bg=COLOR_CHEEK, fg="#7a4a4a",
            activebackground="#d8a5a5", activeforeground="#7a4a4a",
            relief="flat", bd=0, cursor="hand2", padx=26, pady=8)
        self.btn_start.place(relx=0.5, rely=0.60, anchor="center")

        # 「退出」「规则」按钮：右上角并排悬浮
        self.btn_quit = tk.Button(
            self.root, text="退出", command=self.quit_game,
            font=("Microsoft YaHei", 10),
            bg=COLOR_CARD, fg=COLOR_TEXT,
            activebackground=COLOR_CARD_EDGE,
            relief="flat", bd=0, cursor="hand2", padx=10, pady=2)
        self.btn_quit.place(relx=1.0, x=-62, y=10, anchor="ne")
        self.btn_rules = tk.Button(
            self.root, text="规则", command=self.show_rules,
            font=("Microsoft YaHei", 10),
            bg=COLOR_CARD, fg=COLOR_TEXT,
            activebackground=COLOR_CARD_EDGE,
            relief="flat", bd=0, cursor="hand2", padx=10, pady=2)
        self.btn_rules.place(relx=1.0, x=-10, y=10, anchor="ne")

        self.draw()
        self.root.after(self._speed_ms(), self.tick)

    # ---------- 缩放 ----------
    def _apply_zoom(self):
        """按缩放系数重算格子与画布尺寸。"""
        self.cell = max(8, round(CELL * self.zoom))
        self.width = COLS * self.cell
        self.height = ROWS * self.cell
        self.canvas.config(width=self.width, height=self.height)

    def change_zoom(self, delta):
        self.zoom = min(ZOOM_MAX, max(ZOOM_MIN, self.zoom + delta))
        self._apply_zoom()
        self.draw()

    def _font(self, size, bold=False):
        """画布文字字体：随缩放变化。"""
        return ("Microsoft YaHei", max(8, round(size * self.zoom)),
                "bold" if bold else "normal")

    # ---------- 退出 ----------
    def quit_game(self):
        if messagebox.askyesno("退出游戏", "确定要退出贪吃蛇吗？"):
            self.root.destroy()

    # ---------- 开始游戏 ----------
    def start_game(self):
        self.state = "playing"
        self.btn_start.place_forget()
        self.reset()
        self.draw()

    def show_rules(self):
        """右上角「规则」弹窗"""
        win = tk.Toplevel(self.root)
        win.title("游戏规则")
        win.configure(bg=COLOR_CARD)
        win.resizable(False, False)
        win.transient(self.root)
        tk.Label(win, text="游戏规则", bg=COLOR_CARD, fg=COLOR_TEXT,
                 font=("Microsoft YaHei", 14, "bold")
                 ).pack(padx=30, pady=(18, 10))
        for line in RULE_LINES:
            tk.Label(win, text=line, bg=COLOR_CARD, fg=COLOR_TEXT,
                     font=("Microsoft YaHei", 11), anchor="w",
                     justify="left").pack(fill="x", padx=34, pady=2)
        tk.Button(win, text="知道了", command=win.destroy,
                  font=("Microsoft YaHei", 10),
                  bg=COLOR_CHEEK, fg="#7a4a4a",
                  activebackground="#d8a5a5",
                  relief="flat", bd=0, cursor="hand2",
                  padx=16, pady=4).pack(pady=16)
        # 弹窗居中到主窗口
        win.update_idletasks()
        w, h = win.winfo_width(), win.winfo_height()
        px, py = self.root.winfo_rootx(), self.root.winfo_rooty()
        pw, ph = self.root.winfo_width(), self.root.winfo_height()
        win.geometry(f"+{px + (pw - w) // 2}+{py + (ph - h) // 2}")

    # ---------- 游戏状态 ----------
    def reset(self):
        cx = COLS // 2
        cy = ROWS // 2
        self.snake = [(cx - i, cy) for i in range(START_LEN)]
        self.direction = (1, 0)     # 当前实际移动方向
        self.next_direction = (1, 0)  # 玩家输入的方向（下一拍生效）
        self.score = 0
        self.level = 0              # 速度等级
        self.paused = False
        self.game_over = False
        self.game_over_reason = ""
        self.moved = False          # 是否已经起步
        self.eat_flash = None       # (格子, 文案, 剩余显示拍数)
        self._update_hud()

        self.generate_obstacles()   # 每次重开，障碍物重新随机
        self.spawn_food()

    def _speed_ms(self):
        """当前移动间隔：每升一级加快 SPEED_STEP 毫秒。"""
        return max(MIN_SPEED, BASE_SPEED - self.level * SPEED_STEP)

    def _update_hud(self):
        self.score_var.set(f"得分: {self.score}    速度等级: Lv.{self.level}")

    def add_obstacle_block(self):
        """升级时新增一个障碍块，避开蛇、食物、已有障碍和蛇头附近。"""
        hx, hy = self.snake[0]
        occupied = set(self.snake) | self.obstacles
        if self.food:
            occupied.add(self.food)
        candidates = [
            (x, y)
            for x in range(COLS) for y in range(ROWS)
            if (x, y) not in occupied
            # 蛇头附近 5x5 区域不放，避免凭空砸在蛇前面
            and abs(x - hx) > 2 and abs(y - hy) > 2
        ]
        if candidates:
            self.obstacles.add(random.choice(candidates))

    def generate_obstacles(self):
        """随机生成若干障碍物簇，避开出生点安全区和蛇身。"""
        self.obstacles = set()
        hx, hy = self.snake[0]
        allowed = {
            (x, y)
            for x in range(COLS) for y in range(ROWS)
            if abs(x - hx) > SAFE_RADIUS or abs(y - hy) > SAFE_RADIUS
        }
        allowed -= set(self.snake)
        pool = list(allowed)
        random.shuffle(pool)

        used = 0
        for seed in pool:
            if used >= OBSTACLE_GROUPS:
                break
            if seed in self.obstacles:
                continue
            cluster = [seed]
            self.obstacles.add(seed)
            size = random.randint(2, 5)
            for _ in range(size - 1):
                near = []
                for (x, y) in cluster:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        n = (x + dx, y + dy)
                        if n in allowed and n not in self.obstacles:
                            near.append(n)
                if not near:
                    break
                n = random.choice(near)
                self.obstacles.add(n)
                cluster.append(n)
            used += 1

    def spawn_food(self):
        """在空白格随机放一个食物，样式也随机。"""
        occupied = set(self.snake) | self.obstacles
        empty = [(x, y) for x in range(COLS) for y in range(ROWS)
                 if (x, y) not in occupied]
        if not empty:
            self.food = None
            return
        self.food = random.choice(empty)
        self.food_kind = random.choice(list(FOOD_STYLES))

    # ---------- 输入：只改变方向，蛇自己走 ----------
    def on_key(self, event):
        key = event.keysym.lower()

        if key == "escape":         # Esc 退出（带确认）
            self.quit_game()
            return
        if key in ("equal", "kp_add"):        # + 放大
            self.change_zoom(+ZOOM_STEP)
            return
        if key in ("minus", "kp_subtract"):   # - 缩小
            self.change_zoom(-ZOOM_STEP)
            return

        if self.state == "menu":    # 开始界面：回车也能开吃
            if key == "return":
                self.start_game()
            return

        if self.game_over:
            if key == "return":
                self.start_game()
            return

        if key == "space":          # 空格暂停 / 继续
            self.paused = not self.paused
            self.draw()
            return

        direction = KEY_DIRS.get(key)
        if direction is None:
            return

        # 禁止 180 度掉头（原地撞上自己的脖子）
        if direction == (-self.direction[0], -self.direction[1]):
            return

        self.next_direction = direction

    # ---------- 主循环：蛇自动移动 ----------
    def tick(self):
        if (self.state == "playing" and not self.paused
                and not self.game_over):
            # 应用玩家输入的方向
            if self.next_direction != (-self.direction[0], -self.direction[1]):
                self.direction = self.next_direction
            if not self.moved:
                self.moved = True
            self.step()
            # 飘字倒计时
            if self.eat_flash:
                cell, text, ttl = self.eat_flash
                ttl -= 1
                self.eat_flash = (cell, text, ttl) if ttl > 0 else None

        if self.state != "menu":    # 开始界面是静态的，不必每帧重绘
            self.draw()
        self.root.after(self._speed_ms(), self.tick)

    # ---------- 走一步 ----------
    def step(self):
        hx, hy = self.snake[0]
        nx, ny = hx + self.direction[0], hy + self.direction[1]

        # 撞墙
        if not (0 <= nx < COLS and 0 <= ny < ROWS):
            self.game_over = True
            self.game_over_reason = "撞到墙了"
            return

        # 撞障碍物
        if (nx, ny) in self.obstacles:
            self.game_over = True
            self.game_over_reason = "撞到障碍物了"
            return

        # 撞到自己（尾巴这一格本次会移走，所以不算）
        if (nx, ny) in self.snake[:-1]:
            self.game_over = True
            self.game_over_reason = "咬到自己了"
            return

        self.snake.insert(0, (nx, ny))
        if (nx, ny) == self.food:
            old_level = self.level
            self.score += 10
            self.level = self.score // LEVEL_SCORE
            self.eat_flash = ((nx, ny), f"{FOOD_NAMES[self.food_kind]} +10", 4)
            self.spawn_food()
            # 每 LEVEL_SCORE 分：提速 + 新增一个障碍块
            if self.level > old_level:
                self.add_obstacle_block()
                self.eat_flash = ((nx, ny),
                                  "升级！速度加快，新增障碍块", 4)
            self._update_hud()
        else:
            self.snake.pop()

    # ---------- 绘制小工具 ----------
    def _center(self, cell):
        """格子坐标 -> 画布中心点（随缩放变化）"""
        x, y = cell
        return (x * self.cell + self.cell / 2,
                y * self.cell + self.cell / 2)

    @staticmethod
    def _cell_bg(cell):
        """该格的底色（棋盘交错色）"""
        x, y = cell
        return COLOR_BG_ALT if (x + y) % 2 == 0 else COLOR_BG

    # ---------- 绘制：棋盘 ----------
    def draw_grid(self):
        c = self.cell
        for y in range(ROWS):
            for x in range(COLS):
                if (x + y) % 2 == 0:
                    self.canvas.create_rectangle(
                        x * c, y * c, x * c + c, y * c + c,
                        fill=COLOR_BG_ALT, outline="")

    # ---------- 绘制：障碍物 ----------
    def draw_obstacles(self):
        c = self.cell
        pad = max(1, round(c * 0.1))
        rad = round(c * 0.35)
        hl = max(2, round(c * 0.3))     # 高光离边角的距离
        for (x, y) in self.obstacles:
            x0, y0 = x * c, y * c
            # 圆润的鹅卵石（平滑多边形做出圆角）
            pts = [
                x0 + pad + rad, y0 + pad,
                x0 + c - pad - rad, y0 + pad,
                x0 + c - pad, y0 + pad + rad,
                x0 + c - pad, y0 + c - pad - rad,
                x0 + c - pad - rad, y0 + c - pad,
                x0 + pad + rad, y0 + c - pad,
                x0 + pad, y0 + c - pad - rad,
                x0 + pad, y0 + pad + rad,
            ]
            self.canvas.create_polygon(pts, fill=COLOR_ROCK,
                                       outline=COLOR_ROCK_EDGE, width=1,
                                       smooth=True, splinesteps=12)
            # 石头的柔和高光
            self.canvas.create_line(
                x0 + hl, y0 + c - hl, x0 + hl, y0 + hl,
                fill=COLOR_ROCK_LIGHT, width=2, capstyle="round")
            self.canvas.create_line(
                x0 + hl, y0 + hl, x0 + c - hl, y0 + hl,
                fill=COLOR_ROCK_LIGHT, width=2, capstyle="round")

    # ---------- 绘制：食物（多种样式，随机出现） ----------
    def draw_food(self):
        if not self.food:
            return
        cx, cy = self._center(self.food)
        FOOD_STYLES[self.food_kind](self.canvas, cx, cy, self.cell * 0.52,
                                    self._cell_bg(self.food))

    # ---------- 绘制：蛇 ----------
    def draw_snake(self):
        c = self.cell
        path = []
        for cell in self.snake:
            path.extend(self._center(cell))

        if len(self.snake) > 2:
            # 1) 柔和投影，让蛇从浅色背景上"浮"起来
            off = max(2, round(c * 0.15))
            shadow = [p + off for p in path]
            self.canvas.create_line(*shadow, fill=COLOR_SHADOW,
                                    width=c - 6, smooth=True,
                                    splinesteps=16,
                                    capstyle="round", joinstyle="round")
            # 2) 描边
            self.canvas.create_line(*path, fill=COLOR_SNAKE_EDGE,
                                    width=c - 2, smooth=True,
                                    splinesteps=16,
                                    capstyle="round", joinstyle="round")
            # 3) 主体
            self.canvas.create_line(*path, fill=COLOR_SNAKE,
                                    width=c - 7, smooth=True,
                                    splinesteps=16,
                                    capstyle="round", joinstyle="round")
            # 4) 腹部高光条纹（细一号，显得圆润可爱）
            self.canvas.create_line(*path, fill=COLOR_SNAKE_BELLY,
                                    width=max(2, round(c * 0.2)),
                                    smooth=True, splinesteps=16,
                                    capstyle="round", joinstyle="round")
        else:  # 兜底：蛇很短时直接画圆点
            for cell in self.snake:
                cx, cy = self._center(cell)
                rr = (c - 7) / 2
                self.canvas.create_oval(cx - rr, cy - rr, cx + rr, cy + rr,
                                        fill=COLOR_SNAKE, outline="")

        # 圆圆的尾尖
        tr = max(2, round(c * 0.2))
        tx, ty = self._center(self.snake[-1])
        self.canvas.create_oval(tx - tr, ty - tr, tx + tr, ty + tr,
                                fill=COLOR_SNAKE, outline=COLOR_SNAKE_EDGE)

        self.draw_head()

    def draw_head(self):
        c = self.cell
        cx, cy = self._center(self.snake[0])
        dx, dy = self.direction
        px, py = -dy, dx              # 垂直于朝向的单位向量
        r = c * 0.62                  # 脑袋比身体略大，更萌

        # 小舌头（先画，根部被头部盖住）
        tip = r * 1.45
        fork = r * 0.26
        mx, my = cx + dx * tip * 0.85, cy + dy * tip * 0.85
        ex, ey = cx + dx * tip, cy + dy * tip
        self.canvas.create_line(cx + dx * r * 0.7, cy + dy * r * 0.7,
                                mx, my, fill=COLOR_TONGUE,
                                width=2, capstyle="round")
        self.canvas.create_line(mx, my,
                                ex + px * fork, ey + py * fork,
                                fill=COLOR_TONGUE, width=2, capstyle="round")
        self.canvas.create_line(mx, my,
                                ex - px * fork, ey - py * fork,
                                fill=COLOR_TONGUE, width=2, capstyle="round")

        # 脑袋
        self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                fill=COLOR_HEAD, outline=COLOR_HEAD_EDGE,
                                width=2)
        # 头顶柔光
        self.canvas.create_oval(cx - r * 0.55, cy - r * 0.75,
                                cx - r * 0.05, cy - r * 0.28,
                                fill=COLOR_SNAKE_BELLY, outline="")

        # 大眼睛：白眼球 + 深瞳 + 高光小点
        er = c * 0.19
        for sign in (1, -1):
            ox = cx + dx * r * 0.30 + px * r * 0.42 * sign
            oy = cy + dy * r * 0.30 + py * r * 0.42 * sign
            self.canvas.create_oval(ox - er, oy - er, ox + er, oy + er,
                                    fill=COLOR_EYE, outline=COLOR_HEAD_EDGE)
            pr = er * 0.6
            gx = ox + dx * er * 0.30
            gy = oy + dy * er * 0.30
            self.canvas.create_oval(gx - pr, gy - pr, gx + pr, gy + pr,
                                    fill=COLOR_PUPIL, outline="")
            sr = er * 0.22
            self.canvas.create_oval(gx - sr - er * 0.25,
                                    gy - sr - er * 0.30,
                                    gx + sr - er * 0.25,
                                    gy + sr - er * 0.30,
                                    fill=COLOR_EYE, outline="")

        # 腮红：眼睛后方两团藕粉色
        for sign in (1, -1):
            bx = cx - dx * r * 0.18 + px * r * 0.72 * sign
            by = cy - dy * r * 0.18 + py * r * 0.72 * sign
            br = r * 0.26
            self.canvas.create_oval(bx - br, by - br * 0.75,
                                    bx + br, by + br * 0.75,
                                    fill=COLOR_CHEEK, outline="")

    # ---------- 总绘制 ----------
    def draw(self):
        self.canvas.delete("all")

        self.draw_grid()
        self.draw_obstacles()
        self.draw_food()
        self.draw_snake()

        if self.eat_flash:
            (fx, fy), text, _ttl = self.eat_flash
            cx, cy = self._center((fx, fy))
            self.canvas.create_text(cx, cy - self.cell * 0.95, text=text,
                                    fill=COLOR_TEXT,
                                    font=self._font(10, bold=True))

        if self.state == "menu":
            self._draw_menu()
        elif self.game_over:
            self._draw_card(self.game_over_reason, f"得分: {self.score}",
                            "按回车再来一局")
        elif self.paused:
            self.canvas.create_text(
                self.width / 2, self.height / 2, fill=COLOR_TEXT,
                font=self._font(20, bold=True),
                text="已暂停（按空格继续）")
        elif not self.moved:
            self.canvas.create_text(
                self.width / 2, self.height - 18, fill=COLOR_HINT,
                font=self._font(11),
                text="方向键 / WASD 转向，空格暂停；每 50 分提速并新增障碍块")

    def _rounded_card(self, pad_x_ratio, pad_y_ratio, rad_ratio=0.055):
        """以画布中心画一张圆角卡片（尺寸随缩放变化）"""
        pad_x = self.width * pad_x_ratio
        pad_y = self.height * pad_y_ratio
        x0, y0 = self.width / 2 - pad_x, self.height / 2 - pad_y
        x1, y1 = self.width / 2 + pad_x, self.height / 2 + pad_y
        rad = self.cell * rad_ratio * 2
        pts = [
            x0 + rad, y0, x1 - rad, y0, x1, y0 + rad, x1, y1 - rad,
            x1 - rad, y1, x0 + rad, y1, x0, y1 - rad, x0, y0 + rad,
        ]
        self.canvas.create_polygon(pts, fill=COLOR_CARD,
                                   outline=COLOR_CARD_EDGE, width=2,
                                   smooth=True, splinesteps=16)

    def _draw_menu(self):
        """开始界面：棋盘作背景，中间一张圆角卡片 + 「开吃！」按钮"""
        self._rounded_card(0.325, 0.295)
        cx, cy = self.width / 2, self.height / 2
        self.canvas.create_text(cx, cy - self.height * 0.165, text="贪吃蛇",
                                fill=COLOR_TEXT,
                                font=self._font(30, bold=True))
        self.canvas.create_text(cx, cy - self.height * 0.055,
                                text="莫兰迪小吃街，开饭啦～",
                                fill=COLOR_HINT, font=self._font(12))
        # 「开吃！」按钮是实体控件，位于卡片中部（rely 0.60）
        self.canvas.create_text(cx, cy + self.height * 0.23,
                                text="方向键转向 · 空格暂停 · 每 50 分提速",
                                fill=COLOR_HINT, font=self._font(10))

    def _draw_card(self, line1, line2, line3):
        """游戏结束的圆角卡片"""
        self._rounded_card(0.217, 0.165)
        cx, cy = self.width / 2, self.height / 2
        self.canvas.create_text(cx, cy - self.height * 0.075, text=line1,
                                fill=COLOR_TEXT,
                                font=self._font(18, bold=True))
        self.canvas.create_text(cx, cy + self.height * 0.005, text=line2,
                                fill=COLOR_TEXT, font=self._font(14))
        self.canvas.create_text(cx, cy + self.height * 0.085, text=line3,
                                fill=COLOR_HINT, font=self._font(12))


# 食物样式表：名字 -> 绘制函数
FOOD_STYLES = {
    "apple": draw_apple,
    "cupcake": draw_cupcake,
    "waterdrop": draw_waterdrop,
    "grass": draw_grass,
}

FOOD_NAMES = {
    "apple": "苹果",
    "cupcake": "小蛋糕",
    "waterdrop": "水滴",
    "grass": "小草",
}

RULE_LINES = (
    "1. 小蛇会自动前进，方向键 / WASD 只负责转向；",
    "2. 吃到食物 +10 分，食物样式随机出现；",
    "3. 每 50 分升一级：速度加快，并新增一个障碍块；",
    "4. 撞到石块、撞到墙或咬到自己，游戏结束；",
    "5. 空格 暂停 / 继续；结束后按回车再来一局；",
    "6. 底部「－ / ＋」或 +/- 键缩放画面；右上角「退出」或 Esc 退出游戏。",
)


if __name__ == "__main__":
    root = tk.Tk()
    root.resizable(False, False)
    SnakeGame(root)
    root.mainloop()
