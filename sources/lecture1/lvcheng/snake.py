import pygame
import random
import math
import sys

# ══════════════════════════════════════════════════════
#  贪吃蛇 · 奇趣版
#
#  创意玩法:
#    ① 四种食物 —— 红色普通 / 金色高分 / 紫色毒药 / 蓝色加速
#    ② 连击系统 —— 快速连续吃食物, 得分倍率递增(最高 5 倍)
#    ③ 传送门   —— 随机出现一对传送门, 进入一端从另一端穿出
#    ④ 穿墙模式 —— 从屏幕边缘穿过, 对面出现
#    ⑤ 粒子特效 —— 吃食物时彩色粒子爆炸
#    ⑥ 屏幕震动 —— 吃毒药/死亡时画面抖动
#
#  操作: 方向键 / WASD  |  P = 暂停  ESC = 退出
# ══════════════════════════════════════════════════════

pygame.init()

# ───── 画面参数 ─────
CELL     = 24
COLS     = 32
ROWS     = 24
MAP_W    = CELL * COLS
MAP_H    = CELL * ROWS
PANEL_H  = 52
WIN_W    = MAP_W
WIN_H    = MAP_H + PANEL_H

# ───── 配色 ─────
BG_COLOR   = (10, 10, 18)
GRID_COLOR = (22, 22, 30)
PANEL_BG   = (14, 14, 24)
BORDER_CLR = (40, 40, 60)
HEAD_COLOR = (0, 230, 100)
TAIL_COLOR = (0, 120, 50)
FOOD_RED   = (230, 55, 55)
FOOD_GOLD  = (255, 200, 0)
FOOD_PURP  = (150, 50, 220)
FOOD_BLUE  = (50, 190, 255)
PORTAL_A   = (255, 100, 210)
PORTAL_B   = (100, 210, 255)
WHITE      = (240, 240, 240)
GRAY       = (130, 130, 140)
GREEN      = (0, 220, 100)

# ───── 方向 ─────
UP    = ( 0, -1)
DOWN  = ( 0,  1)
LEFT  = (-1,  0)
RIGHT = ( 1,  0)
OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}
KEY_DIR = {
    pygame.K_UP: UP,    pygame.K_w: UP,
    pygame.K_DOWN: DOWN,  pygame.K_s: DOWN,
    pygame.K_LEFT: LEFT,  pygame.K_a: LEFT,
    pygame.K_RIGHT: RIGHT, pygame.K_d: RIGHT,
}


# ───── 跨平台中文字体 ─────
def load_font(size, bold=False):
    for name in ["microsoftyahei", "simhei", "pingfang",
                  "heiti", "notosanssc", "wenquanyimicrohei", None]:
        try:
            f = pygame.font.SysFont(name, size, bold=bold)
            f.render("测", True, (255, 255, 255))
            return f
        except Exception:
            continue
    return pygame.font.Font(None, size)


FONT_BIG = load_font(42, bold=True)
FONT_MED = load_font(24, bold=True)
FONT_SML = load_font(14)


