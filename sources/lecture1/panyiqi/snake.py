import tkinter as tk
import random
import time

# ---------------- 配置 ----------------
CELL = 25
COLS, ROWS = 30, 24                     # 比原来更大的棋盘
WIDTH, HEIGHT = COLS * CELL, ROWS * CELL

BG        = '#0f0c29'                   # 窗口背景（深紫）
BOARD_BG  = '#1a1642'                   # 棋盘背景
GRID      = '#252058'                   # 网格线
TEXT      = '#f1f5f9'
SUB       = '#8b9dc3'
ACCENT    = '#22d3ee'                   # 青色
ACCENT2   = '#a78bfa'                   # 紫色

# 蛇身渐变：翠绿 → 青色 → 紫色
SNAKE_C1  = (52, 211, 153)
SNAKE_C2  = (34, 211, 238)
SNAKE_C3  = (167, 139, 250)
FOOD_RGB  = (251, 113, 133)             # 食物粉红
BOARD_RGB = (26, 22, 66)


def mix(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def hexc(c):
    return '#{:02x}{:02x}{:02x}'.format(c[0], c[1], c[2])


def snake_color(t):
    """t=0 头部，t=1 尾部"""
    t = max(0.0, min(1.0, t))
    if t <= 0.5:
        return hexc(mix(SNAKE_C1, SNAKE_C2, t * 2))
    return hexc(mix(SNAKE_C2, SNAKE_C3, (t - 0.5) * 2))


class SnakeGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("贪吃蛇 · Snake")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        # ---------- 顶部信息栏 ----------
        hud = tk.Frame(self.root, bg=BG, height=58)
        hud.pack(fill='x')
        hud.pack_propagate(False)

        self.score_var = tk.StringVar(value='0')
        self.best_var  = tk.StringVar(value='0')

        left = tk.Frame(hud, bg=BG)
        left.pack(side='left', padx=(26, 0))
        tk.Label(left, text='分数', bg=BG, fg=SUB,
                 font=('Microsoft YaHei UI', 10)).pack(side='left')
        tk.Label(left, textvariable=self.score_var, bg=BG, fg=ACCENT,
                 font=('Consolas', 20, 'bold')).pack(side='left', padx=(8, 0))

        right = tk.Frame(hud, bg=BG)
        right.pack(side='right', padx=(0, 26))
        tk.Label(right, textvariable=self.best_var, bg=BG, fg=ACCENT2,
                 font=('Consolas', 20, 'bold')).pack(side='right')
        tk.Label(right, text='最高', bg=BG, fg=SUB,
                 font=('Microsoft YaHei UI', 10)).pack(side='right', padx=(0, 8))

        # ---------- 画布 ----------
        self.canvas = tk.Canvas(self.root, width=WIDTH, height=HEIGHT,
                                bg=BOARD_BG, highlightthickness=0)
        self.canvas.pack(padx=14, pady=(0, 14))

        # 只绑定方向键（不会触发输入法）
        self.root.bind('<Up>',     lambda e: self.turn(0, -1))
        self.root.bind('<Down>',   lambda e: self.turn(0, 1))
        self.root.bind('<Left>',   lambda e: self.turn(-1, 0))
        self.root.bind('<Right>',  lambda e: self.turn(1, 0))
        self.root.bind('<Escape>', lambda e: self.toggle_pause())
        self.root.bind('<r>',      lambda e: self.restart())
        self.root.bind('<R>',      lambda e: self.restart())

        self._draw_grid()
        self.reset()
        self.last_time = None
        self.tick()
        self.root.mainloop()

    # ---------------- 状态 ----------------
    def reset(self):
        cx, cy = COLS // 2, ROWS // 2
        self.snake = [(cx + 1, cy), (cx, cy), (cx - 1, cy)]
        self.direction = (1, 0)
        self.queue = []
        self.score = 0
        self.best  = getattr(self, 'best', 0)
        self.state = 'ready'            # ready | running | paused | over | win
        self.step_ms = 115
        self.acc = 0.0
        self.place_food()
        self.score_var.set('0')
        self.best_var.set(str(self.best))

    def restart(self):
        self.reset()
        self.state = 'running'

    def toggle_pause(self):
        if self.state == 'running':
            self.state = 'paused'
        elif self.state == 'paused':
            self.state = 'running'
        elif self.state == 'ready':
            self.state = 'running'

    def place_food(self):
        occupied = set(self.snake)
        free = [(x, y) for y in range(ROWS) for x in range(COLS)
                if (x, y) not in occupied]
        if free:
            self.food = random.choice(free)
        else:
            self.food = None
            self.state = 'win'

    # ---------------- 操作 ----------------
    def turn(self, dx, dy):
        if self.state == 'ready':
            self.state = 'running'
        if self.state != 'running':
            return

        last = self.queue[-1] if self.queue else self.direction
        if (dx, dy) == last:
            return
        if (dx, dy) == (-last[0], -last[1]):
            return
        if len(self.queue) < 2:
            self.queue.append((dx, dy))

    def step(self):
        if self.queue:
            self.direction = self.queue.pop(0)

        hx, hy = self.snake[0]
        nx, ny = hx + self.direction[0], hy + self.direction[1]

        if not (0 <= nx < COLS and 0 <= ny < ROWS):
            return self.game_over()

        will_eat = self.food is not None and (nx, ny) == self.food
        body = self.snake if will_eat else self.snake[:-1]
        if (nx, ny) in body:
            return self.game_over()

        self.snake.insert(0, (nx, ny))
        if will_eat:
            self.score += 10
            self.score_var.set(str(self.score))
            self.step_ms = max(55, self.step_ms - 2)
            self.place_food()
        else:
            self.snake.pop()

    def game_over(self):
        self.state = 'over'
        self.best = max(self.best, self.score)
        self.best_var.set(str(self.best))

    # ---------------- 主循环 ----------------
    def tick(self):
        t = time.time() * 1000
        if self.last_time is None:
            self.last_time = t
        dt = min(t - self.last_time, 200)
        self.last_time = t

        if self.state == 'running':
            self.acc += dt
            while self.acc >= self.step_ms and self.state == 'running':
                self.acc -= self.step_ms
                self.step()

        self.draw()
        self.root.after(16, self.tick)

    # ---------------- 绘制 ----------------
    def _draw_grid(self):
        c = self.canvas
        for i in range(1, COLS):
            c.create_line(i * CELL, 0, i * CELL, HEIGHT, fill=GRID)
        for i in range(1, ROWS):
            c.create_line(0, i * CELL, WIDTH, i * CELL, fill=GRID)

    def draw(self):
        c = self.canvas
        c.delete('dyn')

        # ---------- 食物（带光晕） ----------
        if self.food:
            fx, fy = self.food
            cx = fx * CELL + CELL / 2
            cy = fy * CELL + CELL / 2

            # 外圈光晕
            for k in range(4, 0, -1):
                r = CELL / 2 - 4 + k * 2
                col = hexc(mix(FOOD_RGB, BOARD_RGB, k / 4.5))
                c.create_oval(cx - r, cy - r, cx + r, cy + r,
                              fill=col, outline='', tags='dyn')

            # 果肉
            r = CELL / 2 - 4
            c.create_oval(cx - r, cy - r, cx + r, cy + r,
                          fill=hexc(FOOD_RGB), outline='', tags='dyn')

            # 高光
            c.create_oval(cx - r * 0.55, cy - r * 0.75,
                          cx - r * 0.05, cy - r * 0.25,
                          fill='#ffe4e6', outline='', tags='dyn')

        # ---------- 蛇身 ----------
        n = len(self.snake)
        if n > 0:
            # 身体：用圆头粗线连成一整条
            for i in range(n - 1):
                x1, y1 = self.snake[i]
                x2, y2 = self.snake[i + 1]
                cx1 = x1 * CELL + CELL / 2
                cy1 = y1 * CELL + CELL / 2
                cx2 = x2 * CELL + CELL / 2
                cy2 = y2 * CELL + CELL / 2
                col = snake_color((i + 0.5) / n)
                c.create_line(cx1, cy1, cx2, cy2,
                              fill=col, width=CELL - 4,
                              capstyle='round', tags='dyn')

            # 头部圆形
            hx, hy = self.snake[0]
            hcx = hx * CELL + CELL / 2
            hcy = hy * CELL + CELL / 2
            hr = CELL / 2 - 1
            c.create_oval(hcx - hr, hcy - hr, hcx + hr, hcy + hr,
                          fill=snake_color(0), outline='', tags='dyn')

            # 眼睛
            dx, dy = self.direction
            px, py = -dy, dx
            for s in (1, -1):
                ex = hcx + dx * 5 + px * 3.8 * s
                ey = hcy + dy * 5 + py * 3.8 * s
                c.create_oval(ex - 2.8, ey - 2.8, ex + 2.8, ey + 2.8,
                              fill='#0b1029', outline='', tags='dyn')
                c.create_oval(ex - 1.2, ey - 1.4, ex + 0.6, ey + 0.4,
                              fill='#ffffff', outline='', tags='dyn')

        # ---------- 状态遮罩 ----------
        if self.state != 'running':
            c.create_rectangle(0, 0, WIDTH, HEIGHT,
                               fill=BG, outline='', tags='dyn')

            if self.state == 'ready':
                title, sub, tc = '贪 吃 蛇', '按 方 向 键 开 始', ACCENT
            elif self.state == 'paused':
                title, sub, tc = '暂 停 中', '按 Esc 继续游戏', TEXT
            elif self.state == 'over':
                title, sub, tc = '游 戏 结 束', f'得分 {self.score} · 按 R 重新开始', '#fb7185'
            else:
                title, sub, tc = '恭 喜 通 关', '按 R 再来一局', '#fbbf24'

            c.create_text(WIDTH / 2, HEIGHT / 2 - 26, text=title,
                          fill=tc, font=('Microsoft YaHei UI', 34, 'bold'),
                          tags='dyn')
            c.create_text(WIDTH / 2, HEIGHT / 2 + 28, text=sub,
                          fill=SUB, font=('Microsoft YaHei UI', 13),
                          tags='dyn')


if __name__ == '__main__':
    SnakeGame()