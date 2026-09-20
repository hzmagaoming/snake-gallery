from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
SAVE_PATH = DATA_DIR / "save.json"

WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 720
BOARD_SIZE = 600
GRID_SIZE = 18
CELL_SIZE = BOARD_SIZE // GRID_SIZE
BOARD_X = 35
BOARD_Y = 85
HUD_X = 680

FPS = 60
INITIAL_MOVE_INTERVAL_MS = 210
MIN_MOVE_INTERVAL_MS = 100
SKILL_COOLDOWN_SECONDS = 10
SKILL_DURATION_SECONDS = 3
EVENT_DURATIONS_SECONDS = {
    "earthquake": 3.0,
    "communication": 4.0,
    "rain": 5.0,
}
EARTHQUAKE_SHAKE_PIXELS = 5
RAIN_WATER_CELL_COUNT = 4
RADIO_DURATION_SECONDS = 2.0
RADIO_COOLDOWN_RANGE_SECONDS = (15, 30)
RADIO_EASTER_EGG_CHANCE = 0.06
RADIO_EASTER_EGG_MESSAGES = [
    "求是鹰：已空投热茶和备用路线图。",
    "后勤组：你们的路线像教科书一样稳。",
    "指挥中心：保持呼吸，下一段路会更顺。",
]

INITIAL_TEAM = [(9, 10), (8, 10), (7, 10)]
INITIAL_DIRECTION = (1, 0)
MAX_ROUTE_POINTS = 100

INITIAL_RESOURCES = 7
INITIAL_SURVIVORS = 3
SAFE_ZONE_COUNT = 3
SAFE_ZONE_RELOCATION_WARNING_SECONDS = 5.0
SAFE_ZONE_RELOCATION_RESCUES = 2
SAFE_ZONE_RELOCATION_MIN_DISTANCE = 4
SAFE_ZONE_RELOCATION_MAX_DISTANCE = 10
START_PROTECTION_SECONDS = 10
START_PROTECTION_RADIUS = 4

TUTORIAL_FIRST_WINDOW_SECONDS = 20
TUTORIAL_TOTAL_SECONDS = 60
TUTORIAL_SURVIVOR_POS = (11, 10)
TUTORIAL_SAFE_ZONE_POS = (14, 10)
TUTORIAL_EXTRA_SAFE_ZONES = [(14, 7), (12, 13)]
TUTORIAL_OBSTACLES = [(5, 5), (6, 13)]
TUTORIAL_RESOURCES = [(10, 7), (12, 12)]
TUTORIAL_RESCUE_SCORE = 5

DIFFICULTY_STAGES = [
    {
        "name": "熟悉现场",
        "start": 0,
        "move_interval": 260,
        "max_obstacles": 2,
        "event_interval": None,
        "event_kinds": [],
        "event_obstacles": 0,
        "water_cells": 0,
        "survivor_min_distance": 2,
        "survivor_max_distance": 6,
        "rescue_score": 5,
    },
    {
        "name": "展开救援",
        "start": 60,
        "move_interval": 220,
        "max_obstacles": 5,
        "event_interval": (22, 30),
        "event_kinds": ["earthquake"],
        "event_obstacles": 1,
        "water_cells": 2,
        "survivor_min_distance": 3,
        "survivor_max_distance": 8,
        "rescue_score": 8,
    },
    {
        "name": "风险升级",
        "start": 120,
        "move_interval": 195,
        "max_obstacles": 8,
        "event_interval": (10, 16),
        "event_kinds": ["earthquake", "communication", "rain"],
        "event_obstacles": 2,
        "water_cells": 3,
        "survivor_min_distance": 5,
        "survivor_max_distance": 12,
        "rescue_score": 12,
    },
    {
        "name": "高压响应",
        "start": 210,
        "move_interval": 175,
        "max_obstacles": 12,
        "event_interval": (7, 12),
        "event_kinds": ["earthquake", "communication", "rain"],
        "event_obstacles": 3,
        "water_cells": 5,
        "survivor_min_distance": 7,
        "survivor_max_distance": 30,
        "rescue_score": 18,
    },
]