# ══════════════════ 粒子 ══════════════════
class Particle:
    __slots__ = ("x", "y", "vx", "vy", "color", "life", "max_life", "radius")

    def __init__(self, x, y, color):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(1.5, 5)
        self.x, self.y = float(x), float(y)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - 1.5
        self.color = color
        self.life = random.uniform(0.4, 1.0)
        self.max_life = self.life
        self.radius = random.uniform(2, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.08
        self.life -= 1 / 60

    def draw(self, surface):
        if self.life <= 0:
            return
        alpha = self.life / self.max_life
        c = tuple(int(self.color[i] * alpha) for i in range(3))
        r = max(1, int(self.radius * alpha))
        pygame.draw.circle(surface, c, (int(self.x), int(self.y)), r)

    @property
    def alive(self):
        return self.life > 0


# ══════════════════ 主游戏 ══════════════════
class SnakeGame:

    def __init__(self):
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("贪吃蛇 · 奇趣版")
        self.clock = pygame.time.Clock()
        self.particles = []
        self.reset()

    # ───────── 重置 ─────────
    def reset(self):
        cx, cy = COLS // 2, ROWS // 2
        self.snake    = [(cx - i, cy) for i in range(5)]
        self.dir      = RIGHT
        self.buf_dir  = RIGHT
        self.score    = 0
        self.alive    = True
        self.paused   = False
        self.grow     = 0
        self.combo    = 0
        self.combo_cd = 0
        self.boost    = 0
        self.portal   = None
        self.portal_cd = 0
        self.foods    = []
        self.particles = []
        self.frame    = 0
        self.shake    = 0
        self._spawn_food("normal")
        self._spawn_food()
        self._spawn_food()

    # ───────── 随机空位 ─────────
    def _rand_cell(self, extra_ban=()):
        banned = set(self.snake) | set(extra_ban)
        for f in self.foods:
            banned.add(f["pos"])
        if self.portal:
            banned |= {self.portal["a"], self.portal["b"]}
        for _ in range(999):
            p = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
            if p not in banned:
                return p
        return (0, 0)

    # ───────── 生成食物 ─────────
    def _spawn_food(self, kind=None):
        if kind is None:
            r = random.random()
            if   r < 0.50: kind = "normal"
            elif r < 0.72: kind = "gold"
            elif r < 0.88: kind = "speed"
            else:          kind = "poison"
        info = {
            "normal": (FOOD_RED,   10),
            "gold":   (FOOD_GOLD,  30),
            "poison": (FOOD_PURP, -20),
            "speed":  (FOOD_BLUE,  15),
        }[kind]
        self.foods.append({
            "pos":   self._rand_cell(),
            "kind":  kind,
            "color": info[0],
            "points": info[1],
        })

    # ───────── 粒子发射 ─────────
    def _emit(self, gx, gy, color, count=14):
        px = gx * CELL + CELL // 2
        py = gy * CELL + CELL // 2 + PANEL_H
        for _ in range(count):
            self.particles.append(Particle(px, py, color))

    # ───────── 移动间隔: 分越高越快 ─────────
    def _tick_interval(self):
        interval = 7 - min(self.score // 120, 3)
        if self.boost > 0:
            interval = max(2, interval - 2)
        return max(2, interval)

    # ═══════════════ 输入 ═══════════════
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if event.key == pygame.K_p:
                    self.paused = not self.paused
                    return
                if not self.alive:
                    if event.key == pygame.K_SPACE:
                        self.reset()
                    return
                if event.key in KEY_DIR:
                    new_dir = KEY_DIR[event.key]
                    if new_dir != OPPOSITE.get(self.dir):
                        self.buf_dir = new_dir

    # ═══════════════ 逻辑 ═══════════════
    def update(self):
        self.frame += 1

        # 粒子更新
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alive]

        # 震动衰减
        if self.shake > 0:
            self.shake = max(0, self.shake - 0.5)

        if not self.alive or self.paused:
            return

        # 连击冷却
        if self.combo_cd > 0:
            self.combo_cd -= 1
            if self.combo_cd <= 0:
                self.combo = 0

        # 加速冷却
        if self.boost > 0:
            self.boost -= 1

        # 传送门生命周期
        if self.portal:
            self.portal_cd -= 1
            if self.portal_cd <= 0:
                self.portal = None
        if self.portal is None and random.random() < 0.002:
            a = self._rand_cell()
            b = self._rand_cell(extra_ban=[a])
            self.portal = {"a": a, "b": b}
            self.portal_cd = 500

        # 保持食物数量
        while len(self.foods) < 3:
            self._spawn_food()

        # ── 按间隔执行游戏步 ──
        if self.frame % self._tick_interval() != 0:
            return

        self.dir = self.buf_dir
        hx, hy = self.snake[0]
        dx, dy = self.dir
        new_head = ((hx + dx) % COLS, (hy + dy) % ROWS)

        # 传送门
        if self.portal:
            for src, dst, glow_col in [
                (self.portal["a"], self.portal["b"], PORTAL_B),
                (self.portal["b"], self.portal["a"], PORTAL_A),
            ]:
                if new_head == src:
                    new_head = ((dst[0] + dx) % COLS, (dst[1] + dy) % ROWS)
                    self._emit(dst[0], dst[1], glow_col, 18)
                    break

        # 撞自己
        if new_head in self.snake:
            self.alive = False
            self.shake = 12
            self._emit(new_head[0], new_head[1], (255, 80, 80), 30)
            return

        self.snake.insert(0, new_head)

        # 吃食物
        for i, food in enumerate(self.foods):
            if food["pos"] == new_head:
                self.foods.pop(i)
                self.combo += 1
                self.combo_cd = 80
                multiplier = min(self.combo, 5)
                self.score = max(0, self.score + food["points"] * multiplier)
                self._emit(new_head[0], new_head[1], food["color"], 18)
                if food["kind"] == "poison":
                    self.grow -= 2
                    self.shake = 8
                elif food["kind"] == "speed":
                    self.boost = 120
                    self.grow += 2
                else:
                    self.grow += 2
                break

        # 长度调整
        if self.grow > 0:
            self.grow -= 1
        else:
            if len(self.snake) > 1:
                self.snake.pop()
            if self.grow < 0:
                self.grow += 1
                if len(self.snake) > 1:
                    self.snake.pop()

        if len(self.snake) < 2:
            self.alive = False
            self.shake = 12

    # ═══════════════ 绘制 ═══════════════
    def draw(self):
        self.screen.fill(BG_COLOR)
        sk = int(self.shake)
        ox = random.randint(-sk, sk) if sk > 0 else 0
        oy = random.randint(-sk, sk) if sk > 0 else 0

        # ── 状态栏 ──
        pygame.draw.rect(self.screen, PANEL_BG, (0, 0, WIN_W, PANEL_H))
        pygame.draw.line(self.screen, BORDER_CLR, (0, PANEL_H - 1), (WIN_W, PANEL_H - 1))
        self.screen.blit(FONT_MED.render(f"得分: {self.score}", True, GREEN), (14, 12))
        if self.combo > 1:
            txt = FONT_MED.render(f"连击 x{self.combo}!", True, FOOD_GOLD)
            self.screen.blit(txt, (WIN_W // 2 - txt.get_width() // 2, 12))
        self.screen.blit(FONT_SML.render(f"长度: {len(self.snake)}", True, GRAY), (WIN_W - 95, 8))
        if self.boost > 0:
            self.screen.blit(FONT_SML.render(f"加速 {self.boost // 60 + 1}s", True, FOOD_BLUE), (WIN_W - 95, 28))

        # ── 游戏区 ──
        gs = pygame.Surface((MAP_W, MAP_H))
        gs.fill(BG_COLOR)

        for x in range(0, MAP_W, CELL):
            pygame.draw.line(gs, GRID_COLOR, (x, 0), (x, MAP_H))
        for y in range(0, MAP_H, CELL):
            pygame.draw.line(gs, GRID_COLOR, (0, y), (MAP_W, y))
        pygame.draw.rect(gs, BORDER_CLR, (0, 0, MAP_W, MAP_H), 2)

        # 传送门
        if self.portal:
            for pos, color in [(self.portal["a"], PORTAL_A), (self.portal["b"], PORTAL_B)]:
                px = pos[0] * CELL + CELL // 2
                py = pos[1] * CELL + CELL // 2
                pulse = 0.7 + 0.3 * abs(math.sin(self.frame * 0.08))
                r = int(CELL // 2 * pulse)
                glow = pygame.Surface((CELL * 3, CELL * 3), pygame.SRCALPHA)
                pygame.draw.circle(glow, (*color, 35), (CELL * 3 // 2, CELL * 3 // 2), CELL)
                gs.blit(glow, (px - CELL * 3 // 2, py - CELL * 3 // 2))
                pygame.draw.circle(gs, color, (px, py), r, 3)
                pygame.draw.circle(gs, WHITE, (px, py), max(1, r // 2), 1)

        # 食物
        for food in self.foods:
            fx, fy = food["pos"]
            cx = fx * CELL + CELL // 2
            cy = fy * CELL + CELL // 2
            col = food["color"]
            glow_a = int(20 + 12 * math.sin(self.frame * 0.07))
            glow = pygame.Surface((CELL * 3, CELL * 3), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*col, glow_a), (CELL * 3 // 2, CELL * 3 // 2), CELL)
            gs.blit(glow, (cx - CELL * 3 // 2, cy - CELL * 3 // 2))

            kind = food["kind"]
            if kind == "gold":
                star_pts = []
                for i in range(5):
                    for offset, radius in [(-90, CELL / 2.5), (-54, CELL / 5)]:
                        angle = math.radians(i * 72 + offset)
                        star_pts.append((cx + int(math.cos(angle) * radius),
                                         cy + int(math.sin(angle) * radius)))
                pygame.draw.polygon(gs, col, star_pts)
                pygame.draw.polygon(gs, (255, 230, 100), star_pts, 2)
            elif kind == "poison":
                pygame.draw.circle(gs, col, (cx, cy), CELL // 2 - 2)
                for sign in (-1, 1):
                    pygame.draw.line(gs, (80, 20, 120),
                                     (cx + sign * 4, cy - 4), (cx + sign * 1, cy - 1), 2)
                    pygame.draw.line(gs, (80, 20, 120),
                                     (cx + sign * 1, cy - 4), (cx + sign * 4, cy - 1), 2)
            elif kind == "speed":
                bolt = [(cx-3, cy-8), (cx+3, cy-1), (cx-1, cy-1),
                        (cx+4, cy+8), (cx-2, cy+1), (cx+1, cy+1)]
                pygame.draw.polygon(gs, col, bolt)
            else:
                pygame.draw.circle(gs, col, (cx, cy), CELL // 2 - 2)
                hl = tuple(min(255, c + 80) for c in col)
                pygame.draw.circle(gs, hl, (cx - 3, cy - 3), 3)

        # 蛇
        n = len(self.snake)
        for i, (sx, sy) in enumerate(self.snake):
            t = i / max(n - 1, 1)
            color = tuple(int(HEAD_COLOR[j] + (TAIL_COLOR[j] - HEAD_COLOR[j]) * t) for j in range(3))
            if self.boost > 0 and i < 3:
                flash = abs(math.sin(self.frame * 0.25))
                color = tuple(int(color[j] + (255 - color[j]) * flash * 0.35) for j in range(3))
            rect = pygame.Rect(sx * CELL + 1, sy * CELL + 1, CELL - 2, CELL - 2)
            pygame.draw.rect(gs, color, rect, border_radius=6)
            inner = pygame.Rect(sx * CELL + 4, sy * CELL + 4, CELL - 8, CELL - 8)
            lighter = tuple(min(255, color[j] + 20) for j in range(3))
            pygame.draw.rect(gs, lighter, inner, border_radius=4)
            if i == 0:
                hx_px = sx * CELL + CELL // 2
                hy_px = sy * CELL + CELL // 2
                d = self.dir
                perp = (-d[1], d[0])
                for sign in (-1, 1):
                    ex = hx_px + d[0] * 5 + perp[0] * 5 * sign
                    ey = hy_px + d[1] * 5 + perp[1] * 5 * sign
                    pygame.draw.circle(gs, WHITE, (ex, ey), 4)
                    pygame.draw.circle(gs, (10, 10, 10), (ex + d[0] * 2, ey + d[1] * 2), 2)

        self.screen.blit(gs, (ox, PANEL_H + oy))

        # 粒子
        for p in self.particles:
            p.draw(self.screen)

        # 图例
        if self.frame < 360:
            legend = FONT_SML.render(
                "红=普通  金=高分(连击!)  紫=毒药(缩短!)  蓝=加速  传送门=穿越!", True, GRAY)
            self.screen.blit(legend, (14, WIN_H - 22))

        # 暂停
        if self.paused:
            ov = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 140))
            self.screen.blit(ov, (0, 0))
            txt = FONT_BIG.render("暂停", True, WHITE)
            self.screen.blit(txt, (WIN_W // 2 - txt.get_width() // 2, WIN_H // 2 - 30))

        # 游戏结束
        if not self.alive:
            ov = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 180))
            self.screen.blit(ov, (0, 0))
            for text, fnt, color, dy in [
                ("游戏结束", FONT_BIG, FOOD_RED, -80),
                (f"最终得分: {self.score}", FONT_MED, WHITE, -20),
                ("空格键 重新开始  |  ESC 退出", FONT_SML, GRAY, 30),
            ]:
                surf = fnt.render(text, True, color)
                self.screen.blit(surf, (WIN_W // 2 - surf.get_width() // 2, WIN_H // 2 + dy))

        pygame.display.flip()

    # ═══════════════ 主循环 ═══════════════
    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)


if __name__ == "__main__":
    SnakeGame().run()