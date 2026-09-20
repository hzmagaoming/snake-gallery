"""幻彩青蛇 · 单文件提交版

只需发送本文件，无需其他代码、图片或 Notebook。
运行：python 幻彩青蛇_单文件版.py（Python 3，需内置 tkinter 支持）
方向键/WASD 移动，空格暂停，R 重开，H 查看完整规则。
最高分首次刷新后自动写入同目录的「贪吃蛇最高分.txt」，无需预先提供。
"""
import math
import random
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

CELL = 24                 # 每格的像素大小
COLS, ROWS = 25, 20        # 棋盘宽度和高度（格）
DELAY = 130                # 每一步间隔毫秒；越小越快


class SnakeGame:
    def __init__(self, root):
        self.root = root
        root.title("贪吃蛇 · Anaconda Python 课堂练习")
        root.resizable(False, False)
        self.status = tk.StringVar()
        tk.Label(root, textvariable=self.status, font=("Arial", 16),
                 pady=12).pack()
        self.canvas = tk.Canvas(root, width=COLS * CELL, height=ROWS * CELL,
                                bg="#14232b", highlightthickness=0)
        self.canvas.pack()
        tk.Label(root, text="方向键 / WASD 移动　｜　空格暂停　｜　R 重新开始",
                 pady=12).pack()
        root.bind("<KeyPress>", self.key)
        self.reset()
        root.after(DELAY, self.tick)

    def reset(self):
        self.snake = [(8, 10), (7, 10), (6, 10)]
        self.direction = (1, 0)
        self.pending = (1, 0)
        self.turned = False
        self.paused = False
        self.over = False
        self.won = False
        self.started = False
        self.score = 0
        self.food = self.new_food()
        self.draw()

    def new_food(self):
        free = [(x, y) for x in range(COLS) for y in range(ROWS)
                if (x, y) not in self.snake]
        return random.choice(free) if free else None

    def key(self, event):
        key = event.keysym.lower()
        directions = {"up": (0, -1), "w": (0, -1),
                      "down": (0, 1), "s": (0, 1),
                      "left": (-1, 0), "a": (-1, 0),
                      "right": (1, 0), "d": (1, 0)}
        if key == "r":
            self.reset()
        elif key == "space" and not self.over:
            self.paused = not self.paused
            self.draw()
        elif key in directions and not self.over and not self.paused:
            new = directions[key]
            reverse = (-self.direction[0], -self.direction[1])
            if new != reverse and not self.turned:
                self.pending = new
                self.turned = True
                self.started = True




PALETTES = [
    {"name": "翡翠脉冲", "dark": "#174a36", "body": "#37d67a", "light": "#adffb6", "glow": "#54ff9f"},
    {"name": "赛博蓝", "dark": "#17495e", "body": "#20bde5", "light": "#a7f2ff", "glow": "#2fe8ff"},
    {"name": "电光紫", "dark": "#4a286f", "body": "#9a55e9", "light": "#e2c5ff", "glow": "#c16cff"},
    {"name": "熔岩橙", "dark": "#71391f", "body": "#ef7840", "light": "#ffd3a1", "glow": "#ff9a45"},
    {"name": "樱花粉", "dark": "#702a54", "body": "#e952a1", "light": "#ffc1e4", "glow": "#ff65bd"},
    {"name": "黄金风暴", "dark": "#715514", "body": "#e7b72e", "light": "#fff0a3", "glow": "#ffd84a"},
]

FOODS = {
    "normal":  {"name": "能量", "color": "#ff4571", "outline": "#ffafc1", "symbol": "✦"},
    "slow":    {"name": "冰冻", "color": "#3cbcf4", "outline": "#bcecff", "symbol": "❄"},
    "double":  {"name": "双倍", "color": "#ffc83d", "outline": "#fff0a3", "symbol": "×2"},
    "shield":  {"name": "护盾", "color": "#8d6cff", "outline": "#dccfff", "symbol": "◇"},
    "rainbow": {"name": "狂热", "color": "#ff54d9", "outline": "#ffffff", "symbol": "★"},
    "shrink":  {"name": "缩身", "color": "#3b4354", "outline": "#b8c1d8", "symbol": "−"},
}

