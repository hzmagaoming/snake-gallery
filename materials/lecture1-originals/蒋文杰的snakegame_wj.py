import json
import random
import time
import tkinter as tk
from pathlib import Path


CELL_SIZE = 26
GRID_WIDTH = 26
GRID_HEIGHT = 18
BOARD_WIDTH = GRID_WIDTH * CELL_SIZE
BOARD_HEIGHT = GRID_HEIGHT * CELL_SIZE

BASE_DELAY = 145
MIN_DELAY = 72
LEVEL_SCORE_STEP = 6
COMBO_WINDOW = 2.4
SPECIAL_FOOD_LIFETIME = 6.0

BG_COLOR = "#070b12"
PANEL_COLOR = "#0e1a26"
BOARD_COLOR = "#08131c"
GRID_COLOR = "#142a35"
TEXT_COLOR = "#eef8f6"
MUTED_TEXT = "#8fa6af"
CYAN = "#62e7ff"
GREEN = "#44e08b"
GREEN_DARK = "#078d58"
GREEN_LIGHT = "#a8f3a2"
PINK = "#ff4f8a"
GOLD = "#ffd166"
OBSTACLE = "#b94a5b"

SAVE_FILE = Path(__file__).with_name("snake_save.json")


class SnakeGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Serpent Run - Python Snake")
        self.root.configure(bg=BG_COLOR)
        self.root.minsize(760, 640)

        self.high_score = self.load_high_score()
        self.sound_on = tk.BooleanVar(value=True)
        self.obstacles_on = tk.BooleanVar(value=True)

        self.after_id = None
        self.countdown_after_id = None
        self.game_state = "menu"
        self.countdown_value = 3

        self.snake = []
        self.direction = (1, 0)
        self.direction_queue = []
        self.food = None
        self.special_food = None
        self.obstacles = []
        self.particles = []
        self.floating_texts = []

        self.score = 0
        self.level = 1
        self.combo = 1
        self.last_eat_time = 0
        self.game_over_flash = 0

        self.score_var = tk.StringVar()
        self.high_score_var = tk.StringVar()
        self.level_var = tk.StringVar()
        self.speed_var = tk.StringVar()
        self.combo_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.home_high_score_var = tk.StringVar()

        self.build_ui()
        self.bind_events()
        self.show_home()

    def build_ui(self):
        self.container = tk.Frame(self.root, bg=BG_COLOR)
        self.container.pack(fill="both", expand=True, padx=18, pady=18)

        self.home_frame = tk.Frame(
            self.container,
            bg=PANEL_COLOR,
            highlightthickness=1,
            highlightbackground="#203c48",
        )
        self.game_frame = tk.Frame(
            self.container,
            bg=PANEL_COLOR,
            highlightthickness=1,
            highlightbackground="#203c48",
        )

        self.build_home()
        self.build_game()

    def build_home(self):
        tk.Label(
            self.home_frame,
            text="ARCADE SNAKE",
            font=("Arial", 12, "bold"),
            fg=CYAN,
            bg=PANEL_COLOR,
        ).pack(pady=(72, 10))

        tk.Label(
            self.home_frame,
            text="Serpent Run",
            font=("Arial", 48, "bold"),
            fg=TEXT_COLOR,
            bg=PANEL_COLOR,
        ).pack()

        tk.Label(
            self.home_frame,
            text="Python / Anaconda 版本的霓虹风贪吃蛇小游戏",
            font=("Arial", 15),
            fg=MUTED_TEXT,
            bg=PANEL_COLOR,
        ).pack(pady=(8, 30))

        button_row = tk.Frame(self.home_frame, bg=PANEL_COLOR)
        button_row.pack(pady=6)
        self.play_button = self.make_button(button_row, "开始游戏", self.start_game, primary=True)
        self.play_button.pack(side="left", padx=8)
        self.sound_button = self.make_button(button_row, "音效：开", self.toggle_sound)
        self.sound_button.pack(side="left", padx=8)

        info_row = tk.Frame(self.home_frame, bg=PANEL_COLOR)
        info_row.pack(pady=34)
        self.make_info_card(info_row, "最高分", self.home_high_score_var).pack(side="left", padx=8)
        self.make_info_card(info_row, "操作", tk.StringVar(value="WASD / 方向键")).pack(side="left", padx=8)
        self.make_info_card(info_row, "暂停", tk.StringVar(value="空格")).pack(side="left", padx=8)

        tk.Label(
            self.home_frame,
            text="普通食物 +1，金色食物限时出现；连续快速吃到食物会增加 combo。",
            font=("Arial", 12),
            fg=MUTED_TEXT,
            bg=PANEL_COLOR,
        ).pack(pady=(18, 0))

    def build_game(self):
        self.hud = tk.Frame(self.game_frame, bg=PANEL_COLOR)
        self.hud.pack(fill="x", padx=14, pady=(14, 10))
        for title, var in [
            ("得分", self.score_var),
            ("最高分", self.high_score_var),
            ("等级", self.level_var),
            ("速度", self.speed_var),
            ("Combo", self.combo_var),
        ]:
            self.make_info_card(self.hud, title, var, compact=True).pack(
                side="left",
                fill="x",
                expand=True,
                padx=4,
            )

        self.canvas = tk.Canvas(
            self.game_frame,
            width=BOARD_WIDTH,
            height=BOARD_HEIGHT,
            bg=BOARD_COLOR,
            highlightthickness=2,
            highlightbackground="#234b57",
        )
        self.canvas.pack(padx=14, pady=8)

        control_row = tk.Frame(self.game_frame, bg=PANEL_COLOR)
        control_row.pack(fill="x", padx=14, pady=(8, 4))
        self.pause_button = self.make_button(control_row, "暂停", self.toggle_pause)
        self.pause_button.pack(side="left", fill="x", expand=True, padx=4)
        self.restart_button = self.make_button(control_row, "重新开始", self.restart_game)
        self.restart_button.pack(side="left", fill="x", expand=True, padx=4)
        self.menu_button = self.make_button(control_row, "返回首页", self.show_home)
        self.menu_button.pack(side="left", fill="x", expand=True, padx=4)

        option_row = tk.Frame(self.game_frame, bg=PANEL_COLOR)
        option_row.pack(fill="x", padx=18, pady=(4, 12))
        tk.Checkbutton(
            option_row,
            text="障碍物",
            variable=self.obstacles_on,
            command=self.refresh_obstacles_option,
            bg=PANEL_COLOR,
            fg=TEXT_COLOR,
            selectcolor=BG_COLOR,
            activebackground=PANEL_COLOR,
            activeforeground=TEXT_COLOR,
            font=("Arial", 11, "bold"),
        ).pack(side="left")
        tk.Label(
            option_row,
            textvariable=self.status_var,
            bg=PANEL_COLOR,
            fg=MUTED_TEXT,
            font=("Arial", 11),
        ).pack(side="right")

    def make_button(self, parent, text, command, primary=False):
        bg = GREEN if primary else "#142632"
        fg = "#03100d" if primary else TEXT_COLOR
        active_bg = "#62e7ff" if primary else "#1f3a48"
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=active_bg,
            activeforeground="#03100d" if primary else TEXT_COLOR,
            relief="flat",
            bd=0,
            padx=20,
            pady=12,
            font=("Arial", 12, "bold"),
            cursor="hand2",
        )

    def make_info_card(self, parent, title, var, compact=False):
        frame = tk.Frame(parent, bg="#13222c", highlightthickness=1, highlightbackground="#203946")
        tk.Label(
            frame,
            text=title.upper(),
            font=("Arial", 9, "bold"),
            fg=MUTED_TEXT,
            bg="#13222c",
        ).pack(anchor="w", padx=12, pady=(8, 0))
        tk.Label(
            frame,
            textvariable=var,
            font=("Arial", 15 if compact else 17, "bold"),
            fg=TEXT_COLOR,
            bg="#13222c",
        ).pack(anchor="w", padx=12, pady=(2, 10))
        return frame

    def bind_events(self):
        self.root.bind("<KeyPress>", self.on_key_press)

    def show_home(self):
        self.stop_timers()
        self.game_state = "menu"
        self.home_high_score_var.set(str(self.high_score))
        self.home_frame.pack(fill="both", expand=True)
        self.game_frame.pack_forget()

    def start_game(self):
        self.home_frame.pack_forget()
        self.game_frame.pack(fill="both", expand=True)
        self.reset_round()
        self.start_countdown()

    def restart_game(self):
        self.reset_round()
        self.start_countdown()

    def reset_round(self):
        self.stop_timers()
        center_x = GRID_WIDTH // 2
        center_y = GRID_HEIGHT // 2
        self.snake = [(center_x, center_y), (center_x - 1, center_y), (center_x - 2, center_y)]
        self.direction = (1, 0)
        self.direction_queue = []
        self.score = 0
        self.level = 1
        self.combo = 1
        self.last_eat_time = 0
        self.special_food = None
        self.particles = []
        self.floating_texts = []
        self.game_over_flash = 0
        self.game_state = "countdown"
        self.generate_obstacles()
        self.food = self.make_food()
        self.update_labels()
        self.draw()

    def stop_timers(self):
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        if self.countdown_after_id is not None:
            self.root.after_cancel(self.countdown_after_id)
            self.countdown_after_id = None

    def start_countdown(self):
        self.countdown_value = 3
        self.game_state = "countdown"
        self.update_labels()
        self.draw()
        self.run_countdown()

    def run_countdown(self):
        if self.countdown_value > 0:
            self.draw()
            self.countdown_value -= 1
            self.countdown_after_id = self.root.after(700, self.run_countdown)
            return

        if self.countdown_value == 0:
            self.countdown_value = -1
            self.draw()
            self.countdown_after_id = self.root.after(520, self.run_countdown)
            return

        self.countdown_after_id = None
        self.game_state = "running"
        self.update_labels()
        self.schedule_next_move()

    def update_labels(self):
        self.score_var.set(str(self.score))
        self.high_score_var.set(str(self.high_score))
        self.level_var.set(str(self.level))
        self.speed_var.set(f"{BASE_DELAY / self.current_delay():.1f}x")
        self.combo_var.set(f"x{self.combo}")
        self.home_high_score_var.set(str(self.high_score))

        if self.game_state == "menu":
            self.status_var.set("在首页点击开始")
        elif self.game_state == "countdown":
            self.status_var.set("准备开始")
        elif self.game_state == "paused":
            self.status_var.set("已暂停，按空格继续")
        elif self.game_state == "game_over":
            self.status_var.set("游戏结束，按 R 重新开始")
        else:
            self.status_var.set("WASD / 方向键移动，空格暂停")

        self.pause_button.config(
            text="继续" if self.game_state == "paused" else "暂停",
            state=tk.NORMAL if self.game_state in ("running", "paused") else tk.DISABLED,
        )

    def current_delay(self):
        level_drop = (self.level - 1) * 8
        score_drop = min((self.score // 10) * 4, 18)
        return max(MIN_DELAY, BASE_DELAY - level_drop - score_drop)

    def toggle_pause(self):
        if self.game_state == "running":
            if self.after_id is not None:
                self.root.after_cancel(self.after_id)
                self.after_id = None
            self.game_state = "paused"
            self.update_labels()
            self.draw()
        elif self.game_state == "paused":
            self.game_state = "running"
            self.update_labels()
            self.draw()
            self.schedule_next_move()

    def toggle_sound(self):
        self.sound_on.set(not self.sound_on.get())
        self.sound_button.config(text=f"音效：{'开' if self.sound_on.get() else '关'}")
        self.play_sound()

    def refresh_obstacles_option(self):
        if self.game_state in ("running", "paused", "countdown"):
            self.generate_obstacles()
            self.draw()

    def on_key_press(self, event):
        key = event.keysym.lower()
        direction_map = {
            "up": (0, -1),
            "w": (0, -1),
            "down": (0, 1),
            "s": (0, 1),
            "left": (-1, 0),
            "a": (-1, 0),
            "right": (1, 0),
            "d": (1, 0),
        }

        if key in direction_map:
            self.queue_direction(direction_map[key])
        elif key == "space":
            self.toggle_pause()
        elif key == "r" and self.game_state in ("running", "paused", "game_over"):
            self.restart_game()
        elif key == "return" and self.game_state == "menu":
            self.start_game()

    def queue_direction(self, new_direction):
        if self.game_state not in ("running", "countdown"):
            return
        last_direction = self.direction_queue[-1] if self.direction_queue else self.direction
        if self.is_opposite(new_direction, last_direction) or new_direction == last_direction:
            return
        if len(self.direction_queue) < 2:
            self.direction_queue.append(new_direction)

    @staticmethod
    def is_opposite(first, second):
        return first[0] + second[0] == 0 and first[1] + second[1] == 0

    def schedule_next_move(self):
        if self.game_state == "running":
            self.after_id = self.root.after(self.current_delay(), self.move)

    def move(self):
        self.after_id = None
        if self.game_state != "running":
            return

        if self.direction_queue:
            self.direction = self.direction_queue.pop(0)

        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        will_eat = new_head == self.food
        will_eat_special = self.special_food and new_head == self.special_food["position"]
        collision_body = self.snake if will_eat or will_eat_special else self.snake[:-1]

        if self.hit_wall(new_head) or new_head in collision_body or new_head in self.obstacles:
            self.end_game()
            return

        self.snake.insert(0, new_head)
        if will_eat:
            self.eat_food(self.food, "normal")
            self.food = self.make_food()
            self.maybe_make_special_food()
        elif will_eat_special:
            self.eat_food(self.special_food["position"], "special")
            self.special_food = None
        else:
            self.snake.pop()

        self.update_special_food()
        self.update_effects()
        self.update_labels()
        self.draw()
        self.schedule_next_move()

    @staticmethod
    def hit_wall(position):
        x, y = position
        return x < 0 or x >= GRID_WIDTH or y < 0 or y >= GRID_HEIGHT

    def eat_food(self, position, food_kind):
        now = time.time()
        self.combo = min(self.combo + 1, 6) if now - self.last_eat_time <= COMBO_WINDOW else 1
        self.last_eat_time = now
        points = (3 if food_kind == "special" else 1) * self.combo
        self.score += points
        self.add_food_effect(position, points, food_kind)
        self.play_sound()

        new_level = self.score // LEVEL_SCORE_STEP + 1
        if new_level > self.level:
            self.level = new_level
            self.floating_texts.append({"text": "LEVEL UP", "position": position, "life": 10, "color": CYAN})
            self.generate_obstacles()
            self.play_sound()

        self.save_high_score()

    def add_food_effect(self, position, points, food_kind):
        x, y = self.cell_center(position)
        color = GOLD if food_kind == "special" else PINK
        for _ in range(12):
            self.particles.append(
                {
                    "x": x,
                    "y": y,
                    "vx": random.uniform(-3, 3),
                    "vy": random.uniform(-3, 3),
                    "life": 8,
                    "color": color,
                }
            )
        self.floating_texts.append({"text": f"+{points}", "position": position, "life": 10, "color": TEXT_COLOR})

    def update_effects(self):
        new_particles = []
        for particle in self.particles:
            particle["x"] += particle["vx"]
            particle["y"] += particle["vy"]
            particle["life"] -= 1
            if particle["life"] > 0:
                new_particles.append(particle)
        self.particles = new_particles

        for item in self.floating_texts:
            item["life"] -= 1
        self.floating_texts = [item for item in self.floating_texts if item["life"] > 0]

        if self.game_over_flash > 0:
            self.game_over_flash -= 1

    def maybe_make_special_food(self):
        if self.special_food or self.score < 4:
            return
        if random.random() < 0.25:
            self.special_food = {"position": self.make_food(), "created": time.time()}

    def update_special_food(self):
        if self.special_food and time.time() - self.special_food["created"] > SPECIAL_FOOD_LIFETIME:
            self.floating_texts.append(
                {"text": "MISSED", "position": self.special_food["position"], "life": 9, "color": MUTED_TEXT}
            )
            self.special_food = None

    def make_food(self):
        candidates = self.reachable_cells()
        occupied = set(self.snake) | set(self.obstacles)
        if self.food:
            occupied.add(self.food)
        if self.special_food:
            occupied.add(self.special_food["position"])
        candidates = [cell for cell in candidates if cell not in occupied]

        if not candidates:
            candidates = [
                (x, y)
                for x in range(GRID_WIDTH)
                for y in range(GRID_HEIGHT)
                if (x, y) not in occupied
            ]
        if not candidates:
            self.end_game()
            return (0, 0)
        return random.choice(candidates)

    def generate_obstacles(self):
        self.obstacles = []
        if not self.obstacles_on.get() or self.level < 3:
            return

        target_count = min(4 + self.level // 2, 12)
        attempts = 0
        while len(self.obstacles) < target_count and attempts < 500:
            attempts += 1
            candidate = (
                random.randint(2, GRID_WIDTH - 3),
                random.randint(2, GRID_HEIGHT - 3),
            )
            head = self.snake[0]
            near_head = abs(candidate[0] - head[0]) + abs(candidate[1] - head[1]) < 6
            if near_head or candidate in self.snake or candidate in self.obstacles or candidate == self.food:
                continue
            self.obstacles.append(candidate)
            if len(self.reachable_cells()) < GRID_WIDTH * GRID_HEIGHT * 0.38:
                self.obstacles.pop()

    def reachable_cells(self):
        if not self.snake:
            return []
        start = self.snake[0]
        blocked = set(self.snake[1:]) | set(self.obstacles)
        seen = {start}
        queue = [start]
        result = []
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]

        while queue:
            current = queue.pop(0)
            result.append(current)
            for dx, dy in directions:
                nxt = (current[0] + dx, current[1] + dy)
                if self.hit_wall(nxt) or nxt in blocked or nxt in seen:
                    continue
                seen.add(nxt)
                queue.append(nxt)
        return result

    def end_game(self):
        self.stop_timers()
        self.game_state = "game_over"
        self.game_over_flash = 8
        self.save_high_score()
        self.update_labels()
        self.draw()

    def load_high_score(self):
        try:
            if SAVE_FILE.exists():
                data = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
                return int(data.get("high_score", 0))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            pass
        return 0

    def save_high_score(self):
        if self.score <= self.high_score:
            return
        self.high_score = self.score
        try:
            SAVE_FILE.write_text(json.dumps({"high_score": self.high_score}), encoding="utf-8")
        except OSError:
            pass

    def play_sound(self):
        if self.sound_on.get():
            self.root.bell()

    def draw(self):
        self.canvas.delete("all")
        self.draw_background()
        self.draw_obstacles()
        self.draw_food()
        self.draw_snake()
        self.draw_particles()
        self.draw_floating_texts()
        self.draw_overlay()

    def draw_background(self):
        self.canvas.create_rectangle(0, 0, BOARD_WIDTH, BOARD_HEIGHT, fill=BOARD_COLOR, outline="")
        for x in range(0, BOARD_WIDTH + 1, CELL_SIZE):
            self.canvas.create_line(x, 0, x, BOARD_HEIGHT, fill=GRID_COLOR)
        for y in range(0, BOARD_HEIGHT + 1, CELL_SIZE):
            self.canvas.create_line(0, y, BOARD_WIDTH, y, fill=GRID_COLOR)
        self.canvas.create_rectangle(2, 2, BOARD_WIDTH - 2, BOARD_HEIGHT - 2, outline="#2d6370", width=2)
        if self.game_over_flash > 0:
            self.canvas.create_rectangle(0, 0, BOARD_WIDTH, BOARD_HEIGHT, fill="#2a1118", stipple="gray50", outline="")

    def draw_food(self):
        if self.food:
            self.draw_food_orb(self.food, PINK, "#ffb3c8")
        if self.special_food:
            age = time.time() - self.special_food["created"]
            if age <= SPECIAL_FOOD_LIFETIME:
                self.draw_food_orb(self.special_food["position"], GOLD, "#fff4a4", special=True)

    def draw_food_orb(self, position, color, highlight, special=False):
        center_x, center_y = self.cell_center(position)
        pulse = 2 if int(time.time() * 5) % 2 == 0 else 0
        radius = (10 if special else 8) + pulse
        self.canvas.create_oval(
            center_x - radius - 6,
            center_y - radius - 6,
            center_x + radius + 6,
            center_y + radius + 6,
            fill=color,
            outline="",
            stipple="gray25",
        )
        self.canvas.create_oval(
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
            fill=color,
            outline="",
        )
        self.canvas.create_oval(
            center_x - radius // 2,
            center_y - radius // 2,
            center_x,
            center_y,
            fill=highlight,
            outline="",
        )

    def draw_obstacles(self):
        for obstacle in self.obstacles:
            x, y = self.cell_center(obstacle)
            r = CELL_SIZE // 2 - 4
            self.canvas.create_rectangle(x - r, y - r, x + r, y + r, fill=OBSTACLE, outline="#ffd0d6", width=1)

    def draw_snake(self):
        if not self.snake:
            return
        for index in range(len(self.snake) - 1, 0, -1):
            position = self.snake[index]
            center_x, center_y = self.cell_center(position)
            body_ratio = 1 - index / len(self.snake)
            radius = int(CELL_SIZE * (0.34 + body_ratio * 0.08))
            self.canvas.create_oval(
                center_x - radius,
                center_y - radius,
                center_x + radius,
                center_y + radius,
                fill=GREEN,
                outline=GREEN_DARK,
                width=2,
            )
            if index % 2 == 0:
                small = max(3, radius // 3)
                self.canvas.create_oval(
                    center_x - small,
                    center_y - small,
                    center_x + small,
                    center_y + small,
                    fill=GREEN_LIGHT,
                    outline="",
                )
        self.draw_snake_head()

    def draw_snake_head(self):
        head_x, head_y = self.cell_center(self.snake[0])
        dx, dy = self.direction
        perp_x, perp_y = -dy, dx
        radius = CELL_SIZE // 2
        self.canvas.create_oval(
            head_x - radius + dx * 3,
            head_y - radius + dy * 3,
            head_x + radius + dx * 3,
            head_y + radius + dy * 3,
            fill="#22ce78",
            outline=GREEN_DARK,
            width=2,
        )

        for side in (-1, 1):
            eye_x = head_x + dx * 5 + perp_x * 5 * side
            eye_y = head_y + dy * 5 + perp_y * 5 * side
            self.canvas.create_oval(eye_x - 3, eye_y - 3, eye_x + 3, eye_y + 3, fill="white", outline="")
            self.canvas.create_oval(
                eye_x + dx - 1.5,
                eye_y + dy - 1.5,
                eye_x + dx + 1.5,
                eye_y + dy + 1.5,
                fill="black",
                outline="",
            )

        tongue_start_x = head_x + dx * 13
        tongue_start_y = head_y + dy * 13
        tongue_end_x = head_x + dx * 22
        tongue_end_y = head_y + dy * 22
        self.canvas.create_line(tongue_start_x, tongue_start_y, tongue_end_x, tongue_end_y, fill=PINK, width=2)
        self.canvas.create_line(
            tongue_end_x,
            tongue_end_y,
            tongue_end_x + dx * 3 + perp_x * 4,
            tongue_end_y + dy * 3 + perp_y * 4,
            fill=PINK,
            width=2,
        )
        self.canvas.create_line(
            tongue_end_x,
            tongue_end_y,
            tongue_end_x + dx * 3 - perp_x * 4,
            tongue_end_y + dy * 3 - perp_y * 4,
            fill=PINK,
            width=2,
        )

    def draw_particles(self):
        for particle in self.particles:
            self.canvas.create_oval(
                particle["x"] - 2,
                particle["y"] - 2,
                particle["x"] + 2,
                particle["y"] + 2,
                fill=particle["color"],
                outline="",
            )

    def draw_floating_texts(self):
        for item in self.floating_texts:
            x, y = self.cell_center(item["position"])
            y -= (10 - item["life"]) * 2
            self.canvas.create_text(x, y, text=item["text"], fill=item["color"], font=("Arial", 13, "bold"))

    def draw_overlay(self):
        if self.game_state == "countdown":
            title = "GO" if self.countdown_value < 0 else str(max(1, self.countdown_value + 1))
            self.draw_overlay_card("准备", title, "马上开始，找好第一步方向")
        elif self.game_state == "paused":
            self.draw_overlay_card("暂停", "PAUSE", "按空格或点击继续")
        elif self.game_state == "game_over":
            self.draw_overlay_card(
                "游戏结束",
                "GAME OVER",
                f"本局得分 {self.score}  |  最高分 {self.high_score}  |  按 R 重来",
            )

    def draw_overlay_card(self, kicker, title, message):
        self.canvas.create_rectangle(0, 0, BOARD_WIDTH, BOARD_HEIGHT, fill="#03070c", stipple="gray50", outline="")
        card_w, card_h = 420, 170
        left = (BOARD_WIDTH - card_w) // 2
        top = (BOARD_HEIGHT - card_h) // 2
        self.canvas.create_rectangle(left, top, left + card_w, top + card_h, fill="#0d1824", outline="#2b5360", width=2)
        self.canvas.create_text(
            BOARD_WIDTH // 2,
            top + 34,
            text=kicker.upper(),
            fill=CYAN,
            font=("Arial", 11, "bold"),
        )
        self.canvas.create_text(
            BOARD_WIDTH // 2,
            top + 78,
            text=title,
            fill=TEXT_COLOR,
            font=("Arial", 30, "bold"),
        )
        self.canvas.create_text(
            BOARD_WIDTH // 2,
            top + 122,
            text=message,
            fill=MUTED_TEXT,
            font=("Arial", 12, "bold"),
        )

    def cell_center(self, position):
        x, y = position
        return x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2


if __name__ == "__main__":
    window = tk.Tk()
    game = SnakeGame(window)
    window.mainloop()
