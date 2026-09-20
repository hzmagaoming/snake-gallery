from dataclasses import dataclass
import random
import time

@dataclass
class Settings:
    # 棋盘：宽高相同，格子数 × 每格像素
    grid_size: int = 25
    cell_size: int = 24
    step_ms: int = 140
    initial_length: int = 4

    # 范围上下限均包含；数量始终不超过上限
    apple_range: tuple = (1, 3)
    poison_range: tuple = (0, 1)
    apple_refresh_s: float = 8.0
    poison_refresh_s: float = 5.0
    apple_score: int = 10
    apple_growth: int = 1
    poison_penalty: int = 15
    poison_shrink: int = 2
    min_length: int = 2

    # shape 可选 circle、square、diamond
    sprite_art: bool = True     # V4 使用项目内透明 PNG 贴图
    asset_dir: str = "snake_assets_v4"
    realistic_art: bool = True  # sprite_art=False 时使用 V3 Canvas 造型
    snake_shape: str = "circle"
    apple_shape: str = "circle"
    poison_shape: str = "diamond"
    snake_color: str = "#45cc86"
    head_color: str = "#9cffb3"
    apple_color: str = "#ffbe55"
    poison_color: str = "#ca85ff"
    background: str = "#111827"
    grid_color: str = "#223047"
    show_grid: bool = True
    wrap_edges: bool = False
    random_seed: object = None

    def validate(self):
        for name in ("grid_size", "cell_size", "step_ms", "initial_length",
                     "apple_growth", "poison_shrink", "min_length"):
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise ValueError(f"{name} 必须是正整数")
        if not 2 <= self.min_length <= self.initial_length <= self.grid_size:
            raise ValueError("要求 2 <= min_length <= initial_length <= grid_size")
        for name in ("apple_range", "poison_range"):
            bounds = getattr(self, name)
            if (not isinstance(bounds, (tuple, list)) or len(bounds) != 2
                    or any(type(x) is not int for x in bounds)
                    or not 0 <= bounds[0] <= bounds[1]):
                raise ValueError(f"{name} 必须是 (非负下限, 不小于下限的上限)")
        if self.apple_range[1] + self.poison_range[1] > self.grid_size ** 2 - self.initial_length:
            raise ValueError("食物数量上限之和不能超过初始空格数")
        for name in ("apple_refresh_s", "poison_refresh_s"):
            if not isinstance(getattr(self, name), (int, float)) or not 0 < getattr(self, name) < float("inf"):
                raise ValueError(f"{name} 必须是有限正数")
        for name in ("apple_score", "poison_penalty"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 0:
                raise ValueError(f"{name} 必须是非负整数")
        for name in ("snake_shape", "apple_shape", "poison_shape"):
            if getattr(self, name) not in {"circle", "square", "diamond"}:
                raise ValueError(f"{name} 只能是 circle、square 或 diamond")


class SnakeGame:
    """只管理游戏规则；不依赖窗口，便于测试或修改。"""
    def __init__(self, settings, now=None):
        settings.validate()
        self.cfg = settings
        self.rng = random.Random(settings.random_seed)
        self.reset(time.monotonic() if now is None else now)

    def reset(self, now):
        c = self.cfg
        y = c.grid_size // 2
        self.snake = [(c.initial_length - 1 - i, y) for i in range(c.initial_length)]
        self.direction = (1, 0)
        self.pending_direction = self.direction
        self.turn_pending = False
        self.growth_left = 0
        self.score = 0
        self.alive = True
        self.message = ""
        self.apples, self.poisons = set(), set()
        self.respawn("apple")
        self.respawn("poison")
        self.next_apple = now + c.apple_refresh_s
        self.next_poison = now + c.poison_refresh_s

    def free_cells(self):
        occupied = set(self.snake) | self.apples | self.poisons
        return [(x, y) for y in range(self.cfg.grid_size)
                for x in range(self.cfg.grid_size) if (x, y) not in occupied]

    def respawn(self, kind):
        # 每次刷新替换该类全部食物，所以不会累积毒苹果。
        target = self.apples if kind == "apple" else self.poisons
        bounds = self.cfg.apple_range if kind == "apple" else self.cfg.poison_range
        target.clear()
        free = self.free_cells()
        count = min(self.rng.randint(*bounds), len(free))
        target.update(self.rng.sample(free, count))

    def refill_minimum(self):
        # 吃完立刻补足下限；上限为零时完全禁用该类食物。
        for target, bounds in ((self.apples, self.cfg.apple_range),
                               (self.poisons, self.cfg.poison_range)):
            free = self.free_cells()
            count = min(max(0, bounds[0] - len(target)), len(free))
            target.update(self.rng.sample(free, count))

    def turn(self, direction):
        if direction not in {(x, y) for x in (-1, 0, 1) for y in (-1, 0, 1) if (x, y) != (0, 0)}:
            return
        # 一步只接受一次转向，避免快速连按绕过禁止掉头的规则。
        if self.turn_pending or direction == self.direction:
            return
        if direction == (-self.direction[0], -self.direction[1]):
            return
        self.pending_direction = direction
        self.turn_pending = True

    def refresh(self, now):
        if now >= self.next_apple:
            self.respawn("apple")
            self.next_apple = now + self.cfg.apple_refresh_s
        if now >= self.next_poison:
            self.respawn("poison")
            self.next_poison = now + self.cfg.poison_refresh_s

    def step(self, now):
        if not self.alive:
            return
        c = self.cfg
        self.refresh(now)
        self.direction = self.pending_direction
        self.turn_pending = False
        x, y = self.snake[0]
        dx, dy = self.direction
        head = (x + dx, y + dy)
        if c.wrap_edges:
            head = (head[0] % c.grid_size, head[1] % c.grid_size)
        elif not (0 <= head[0] < c.grid_size and 0 <= head[1] < c.grid_size):
            self.alive, self.message = False, "撞墙了"
            return
        apple, poison = head in self.apples, head in self.poisons
        # 生长欠账支持一次奖励增长多个格子。
        growth = getattr(self, "growth_left", 0)
        if apple:
            growth += c.apple_growth
        if poison:
            growth = 0  # 毒苹果也会取消尚未完成的增长
        keep_tail = growth > 0
        occupied = self.snake if keep_tail else self.snake[:-1]
        if head in occupied:
            self.alive, self.message = False, "撞到自己了"
            return
        self.snake.insert(0, head)
        if keep_tail:
            growth -= 1
        else:
            self.snake.pop()
        self.growth_left = growth
        if apple:
            self.apples.remove(head)
            self.score += c.apple_score
        if poison:
            self.poisons.remove(head)
            self.score -= c.poison_penalty
            if len(self.snake) - c.poison_shrink < c.min_length:
                self.alive, self.message = False, "毒苹果使蛇短于最小长度"
                return
            del self.snake[-c.poison_shrink:]
        if len(self.snake) == c.grid_size ** 2:
            self.alive, self.message = False, "你填满了棋盘，胜利！"
            return
        self.refill_minimum()


# ===== 下一个单元格 =====

import tkinter as tk
import math
from pathlib import Path
from PIL import Image, ImageTk

class SnakeWindow:
    # Q W E / A D / Z X C 对应八方向；方向键控制上下左右
    KEYS = {
        "q": (-1, -1), "w": (0, -1), "e": (1, -1),
        "a": (-1, 0),                "d": (1, 0),
        "z": (-1, 1),  "x": (0, 1),  "c": (1, 1),
        "Up": (0, -1), "Down": (0, 1), "Left": (-1, 0), "Right": (1, 0),
        "Home": (-1, -1), "Prior": (1, -1), "End": (-1, 1), "Next": (1, 1),
    }

    def __init__(self, settings):
        self.cfg = settings
        self.game = SnakeGame(settings)
        self.root = tk.Tk()
        self.root.title("八方向贪吃蛇 | 金苹果 + / 紫毒苹果 −")
        size = settings.grid_size * settings.cell_size
        self.root.geometry(f"{size}x{size}")
        self.root.resizable(False, False)
        self.canvas = tk.Canvas(self.root, width=size, height=size,
                                background=settings.background, highlightthickness=0)
        self.canvas.pack()
        if settings.sprite_art:
            self.load_sprites()
        self.paused = False
        self.pause_started = None
        self.after_id = None
        self.closed = False
        self.held_arrows = set()
        self.root.bind("<KeyPress>", self.on_key)
        self.root.bind("<KeyRelease>", self.on_release)
        self.root.bind("<FocusOut>", lambda event: self.held_arrows.clear())
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.next_move = time.monotonic() + settings.step_ms / 1000
        self.draw()
        self.canvas.focus_set()

    def on_key(self, event):
        key = event.keysym if event.keysym in self.KEYS or event.keysym == "Escape" else event.keysym.lower()
        if key in {"Up", "Down", "Left", "Right"}:
            if self.game.alive and not self.paused:
                self.held_arrows.add(key)
            return
        if key == "Escape":
            self.close()
        elif key == "r":
            now = time.monotonic()
            self.game = SnakeGame(self.cfg, now)
            self.held_arrows.clear()
            self.paused = False
            self.pause_started = None
            self.next_move = now + self.cfg.step_ms / 1000
        elif key == "space" and self.game.alive:
            now = time.monotonic()
            self.held_arrows.clear()
            if not self.paused:
                self.paused, self.pause_started = True, now
            else:
                elapsed = now - self.pause_started
                self.game.next_apple += elapsed
                self.game.next_poison += elapsed
                self.next_move += elapsed
                self.paused = False
        elif key in self.KEYS and self.game.alive and not self.paused:
            self.game.turn(self.KEYS[key])

    def on_release(self, event):
        self.held_arrows.discard(event.keysym)

    def arrow_direction(self):
        # 同轴相反键抵消；释放全部键后保持当前运动方向。
        dx = int("Right" in self.held_arrows) - int("Left" in self.held_arrows)
        dy = int("Down" in self.held_arrows) - int("Up" in self.held_arrows)
        return (dx, dy) if dx or dy else None

    def load_sprites(self):
        """载入项目内 PNG。保留透明通道，并在绘制时按棋格缓存缩放/旋转版本。"""
        folder = Path(self.cfg.asset_dir).expanduser()
        if not folder.is_absolute():
            folder = Path.cwd() / folder
        files = {
            "head": "snake_head.png", "body": "snake_body.png",
            "tail": "snake_tail.png", "apple": "apple.png",
            "poison": "poison_apple.png",
        }
        missing = [name for name in files.values() if not (folder / name).exists()]
        if missing:
            raise FileNotFoundError(
                "缺少贴图：" + ", ".join(missing) +
                f"。请确认文件夹位于 {folder}"
            )

        def open_trim(name, crop_mode="alpha"):
            image = Image.open(folder / files[name]).convert("RGBA")
            if crop_mode == "body":
                # 生成的身体纹理横向贯穿画布；固定截取中间鳞片带。
                w, h = image.size
                image = image.crop((0, int(h*.40), w, int(h*.66)))
            else:
                box = image.getchannel("A").getbbox()
                if box:
                    image = image.crop(box)
            return image

        self.sprite_sources = {
            "head": open_trim("head"),
            "body": open_trim("body", "body"),
            "tail": open_trim("tail"),
            "apple": open_trim("apple"),
            "poison": open_trim("poison"),
        }
        self.sprite_cache = {}

    def sprite(self, name, angle=0):
        s = self.cfg.cell_size
        dimensions = {
            "head": (int(s*1.72), int(s*1.72)),
            "body": (int(s*1.62), int(s*.82)),
            "tail": (int(s*1.82), int(s*1.04)),
            "apple": (int(s*1.32), int(s*1.32)),
            "poison": (int(s*1.40), int(s*1.40)),
        }
        # 两度取整足以覆盖八方向与转角切线，同时避免每帧创建新图片。
        rounded = int(round(angle / 2) * 2)
        key = (name, rounded, s)
        if key not in self.sprite_cache:
            image = self.sprite_sources[name].resize(dimensions[name], Image.Resampling.LANCZOS)
            if rounded:
                image = image.rotate(-rounded, resample=Image.Resampling.BICUBIC,
                                     expand=True)
            self.sprite_cache[key] = ImageTk.PhotoImage(image)
        return self.sprite_cache[key]

    def board_delta(self, a, b):
        """返回从 b 指向 a 的最短网格向量，兼容穿墙模式。"""
        dx, dy = a[0]-b[0], a[1]-b[1]
        if self.cfg.wrap_edges:
            half = self.cfg.grid_size / 2
            if dx > half: dx -= self.cfg.grid_size
            if dx < -half: dx += self.cfg.grid_size
            if dy > half: dy -= self.cfg.grid_size
            if dy < -half: dy += self.cfg.grid_size
        return dx, dy

    def draw_food_sprite(self, point, poison=False):
        s = self.cfg.cell_size
        image = self.sprite("poison" if poison else "apple")
        self.canvas.create_image((point[0]+.5)*s, (point[1]+.5)*s,
                                 image=image, anchor="center")

    def draw_snake_sprites(self):
        cv, c, g = self.canvas, self.cfg, self.game
        s = c.cell_size

        # 深色中心线连接棋格并填补转角，贴图覆盖其上。
        for a, b in zip(g.snake, g.snake[1:]):
            dx, dy = self.board_delta(a, b)
            if max(abs(dx), abs(dy)) > 1:
                continue
            ax, ay = (a[0]+.5)*s, (a[1]+.5)*s
            bx, by = ax-dx*s, ay-dy*s
            cv.create_line(ax+1, ay+s*.055, bx+1, by+s*.055,
                           fill="#071c13", width=max(4, int(s*.72)),
                           capstyle=tk.ROUND)
            cv.create_line(ax, ay, bx, by, fill=self.shade(c.snake_color,-.22),
                           width=max(3, int(s*.62)), capstyle=tk.ROUND)

        # 从尾到头叠放：鳞片保持清晰，头部永远位于最上层。
        if len(g.snake) > 1:
            tail, before = g.snake[-1], g.snake[-2]
            dx, dy = self.board_delta(tail, before)
            angle = math.degrees(math.atan2(dy, dx))
            cv.create_image((tail[0]+.5)*s, (tail[1]+.5)*s,
                            image=self.sprite("tail", angle), anchor="center")

        for i in range(len(g.snake)-2, 0, -1):
            point, toward_head, toward_tail = g.snake[i], g.snake[i-1], g.snake[i+1]
            hx, hy = self.board_delta(toward_head, point)
            tx, ty = self.board_delta(point, toward_tail)
            dx, dy = hx+tx, hy+ty
            if dx == 0 and dy == 0:
                dx, dy = hx, hy
            angle = math.degrees(math.atan2(dy, dx))
            cv.create_image((point[0]+.5)*s, (point[1]+.5)*s,
                            image=self.sprite("body", angle), anchor="center")

        hx, hy = g.snake[0]
        dx, dy = g.direction
        angle = math.degrees(math.atan2(dy, dx))
        cv.create_image((hx+.5)*s, (hy+.5)*s,
                        image=self.sprite("head", angle), anchor="center")

    def shade(self, color, amount):
        rgb = [v / 257 for v in self.root.winfo_rgb(color)]
        rgb = [v + (255-v)*amount if amount >= 0 else v*(1+amount) for v in rgb]
        return "#" + "".join(f"{max(0, min(255, round(v))):02x}" for v in rgb)

    def draw_apple(self, point, color, poison=False):
        cv, s = self.canvas, self.cfg.cell_size
        x, y = (point[0]+.5)*s, (point[1]+.5)*s
        def oval(a, b, c, d, fill):
            cv.create_oval(x+a*s, y+b*s, x+c*s, y+d*s, fill=fill, outline="")
        # 双肩、底部凹口与分层高光形成苹果轮廓。
        outline = [(-.36,-.14),(-.31,-.32),(-.14,-.37),(0,-.27),
                   (.14,-.37),(.32,-.29),(.38,-.10),(.31,.20),
                   (.16,.36),(0,.30),(-.16,.36),(-.31,.19)]
        oval(-.34,.26,.37,.43,"#080e18")
        for scale, off, fill in [(1,0,self.shade(color,-.38)),
                                  (.91,-.025,color),(.69,-.065,self.shade(color,.20))]:
            coords=[v for a,b in outline for v in (x+(a*scale+off)*s,y+(b*scale+off)*s)]
            cv.create_polygon(*coords, smooth=True, splinesteps=16, fill=fill, outline="")
        cv.create_line(x,y-.27*s,x+.025*s,y-.43*s,x+.095*s,y-.46*s,
                       smooth=True, fill="#865535", width=max(1.5,s*.07), capstyle=tk.ROUND)
        cv.create_polygon(x+.035*s,y-.34*s,x+.15*s,y-.48*s,
                          x+.36*s,y-.40*s,x+.21*s,y-.27*s,
                          smooth=True,fill="#85ac53" if not poison else "#7a965a",outline="")
        cv.create_line(x+.075*s,y-.33*s,x+.27*s,y-.40*s,
                       fill="#c6df89",width=max(1,s*.025))
        oval(-.23,-.24,-.12,-.02,self.shade(color,.70))
        oval(-.12,-.28,-.06,-.20,self.shade(color,.80))
        if poison:
            # 枯斑与骷髅：即使更改颜色也能辨认毒苹果。
            for a,b in [(.24,-.10),(-.20,.18),(.22,.20)]:
                oval(a-.035,b-.035,a+.035,b+.035,self.shade(color,-.55))
            oval(-.12,-.04,.18,.18,"#f1e8ce")
            cv.create_rectangle(x-.055*s,y+.10*s,x+.105*s,y+.23*s,
                                fill="#f1e8ce",outline="")
            for a in (-.045,.095):
                oval(a-.028,.045,a+.028,.10,"#352e46")
            cv.create_line(x+.025*s,y+.15*s,x+.025*s,y+.22*s,
                           fill="#352e46",width=1)

    def draw_snake(self):
        """沿身体中心线绘制渐细轮廓；短距离圆角，不改变碰撞网格。"""
        cv, c, g = self.canvas, self.cfg, self.game
        s = c.cell_size
        centers = [((x+.5)*s, (y+.5)*s) for x,y in reversed(g.snake)]
        body = c.snake_color
        # 先断开穿墙跳跃，避免出现横穿地图的身体。
        runs, run = [], []
        for p in centers:
            if run and max(abs(p[0]-run[-1][0]), abs(p[1]-run[-1][1])) > s*1.1:
                runs.append(run)
                run=[]
            run.append(p)
        if run:
            runs.append(run)

        def smooth_path(points):
            if len(points)<3:
                return points
            result=[points[0]]
            for i in range(1,len(points)-1):
                a,b,d=points[i-1],points[i],points[i+1]
                entry=(b[0]+(a[0]-b[0])*.22,b[1]+(a[1]-b[1])*.22)
                leave=(b[0]+(d[0]-b[0])*.22,b[1]+(d[1]-b[1])*.22)
                result.append(entry)
                for j in range(1,7):
                    t=j/6
                    result.append(((1-t)**2*entry[0]+2*t*(1-t)*b[0]+t*t*leave[0],
                                   (1-t)**2*entry[1]+2*t*(1-t)*b[1]+t*t*leave[1]))
            result.append(points[-1])
            return result

        for ri,points in enumerate(runs):
            path=smooth_path(points)
            if len(path)<2:
                x,y=path[0]
                cv.create_oval(x-s*.30,y-s*.30,x+s*.30,y+s*.30,fill=body,outline="")
                continue
            # 细密采样让尾端在约 1.5 格内平滑变宽，不再逐格出现圆斑。
            samples=[path[0]]
            for a,b in zip(path,path[1:]):
                steps=max(1,math.ceil(math.hypot(b[0]-a[0],b[1]-a[1])/(s*.12)))
                samples.extend((a[0]+(b[0]-a[0])*j/steps,a[1]+(b[1]-a[1])*j/steps)
                               for j in range(1,steps+1))
            distances=[0.]
            for a,b in zip(samples,samples[1:]):
                distances.append(distances[-1]+math.hypot(b[0]-a[0],b[1]-a[1]))
            normals=[]
            for i,p in enumerate(samples):
                a=samples[max(0,i-1)];b=samples[min(len(samples)-1,i+1)]
                dx,dy=b[0]-a[0],b[1]-a[1]
                length=math.hypot(dx,dy) or 1
                normals.append((-dy/length,dx/length))
            def ribbon(scale, offset, color):
                left,right=[],[]
                for p,(nx,ny),distance in zip(samples,normals,distances):
                    taper=min(1.,distance/(s*1.5)) if ri==0 else 1.
                    radius=s*(.025+.29*math.sin(taper*math.pi/2))*scale
                    cx,cy=p[0]+offset[0]*s,p[1]+offset[1]*s
                    left.extend((cx+nx*radius,cy+ny*radius))
                    right.append((cx-nx*radius,cy-ny*radius))
                coords=left+[v for p in reversed(right) for v in p]
                cv.create_polygon(*coords,fill=color,outline="")
            ribbon(1.14,(.025,.075),"#080e18")
            ribbon(1.06,(0,0),self.shade(body,-.38))
            ribbon(.92,(-.018,-.025),body)
            ribbon(.60,(-.038,-.065),self.shade(body,.14))
            ribbon(.20,(-.06,-.09),self.shade(body,.29))

        hx,hy=g.snake[0]
        x,y=(hx+.5)*s,(hy+.5)*s
        dx,dy=g.direction
        length=math.hypot(dx,dy)
        ux,uy=dx/length,dy/length
        def p(f,t):
            return x+s*(ux*f-uy*t), y+s*(uy*f+ux*t)
        # 杏仁形蛇头，采用原头部颜色；小眼睛、鼻孔与细嘴线。
        head=[(-.42,-.19),(-.25,-.29),(.02,-.32),(.27,-.23),
              (.40,-.10),(.42,0),(.40,.10),(.27,.23),(.02,.32),(-.25,.29),(-.42,.19)]
        rim=self.shade(body,-.40)
        cv.create_polygon(*[v for f,t in head for v in p(f,t)],smooth=True,
                          splinesteps=24,fill=c.head_color,outline=rim,width=max(1,s*.04))
        cv.create_polygon(*[v for f,t in [(-.31,-.10),(-.08,-.22),(.23,-.11),(.28,0),
                                         (.0,.07),(-.28,.04)] for v in p(f,t)],
                          smooth=True,fill=self.shade(c.head_color,.18),outline="")
        for side in (-1,1):
            ex,ey=p(.10,side*.225)
            r=s*.077
            cv.create_oval(ex-r,ey-r,ex+r,ey+r,fill="#edcc6b",outline=rim,width=max(1,s*.03))
            cv.create_line(*p(.065,side*.225),*p(.135,side*.225),
                           fill="#13251c",width=max(1.4,s*.047),capstyle=tk.ROUND)
            px,py=p(.08,side*.20)
            cv.create_oval(px-s*.017,py-s*.017,px+s*.017,py+s*.017,fill="#fff7da",outline="")
            nx,ny=p(.31,side*.095)
            r=max(.65,s*.022)
            cv.create_oval(nx-r,ny-r,nx+r,ny+r,fill=rim,outline="")
        cv.create_line(*p(.29,-.13),*p(.34,0),*p(.29,.13),
                       smooth=True,fill=self.shade(body,-.2),width=max(1,s*.025))

    def shape(self, position, kind, color, symbol=""):
        s = self.cfg.cell_size
        x, y = position
        left, top, right, bottom = x*s+2, y*s+2, (x+1)*s-2, (y+1)*s-2
        cx, cy = (left+right)/2, (top+bottom)/2
        if kind == "circle":
            self.canvas.create_oval(left, top, right, bottom, fill=color, outline="")
        elif kind == "square":
            self.canvas.create_rectangle(left, top, right, bottom, fill=color, outline="")
        else:
            self.canvas.create_polygon(cx, top, right, cy, cx, bottom, left, cy,
                                       fill=color, outline="")
        if symbol:
            self.canvas.create_text(cx, cy, text=symbol, fill="#111827",
                                    font=("Arial", max(8, s//2), "bold"))

    def draw(self):
        cv, g, c = self.canvas, self.game, self.cfg
        cv.delete("all")
        size = c.grid_size * c.cell_size
        if c.show_grid:
            for p in range(0, size + 1, c.cell_size):
                cv.create_line(p, 0, p, size, fill=c.grid_color)
                cv.create_line(0, p, size, p, fill=c.grid_color)
        for point in g.apples:
            if c.sprite_art:
                self.draw_food_sprite(point)
            elif c.realistic_art:
                self.draw_apple(point, c.apple_color)
            else:
                self.shape(point, c.apple_shape, c.apple_color, "+")
        for point in g.poisons:
            if c.sprite_art:
                self.draw_food_sprite(point, poison=True)
            elif c.realistic_art:
                self.draw_apple(point, c.poison_color, poison=True)
            else:
                self.shape(point, c.poison_shape, c.poison_color, "−")
        if c.sprite_art:
            self.draw_snake_sprites()
        elif c.realistic_art:
            self.draw_snake()
        else:
            for i in range(len(g.snake)-1,-1,-1):
                self.shape(g.snake[i],c.snake_shape,c.head_color if i == 0 else c.snake_color)
        now = self.pause_started if self.paused else time.monotonic()
        status = (f"分数 {g.score}  长度 {len(g.snake)}  "
                  f"苹果 {len(g.apples)} / 毒 {len(g.poisons)}  "
                  f"刷新 {max(0, g.next_apple-now):.1f}s / {max(0, g.next_poison-now):.1f}s")
        self.root.title("贪吃蛇 V4 | " + status)
        if self.paused or not g.alive:
            cv.create_rectangle(size*.07, size*.37, size*.93, size*.63,
                                fill="#182338", outline="#6b829f")
            cv.create_text(size/2, size*.46, text="已暂停" if self.paused else g.message,
                           fill="white", font=("Arial", 18, "bold"), width=size*.8)
            cv.create_text(size/2, size*.56,
                           text="空格继续 · R 重开 · Esc 退出" if self.paused else "R 重新开始 · Esc 退出",
                           fill="#d3dce9", font=("Arial", 12), width=size*.8)

    def tick(self):
        if self.closed:
            return
        now = time.monotonic()
        if self.game.alive and not self.paused:
            self.game.refresh(now)
            if now >= self.next_move:
                direction = self.arrow_direction()
                if direction is not None:
                    self.game.turn(direction)
                self.game.step(now)
                self.next_move = now + self.cfg.step_ms / 1000
        self.draw()
        self.after_id = self.root.after(30, self.tick)

    def close(self):
        self.closed = True
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.root.destroy()

    def run(self):
        self.tick()
        self.root.mainloop()

class MapPicker:
    """开始前选择正方形地图；点击开始才创建游戏与刷新计时器。"""
    def __init__(self, settings):
        self.settings = settings
        self.result = None
        self.root = tk.Tk()
        self.root.title("贪吃蛇 V4 · 选择地图")
        self.root.geometry("520x520")
        self.root.resizable(False, False)
        self.root.configure(bg="#111827")
        self.root.protocol("WM_DELETE_WINDOW", self.cancel)
        self.size = tk.StringVar(value=str(settings.grid_size))
        self.error = tk.StringVar()
        self.description = tk.StringVar()
        frame=tk.Frame(self.root,bg="#111827",padx=36,pady=25)
        frame.pack(fill="both",expand=True)
        tk.Label(frame,text="S N A K E  /  V3",fg="#7ad3a6",bg="#111827",
                 font=("Helvetica",12,"bold")).pack(anchor="w")
        tk.Label(frame,text="选择你的地图",fg="#f4f7fb",bg="#111827",
                 font=("Helvetica",27,"bold")).pack(anchor="w",pady=(10,6))
        tk.Label(frame,text="小地图更紧张，大地图有更多腾挪空间。",fg="#9cacbf",
                 bg="#111827",font=("Helvetica",12)).pack(anchor="w")
        row=tk.Frame(frame,bg="#111827")
        row.pack(fill="x",pady=(22,14))
        for title,n in (("紧凑 · 15×15",15),("标准 · 25×25",25),("宽阔 · 35×35",35)):
            tk.Button(row,text=title,command=lambda n=n:self.size.set(str(n)),
                      padx=8,pady=8,font=("Helvetica",11)).pack(side="left",expand=True,fill="x",padx=3)
        custom=tk.Frame(frame,bg="#111827")
        custom.pack(fill="x")
        tk.Label(custom,text="自定义边长（10–50 格）",fg="#d8e4ef",bg="#111827",
                 font=("Helvetica",12)).pack(side="left")
        tk.Spinbox(custom,from_=10,to=50,textvariable=self.size,width=6,
                   font=("Helvetica",15),justify="center").pack(side="right")
        self.preview=tk.Canvas(frame,width=110,height=110,bg="#111827",highlightthickness=0)
        self.preview.pack(pady=(14,4))
        tk.Label(frame,textvariable=self.description,fg="#a8c4b7",bg="#111827",
                 font=("Helvetica",11)).pack()
        tk.Label(frame,textvariable=self.error,fg="#ff9b9b",bg="#111827",
                 wraplength=430,font=("Helvetica",11)).pack(pady=(5,5))
        tk.Button(frame,text="开始游戏  →",command=self.start,font=("Helvetica",15,"bold"),
                  padx=30,pady=9).pack(fill="x")
        self.root.bind("<Return>",lambda event:self.start())
        self.root.bind("<Escape>",lambda event:self.cancel())
        self.size.trace_add("write",lambda *args:self.update_preview())
        self.update_preview()

    def selected_settings(self):
        from dataclasses import replace
        try:
            n=int(self.size.get())
        except ValueError:
            raise ValueError("请输入 10–50 之间的整数。")
        if not 10 <= n <= 50:
            raise ValueError("地图边长应为 10–50 格。")
        # 保持正方形，在大地图时缩小格子，避免窗口超出屏幕。
        available=min(self.root.winfo_screenwidth()-100,self.root.winfo_screenheight()-140)
        cell=min(self.settings.cell_size,max(1,available//n))
        cfg=replace(self.settings,grid_size=n,cell_size=cell)
        cfg.validate()
        return cfg

    def update_preview(self):
        self.preview.delete("all")
        try:
            cfg=self.selected_settings()
            self.error.set("")
        except ValueError as exc:
            self.error.set(str(exc));self.description.set("")
            return
        n=cfg.grid_size
        for i in range(n+1):
            p=5+i*100/n
            self.preview.create_line(p,5,p,105,fill="#28463e")
            self.preview.create_line(5,p,105,p,fill="#28463e")
        self.preview.create_rectangle(5,5,105,105,outline="#7ad3a6",width=2)
        self.description.set(f"{n} × {n} 格  ·  {n*n} 个格子  ·  窗口 {n*cfg.cell_size} × {n*cfg.cell_size} 像素")

    def start(self):
        try:
            self.result=self.selected_settings()
        except ValueError as exc:
            self.error.set(str(exc))
            return
        self.root.destroy()

    def cancel(self):
        self.result=None
        self.root.destroy()

    def run(self):
        self.root.mainloop()
        return self.result


# ===== 下一个单元格 =====

settings = Settings(
    sprite_art=True,       # V4 鳞片蛇与苹果贴图
    asset_dir="snake_assets_v4",
    realistic_art=True,    # 关闭 sprite_art 时退回 V3 Canvas 造型
    grid_size=25,
    cell_size=24,           # 窗口为 25 × 24 = 600 像素的正方形
    step_ms=140,           # 越小越快
    apple_range=(1, 3),    # 每次刷新随机生成 1~3 个苹果
    poison_range=(0, 1),   # 每次刷新随机生成 0~1 个毒苹果，总数最多 1
    apple_refresh_s=8.0,
    poison_refresh_s=5.0,
    apple_score=10,
    apple_growth=1,
    poison_penalty=15,
    poison_shrink=2,
    snake_shape="circle",
    snake_color="#45cc86",
    head_color="#9cffb3",
    apple_shape="circle",
    apple_color="#ffbe55",
    poison_shape="diamond",
    poison_color="#ca85ff",
    wrap_edges=False,
)

# 再次执行时关闭同一内核中旧的游戏窗口。
if "window" in globals() and not window.closed:
    window.close()
selected_settings = MapPicker(settings).run()
if selected_settings is not None:
    print(f"启动 V4：{selected_settings.grid_size}×{selected_settings.grid_size} 地图。")
    window = SnakeWindow(selected_settings)
    window.run()
else:
    print("已取消启动。")