RULES = """目标：吃豆得分并刷新最高分。棋盘内始终有一颗豆，吃完立即刷新。

方向键/WASD移动；空格暂停；R重新开始；H查看规则。

红豆：+1分，增长一节。
蓝豆：+1分，减速6秒。
黄豆：+2分，可与狂热倍数叠加。
紫豆：+1分，恢复1次撞墙护盾（上限1次）。
粉豆：+1分，激活或续时8秒狂热，至少为1级。
黑豆：+1分，蛇身净缩短3节，最短保留4节。
除黑豆外，每颗豆均增长一节；所有豆都会切换蛇身配色。

连击：相邻两次吃豆间隔不超过10秒。
3/6/9连击分别触发1/2/3级狂热，后续得分为2/3/4倍。
狂热持续8秒；达到3连击后继续连吃会刷新持续时间。
狂热不提供无敌，也不会额外加速，方便你追逐连击。

蓝紫传送门：进入一个会从另一个出现，方向不变。
出口被身体占用时，本次不传送，可以直接经过入口。
穿越只连接真实蛇身，不会形成横跨地图的碰撞区域。

护盾：开局1次，撞墙时消耗并从对面穿出。
护盾仅保护撞墙，撞到身体仍会结束；穿出后也要避开身体。
每5分升1级并略微加速，速度有上限。

暂停和查看规则都会冻结连击、狂热、减速计时。
填满除传送门外的空位即可获胜。最高分自动保存到本地。"""


