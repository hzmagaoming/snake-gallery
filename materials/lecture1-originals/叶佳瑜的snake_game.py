import random
import tkinter as tk


CELL_SIZE = 24
COLS = 28
ROWS = 20
WIDTH = COLS * CELL_SIZE
HEIGHT = ROWS * CELL_SIZE
DIFFICULTIES = {
    "低": {"speed": 165, "grass": 5},
    "中": {"speed": 125, "grass": 10},
    "高": {"speed": 90, "grass": 15},
}


class SnakeGame:
    def __init__(self, root):
        self.root = root
        self.root.title("花园贪吃蛇")
        self.root.configure(bg="#e9f5df")
        self.root.resizable(False, False)

        self.difficulty = tk.StringVar(value="中")
        header = tk.Frame(root, bg="#e9f5df")
        header.pack(fill="x", padx=14, pady=(10, 6))
        self.score_label = tk.Label(
            header, text="得分  0", fg="#275d38", bg="#e9f5df",
            font=("Microsoft YaHei", 17, "bold")
        )
        self.score_label.pack(side="left")
        tk.Label(
            header, text="🍬 +10    🍰 +20", fg="#527a55", bg="#e9f5df",
            font=("Apple Color Emoji", 13)
        ).pack(side="right")

        level_bar = tk.Frame(root, bg="#e9f5df")
        level_bar.pack(fill="x", padx=14, pady=(0, 7))
        tk.Label(
            level_bar, text="选择难度：", fg="#275d38", bg="#e9f5df",
            font=("Microsoft YaHei", 12, "bold")
        ).pack(side="left")
        for level in ("低", "中", "高"):
            config = DIFFICULTIES[level]
            tk.Radiobutton(
                level_bar,
                text=f"{level}（🌿×{config['grass']}）",
                variable=self.difficulty,
                value=level,
                command=self.reset,
                bg="#e9f5df",
                fg="#356b43",
                activebackground="#e9f5df",
                selectcolor="#d5ebc7",
                font=("Microsoft YaHei", 11),
            ).pack(side="left", padx=(0, 10))
        self.pause_button = tk.Button(
            level_bar, text="暂停（P）", command=self.toggle_pause,
            bg="#4f9b5f", fg="white", activebackground="#3d814c",
            activeforeground="white", relief="flat", padx=12,
            font=("Microsoft YaHei", 11, "bold"), cursor="hand2"
        )
        self.pause_button.pack(side="right")

        self.canvas = tk.Canvas(
            root, width=WIDTH, height=HEIGHT, bg="#cfe8b4",
            highlightthickness=3, highlightbackground="#7aaa62"
        )
        self.canvas.pack(padx=14, pady=(0, 8))
        rules = (
            "游戏规则：只能吃 🍬 糖果（+10 分）和 🍰 蛋糕（+20 分）\n"
            "不能撞墙、撞自己或撞到 🌿 小草｜方向键 / WASD 移动｜P 键暂停｜空格键重新开始"
        )
        tk.Label(
            root, text=rules, fg="#416a48", bg="#e9f5df",
            font=("Microsoft YaHei", 11), justify="center"
        ).pack(pady=(0, 10))

        self.root.bind("<KeyPress>", self.change_direction)
        self.root.bind("<space>", self.restart)
        self.root.bind("<p>", self.toggle_pause)
        self.root.bind("<P>", self.toggle_pause)
        self.timer = None
        self.reset()

    def reset(self):
        if self.timer is not None:
            self.root.after_cancel(self.timer)
        center_x, center_y = COLS // 2, ROWS // 2
        self.snake = [(center_x, center_y), (center_x - 1, center_y), (center_x - 2, center_y)]
        self.direction = (1, 0)
        self.next_direction = self.direction
        self.score = 0
        settings = DIFFICULTIES[self.difficulty.get()]
        self.base_speed = settings["speed"]
        self.speed = self.base_speed
        self.running = True
        self.paused = False
        self.pause_button.config(text="暂停（P）", state="normal")
        self.obstacle_count = settings["grass"]
        self.obstacles = self.create_obstacles()
        self.foods = {}
        self.foods["candy"] = self.create_food()
        self.foods["cake"] = self.create_food()
        self.draw()
        self.schedule_tick()

    def create_obstacles(self):
        safe = set(self.snake)
        head_x, head_y = self.snake[0]
        safe.update((head_x + x, head_y + y) for x in range(-4, 5) for y in range(-3, 4))
        candidates = [
            (x, y) for x in range(1, COLS - 1) for y in range(1, ROWS - 1)
            if (x, y) not in safe
        ]
        return set(random.sample(candidates, min(self.obstacle_count, len(candidates))))

    def create_food(self):
        occupied_foods = {cell for cell in self.foods.values() if cell is not None}
        free_cells = [
            (x, y) for x in range(COLS) for y in range(ROWS)
            if (x, y) not in self.snake
            and (x, y) not in self.obstacles
            and (x, y) not in occupied_foods
        ]
        return random.choice(free_cells) if free_cells else None

    def change_direction(self, event):
        directions = {
            "Up": (0, -1), "Down": (0, 1), "Left": (-1, 0), "Right": (1, 0),
            "w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0),
            "W": (0, -1), "S": (0, 1), "A": (-1, 0), "D": (1, 0),
        }
        new_direction = directions.get(event.keysym)
        if new_direction and new_direction != (-self.direction[0], -self.direction[1]):
            self.next_direction = new_direction

    def schedule_tick(self):
        self.timer = self.root.after(self.speed, self.tick)

    def tick(self):
        self.timer = None
        if not self.running or self.paused:
            return
        self.direction = self.next_direction
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)
        eaten = next((kind for kind, cell in self.foods.items() if cell == new_head), None)
        grows = eaten is not None
        hits_wall = not (0 <= new_head[0] < COLS and 0 <= new_head[1] < ROWS)
        hits_body = new_head in (self.snake if grows else self.snake[:-1])
        hits_obstacle = new_head in self.obstacles

        if hits_wall or hits_body or hits_obstacle:
            self.game_over()
            return

        self.snake.insert(0, new_head)
        if eaten:
            self.score += 20 if eaten == "cake" else 10
            self.speed = max(50, self.base_speed - (self.score // 60) * 6)
            self.foods[eaten] = self.create_food()
            if self.foods[eaten] is None:
                self.game_over(won=True)
                return
        else:
            self.snake.pop()

        self.draw()
        self.schedule_tick()

    def toggle_pause(self, _event=None):
        if not self.running:
            return
        self.paused = not self.paused
        if self.paused:
            if self.timer is not None:
                self.root.after_cancel(self.timer)
                self.timer = None
            self.pause_button.config(text="继续（P）")
            self.canvas.create_rectangle(
                WIDTH // 2 - 105, HEIGHT // 2 - 42,
                WIDTH // 2 + 105, HEIGHT // 2 + 42,
                fill="#fffaf0", outline="#4c8c55", width=3, tags="pause_overlay"
            )
            self.canvas.create_text(
                WIDTH // 2, HEIGHT // 2, text="游戏已暂停",
                fill="#275d38", font=("Microsoft YaHei", 23, "bold"),
                tags="pause_overlay"
            )
        else:
            self.pause_button.config(text="暂停（P）")
            self.canvas.delete("pause_overlay")
            self.schedule_tick()

    def draw(self):
        self.canvas.delete("all")
        self.score_label.config(text=f"得分  {self.score}")

        for x in range(COLS):
            for y in range(ROWS):
                if (x + y) % 2 == 0:
                    self.canvas.create_rectangle(
                        x * CELL_SIZE, y * CELL_SIZE, (x + 1) * CELL_SIZE,
                        (y + 1) * CELL_SIZE, fill="#c8e2ac", outline=""
                    )

        for cell in self.obstacles:
            self.draw_emoji(cell, "🌿", 17)
        if self.foods.get("candy"):
            self.draw_emoji(self.foods["candy"], "🍬", 18)
        if self.foods.get("cake"):
            self.draw_emoji(self.foods["cake"], "🍰", 18)

        for index in range(len(self.snake) - 1, 0, -1):
            x, y = self.snake[index]
            cx, cy = x * CELL_SIZE + CELL_SIZE / 2, y * CELL_SIZE + CELL_SIZE / 2
            shade = "#4fae58" if index % 2 else "#62bf62"
            self.canvas.create_oval(cx - 10, cy - 10, cx + 10, cy + 10, fill=shade, outline="#348a47", width=1)
            self.canvas.create_oval(cx - 4, cy - 6, cx + 1, cy - 1, fill="#91d77d", outline="")

        self.draw_snake_head()

    def draw_snake_head(self):
        x, y = self.snake[0]
        cx, cy = x * CELL_SIZE + CELL_SIZE / 2, y * CELL_SIZE + CELL_SIZE / 2
        dx, dy = self.direction
        self.canvas.create_oval(cx - 11, cy - 11, cx + 11, cy + 11, fill="#6dce68", outline="#2f8241", width=2)
        px, py = -dy, dx
        for side in (-1, 1):
            ex = cx + dx * 5 + px * side * 5
            ey = cy + dy * 5 + py * side * 5
            self.canvas.create_oval(ex - 3.2, ey - 3.2, ex + 3.2, ey + 3.2, fill="white", outline="")
            self.canvas.create_oval(ex + dx - 1.5, ey + dy - 1.5, ex + dx + 1.5, ey + dy + 1.5, fill="#19351f", outline="")
        tx1, ty1 = cx + dx * 10, cy + dy * 10
        tx2, ty2 = cx + dx * 16, cy + dy * 16
        self.canvas.create_line(tx1, ty1, tx2, ty2, fill="#e64c78", width=2)
        self.canvas.create_line(tx2, ty2, tx2 + px * 3 - dx * 2, ty2 + py * 3 - dy * 2, fill="#e64c78", width=2)
        self.canvas.create_line(tx2, ty2, tx2 - px * 3 - dx * 2, ty2 - py * 3 - dy * 2, fill="#e64c78", width=2)

    def draw_emoji(self, cell, emoji, size):
        x, y = cell
        self.canvas.create_text(
            x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2,
            text=emoji, font=("Apple Color Emoji", size)
        )

    def game_over(self, won=False):
        self.running = False
        self.paused = False
        self.pause_button.config(text="暂停（P）", state="disabled")
        self.canvas.create_rectangle(
            125, 155, WIDTH - 125, HEIGHT - 155,
            fill="#fffaf0", outline="#4c8c55", width=3
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - 30,
            text="花园通关！" if won else "撞到了障碍！",
            fill="#275d38", font=("Microsoft YaHei", 27, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 27,
            text=f"最终得分：{self.score}\n按空格键再玩一次",
            fill="#527a55", font=("Microsoft YaHei", 14), justify="center"
        )

    def restart(self, _event=None):
        if not self.running:
            self.reset()


if __name__ == "__main__":
    app_root = tk.Tk()
    SnakeGame(app_root)
    app_root.mainloop()
