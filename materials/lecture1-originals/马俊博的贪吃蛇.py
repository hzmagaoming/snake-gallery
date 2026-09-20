"""
贪吃蛇（tkinter 版，真实化外观）
方向键 / WASD 控制，空格暂停，回车重开
"""
import random
import tkinter as tk

CELL = 22          # 每格像素
COLS = 24          # 横向格数
ROWS = 24          # 纵向格数
SPEED = 110        # 移动间隔(ms)，越小越快


def lerp(a, b, t):
    return int(a + (b - a) * t)


def body_color(i, n):
    """蛇身渐变：头(亮绿) -> 尾(深绿)"""
    t = i / max(n - 1, 1)
    r = lerp(70, 22, t)
    g = lerp(225, 110, t)
    b = lerp(75, 35, t)
    return f"#{r:02x}{g:02x}{b:02x}"


class Snake:
    def __init__(self, root):
        self.root = root
        self.root.title("贪吃蛇")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=COLS * CELL, height=ROWS * CELL,
                                bg="#15241a", highlightthickness=0)
        self.canvas.pack()

        self.label = tk.Label(root, text="方向键/WASD 移动 · 空格暂停 · 回车重开",
                              font=("Consolas", 11), bg="#22332a", fg="#cccccc")
        self.label.pack(fill=tk.X)

        self.reset()
        self.root.bind("<Key>", self.on_key)
        self.tick()

    def reset(self):
        self.snake = [(COLS // 2, ROWS // 2)]
        self.dir = (1, 0)
        self.next_dir = (1, 0)
        self.alive = True
        self.paused = False
        self.score = 0
        self.frame = 0
        self.spawn_food()
        self.draw()

    def spawn_food(self):
        empty = [(x, y) for x in range(COLS) for y in range(ROWS)
                 if (x, y) not in self.snake]
        self.food = random.choice(empty) if empty else None

    def on_key(self, e):
        k = e.keysym
        if k in ("Return",):
            self.reset()
        elif k in ("space",):
            if self.alive:
                self.paused = not self.paused
        elif k in ("Up", "w", "W") and self.dir != (0, 1):
            self.next_dir = (0, -1)
        elif k in ("Down", "s", "S") and self.dir != (0, -1):
            self.next_dir = (0, 1)
        elif k in ("Left", "a", "A") and self.dir != (1, 0):
            self.next_dir = (-1, 0)
        elif k in ("Right", "d", "D") and self.dir != (-1, 0):
            self.next_dir = (1, 0)

    def tick(self):
        if self.alive and not self.paused:
            self.frame += 1
            self.step()
        self.root.after(SPEED, self.tick)

    def step(self):
        self.dir = self.next_dir
        head = (self.snake[0][0] + self.dir[0], self.snake[0][1] + self.dir[1])

        # 撞墙或撞自己 -> 死亡
        if (head[0] < 0 or head[0] >= COLS or head[1] < 0 or head[1] >= ROWS
                or head in self.snake):
            self.alive = False
            self.draw()
            return

        self.snake.insert(0, head)
        if head == self.food:
            self.score += 1
            self.spawn_food()
        else:
            self.snake.pop()

        self.draw()

    def draw(self):
        self.canvas.delete("all")
        self.draw_grid()
        n = len(self.snake)
        # 从尾到头绘制，保证头在最上层
        for idx in range(n - 1, -1, -1):
            x, y = self.snake[idx]
            cx, cy = x * CELL + CELL / 2, y * CELL + CELL / 2
            if idx == 0:
                self.draw_head(cx, cy)
            else:
                r = CELL * 0.46
                col = body_color(idx, n)
                self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                        fill=col, outline="#0d3311", width=1)
                # 鳞片高光
                self.canvas.create_oval(cx - r * 0.5, cy - r * 0.55,
                                        cx + r * 0.1, cy - r * 0.05,
                                        fill="#bff5b0", outline="", stipple="gray25")

        self.draw_food()

        self.canvas.create_text(COLS * CELL - 6, 6, anchor="ne",
                                text=f"得分: {self.score}", fill="#ffffff",
                                font=("Consolas", 12))
        if not self.alive:
            self.overlay("游戏结束 · 回车重开", "#ff6b6b")
        elif self.paused:
            self.overlay("已暂停", "#ffeb3b")

    def draw_grid(self):
        for i in range(1, COLS):
            self.canvas.create_line(i * CELL, 0, i * CELL, ROWS * CELL,
                                    fill="#1c3326", width=1)
        for j in range(1, ROWS):
            self.canvas.create_line(0, j * CELL, COLS * CELL, j * CELL,
                                    fill="#1c3326", width=1)

    def draw_head(self, cx, cy):
        r = CELL * 0.5
        dx, dy = self.dir
        px, py = -dy, dx  # 垂直于行进方向的向量

        # 头部
        self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                fill="#46e34b", outline="#0d3311", width=1)

        # 吐信（每 6 帧闪现约一半时间）
        if self.alive and not self.paused and self.frame % 6 < 3:
            fx, fy = cx + dx * (r + 1), cy + dy * (r + 1)
            tx, ty = cx + dx * (r + 10), cy + dy * (r + 10)
            self.canvas.create_line(fx, fy, tx, ty, fill="#ff4d6d", width=2)
            f1 = (tx + dx * 4 - py * 4, ty + dy * 4 - px * 4)
            f2 = (tx + dx * 4 + py * 4, ty + dy * 4 + px * 4)
            self.canvas.create_line(tx, ty, *f1, fill="#ff4d6d", width=1.5)
            self.canvas.create_line(tx, ty, *f2, fill="#ff4d6d", width=1.5)

        # 眼睛（朝行进方向前移）
        e_fwd = r * 0.38
        e_off = r * 0.5
        for s in (1, -1):
            ex = cx + dx * e_fwd + px * e_off * s
            ey = cy + dy * e_fwd + py * e_off * s
            self.canvas.create_oval(ex - 3.2, ey - 3.2, ex + 3.2, ey + 3.2,
                                    fill="white", outline="")
            self.canvas.create_oval(ex - 1.4, ey - 1.4, ex + 1.4, ey + 1.4,
                                    fill="black", outline="")
            # 高光
            self.canvas.create_oval(ex - 1.2, ey - 1.6, ex - 0.2, ey - 0.6,
                                    fill="white", outline="")

    def draw_food(self):
        if not self.food:
            return
        x, y = self.food
        cx, cy = x * CELL + CELL / 2, y * CELL + CELL / 2
        r = CELL * 0.4
        # 苹果
        self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                fill="#e53935", outline="#a31515", width=1)
        # 高光
        self.canvas.create_oval(cx - r * 0.55, cy - r * 0.6, cx - r * 0.05,
                                cy - r * 0.1, fill="#ff8a80", outline="")
        # 果柄
        self.canvas.create_line(cx, cy - r, cx + 2, cy - r - 5,
                                fill="#6d4c41", width=2)
        # 叶子
        self.canvas.create_oval(cx + 2, cy - r - 7, cx + 9, cy - r - 2,
                                fill="#66bb6a", outline="")

    def overlay(self, text, color):
        self.canvas.create_rectangle(0, 0, COLS * CELL, ROWS * CELL,
                                     fill="#000000", stipple="gray50", outline="")
        self.canvas.create_text(COLS * CELL / 2, ROWS * CELL / 2,
                                text=text, fill=color,
                                font=("Consolas", 18), anchor="center")


if __name__ == "__main__":
    Snake(tk.Tk()).root.mainloop()