class NeonSnake(SnakeGame):
    def __init__(self, root):
        self.palette_index = 0
        self.particles = []
        self.flash = 0
        self.combo = 0
        self.combo_timer = 0
        self.shield_available = True
        self.shield_timer = 0
        self.slow_ticks = 0
        self.fever_ticks = 0
        self.fever_level = 0
        self.elapsed = 0
        self.save_error = False
        self.event_timer = 0
        self.event_message = ""
        self.food_type = "normal"
        self.portals = []
        self.high_score_file = Path(__file__).with_name("贪吃蛇最高分.txt")
        self.high_score = self.load_high_score()
        self.frame = 0
        self.speed = 130
        self.stars = [(random.randrange(COLS * CELL), random.randrange(ROWS * CELL),
                       random.choice((1, 1, 1, 2)), random.random() * math.tau)
                      for _ in range(55)]
        super().__init__(root)
        root.title("幻彩青蛇 · Anaconda Python 课堂练习")
        root.configure(bg="#08141d")
        self.canvas.configure(bg="#07151d")
        self.notice = tk.StringVar()
        tk.Label(root, textvariable=self.notice, bg="#08141d", fg="#99e8ff",
                 font=("Arial", 12), pady=7, wraplength=580).pack(before=self.canvas)
        tk.Label(root, text="红 +1   蓝 减速   黄 +2   紫 补盾   粉 狂热   黑 缩身",
                 bg="#08141d", fg="#c5dce3", pady=5).pack()
        tk.Button(root, text="玩法规则（H）", command=self.show_rules).pack(pady=(0, 8))
        for widget in root.winfo_children():
            if isinstance(widget, tk.Label):
                widget.configure(bg="#08141d", fg="#d7eff4")
                if "方向键" in str(widget.cget("text")):
                    widget.configure(text="方向键/WASD移动  ·  空格暂停  ·  R重开  ·  彩虹豆触发狂热")
        self.draw()

    def key(self, event):
        if event.keysym.lower() == "h":
            self.show_rules()
        else:
            super().key(event)

    def show_rules(self):
        was_paused = self.paused
        self.paused = True
        self.draw()
        messagebox.showinfo("幻彩青蛇 · 玩法规则", RULES, parent=self.root)
        self.paused = was_paused
        self.draw()

    @property
    def palette(self):
        if self.fever_ticks:
            return PALETTES[(self.frame // 2) % len(PALETTES)]
        return PALETTES[self.palette_index]

    def load_high_score(self):
        try:
            return max(0, int(self.high_score_file.read_text(encoding="utf-8").strip()))
        except (FileNotFoundError, ValueError, OSError):
            return 0

    def save_high_score(self):
        if self.score > self.high_score:
            self.high_score = self.score
            try:
                self.high_score_file.write_text(str(self.high_score), encoding="utf-8")
            except OSError:
                self.save_error = True

    def reset(self):
        super().reset()
        self.snake = [(11 - i, 10) for i in range(8)]
        self.palette_index = 0
        self.particles = []
        self.flash = 0
        self.combo = 0
        self.combo_timer = 0
        self.shield_available = True
        self.shield_timer = 0
        self.slow_ticks = 0
        self.fever_ticks = 0
        self.fever_level = 0
        self.elapsed = 0
        self.event_timer = 0
        self.event_message = ""
        self.speed = 130
        self.generate_portals()
        self.spawn_food()
        self.draw()

    def generate_portals(self):
        free = [(x, y) for x in range(2, COLS-2) for y in range(3, ROWS-2)
                if (x, y) not in self.snake]
        first = random.choice(free)
        distant = [cell for cell in free
                   if abs(cell[0]-first[0]) + abs(cell[1]-first[1]) >= 14]
        second = random.choice(distant or free)
        self.portals = [first, second]

    def spawn_food(self):
        free = [(x, y) for x in range(COLS) for y in range(ROWS)
                if (x, y) not in self.snake and (x, y) not in self.portals]
        self.food = random.choice(free) if free else None
        self.food_type = random.choices(
            list(FOODS), weights=(42, 12, 12, 11, 10, 13), k=1
        )[0]
        if self.food is None:
            self.over = self.won = True

    def teleport(self, head):
        if head not in self.portals:
            return head
        exit_cell = self.portals[1] if head == self.portals[0] else self.portals[0]
        if exit_cell in self.snake[:-1]:
            self.event_message = "出口被蛇身占用 · 本次直接经过入口"
            self.event_timer = 2.5
            return head
        px, py = [(value + .5) * CELL for value in head]
        ex, ey = [(value + .5) * CELL for value in exit_cell]
        self.burst(px, py, "#65e7ff", 18)
        self.burst(ex, ey, "#d965ff", 18)
        self.event_message = "虫洞跃迁！"
        self.event_timer = 2.5
        return exit_cell

    def apply_food_power(self):
        """应用当前豆子的能力，并返回本次应增加的分数。"""
        points = 2 if self.food_type == "double" else 1
        if self.fever_ticks:
            points *= self.fever_level + 1
        if self.food_type == "slow":
            self.slow_ticks = 6
            self.event_message = "时间冻结 · 蛇速暂时降低"
        elif self.food_type == "shield":
            self.shield_available = True
            self.event_message = "护盾重新充能！"
        elif self.food_type == "rainbow":
            self.fever_ticks = 8
            self.fever_level = max(1, self.fever_level)
            self.event_message = f"狂热 {self.fever_level} 级 · 后续得分 ×{self.fever_level+1}"
        elif self.food_type == "shrink":
            # 本步已插入蛇头，因此移除四节实现净缩短三节。
            remove_count = min(4, max(0, len(self.snake) - 4))
            if remove_count:
                del self.snake[-remove_count:]
            self.event_message = "轻盈术 · 蛇身缩短"
        elif self.food_type == "double":
            self.event_message = f"双倍能量 +{points}"
        else:
            self.event_message = f"能量吸收 +{points}"
        self.event_timer = 2.5
        return points

    def tick(self):
        """处理移动、吃豆特效和随分数逐步加速。"""
        self.frame += 1
        self.update_effects()
        if self.started and not self.paused and not self.over:
            # 当仍有空位时，确保每一步都有可收集的食物。
            if self.food is None or self.food in self.snake or self.food in self.portals:
                self.spawn_food()
                if self.over:
                    self.draw()
                    self.root.after(self.speed, self.tick)
                    return
            self.direction = self.pending
            self.turned = False
            x, y = self.snake[0]
            dx, dy = self.direction
            head = (x + dx, y + dy)
            hit_wall = not (0 <= head[0] < COLS and 0 <= head[1] < ROWS)
            fatal_wall = hit_wall
            if hit_wall and self.shield_available:
                self.shield_available = False
                self.shield_timer = 3
                fatal_wall = False
                # 护盾把蛇从撞击点传送到棋盘的另一侧。
                head = (head[0] % COLS, head[1] % ROWS)
                edge_x = min(max((x + .5) * CELL, 4), COLS * CELL - 4)
                edge_y = min(max((y + .5) * CELL, 4), ROWS * CELL - 4)
                self.burst(edge_x, edge_y, "#7de9ff", 45)
                self.flash = 9
            if not fatal_wall:
                head = self.teleport(head)
            eating = head == self.food
            body = self.snake if eating else self.snake[:-1]
            if fatal_wall or head in body:
                self.over = True
                self.burst((x + .5) * CELL, (y + .5) * CELL, "#ff4d6d", 28)
                self.flash = 7
            else:
                self.snake.insert(0, head)
                if eating:
                    fx, fy = [(v + .5) * CELL for v in self.food]
                    self.score += self.apply_food_power()
                    self.save_high_score()
                    self.combo += 1
                    self.combo_timer = 10
                    if self.combo >= 3:
                        self.fever_level = max(self.fever_level, min(3, self.combo // 3))
                        self.fever_ticks = 8
                        self.event_message = f"{self.combo}连击！狂热{self.fever_level}级 · ×{self.fever_level+1}分"
                        self.event_timer = 3
                    self.palette_index = (self.palette_index + 1) % len(PALETTES)
                    self.burst(fx, fy, self.palette["glow"], 34)
                    self.flash = 5
                    self.spawn_food()
                    if self.food is None:
                        self.over = self.won = True
                else:
                    self.snake.pop()
        self.draw()
        self.root.after(self.speed if self.started else 90, self.tick)

    def burst(self, x, y, color, count):
        for _ in range(count):
            angle = random.random() * math.tau
            velocity = random.uniform(2.0, 7.0)
            self.particles.append({
                "x": x, "y": y,
                "dx": math.cos(angle) * velocity,
                "dy": math.sin(angle) * velocity,
                "life": random.randint(9, 18),
                "size": random.uniform(1.8, 4.5),
                "color": color,
            })

    def update_effects(self):
        for particle in self.particles:
            particle["x"] += particle["dx"]
            particle["y"] += particle["dy"]
            particle["dx"] *= .91
            particle["dy"] = particle["dy"] * .91 + .12
            particle["life"] -= 1
        self.particles = [p for p in self.particles if p["life"] > 0]
        self.flash = max(0, self.flash - 1)
        # 游戏时间只随实际游戏步推进，暂停或查看规则不会消耗能力。
        if self.started and not self.paused and not self.over:
            dt = self.speed / 1000
            self.elapsed += dt
            for name in ('shield_timer', 'slow_ticks', 'fever_ticks', 'event_timer', 'combo_timer'):
                setattr(self, name, max(0, getattr(self, name) - dt))
            if not self.combo_timer:
                self.combo = 0
            if not self.fever_ticks:
                self.fever_level = 0
        base_speed = max(85, 155 - (self.score // 5) * 7)
        self.speed = base_speed + 42 if self.slow_ticks else base_speed

    def path(self):
        """对蛇身折线插值，使转弯更圆润。"""
        points = [((x + .5) * CELL, (y + .5) * CELL) for x, y in self.snake]
        extended = [points[0]] + points + [points[-1]]
        result = []
        for i in range(1, len(extended) - 2):
            a, b, c, d = extended[i - 1:i + 3]
            for step in range(6):
                t = step / 6
                result.append(tuple(.5 * (2*b[k] + (-a[k]+c[k])*t
                    + (2*a[k]-5*b[k]+4*c[k]-d[k])*t*t
                    + (-a[k]+3*b[k]-3*c[k]+d[k])*t*t*t) for k in (0, 1)))
        result.append(points[-1])
        return result

    def draw_background(self):
        canvas = self.canvas
        canvas.create_rectangle(0, 0, COLS*CELL, ROWS*CELL, fill="#07151d", outline="")
        for x, y, radius, phase in self.stars:
            glow = .5 + .5 * math.sin(self.frame * .18 + phase)
            color = "#327080" if glow > .55 else "#193e49"
            r = radius + (1 if glow > .86 else 0)
            canvas.create_oval(x-r, y-r, x+r, y+r, fill=color, outline="")
        for x in range(0, COLS * CELL, CELL):
            canvas.create_line(x, 0, x, ROWS*CELL, fill="#102c35")
        for y in range(0, ROWS * CELL, CELL):
            canvas.create_line(0, y, COLS*CELL, y, fill="#102c35")

    def draw_food(self):
        if self.food is None:
            return
        canvas = self.canvas
        x, y = [(v + .5)*CELL for v in self.food]
        food = FOODS[self.food_type]
        pulse = 2 + 2 * math.sin(self.frame * .45)
        for radius, color in ((17+pulse, "#153846"), (13+pulse/2, food["outline"])):
            canvas.create_oval(x-radius, y-radius, x+radius, y+radius, outline=color, width=2)
        canvas.create_oval(x-10, y-10, x+10, y+10,
                           fill=food["color"], outline=food["outline"], width=2)
        canvas.create_oval(x-5, y-6, x-1, y-2, fill="#ffffff", outline="")
        canvas.create_text(x, y+1, text=food["symbol"], fill="#fff9e8",
                           font=("Arial", 10, "bold"))

    def draw_portals(self):
        canvas = self.canvas
        for index, (cell_x, cell_y) in enumerate(self.portals):
            x, y = (cell_x + .5) * CELL, (cell_y + .5) * CELL
            color = "#4de5ff" if index == 0 else "#d75aff"
            reverse = -1 if index else 1
            for radius, width in ((13, 3), (9, 2), (5, 1)):
                start = (self.frame * 16 * reverse + radius * 8) % 360
                canvas.create_arc(x-radius, y-radius, x+radius, y+radius,
                                  start=start, extent=230, style=tk.ARC,
                                  outline=color, width=width)
            canvas.create_oval(x-3, y-3, x+3, y+3, fill="#eefcff", outline="")

    def draw_snake(self):
        # 穿墙和传送造成坐标跳跃；按连续段分别绘制，避免横贯棋盘的假蛇身。
        original = self.snake
        segments = []
        for cell in original:
            if not segments or sum(abs(a-b) for a,b in zip(segments[-1][-1], cell)) > 1:
                segments.append([cell])
            else:
                segments[-1].append(cell)
        try:
            for i in range(len(segments)-1, -1, -1):
                self.snake = segments[i]
                self.draw_snake_segment(draw_head=(i == 0))
        finally:
            self.snake = original

    def draw_snake_segment(self, draw_head=True):
        canvas = self.canvas
        colors = self.palette
        points = self.path()
        if len(points) == 1:
            x, y = points[0]
            canvas.create_oval(x-8, y-8, x+8, y+8, fill=colors['body'], outline=colors['glow'])
            if not draw_head:
                return
            points = [(x, y), (x-self.direction[0], y-self.direction[1])]
        frames = []
        for i, (x, y) in enumerate(points):
            previous = points[max(0, i-1)]
            following = points[min(len(points)-1, i+1)]
            dx, dy = following[0]-previous[0], following[1]-previous[1]
            length = math.hypot(dx, dy) or 1
            nx, ny = -dy/length, dx/length
            fraction = i / max(1, len(points)-1)
            radius = 8.7 * min(1, (1-fraction)*4 + .07)
            frames.append((x, y, nx, ny, radius))

        def ribbon(scale, offset=0):
            left = [(x+nx*r*scale, y+ny*r*scale+offset) for x,y,nx,ny,r in frames]
            right = [(x-nx*r*scale, y-ny*r*scale+offset) for x,y,nx,ny,r in reversed(frames)]
            return [value for point in left+right for value in point]

        canvas.create_polygon(*ribbon(1.75), fill="#0b2631", outline="")
        if self.fever_ticks:
            # 狂热模式下在蛇身后方叠加多色残影。
            for offset, palette in zip((5, 3, 1), PALETTES[::2]):
                canvas.create_polygon(*ribbon(1.42, offset), fill=palette["glow"], outline="")
        canvas.create_polygon(*ribbon(1.38), fill=colors["dark"], outline="")
        canvas.create_polygon(*ribbon(1.08), fill=colors["body"], outline=colors["glow"], width=1)
        canvas.create_polygon(*ribbon(.66), fill=colors["light"], outline="")
        for i in range(3, len(frames)-2, 3):
            x,y,nx,ny,radius = frames[i]
            tx,ty = ny,-nx
            size = min(3.4, radius*.55)
            for side in (-.52, .52):
                sx,sy = x+nx*radius*side, y+ny*radius*side
                canvas.create_polygon(sx+tx*3,sy+ty*3, sx+nx*size,sy+ny*size,
                                      sx-tx*3,sy-ty*3, sx-nx*size,sy-ny*size,
                                      fill=colors["dark"], outline=colors["light"], width=.5)

        if not draw_head:
            return
        hx, hy = points[0]
        dx, dy = self.direction
        nx, ny = -dy, dx

        def local(a, b):
            return hx+dx*a+nx*b, hy+dy*a+ny*b

        def polygon(coords, **kwargs):
            canvas.create_polygon(*[value for a,b in coords for value in local(a,b)], **kwargs)

        def dot(a, b, radius, fill):
            x, y = local(a, b)
            canvas.create_oval(x-radius, y-radius, x+radius, y+radius, fill=fill, outline="")

        # 尚未使用的护盾会在蛇头周围形成旋转感的双层能量环。
        if self.shield_available:
            pulse = 1.5 + math.sin(self.frame * .35)
            canvas.create_oval(hx-16-pulse, hy-16-pulse, hx+16+pulse, hy+16+pulse,
                               outline="#6ee7ff", width=2)
            canvas.create_arc(hx-20, hy-20, hx+20, hy+20,
                              start=(self.frame * 18) % 360, extent=115,
                              style=tk.ARC, outline="#d4f8ff", width=2)

        if not self.over:
            tongue = "#ff497d"
            canvas.create_line(*local(10,0), *local(20,0), fill=tongue, width=2)
            for side in (-1, 1):
                canvas.create_line(*local(20,0), *local(24,side*3), fill=tongue, width=2)
        head = [(-11,-6),(-6,-10),(2,-10),(10,-6),(12,-2),(12,2),(10,6),(2,10),(-6,10),(-11,6)]
        polygon(head, fill=colors["body"], outline=colors["glow"], width=2, smooth=True)
        polygon([(-9,-2),(-3,-6),(8,-3),(10,0),(8,3),(-3,6),(-9,2)],
                fill=colors["light"], outline="", smooth=True)
        for side in (-1, 1):
            dot(3, side*7, 3.4, "#07151d")
            dot(3.6, side*7, 2.4, "#ffe66d")
            x1,y1 = local(2, side*7)
            x2,y2 = local(5, side*7)
            canvas.create_line(x1,y1,x2,y2,fill="#07151d",width=1.8)
            dot(3.4, side*7-.7, .7, "white")

    def draw_particles(self):
        for particle in self.particles:
            radius = particle["size"] * min(1, particle["life"] / 5)
            self.canvas.create_oval(particle["x"]-radius, particle["y"]-radius,
                                    particle["x"]+radius, particle["y"]+radius,
                                    fill=particle["color"], outline="")

    def draw(self):
        canvas = self.canvas
        canvas.delete("all")
        self.draw_background()
        self.draw_portals()
        self.draw_snake()
        self.draw_particles()
        self.draw_food()
        if self.flash:
            canvas.create_rectangle(0, 0, COLS*CELL, ROWS*CELL,
                                    outline=self.palette["glow"], width=self.flash)

        message = "按方向键开始 · 吃豆变色"
        if self.started:
            message = "追逐能量豆 · 空格暂停 · R 重开"
        if self.paused:
            message = "时空冻结 · 按空格继续"
        if self.over:
            message = "满屏制霸 · R 再战" if self.won else "撞击警报 · 按 R 重启"
        elif self.shield_timer:
            message = "能量护盾启动！已从对面边界穿出"
        elif self.event_timer:
            message = self.event_message
        elif self.fever_ticks:
            message = f"狂热{self.fever_level}级 · ×{self.fever_level+1}分 · 剩余{self.fever_ticks:.1f}秒"
        if self.paused and not self.over:
            message = "已暂停 · 能力时间冻结 · 空格继续"
        if self.combo_timer and self.combo:
            message += f"  |  {self.combo}连击 · {self.combo_timer:.1f}秒内再吃一颗"
        if self.slow_ticks:
            message += f"  |  减速{self.slow_ticks:.1f}秒"
        if hasattr(self, 'notice'):
            self.notice.set(message)
        level = 1 + self.score // 5
        shield = "护盾 1" if self.shield_available else "护盾 0"
        target = f"目标：{FOODS[self.food_type]['name']}豆" if self.food else "满盘通关"
        self.status.set(
            f"得分 {self.score:02d}  最高 {self.high_score:02d}  LV.{level}  "
            f"{shield}  {target}"
        )
        if self.save_error and hasattr(self, 'notice'):
            self.notice.set(message + ' | 最高分仅保存在本次运行中')


if __name__ == "__main__":
    window = tk.Tk()
    game = NeonSnake(window)
    window.mainloop()

