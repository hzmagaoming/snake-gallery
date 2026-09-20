import pygame
import math
import random
import sys

# 初始化 pygame
pygame.init()

# ========================================
# 游戏配置常量
# ========================================
RENDER_SCALE = 2               # 超采样倍率：内部按2倍分辨率绘制再平滑缩放，画质更清晰
WIN_WIDTH = 960                # 窗口宽
WIN_HEIGHT = 720               # 窗口高（足够容纳主界面全部分区，不再有内容被裁切）
SCREEN_WIDTH = WIN_WIDTH * RENDER_SCALE    # 内部画布（游戏逻辑坐标）
SCREEN_HEIGHT = WIN_HEIGHT * RENDER_SCALE
BLOCK_SIZE = 20 * RENDER_SCALE
INITIAL_SPEED = 7
BOOST_FACTOR = 2               # 按住空格的加速倍率
WIN_SCORE = 100                # 满分，达到即通关
NPC_COUNT = 3                  # 场上随机小蛇的数量
FPS = 60                       # 固定帧率：渲染顺滑，移动节奏由"移动间隔"控制

# 游戏模式 / 速度 选项（主界面可鼠标点选）
MODE_NAMES = ["经典边界模式", "无边界穿墙模式"]
SPEED_NAMES = ["悠闲速度", "标准速度", "闪电速度"]
SPEED_MULT = [0.75, 1.0, 1.5]

# 窗口与画布的换算比例（鼠标坐标需要缩放）
MOUSE_SCALE = RENDER_SCALE

# 音频总开关（初始化失败时自动降级为静音，不影响游戏运行）
AUDIO_ON = True

# ========================================
# 颜色配置 (RGB格式) —— 清新绿色卡通风
# ========================================
# 基础颜色
BG_COLOR = (222, 246, 212)      # 浅绿天空（更柔和）
GRID_COLOR = (212, 240, 202)    # 极淡网格线，不干扰视线
HILL_COLOR = (176, 226, 168)    # 草地山丘（远，柔和）
HILL2_COLOR = (192, 234, 182)   # 草地山丘（近）
CLOUD_COLOR = (255, 255, 255)   # 白云
SUN_COLOR = (255, 238, 158)     # 柔和的太阳
TEXT_COLOR = (40, 110, 60)      # 深绿文字
TEXT_SHADOW = (255, 255, 255)   # 白色描边阴影

# 食物颜色（卡通小苹果）
FOOD_COLOR = (235, 70, 70)

# 蛇的通用细节配色 + 界面主题色
HEAD_COLOR = (86, 200, 120)     # 界面主题绿（标题等）
EYE_COLOR = (45, 45, 45)        # 眼睛颜色：深灰黑
BLUSH_COLOR = (255, 160, 175)   # 腮红粉
TONGUE_COLOR = (255, 90, 100)   # 小舌头红
BOOST_COLOR = (255, 150, 60)    # 加速提示色

# 皮肤库：玩家开局自选一款；随机小蛇只会从"其余皮肤"中取色，
# 因此绝对不会出现玩家蛇和小蛇颜色或样式相同的情况
SKINS = [
    {   # 1. 翠绿蛇（经典款）
        "name": "翠翠·绿",
        "head": (86, 200, 120),
        "body": [(140, 224, 140), (104, 210, 126), (76, 188, 108)],
    },
    {   # 2. 海蓝蛇
        "name": "蓝蓝·海",
        "head": (86, 156, 255),
        "body": [(150, 196, 255), (110, 170, 250), (80, 145, 240)],
    },
    {   # 3. 阳光金蛇
        "name": "金金·阳",
        "head": (255, 200, 60),
        "body": [(255, 225, 130), (250, 205, 90), (240, 185, 60)],
    },
    {   # 4. 樱花粉蛇
        "name": "桃桃·樱",
        "head": (255, 130, 170),
        "body": [(255, 180, 205), (250, 155, 185), (242, 132, 168)],
    },
    {   # 5. 紫罗兰蛇
        "name": "莓莓·紫",
        "head": (172, 126, 255),
        "body": [(204, 166, 255), (184, 142, 248), (160, 116, 236)],
    },
    {   # 6. 活力橙蛇
        "name": "桔桔·橙",
        "head": (255, 152, 64),
        "body": [(255, 196, 130), (250, 172, 96), (242, 150, 70)],
    },
]

# 设置屏幕：内部高分辨率画布 + 平滑缩放到窗口（高清画质）
screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
display = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("卡通小绿蛇大作战")
clock = pygame.time.Clock()

def get_chinese_font(size):
    """
    获取支持中文的系统字体（卡通可爱风优先）。
    直接按路径加载字体文件，绕开 pygame.font.match_font
    （pygame 2.6.1 在部分 Windows 环境下扫描注册表会因
    异常注册表项抛出 TypeError）。
    """
    import os
    base = os.path.dirname(os.path.abspath(__file__))
    font_paths = [
        # 1) 游戏自带的免费卡通字体：站酷快乐体（圆润活泼）
        os.path.join(base, "ZCOOLKuaiLe-Regular.ttf"),
        # 2) 系统常见可爱风字体（如有）
        r"C:\Windows\Fonts\SIMYOU.TTF",    # 幼圆
        r"C:\Windows\Fonts\STHUPO.TTF",    # 华文琥珀
        # 3) 兜底的常规中文字体
        r"C:\Windows\Fonts\msyh.ttc",      # 微软雅黑
        r"C:\Windows\Fonts\msyh.ttf",
        r"C:\Windows\Fonts\simhei.ttf",    # 黑体
        "/System/Library/Fonts/PingFang.ttc",          # macOS
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # Linux
    ]
    for path in font_paths:
        if os.path.exists(path):
            return pygame.font.Font(path, size)

    # 兜底：尝试 match_font（用 try/except 防御注册表异常）
    try:
        for f in ['microsoftyahei', 'simhei', 'pingfang', 'stheiti', 'arial']:
            match = pygame.font.match_font(f)
            if match:
                return pygame.font.Font(match, size)
    except Exception:
        pass

    # 如果没找到中文字体，回退到默认字体
    return pygame.font.Font(None, size)


def set_font_bold(font, bold=True):
    """给字体开启仿粗体。
    站酷快乐体本身笔画偏细，在大字号标题/结算上开启伪粗体后更饱满醒目。
    若该 pygame 版本不支持 set_bold，则静默忽略（不影响运行）。"""
    try:
        font.set_bold(bold)
    except Exception:
        pass
    return font