BATTERY_MIN_RISK_LEVEL = 3
BATTERY_SPAWN_CHANCE = 0.2
MEDICAL_SPAWN_CHANCE = 0.15
EAGLE_SPAWN_CHANCE = 0.03
EAGLE_SUPPORT_SECONDS = 4.0
RESOURCE_SCORE = 1
EAGLE_RESOURCE_VALUE = 2
RESOURCE_DELIVERY_SCORE = 2
RESCUE_STREAK_SIZE = 3
RESCUE_STREAK_BONUS = 2
LOAD_SPEED_PENALTY_MS = 7

# Cover-derived art rules: quiet grey-green/khaki paper, vermilion vehicles,
# blue-grey glazing, soft pencil edges and upper-left light with southeast shadows.
VISUAL = {
    "colors": {
        "paper": (238, 236, 219),
        "paper_warm": (244, 239, 220),
        "paper_green": (225, 228, 211),
        "paper_blue": (224, 228, 222),
        "paper_shadow": (139, 143, 123),
        "ink": (66, 70, 56),
        "pencil": (122, 124, 107),
        "grid": (205, 218, 202),
        "river": (186, 205, 208),
        "river_dark": (94, 124, 128),
        "hill": (154, 191, 143),
        "tree": (91, 151, 106),
        "grass": (127, 178, 116),
        "road": (220, 196, 142),
        "vehicle": (222, 104, 73),
        "vehicle_dark": (169, 72, 62),
        "vehicle_aux": (191, 158, 97),
        "window": (106, 165, 173),
        "wheel": (65, 68, 58),
        "survivor_body": (189, 109, 77),
        "survivor_skin": (247, 203, 172),
        "tent": (146, 164, 123),
        "tent_dark": (75, 112, 81),
        "supply_box": (217, 156, 78),
        "supply_tape": (143, 103, 67),
        "medical": (253, 250, 238),
        "rubble": (172, 137, 113),
        "rubble_dark": (108, 91, 80),
        "water": (125, 157, 164),
        "water_edge": (73, 108, 120),
        "eagle": (204, 177, 109),
        "eagle_dark": (120, 94, 48),
        "danger": (204, 82, 62),
    },
    "line": {
        "thin": 1,
        "normal": 1,
        "bold": 2,
    },
    "radius": {
        "card": 7,
        "button": 7,
        "cell": 7,
    },
    "shadow": {
        "offset": (2, 3),
        "alpha": 28,
    },
    "font": {
        "title": 40,
        "body": 24,
        "small": 16,
        "mini": 13,
    },
    "sprite_size": {
        "rescue": 43, "body": 35, "person": 44,
        "tent": 48, "resource": 38, "rubble": 39,
    },
}

FONT_CANDIDATES = [
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/ArialHB.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
]

SCENARIOS = [
    {
        "title": "山区暴雨",
        "background_theme": "rain",
        "short": "山区暴雨",
        "intro": "持续降雨导致部分道路中断，救援队正在转移受困群众。",
        "event_bias": "rain",
        "sky": (231, 238, 230),
        "map": (244, 240, 231),
    },
    {
        "title": "地震余震",
        "background_theme": "earthquake",
        "short": "地震余震",
        "intro": "部分建筑受损，请优先搜救并送往临时安置点。",
        "event_bias": "earthquake",
        "sky": (238, 233, 225),
        "map": (246, 240, 236),
    },
    {
        "title": "城区内涝",
        "background_theme": "flood",
        "short": "城区内涝",
        "intro": "积水正在扩大，请及时完成物资运输与人员转移。",
        "event_bias": "rain",
        "sky": (226, 237, 242),
        "map": (243, 240, 235),
    },
]

SCENARIO_BACKGROUNDS = {
    "rain": ("river_valley", "wet_hillside", "mountain_bend"),
    "earthquake": ("damaged_district", "relief_corridor", "dusty_crossroads"),
    "flood": ("canal_street", "flooded_square", "riverside_blocks"),
}

GAME_OVER_MESSAGES = [
    "路线规划很稳，记得永远为自己留一条撤离路线。",
    "这次行动很有分寸，下一次要更快完成转移。",
    "救援现场很拼，接下来继续保护队列与撤离路线。",
    "危机不止一次，记住安全线与资源线的关系。",
]

RADIO_MESSAGES = [
    "指挥中心：前方发现受困群众。",
    "收到，安置点已经开放。",
    "注意，余震风险正在升高。",
    "做得好，人已经安全送达。",
    "指挥中心：道路通行情况已复核。",
]