# 预加载字体（画布是2倍分辨率，字号同步放大）
font_large = get_chinese_font(120)     # 标题 / 结算主信息
font_medium = get_chinese_font(72)     # 次级标题 / 按钮大字
font_small = get_chinese_font(48)      # 正文说明
font_tiny = get_chinese_font(40)       # 分区小标题 / 规则文字
font_key = get_chinese_font(28)        # 按钮内文字

# 标题与结算用的大字开启仿粗体：笔画更饱满、更清晰醒目（无重影）
set_font_bold(font_large, True)
set_font_bold(font_medium, True)


def get_font(size, bold=False):
    """按需另取字号（用于主界面错落有致的排版），并做缓存避免重复创建。
    站酷快乐体在不同字号下观感差异较大，单独取字号能让各级标题层次更分明。"""
    key = (size, bold)
    f = _font_pool.get(key)
    if f is None:
        f = get_chinese_font(size)
        if bold:
            set_font_bold(f, True)
        _font_pool[key] = f
    return f


_font_pool = {}


# 主界面专用字号：与游戏内字号解耦，只为排版好看
font_title = get_font(104, bold=True)   # 大标题
font_sub = get_font(40)                 # 标题副标语
font_section = get_font(44, bold=True)  # 分区标题（游戏模式/游戏速度…）
font_btn = get_font(32)                 # 按钮内文字
font_rule = get_font(34)                # 规则文字


# ========================================
# 文字渲染缓存
# 同一段文字每帧重复 render 很耗性能，缓存起来后直接贴图，
# 这是保持 60FPS 顺滑的关键优化之一。
# ========================================
_text_cache = {}


def blit_text_cached(surface, text, font, color, x, y):
    """带缓存的文字绘制（相同文字+字体+颜色只渲染一次）"""
    key = (text, id(font), color)
    img = _text_cache.get(key)
    if img is None:
        img = font.render(text, True, color)
        _text_cache[key] = img
    surface.blit(img, (x, y))
    return img


def text_size_cached(text, font):
    """带缓存的文字尺寸查询"""
    key = ("__size__", text, id(font))
    size = _text_cache.get(key)
    if size is None:
        size = font.size(text)
        _text_cache[key] = size
    return size


def draw_centered(text, font, color, center_x, y):
    """居中绘制文字（自动使用缓存）"""
    w = text_size_cached(text, font)[0]
    return blit_text_cached(screen, text, font, color, center_x - w // 2, y)


# ========================================
# 音频：背景音乐 + 三种简短音效（纯代码合成，无需外部音频文件）
# ========================================
def _make_tone(notes, volume=0.35):
    """用正弦波合成一小段音频。
    notes: [(起始秒, 时长秒, 频率Hz), ...]，0 频率表示休止。
    不依赖 numpy，直接用数组模块生成，兼容性好。"""
    try:
        import array
        rate = 22050
        total = sum(start + dur for start, dur, _f in notes)
        total = max(total, 0.05)
        n = int(rate * total)
        buf = array.array("h", bytes(2 * n))
        for start, dur, freq in notes:
            if freq <= 0:
                continue
            i0, i1 = int(start * rate), min(int((start + dur) * rate), n)
            length = max(i1 - i0, 1)
            import math as _m
            for i in range(i0, i1):
                # 末段做淡出，避免爆音
                env = min(1.0, (i1 - i) / (rate * 0.03))
                buf[i] += int(32767 * volume * env * _m.sin(2 * _m.pi * freq * (i - i0) / rate))
        return pygame.mixer.Sound(buffer=buf.tobytes())
    except Exception:
        return None


def _init_audio():
    """初始化音频并生成音效/BGM。任一步失败都静默降级，不影响游戏。"""
    global AUDIO_ON
    try:
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.mixer.init(22050, -16, 1, 512)
        pygame.mixer.set_num_channels(8)
    except Exception:
        AUDIO_ON = False
        return None, None, None, None

    # 音效1：吃到苹果 —— 清脆上扬的两连音
    sfx_eat = _make_tone([(0.0, 0.07, 880), (0.06, 0.09, 1320)], volume=0.30)
    # 音效2：击杀小蛇 —— 活泼的三连音
    sfx_kill = _make_tone([(0.0, 0.06, 660), (0.05, 0.06, 880), (0.10, 0.12, 1180)], volume=0.32)
    # 音效3：失败/撞墙 —— 低沉下坠音
    sfx_die = _make_tone([(0.0, 0.14, 440), (0.12, 0.16, 330), (0.26, 0.26, 220)], volume=0.34)
    # 音效4：通关 —— 欢快的上行琶音
    sfx_win = _make_tone([(0.0, 0.10, 660), (0.09, 0.10, 880), (0.18, 0.10, 1100), (0.27, 0.28, 1320)],
                         volume=0.32)

    # 背景音乐：舒缓循环的柔和旋律（间隔留白，听感轻松不吵）
    bgm_notes = []
    melody = [523, 587, 659, 784, 659, 587, 523, 440, 494, 523, 587, 523]
    t = 0.0
    for i, f in enumerate(melody):
        dur = 0.62 if i % 4 != 3 else 0.95
        bgm_notes.append((t, dur * 0.55, f))
        bgm_notes.append((t, dur * 0.55, f * 0.5))   # 低八度叠加，更饱满
        t += dur
    bgm = _make_tone(bgm_notes, volume=0.10)
    if bgm:
        try:
            bgm.play(loops=-1)
        except Exception:
            pass
    return sfx_eat, sfx_kill, sfx_die, sfx_win


SFX_EAT, SFX_KILL, SFX_DIE, SFX_WIN = _init_audio()


def play(sound):
    """播放音效（失败静默）"""
    if AUDIO_ON and sound is not None:
        try:
            sound.play()
        except Exception:
            pass

def _build_background():
    """把静态背景（天空/太阳/云/网格/山丘/小花）一次性画好并缓存成图片。
    游戏运行时直接贴图，避免每帧重复绘制上百个图元导致的卡顿，帧率更顺滑。"""
    S = RENDER_SCALE
    bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    bg.fill(BG_COLOR)

    # 太阳（右上角，柔和带光芒）
    sun_center = (SCREEN_WIDTH - 90 * S, 90 * S)
    pygame.draw.circle(bg, SUN_COLOR, sun_center, 36 * S)
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        x1 = sun_center[0] + math.cos(rad) * 44 * S
        y1 = sun_center[1] + math.sin(rad) * 44 * S
        x2 = sun_center[0] + math.cos(rad) * 56 * S
        y2 = sun_center[1] + math.sin(rad) * 56 * S
        pygame.draw.line(bg, SUN_COLOR, (int(x1), int(y1)), (int(x2), int(y2)), 4 * S)

    # 白云
    def draw_cloud(cx, cy, s=1.0):
        for dx, dy, r in ((0, 0, 18), (18, -8, 14), (-18, -6, 13), (32, 3, 11), (-31, 4, 11)):
            pygame.draw.circle(bg, CLOUD_COLOR,
                               (int(cx + dx * s * S), int(cy + dy * s * S)), int(r * s * S))
    draw_cloud(int(SCREEN_WIDTH * 0.16), int(SCREEN_HEIGHT * 0.20), 1.2)
    draw_cloud(int(SCREEN_WIDTH * 0.52), int(SCREEN_HEIGHT * 0.12), 1.0)
    draw_cloud(int(SCREEN_WIDTH * 0.72), int(SCREEN_HEIGHT * 0.32), 0.8)

    # 极淡网格
    for x in range(0, SCREEN_WIDTH, BLOCK_SIZE):
        pygame.draw.line(bg, GRID_COLOR, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, BLOCK_SIZE):
        pygame.draw.line(bg, GRID_COLOR, (0, y), (SCREEN_WIDTH, y))

    # 草地山丘
    pygame.draw.ellipse(bg, HILL_COLOR,
                        (int(-160 * S), SCREEN_HEIGHT - 130 * S, SCREEN_WIDTH + 520 * S, 280 * S))
    pygame.draw.ellipse(bg, HILL2_COLOR,
                        (int(-280 * S), SCREEN_HEIGHT - 90 * S, SCREEN_WIDTH + 620 * S, 210 * S))

    # 小花
    def draw_flower(cx, cy, petal=(255, 190, 210), center_c=(255, 235, 160)):
        for dx, dy in ((0, -6), (0, 6), (-6, 0), (6, 0)):
            pygame.draw.circle(bg, petal, (int(cx + dx * S), int(cy + dy * S)), 5 * S)
        pygame.draw.circle(bg, center_c, (int(cx), int(cy)), 4 * S)
    draw_flower(int(SCREEN_WIDTH * 0.09), SCREEN_HEIGHT - 45 * S)
    draw_flower(int(SCREEN_WIDTH * 0.26), SCREEN_HEIGHT - 28 * S)
    draw_flower(int(SCREEN_WIDTH * 0.44), SCREEN_HEIGHT - 50 * S, petal=(255, 255, 255))
    draw_flower(int(SCREEN_WIDTH * 0.65), SCREEN_HEIGHT - 32 * S)
    draw_flower(int(SCREEN_WIDTH * 0.88), SCREEN_HEIGHT - 46 * S, petal=(255, 255, 255))
    return bg


# 缓存静态背景与菜单遮罩（只算一次，之后每帧直接贴图）
BG_SURFACE = _build_background()
MENU_OVERLAY = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
MENU_OVERLAY.fill((255, 255, 255, 150))


class Button:
    """可鼠标点击 / 悬停高亮的选择按钮。

    三态外观：
    - 选中：暖黄底 + 绿色粗描边 + 左侧小对勾，一眼看出当前选择
    - 悬停：淡绿底 + 轻微上浮感，给鼠标操作即时反馈
    - 常态：白底 + 浅灰绿描边
    """
    def __init__(self, rect, text, value):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.value = value
        self.hover = False

    def draw(self, surface, selected, font):
        S = RENDER_SCALE
        if selected:
            fill, border, tcol, bw = (255, 250, 226), HEAD_COLOR, HEAD_COLOR, 3 * S
        elif self.hover:
            fill, border, tcol, bw = (238, 252, 232), (120, 190, 140), TEXT_COLOR, 2 * S
        else:
            fill, border, tcol, bw = (255, 255, 255), (176, 206, 182), TEXT_COLOR, 2 * S

        # 圆角胶囊形按钮 + 底部投影，更有立体感
        shadow = self.rect.move(0, 3 * S)
        pygame.draw.rect(surface, (200, 222, 200), shadow, border_radius=14 * S)
        pygame.draw.rect(surface, fill, self.rect, border_radius=14 * S)
        pygame.draw.rect(surface, border, self.rect, bw, border_radius=14 * S)

        # 选中态在左侧画一个小对勾
        if selected:
            tick_x = self.rect.left + 16 * S
            cy = self.rect.centery
            pygame.draw.lines(surface, HEAD_COLOR, False, [
                (tick_x, cy),
                (tick_x + 5 * S, cy + 6 * S),
                (tick_x + 14 * S, cy - 7 * S),
            ], 3 * S)

        img = font.render(self.text, True, tcol)
        surface.blit(img, img.get_rect(center=self.rect.center))

    def hit(self, pos):
        return self.rect.collidepoint(pos)

def draw_text(text, font, text_col, x, y, shadow=True):
    """在屏幕上绘制带有可选阴影的文本"""
    if shadow:
        shadow_img = font.render(text, True, TEXT_SHADOW)
        screen.blit(shadow_img, (x + 3 * RENDER_SCALE, y + 3 * RENDER_SCALE))
    
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

class Snake:
    def __init__(self, skin):
        # 记住自己的皮肤（颜色方案），随机小蛇不会使用同一款
        self.skin = skin
        # 初始位置靠近屏幕中央，并对齐到网格（否则永远吃不到食物）
        start_x = (SCREEN_WIDTH // 2 // BLOCK_SIZE) * BLOCK_SIZE
        start_y = (SCREEN_HEIGHT // 2 // BLOCK_SIZE) * BLOCK_SIZE
        
        # 蛇身坐标列表 (x, y)，初始长度为3
        self.body = [
            (start_x, start_y),
            (start_x - BLOCK_SIZE, start_y),
            (start_x - BLOCK_SIZE * 2, start_y)
        ]
        
        # 初始方向：向右
        self.direction = (BLOCK_SIZE, 0)
        # 转向队列：缓存最多2个按键，连续快速输入也不会丢，且逐个生效（操作更跟手）
        self.pending_turns = []

    def turn(self, new_dir):
        """记录一次转向请求（相对上一次排队方向判断，避免连续按键被吞）"""
        last = self.pending_turns[-1] if self.pending_turns else self.direction
        if new_dir == last or new_dir == (-last[0], -last[1]):
            return                      # 同方向或直接180度掉头，忽略
        if len(self.pending_turns) < 2:
            self.pending_turns.append(new_dir)

    def update(self, wrap=False):
        """更新蛇的位置；wrap=True 时穿墙（从另一边出来）"""
        if self.pending_turns:
            self.direction = self.pending_turns.pop(0)

        # 计算新头部位置
        head_x, head_y = self.body[0]
        dir_x, dir_y = self.direction
        new_x, new_y = head_x + dir_x, head_y + dir_y

        if wrap:
            # 无边界模式：超出后从对面出来
            new_x %= SCREEN_WIDTH
            new_y %= SCREEN_HEIGHT

        self.body.insert(0, (new_x, new_y))
        
        # 默认不移除尾巴（如果吃到了食物，外部逻辑会跳过移除操作从而变长）
        # 这里由主循环控制，默认移动时外部会调用 pop() 移除尾巴
        
    def draw(self, surface):
        """先画蛇身（绿色渐变圆），再画可爱的蛇头（大眼睛+腮红+小舌头）"""
        S = RENDER_SCALE
        # ---- 蛇身（比格子大一圈，玩家蛇更醒目威风）----
        grow = 2 * S
        for i, segment in enumerate(self.body[1:], start=1):
            x, y = segment
            color_index = (i - 1) % len(self.skin["body"])
            color = self.skin["body"][color_index]
            center = (x + BLOCK_SIZE // 2, y + BLOCK_SIZE // 2)
            pygame.draw.circle(surface, color, center, BLOCK_SIZE // 2 + grow)

        # ---- 蛇头 ----
        x, y = self.body[0]
        rect = pygame.Rect(x - grow, y - grow, BLOCK_SIZE + 2 * grow, BLOCK_SIZE + 2 * grow)
        pygame.draw.rect(surface, self.skin["head"], rect, border_radius=10 * S + grow)

        cx = x + BLOCK_SIZE // 2
        cy = y + BLOCK_SIZE // 2
        fx, fy = self.direction[0] // BLOCK_SIZE, self.direction[1] // BLOCK_SIZE  # 朝向
        px, py = -fy, fx                                                            # 垂直朝向

        # 腮红（眼睛后侧两团粉色）
        for s in (-1, 1):
            bx = int(cx - fx * 2 * S + px * 8 * S * s)
            by = int(cy - fy * 2 * S + py * 8 * S * s)
            pygame.draw.circle(surface, BLUSH_COLOR, (bx, by), 3 * S)

        # 大眼睛（白底 + 黑瞳 + 高光），会俏皮地眨眼
        now = pygame.time.get_ticks()
        blinking = now % 3200 < 160
        for s in (-1, 1):
            ex = int(cx + fx * 3 * S + px * 5 * S * s)
            ey = int(cy + fy * 3 * S + py * 5 * S * s)
            if blinking:
                # 眯眯眼~
                pygame.draw.line(surface, EYE_COLOR,
                                 (ex - 4 * S, ey), (ex + 4 * S, ey), 2 * S)
            else:
                pygame.draw.circle(surface, (255, 255, 255), (ex, ey), 5 * S)
                pygame.draw.circle(surface, EYE_COLOR, (ex + fx * 2 * S, ey + fy * 2 * S), 3 * S)
                pygame.draw.circle(surface, (255, 255, 255), (ex + fx * 3 * S, ey + fy * 3 * S), 1 * S)

        # 调皮的小舌头（时不时吐一下）
        if now % 1400 < 850:
            pygame.draw.line(surface, TONGUE_COLOR,
                             (int(cx + fx * 10 * S), int(cy + fy * 10 * S)),
                             (int(cx + fx * 16 * S), int(cy + fy * 16 * S)), 2 * S)

    def check_collision(self, wrap=False):
        """检查是否撞墙（穿墙模式下忽略）或撞到自己"""
        head = self.body[0]
        if not wrap:
            head_x, head_y = head
            if head_x < 0 or head_x >= SCREEN_WIDTH or head_y < 0 or head_y >= SCREEN_HEIGHT:
                return True

        # 撞到自己检测（尾尖下一步会让位，允许跟着走）
        if head in self.body[1:]:
            return True

        return False

class Food:
    def __init__(self, occupied=(), position=None):
        if position is not None:
            # 直接指定位置（用于小蛇原地变成苹果）
            self.position = position
        else:
            self.position = (0, 0)
            self.randomize_position(list(occupied))

    def randomize_position(self, snake_body):
        """在网格上随机生成食物，且避开蛇的身体"""
        while True:
            x = random.randint(0, (SCREEN_WIDTH - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE
            y = random.randint(0, (SCREEN_HEIGHT - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE
            if (x, y) not in snake_body:
                self.position = (x, y)
                break

    def draw(self, surface):
        """将食物绘制为卡通小苹果（红果子+高光+果柄+绿叶）"""
        S = RENDER_SCALE
        x, y = self.position
        cx = x + BLOCK_SIZE // 2
        cy = y + BLOCK_SIZE // 2
        radius = BLOCK_SIZE // 2 - 1

        # 苹果主体
        pygame.draw.circle(surface, FOOD_COLOR, (cx, cy), radius)
        # 高光
        pygame.draw.circle(surface, (255, 185, 195), (cx - 4 * S, cy - 4 * S), 3 * S)
        # 果柄
        pygame.draw.line(surface, (120, 80, 40),
                         (cx, cy - radius + 1), (cx + 2 * S, cy - radius - 5 * S), 2 * S)
        # 叶子
        pygame.draw.circle(surface, (80, 180, 90), (cx + 5 * S, cy - radius - 3 * S), 3 * S)


class NPCSnake:
    """场上随机游走的小蛇（紫/橙/粉色，外观与玩家的绿蛇明显不同）。

    规则：
    - 玩家的【头】碰到它的任何部位 -> 游戏失败
    - 玩家的【身体】碰到它的【头】 -> 它死亡，变成 2 个食物
    """
    def __init__(self, palette, occupied=(), avoid=None):
        self.palette = palette
        # 每隔几帧走一步，移动更慢、更好预判（玩家更容易用身体截住它）
        self.interval = random.randint(3, 4)
        self.tick = random.randint(0, self.interval - 1)
        length = random.randint(3, 5)
        # avoid: [(位置, 最小曼哈顿间距像素), ...]
        # 出生时与这些位置保持安全距离（玩家蛇头5格、其他小蛇3格），保证公平
        checks = avoid if avoid else []
        while True:
            gx = random.randint(1, SCREEN_WIDTH // BLOCK_SIZE - 2) * BLOCK_SIZE
            gy = random.randint(1, SCREEN_HEIGHT // BLOCK_SIZE - 2) * BLOCK_SIZE
            dx, dy = random.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
            body = [(gx - dx * BLOCK_SIZE * i, gy - dy * BLOCK_SIZE * i) for i in range(length)]
            ok = all(
                0 <= sx < SCREEN_WIDTH and 0 <= sy < SCREEN_HEIGHT
                and (sx, sy) not in occupied
                for sx, sy in body
            )
            if ok:
                for pos, gap in checks:
                    if not all(abs(sx - pos[0]) + abs(sy - pos[1]) >= gap for sx, sy in body):
                        ok = False
                        break
            if ok:
                self.body = body
                break
        self.direction = (dx * BLOCK_SIZE, dy * BLOCK_SIZE)
        # 出生保护：刚出生时原地冻结片刻，绝不偷袭，玩家也不会开局就撞上
        self.frozen_until = pygame.time.get_ticks() + 1200

    def update(self, occupied, wrap=False):
        """随机游走：倾向直行，遇到墙/障碍会转向，不会主动掉头"""
        # 出生冻结期内不动
        if pygame.time.get_ticks() < self.frozen_until:
            return
        self.tick += 1
        if self.tick % self.interval:
            return
        fx, fy = self.direction[0] // BLOCK_SIZE, self.direction[1] // BLOCK_SIZE
        head_x, head_y = self.body[0]

        options = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        options = [d for d in options if (d[0] * -1, d[1] * -1) != (fx, fy)]  # 不掉头

        def cell_ok(d):
            nx, ny = head_x + d[0] * BLOCK_SIZE, head_y + d[1] * BLOCK_SIZE
            if wrap:
                nx %= SCREEN_WIDTH
                ny %= SCREEN_HEIGHT
            elif not (0 <= nx < SCREEN_WIDTH and 0 <= ny < SCREEN_HEIGHT):
                return False
            return (nx, ny) not in occupied

        safe = [d for d in options if cell_ok(d)]
        if safe:
            if (fx, fy) in safe and random.random() < 0.85:
                d = (fx, fy)          # 大概率直行，路线好预判
            else:
                d = random.choice(safe)
        else:
            d = (fx, fy)              # 无路可走，直行听天由命

        self.direction = (d[0] * BLOCK_SIZE, d[1] * BLOCK_SIZE)
        nx, ny = head_x + d[0] * BLOCK_SIZE, head_y + d[1] * BLOCK_SIZE
        if wrap:
            nx %= SCREEN_WIDTH
            ny %= SCREEN_HEIGHT
        self.body.insert(0, (nx, ny))
        self.body.pop()               # 长度固定

    def draw(self, surface):
        """更精致可爱的小蛇：描边身体 + 亮亮大眼睛 + 腮红 + 小舌头"""
        S = RENDER_SCALE
        pal = self.palette

        # 让随机小蛇整体"退后一步"：颜色向背景柔化 + 体型更小，
        # 一眼就能和玩家的粗壮小蛇区分开，也不会喧宾夺主干扰视线
        def soften(c, t=0.22):
            return tuple(int(c[k] * (1 - t) + BG_COLOR[k] * t) for k in range(3))

        # 身体（更小 + 带描边）
        for i, (x, y) in enumerate(self.body[1:], start=1):
            color = soften(pal["body"][(i - 1) % len(pal["body"])])
            border = tuple(int(c * 0.78) for c in color)
            center = (x + BLOCK_SIZE // 2, y + BLOCK_SIZE // 2)
            r = BLOCK_SIZE // 2 - 2 * S
            pygame.draw.circle(surface, color, center, r)
            pygame.draw.circle(surface, border, center, r, 2 * S)
        # 头（同样更小 + 描边）
        x, y = self.body[0]
        rect = pygame.Rect(x, y, BLOCK_SIZE, BLOCK_SIZE)
        pygame.draw.rect(surface, soften(pal["head"]), rect, border_radius=10 * S)
        head_border = tuple(int(c * 0.78) for c in soften(pal["head"]))
        pygame.draw.rect(surface, head_border, rect, 2 * S, border_radius=10 * S)

        cx = x + BLOCK_SIZE // 2
        cy = y + BLOCK_SIZE // 2
        fx, fy = self.direction[0] // BLOCK_SIZE, self.direction[1] // BLOCK_SIZE
        px, py = -fy, fx
        # 腮红
        for s in (-1, 1):
            bx = int(cx - fx * 2 * S + px * 8 * S * s)
            by = int(cy - fy * 2 * S + py * 8 * S * s)
            pygame.draw.circle(surface, BLUSH_COLOR, (bx, by), 3 * S)
        # 大眼睛（白底 + 黑瞳 + 双高光，会眨眼），随方向转
        now = pygame.time.get_ticks()
        blinking = now % 2900 < 150
        for s in (-1, 1):
            ex = int(cx + fx * 3 * S + px * 5 * S * s)
            ey = int(cy + fy * 3 * S + py * 5 * S * s)
            if blinking:
                pygame.draw.line(surface, EYE_COLOR,
                                 (ex - 4 * S, ey), (ex + 4 * S, ey), 2 * S)
            else:
                pygame.draw.circle(surface, (255, 255, 255), (ex, ey), 5 * S)
                pygame.draw.circle(surface, EYE_COLOR, (ex + fx * 2 * S, ey + fy * 2 * S), 3 * S)
                pygame.draw.circle(surface, (255, 255, 255), (ex + fx * 3 * S, ey + fy * 3 * S), 1 * S)
        # 小舌头（时不时吐一下）
        if now % 1700 < 800:
            pygame.draw.line(surface, TONGUE_COLOR,
                             (int(cx + fx * 10 * S), int(cy + fy * 10 * S)),
                             (int(cx + fx * 16 * S), int(cy + fy * 16 * S)), 2 * S)

def create_npc_snakes(snake, foods, existing, count, npc_pool):
    """生成 count 条随机小蛇，保证开局公平：
    - 不与玩家、食物、其他小蛇重叠
    - 距离玩家蛇头至少 5 格
    - 距离其他小蛇的蛇头至少 3 格（小蛇之间不会挤在一起、不会相互碰头）
    """
    created = []
    occ = set(snake.body) | {f.position for f in foods}
    for other in existing:
        occ |= set(other.body)
    for _ in range(count):
        avoid = [(snake.body[0], 5 * BLOCK_SIZE)]
        for other in existing + created:
            avoid.append((other.body[0], 3 * BLOCK_SIZE))
        npc = NPCSnake(random.choice(npc_pool), occ, avoid=avoid)
        created.append(npc)
        occ |= set(npc.body)
    return created


def start_new_round(player_skin, npc_pool):
    """开始新一局：创建玩家蛇、食物和随机小蛇"""
    snake = Snake(player_skin)
    foods = [Food(snake.body)]
    npcs = create_npc_snakes(snake, foods, [], NPC_COUNT, npc_pool)
    return snake, foods, npcs


def main():
    game_state = "START" # 可选状态: START, PLAYING, GAME_OVER, WIN

    skin_index = 0                 # 开局选择的皮肤编号
    mode_index = 0                 # 0 经典边界 / 1 无边界穿墙
    speed_index = 1                # 0 悠闲 / 1 标准 / 2 闪电
    player_skin = SKINS[skin_index]
    npc_pool = [s for s in SKINS if s is not player_skin]  # 小蛇只能用其余皮肤

    snake, foods, npc_snakes = start_new_round(player_skin, npc_pool)
    score = 0
    # 结算统计：吃掉的苹果数 & 击倒的小蛇数
    stats = {"apples": 0, "kills": 0}

    # ---- 基于时间的移动节拍（比"按帧移动"顺滑得多）----
    move_timer = 0.0               # 累计时间（毫秒）
    MOVE_MS_BASE = 1000 / INITIAL_SPEED   # 初始每步所需毫秒

    # ---- 主界面布局 ----
    # 坐标一律用【画布坐标】(W=1920, H=1440)，窗口坐标 = 数值 / 2。
    # 自上而下按「标题 → 皮肤预览 → 三组选项 → 开始 → 规则」分区，
    # 每块精确分配 y 并预留充足留白，保证错落有致、互不重叠、不越界。
    S = RENDER_SCALE
    cx = SCREEN_WIDTH // 2

    Y_TITLE = 22 * S         # 大标题        窗口  11 ~  63
    Y_SUB = 118 * S          # 副标语        窗口  59 ~  79
    Y_PREVIEW = 172 * S      # 皮肤预览中心  窗口  76 ~  96
    Y_SKIN_LABEL = 216 * S   # 颜色标题      窗口 108 ~ 130
    Y_SKIN_BTN = 250 * S     # 皮肤按钮      窗口 125 ~ 159
    Y_MODE_LABEL = 310 * S   # 模式标题      窗口 155 ~ 177
    Y_MODE_BTN = 344 * S     # 模式按钮      窗口 172 ~ 206
    Y_SPEED_LABEL = 404 * S  # 速度标题      窗口 202 ~ 224
    Y_SPEED_BTN = 438 * S    # 速度按钮      窗口 219 ~ 253
    Y_START_BTN = 506 * S    # 开始按钮      窗口 253 ~ 294
    Y_RULES = 592 * S        # 规则文字起始  窗口 296 起

    BH = 34 * S              # 通用按钮高度
    RULE_LH = 32 * S         # 规则行距
    skin_btns, mode_btns, speed_btns = [], [], []

    # 6 个皮肤按钮横向排布（总宽 6*140+5*10 = 890*S，居中）
    bw = 140 * S
    gap = 10 * S
    total_w = len(SKINS) * bw + (len(SKINS) - 1) * gap
    sx0 = cx - total_w // 2
    for i, sk in enumerate(SKINS):
        skin_btns.append(Button((sx0 + i * (bw + gap), Y_SKIN_BTN, bw, BH), f"{sk['name']}", i))

    # 模式按钮（2 个，横向）
    mw = 280 * S
    mgap = 16 * S
    total_m = len(MODE_NAMES) * mw + (len(MODE_NAMES) - 1) * mgap
    mx0 = cx - total_m // 2
    for i, n in enumerate(MODE_NAMES):
        mode_btns.append(Button((mx0 + i * (mw + mgap), Y_MODE_BTN, mw, BH), n, i))

    # 速度按钮（3 个，横向）
    sw = 200 * S
    sgap = 14 * S
    total_s = len(SPEED_NAMES) * sw + (len(SPEED_NAMES) - 1) * sgap
    sx1 = cx - total_s // 2
    for i, n in enumerate(SPEED_NAMES):
        speed_btns.append(Button((sx1 + i * (sw + sgap), Y_SPEED_BTN, sw, BH), n, i))

    start_btn = Button((cx - 170 * S, Y_START_BTN, 340 * S, 42 * S), "按回车 出发!", -1)

    # 全部按钮放进一个列表，统一做鼠标悬停高亮
    all_btns = skin_btns + mode_btns + speed_btns + [start_btn]

    running = True
    while running:
        # 本帧用时（毫秒），用于时间节拍；上限 100ms，防止窗口卡顿后一次性追帧
        dt = min(clock.tick(FPS), 100)

        # 鼠标位置换算成画布坐标
        mouse_win = pygame.mouse.get_pos()
        mouse = (mouse_win[0] * MOUSE_SCALE, mouse_win[1] * MOUSE_SCALE)

        # 鼠标悬停高亮（只影响主界面观感，不影响逻辑）
        hovering_start = game_state == "START"
        for b in all_btns:
            b.hover = hovering_start and b.hit(mouse)

        # 空格加速：仅游戏进行中按住空格生效
        boost = game_state == "PLAYING" and bool(pygame.key.get_pressed()[pygame.K_SPACE])
        wrap = MODE_NAMES[mode_index] == MODE_NAMES[1]

        # ========================================
        # 1. 事件处理
        # ========================================
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game_state == "START":
                    for b in skin_btns:
                        if b.hit(mouse):
                            skin_index = b.value
                    for b in mode_btns:
                        if b.hit(mouse):
                            mode_index = b.value
                    for b in speed_btns:
                        if b.hit(mouse):
                            speed_index = b.value
                    if start_btn.hit(mouse):
                        player_skin = SKINS[skin_index]
                        npc_pool = [s for s in SKINS if s is not player_skin]
                        snake, foods, npc_snakes = start_new_round(player_skin, npc_pool)
                        score = 0
                        stats = {"apples": 0, "kills": 0}
                        move_timer = 0.0
                        MOVE_MS_BASE = 1000 / INITIAL_SPEED
                        game_state = "PLAYING"

            if event.type == pygame.KEYDOWN:
                if game_state == "START":
                    # 数字键 1-6 选择皮肤
                    if pygame.K_1 <= event.key <= pygame.K_6:
                        skin_index = event.key - pygame.K_1
                    elif event.key == pygame.K_LEFT:
                        skin_index = (skin_index - 1) % len(SKINS)
                    elif event.key == pygame.K_RIGHT:
                        skin_index = (skin_index + 1) % len(SKINS)
                    elif event.key == pygame.K_UP:
                        mode_index = (mode_index - 1) % len(MODE_NAMES)
                    elif event.key == pygame.K_DOWN:
                        mode_index = (mode_index + 1) % len(MODE_NAMES)
                    elif event.key in (pygame.K_COMMA, pygame.K_MINUS):
                        speed_index = (speed_index - 1) % len(SPEED_NAMES)
                    elif event.key in (pygame.K_PERIOD, pygame.K_EQUALS):
                        speed_index = (speed_index + 1) % len(SPEED_NAMES)
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        player_skin = SKINS[skin_index]
                        npc_pool = [s for s in SKINS if s is not player_skin]
                        snake, foods, npc_snakes = start_new_round(player_skin, npc_pool)
                        score = 0
                        stats = {"apples": 0, "kills": 0}
                        move_timer = 0.0
                        MOVE_MS_BASE = 1000 / INITIAL_SPEED
                        game_state = "PLAYING"

                elif game_state in ("GAME_OVER", "WIN"):
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        # 回车：保持当前设置，直接在本界面重新开始
                        snake, foods, npc_snakes = start_new_round(player_skin, npc_pool)
                        score = 0
                        stats = {"apples": 0, "kills": 0}
                        move_timer = 0.0
                        MOVE_MS_BASE = 1000 / INITIAL_SPEED
                        game_state = "PLAYING"
                    elif event.key == pygame.K_ESCAPE:
                        # ESC：退回主界面，可重新选择模式/速度/皮肤
                        game_state = "START"

                elif game_state == "PLAYING":
                    # 方向键入队，连续快速按键不会丢失，操作更跟手
                    if event.key == pygame.K_UP:
                        snake.turn((0, -BLOCK_SIZE))
                    elif event.key == pygame.K_DOWN:
                        snake.turn((0, BLOCK_SIZE))
                    elif event.key == pygame.K_LEFT:
                        snake.turn((-BLOCK_SIZE, 0))
                    elif event.key == pygame.K_RIGHT:
                        snake.turn((BLOCK_SIZE, 0))
                    elif event.key == pygame.K_ESCAPE:
                        # 游戏中按 ESC 也可直接回主界面
                        game_state = "START"

        # ========================================
        # 2. 游戏逻辑更新（按时间节拍推进，帧率恒定 60 更顺滑）
        # ========================================
        if game_state == "PLAYING":
            speed_mult = SPEED_MULT[speed_index]
            step_ms = MOVE_MS_BASE / speed_mult
            if boost:
                step_ms /= BOOST_FACTOR
            move_timer += dt
            # 安全钳制：拖动窗口/切出后 dt 可能很大，最多只补一步，
            # 避免蛇"瞬移"一大截造成操作失控与卡顿感
            if move_timer > step_ms * 2:
                move_timer = step_ms
            if move_timer < step_ms:
                pass
            else:
                move_timer -= step_ms

                snake.update(wrap=wrap)

                # 检测是否吃到食物
                eaten = False
                for f in foods[:]:
                    if snake.body[0] == f.position:
                        foods.remove(f)
                        score += 10
                        stats["apples"] += 1
                        eaten = True
                if eaten:
                    play(SFX_EAT)          # 音效1：吃到苹果
                    if len(foods) == 0:
                        foods.append(Food(set(snake.body) | {f.position for f in foods}))
                    if score % 50 == 0:
                        MOVE_MS_BASE = max(45, MOVE_MS_BASE - (1000 / INITIAL_SPEED) * 0.12)
                else:
                    snake.body.pop()

                if snake.check_collision(wrap=wrap):
                    play(SFX_DIE)          # 音效3：失败/撞墙
                    game_state = "GAME_OVER"
                elif score >= WIN_SCORE:
                    play(SFX_WIN)          # 通关欢快音
                    game_state = "WIN"
                else:
                    # ---- 随机小蛇移动 ----
                    player_head_cell = snake.body[0]
                    for npc in npc_snakes:
                        occupied = {f.position for f in foods} | {player_head_cell}
                        for other in npc_snakes:
                            if other is not npc:
                                occupied |= set(other.body)
                        npc.update(occupied, wrap=wrap)

                    # ---- 小蛇碰撞判定 ----
                    player_head = snake.body[0]
                    player_body = set(snake.body[1:])
                    dead_npcs = []
                    for npc in npc_snakes:
                        if player_head in npc.body:
                            game_state = "GAME_OVER"
                            break
                        if npc.body[0] in player_body:
                            dead_npcs.append(npc)
                    for npc in dead_npcs:
                        dead_head = npc.body[0]
                        npc_snakes.remove(npc)
                        stats["kills"] += 1
                        play(SFX_KILL)     # 音效2：击杀随机小蛇
                        occ = set(snake.body) | {f.position for f in foods}
                        for other in npc_snakes:
                            occ |= set(other.body)
                        hx, hy = dead_head
                        near = [(hx + dx * BLOCK_SIZE, hy + dy * BLOCK_SIZE)
                                for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1))]
                        spots = []
                        for cell in near:
                            if len(spots) >= 2:
                                break
                            if (0 <= cell[0] < SCREEN_WIDTH and 0 <= cell[1] < SCREEN_HEIGHT
                                    and cell not in occ and cell not in spots):
                                spots.append(cell)
                        while len(spots) < 2:
                            tmp = Food(occ)
                            spots.append(tmp.position)
                        for sp in spots:
                            foods.append(Food(occ, position=sp))
                            occ.add(sp)
                        npc_snakes += create_npc_snakes(snake, foods, npc_snakes, 1, npc_pool)

        # ========================================
        # 3. 画面渲染（背景为缓存贴图，只绘制动态元素，帧率更稳定顺滑）
        # ========================================
        screen.blit(BG_SURFACE, (0, 0))

        if game_state == "START":
            # 半透明白色面板，让主界面选项更清晰
            screen.blit(MENU_OVERLAY, (0, 0))

            # ---- 大标题（居中）+ 两侧小装饰，活泼不呆板 ----
            title = "萌萌蛇大冒险"
            tw = text_size_cached(title, font_title)[0]
            tx = cx - tw // 2
            # 标题投影：先画一层浅色偏移，再叠主体（错位而非描边，无重影）
            blit_text_cached(screen, title, font_title, (255, 255, 255), tx + 4 * S, Y_TITLE + 4 * S)
            blit_text_cached(screen, title, font_title, HEAD_COLOR, tx, Y_TITLE)
            # 标题左右各画一条渐隐短线，视觉上稳住中线
            ly = Y_TITLE + font_title.get_height() // 2
            for side in (-1, 1):
                x1 = cx + side * (tw // 2 + 18 * S)
                x2 = cx + side * (tw // 2 + 66 * S)
                pygame.draw.line(screen, HEAD_COLOR, (x1, ly), (x2, ly), 4 * S)
                pygame.draw.circle(screen, (255, 200, 90), (x2 + side * 8 * S, ly), 5 * S)

            # 副标语：说明玩法定位，一句话点题
            draw_centered("躲小蛇 · 吃苹果 · 冲满分", font_sub, (110, 170, 120), cx, Y_SUB)

            # ---- 皮肤预览（当前所选，朝右）----
            skin = SKINS[skin_index]
            r = BLOCK_SIZE // 2 - 1
            for i in range(3):
                bx = cx - (i + 1) * BLOCK_SIZE
                pygame.draw.circle(screen, skin["body"][i % len(skin["body"])], (bx, Y_PREVIEW), r)
            head_rect = pygame.Rect(cx, Y_PREVIEW - BLOCK_SIZE // 2, BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.rect(screen, skin["head"], head_rect, border_radius=10 * S)
            hxx = cx + BLOCK_SIZE // 2
            for sgn in (-1, 1):
                ex, ey = hxx + 2 * S, Y_PREVIEW + 6 * S * sgn
                pygame.draw.circle(screen, (255, 255, 255), (ex, ey), 5 * S)
                pygame.draw.circle(screen, EYE_COLOR, (ex + 2 * S, ey), 3 * S)
                pygame.draw.circle(screen, BLUSH_COLOR, (hxx - 6 * S, Y_PREVIEW + 9 * S * sgn), 3 * S)
            pygame.draw.line(screen, TONGUE_COLOR, (hxx + BLOCK_SIZE // 2, Y_PREVIEW),
                             (hxx + BLOCK_SIZE // 2 + 8 * S, Y_PREVIEW), 2 * S)

            # ---- 三个分区：左边一条主题色竖线 + 标题，形成整齐的视觉节奏 ----
            def draw_section(label, extra, y_label):
                """分区标题：左侧色条 + 主标题，右侧跟一个次要说明。"""
                lw = text_size_cached(label, font_section)[0]
                ew = text_size_cached(extra, font_rule)[0] if extra else 0
                total = lw + (12 * S + ew if extra else 0)
                x0 = cx - total // 2
                # 左侧主题色竖条
                pygame.draw.rect(screen, HEAD_COLOR,
                                 (x0 - 18 * S, y_label + 4 * S, 6 * S, 26 * S),
                                 border_radius=3 * S)
                blit_text_cached(screen, label, font_section, TEXT_COLOR, x0, y_label)
                if extra:
                    # 次要说明用浅色，形成主次对比
                    ey2 = y_label + (font_section.get_height() - font_rule.get_height()) - 2 * S
                    blit_text_cached(screen, extra, font_rule, (128, 178, 136), x0 + lw + 12 * S, ey2)

            draw_section("小蛇颜色", f"当前：{skin['name']}", Y_SKIN_LABEL)
            for i, b in enumerate(skin_btns):
                b.draw(screen, i == skin_index, font_btn)

            draw_section("游戏模式", "决定撞墙还是穿墙", Y_MODE_LABEL)
            for i, b in enumerate(mode_btns):
                b.draw(screen, i == mode_index, font_btn)

            draw_section("游戏速度", "随时可回主界面重选", Y_SPEED_LABEL)
            for i, b in enumerate(speed_btns):
                b.draw(screen, i == speed_index, font_btn)

            start_btn.draw(screen, False, font_btn)

            # ---- 规则说明（分条列出，行距充裕，绝不堆叠）----
            rules = [
                "方向键 操控小蛇   ·   按住 空格 加速",
                "吃苹果 +10 分，满 100 分通关；蛇头碰到小蛇会失败",
                "小秘诀：用身体顶住小蛇的头，它会在原地变成 2 个苹果!",
            ]
            ry = Y_RULES
            for line in rules:
                w = text_size_cached(line, font_rule)[0]
                # 每条规则前加一个小圆点，读起来更清爽
                pygame.draw.circle(screen, (150, 205, 160), (cx - w // 2 - 14 * S, ry + 14 * S), 4 * S)
                draw_centered(line, font_rule, TEXT_COLOR, cx, ry)
                ry += RULE_LH

        elif game_state in ("PLAYING", "GAME_OVER", "WIN"):
            # 绘制食物、随机小蛇和玩家的蛇
            for f in foods:
                f.draw(screen)
            for npc in npc_snakes:
                npc.draw(screen)
            snake.draw(screen)

            # 左上角：实时分数 + 当前模式与速度
            score_text = f"得分: {score}"
            img = blit_text_cached(screen, score_text, font_medium, TEXT_COLOR, 20, 20)
            info_text = f"{MODE_NAMES[mode_index]} · {SPEED_NAMES[speed_index]}"
            blit_text_cached(screen, info_text, font_tiny, TEXT_COLOR, 22, 24 + img.get_height())

            # 加速提示（右上角）
            if boost:
                bimg = blit_text_cached(screen, "冲鸭~ 加速中!", font_small, BOOST_COLOR, 0, 0)
                blit_text_cached(screen, "冲鸭~ 加速中!", font_small, BOOST_COLOR,
                                 SCREEN_WIDTH - 20 - bimg.get_width(), 20)

            if game_state == "GAME_OVER" or game_state == "WIN":
                # 半透明黑色遮罩
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                overlay.set_alpha(150)
                overlay.fill((0, 0, 0))
                screen.blit(overlay, (0, 0))

                if game_state == "WIN":
                    over_text = "太棒啦! 满分通关!"
                    over_color = HEAD_COLOR
                else:
                    over_text = "呜呜, 被逮住了..."
                    over_color = FOOD_COLOR
                stat1_text = f"吃掉小苹果: {stats['apples']} 个"
                stat2_text = f"击倒小蛇: {stats['kills']} 条"
                restart_text = "按 [回车] 再来一次!"
                quit_text = "按 [ESC] 返回主界面"

                # 结算界面：大字号 + 无阴影(无重影)，成功失败都有成就感
                total_text = f"总分 {score} 分!"
                total_color = (255, 215, 0) if game_state == "WIN" else (255, 255, 255)

                draw_centered(over_text, font_large, over_color, cx, int(SCREEN_HEIGHT * 0.22))
                draw_centered(total_text, font_large, total_color, cx, int(SCREEN_HEIGHT * 0.40))
                draw_centered(stat1_text, font_large, (255, 255, 255), cx, int(SCREEN_HEIGHT * 0.56))
                draw_centered(stat2_text, font_large, (255, 255, 255), cx,
                              int(SCREEN_HEIGHT * 0.56) + 140)
                draw_centered(restart_text, font_medium, (255, 255, 255), cx,
                              int(SCREEN_HEIGHT * 0.82))
                draw_centered(quit_text, font_medium, (255, 255, 255), cx,
                              int(SCREEN_HEIGHT * 0.82) + 90)

        # 高清输出：把高分辨率画布平滑缩放到小窗口
        scaled = pygame.transform.smoothscale(screen, (WIN_WIDTH, WIN_HEIGHT))
        display.blit(scaled, (0, 0))
        pygame.display.flip()

    # 退出游戏循环后的清理工作
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
