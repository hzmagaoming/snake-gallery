from __future__ import annotations

import math
import random
from typing import Optional

import pygame

from config import (
    BOARD_SIZE,
    BOARD_X,
    BOARD_Y,
    BATTERY_MIN_RISK_LEVEL,
    BATTERY_SPAWN_CHANCE,
    CELL_SIZE,
    DIFFICULTY_STAGES,
    EARTHQUAKE_SHAKE_PIXELS,
    EAGLE_RESOURCE_VALUE,
    EAGLE_SUPPORT_SECONDS,
    EAGLE_SPAWN_CHANCE,
    EVENT_DURATIONS_SECONDS,
    FPS,
    GAME_OVER_MESSAGES,
    GRID_SIZE,
    HUD_X,
    INITIAL_DIRECTION,
    INITIAL_MOVE_INTERVAL_MS,
    INITIAL_RESOURCES,
    INITIAL_SURVIVORS,
    INITIAL_TEAM,
    LOAD_SPEED_PENALTY_MS,
    MAX_ROUTE_POINTS,
    MEDICAL_SPAWN_CHANCE,
    MIN_MOVE_INTERVAL_MS,
    RAIN_WATER_CELL_COUNT,
    RADIO_COOLDOWN_RANGE_SECONDS,
    RADIO_EASTER_EGG_CHANCE,
    RADIO_EASTER_EGG_MESSAGES,
    RADIO_DURATION_SECONDS,
    RADIO_MESSAGES,
    RESOURCE_DELIVERY_SCORE,
    RESOURCE_SCORE,
    RESCUE_STREAK_BONUS,
    RESCUE_STREAK_SIZE,
    SAFE_ZONE_COUNT,
    SAFE_ZONE_RELOCATION_MAX_DISTANCE,
    SAFE_ZONE_RELOCATION_MIN_DISTANCE,
    SAFE_ZONE_RELOCATION_RESCUES,
    SAFE_ZONE_RELOCATION_WARNING_SECONDS,
    SCENARIOS,
    SKILL_COOLDOWN_SECONDS,
    SKILL_DURATION_SECONDS,
    START_PROTECTION_RADIUS,
    START_PROTECTION_SECONDS,
    TUTORIAL_EXTRA_SAFE_ZONES,
    TUTORIAL_FIRST_WINDOW_SECONDS,
    TUTORIAL_OBSTACLES,
    TUTORIAL_RESCUE_SCORE,
    TUTORIAL_RESOURCES,
    TUTORIAL_SAFE_ZONE_POS,
    TUTORIAL_SURVIVOR_POS,
    TUTORIAL_TOTAL_SECONDS,
    VISUAL,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from entities import DisasterEvent, GameState, Resource, SafeZone, Survivor
from storage import load_save, save_record as write_save
from ui import load_font
from map_art import MapArt
from entry_art import EntryArt


class Game:
    """EMERGENCY RUN 的主控制器。"""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.map_art = MapArt()
        self.entry_art = EntryArt(self.map_art)
        self.paper_background = pygame.transform.smoothscale(self.map_art.paper_texture, screen.get_size())
        self.paper_cards = {}
        self.text_cache = {}
        self.safe_zone_glow = pygame.Surface((74, 74), pygame.SRCALPHA)
        self.shake_frame = pygame.Surface(screen.get_size()).convert()
        self.communication_overlay = pygame.Surface((295, 420), pygame.SRCALPHA)
        self.communication_overlay.fill((70, 63, 52, 145))

        # 字体：改为真实文件路径字体+纯系统字体兜底，避免中文显示成小方框
        font_sizes = VISUAL["font"]
        self.font_title = load_font(font_sizes["title"], bold=True)
        self.font_body = load_font(font_sizes["body"])
        self.font_small = load_font(font_sizes["small"])
        self.font_mini = load_font(font_sizes["mini"])

        self.scenario = random.choice(SCENARIOS)
        self.game_over_message = random.choice(GAME_OVER_MESSAGES)
        self.game_over_rank = "救援先锋"
        self.save_data = load_save()
        self.tutorial_completed = self.save_data["tutorial_completed"]
        self.force_tutorial = False
        self.tutorial_mode = False
        self.tutorial_picked_survivor = False
        self.tutorial_rescue_done = False
        self.tutorial_e_hint_shown = False
        self.tutorial_second_hint_shown = False
        self.stage_index = 0
        self.announced_stages: set[int] = set()
        self.obstacle_growth_timer = 0.0
        self.last_safe_zone_rescue_milestone = 0
        self.safe_zone_relocation_timer = 0.0
        self.safe_zone_relocation_pending = False
        self.eagle_support_timer = 0.0
        self.streak_bonus_timer = 0.0
        self.radio_message = ""
        self.radio_timer = 0
        self.radio_cooldown = random.randint(*RADIO_COOLDOWN_RANGE_SECONDS)
        self.radio_alive = False

        self.state = GameState.MENU
        self.running = True
        self.started_at_ms = pygame.time.get_ticks()

        self.score = 0
        self.rescued = 0
        self.resources_collected = 0
        self.update_risk()

        self.team: list[tuple[int, int]] = list(INITIAL_TEAM)
        self.direction = INITIAL_DIRECTION
        self.next_direction = INITIAL_DIRECTION
        self.route: list[tuple[int, int]] = [INITIAL_TEAM[0]]

        self.resources: list[Resource] = []
        self.survivors: list[Survivor] = []
        self.safe_zones: list[SafeZone] = []
        self.obstacles: list[tuple[int, int]] = []
        self.water: list[tuple[int, int]] = []
        self.event: Optional[DisasterEvent] = None
        self.inventory: list[str] = []

        self.onboard_survivors: list[Survivor] = []
        self.move_timer = 0
        self.move_interval = INITIAL_MOVE_INTERVAL_MS
        self.reset_vehicle_motion()
        self.reset_event_cooldown()
        self.skill_cooldown = 0
        self.skill_timer = 0
        self.message = "应急行动待命"
        self.message_timer = 0
        self.show_hud = True

        self.menu_buttons = {
            "start": pygame.Rect(760, 468, 250, 54),
            "tutorial": pygame.Rect(777, 535, 233, 54),
            "quit": pygame.Rect(794, 602, 216, 50),
        }
        self.gameover_buttons = {
            "again": pygame.Rect(360, 610, 160, 50),
            "menu": pygame.Rect(590, 610, 160, 50),
        }
        self.brief_button = pygame.Rect(650, 548, 170, 54)
        self.entry_back_button = pygame.Rect(260, 107, 110, 40)
        self.guide_buttons = {
            "back": pygame.Rect(140, 640, 190, 54),
            "learn": pygame.Rect(740, 640, 220, 54),
        }

    def reset_game(self, tutorial_mode: bool = False, scenario=None):
        """清理并重置新一局。"""
        self.tutorial_mode = tutorial_mode
        self.tutorial_picked_survivor = False
        self.tutorial_rescue_done = False
        self.tutorial_e_hint_shown = False
        self.tutorial_second_hint_shown = False
        self.stage_index = 0
        self.announced_stages = {0}
        self.obstacle_growth_timer = 0.0
        self.last_safe_zone_rescue_milestone = 0
        self.safe_zone_relocation_timer = 0.0
        self.safe_zone_relocation_pending = False
        self.eagle_support_timer = 0.0
        self.streak_bonus_timer = 0.0
        self.score = 0
        self.rescued = 0
        self.resources_collected = 0
        self.team = list(INITIAL_TEAM)
        self.direction = INITIAL_DIRECTION
        self.next_direction = INITIAL_DIRECTION
        self.route = [INITIAL_TEAM[0]]

        self.resources = []
        self.survivors = []
        self.safe_zones = []
        self.obstacles = []
        self.water = []
        self.event = None
        self.inventory = []

        self.scenario = scenario if scenario is not None else random.choice(SCENARIOS)
        self.map_art.select_background(self.scenario["background_theme"])
        self.background_variant = self.map_art.background_variant
        self.game_over_message = random.choice(GAME_OVER_MESSAGES)
        self.game_over_rank = "救援先锋"
        self.radio_message = ""
        self.radio_timer = 0
        self.radio_cooldown = random.randint(*RADIO_COOLDOWN_RANGE_SECONDS)
        self.radio_alive = False
        self.started_at_ms = pygame.time.get_ticks()

        self.onboard_survivors = []
        self.move_timer = 0
        self.move_interval = INITIAL_MOVE_INTERVAL_MS
        self.reset_vehicle_motion()
        self.reset_event_cooldown()
        self.skill_cooldown = 0
        self.skill_timer = 0
        self.message = "应急行动待命"
        self.message_timer = 0
        self.show_hud = True
        self.update_risk()

        if tutorial_mode:
            self.setup_tutorial_layout()
            self.message = "先前往这里，接触受困群众"
            self.message_timer = 8.0
        else:
            self.make_safe_zones()
            self.spawn_obstacles(self.current_stage()["max_obstacles"])
            self.spawn_resources(INITIAL_RESOURCES)
            self.spawn_survivors(INITIAL_SURVIVORS)
        self.state = GameState.PLAYING

    def start_from_menu(self, force_tutorial: bool = False):
        self.force_tutorial = force_tutorial
        self.scenario = random.choice(SCENARIOS)
        self.state = GameState.MISSION_BRIEF

    def setup_tutorial_layout(self):
        self.safe_zones = [
            SafeZone(*TUTORIAL_SAFE_ZONE_POS),
            *[SafeZone(*pos) for pos in TUTORIAL_EXTRA_SAFE_ZONES],
        ]
        self.survivors = [Survivor(*TUTORIAL_SURVIVOR_POS)]
        self.resources = [Resource("supply", x, y) for x, y in TUTORIAL_RESOURCES]
        self.obstacles = list(TUTORIAL_OBSTACLES)

    def make_safe_zones(self):
        """随机生成安全区，确保不落在障碍和救援队身体上。"""
        self.safe_zones = []
        attempts = 0
        stage = self.current_stage()
        while len(self.safe_zones) < SAFE_ZONE_COUNT and attempts < 200:
            attempts += 1
            if len(self.safe_zones) == 0 and stage["survivor_max_distance"] <= 8:
                x, y = self.random_near_head(4, 7)
            else:
                x = random.randint(2, GRID_SIZE - 3)
                y = random.randint(2, GRID_SIZE - 3)
            if (x, y) in self.team or (x, y) in self.obstacles:
                continue
            if any(sz.x == x and sz.y == y for sz in self.safe_zones):
                continue
            self.safe_zones.append(SafeZone(x, y))

    def spawn_obstacles(self, count: int):
        """随机生成障碍覆盖层，避免直接让玩家完全封死。"""
        for _ in range(count):
            free = self.free_cells_for_obstacles()
            if not free:
                break
            x, y = random.choice(free)
            self.obstacles.append((x, y))

    def free_cells_for_obstacles(self):
        """障碍可以生成的合法格子。"""
        outs = []
        for y in range(1, GRID_SIZE - 1):
            for x in range(1, GRID_SIZE - 1):
                if self.in_start_protection(x, y):
                    continue
                if (x, y) in self.obstacles:
                    continue
                if (x, y) in self.team:
                    continue
                if any(s.x == x and s.y == y for s in self.safe_zones):
                    continue
                if any(s.x == x and s.y == y for s in self.survivors):
                    continue
                if any(r.x == x and r.y == y for r in self.resources):
                    continue
                outs.append((x, y))
        return outs

    def spawn_resources(self, count: int):
        """生成应急资源：物资包、医疗包、通讯电池、求是鹰支援。"""
        for _ in range(count):
            free = []
            for y in range(1, GRID_SIZE - 1):
                for x in range(1, GRID_SIZE - 1):
                    if self.cell_blocked(x, y):
                        continue
                    free.append((x, y))
            if not free:
                break
            x, y = random.choice(free)
            if self.risk_level >= BATTERY_MIN_RISK_LEVEL and random.random() < BATTERY_SPAWN_CHANCE:
                rkind = "battery"
            elif random.random() < MEDICAL_SPAWN_CHANCE:
                rkind = "medical"
            elif random.random() < EAGLE_SPAWN_CHANCE:
                rkind = "eagle"
            else:
                rkind = "supply"
            self.resources.append(Resource(rkind, x, y))

    def spawn_survivors(self, count: int):
        """生成受困群众，随机位置不冲突。"""
        stage = self.current_stage()
        for _ in range(count):
            free = []
            for y in range(1, GRID_SIZE - 1):
                for x in range(1, GRID_SIZE - 1):
                    if self.cell_blocked(x, y):
                        continue
                    distance = self.distance_from_head(x, y)
                    if distance < stage["survivor_min_distance"]:
                        continue
                    if distance > stage["survivor_max_distance"]:
                        continue
                    free.append((x, y))
            if not free:
                free = self.free_spawn_cells()
            if not free:
                break
            x, y = random.choice(free)
            self.survivors.append(Survivor(x, y))

    def free_spawn_cells(self) -> list[tuple[int, int]]:
        free = []
        for y in range(1, GRID_SIZE - 1):
            for x in range(1, GRID_SIZE - 1):
                if not self.cell_blocked(x, y):
                    free.append((x, y))
        return free

    def random_near_head(self, min_distance: int, max_distance: int) -> tuple[int, int]:
        hx, hy = self.team[0]
        candidates = []
        for y in range(1, GRID_SIZE - 1):
            for x in range(1, GRID_SIZE - 1):
                distance = abs(x - hx) + abs(y - hy)
                if min_distance <= distance <= max_distance:
                    candidates.append((x, y))
        return random.choice(candidates) if candidates else (hx, hy)

    def distance_from_head(self, x: int, y: int) -> int:
        hx, hy = self.team[0]
        return abs(x - hx) + abs(y - hy)

    def in_start_protection(self, x: int, y: int) -> bool:
        return self.elapsed_seconds() < START_PROTECTION_SECONDS and self.distance_from_head(x, y) <= START_PROTECTION_RADIUS

    def cell_blocked(self, x: int, y: int) -> bool:
        """检查格子是否被队伍、障碍、安全区、资源、群众占用。"""
        if (x, y) in self.team:
            return True
        if (x, y) in self.obstacles:
            return True
        if any(sz.x == x and sz.y == y for sz in self.safe_zones):
            return True
        if any(r.x == x and r.y == y for r in self.resources):
            return True
        if any(s.x == x and s.y == y for s in self.survivors):
            return True
        return False

    def update(self, dt):
        """主更新循环，处理移动、事件计时、情景无线电、风险升级。"""
        if self.state != GameState.PLAYING:
            return
        self.update_stage()
        self.update_tutorial_hints()

        # 无线电消息：每隔 15-30 秒发生一次短消息，持续 2-3 秒
        if self.radio_timer > 0:
            self.radio_timer -= dt
            if self.radio_timer <= 0:
                self.radio_alive = False
                self.radio_message = ""
        else:
            self.radio_cooldown -= dt
            if self.radio_cooldown <= 0:
                self.trigger_radio_message()
                self.radio_cooldown = random.randint(*RADIO_COOLDOWN_RANGE_SECONDS)

        # 技能冷却/扫描计时
        if self.skill_cooldown > 0:
            self.skill_cooldown = max(0, self.skill_cooldown - dt)
        if self.skill_timer > 0:
            self.skill_timer -= dt
            if self.skill_timer <= 0:
                self.skill_timer = 0
        if self.eagle_support_timer > 0:
            self.eagle_support_timer = max(0, self.eagle_support_timer - dt)
        if self.streak_bonus_timer > 0:
            self.streak_bonus_timer = max(0, self.streak_bonus_timer - dt)

        # 消息动画计时
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message = "应急行动待命"

        # 风险计算与移动速度
        self.update_risk()
        stage = self.current_stage()
        self.move_interval = max(
            MIN_MOVE_INTERVAL_MS,
            stage["move_interval"]
            - (self.risk_level - 1) * 18
            - self.score // 5 * 4
            - self.pending_load_count() * LOAD_SPEED_PENALTY_MS,
        )
        self.grow_obstacles(dt)
        self.update_safe_zone_relocation(dt)

        self.visual_elapsed_ms += dt * 1000
        self.move_timer += dt * 1000
        while self.move_timer >= self.move_interval and self.state == GameState.PLAYING:
            self.move_timer -= self.move_interval
            if self.move_team():
                self.visual_elapsed_ms = self.move_timer

        # 事件间隔
        if self.events_allowed():
            self.event_cooldown -= dt
        if self.event_cooldown <= 0 and self.event is None and self.events_allowed():
            self.trigger_event()
            self.reset_event_cooldown()

        if self.event:
            self.event.timer -= dt
            if self.event.timer <= 0:
                self.finish_event()

    def update_risk(self):
        """灾情风险等级只由当前难度阶段决定。"""
        self.risk_level = self.stage_index + 1
        labels = {
            1: "Ⅰ级 关注",
            2: "Ⅱ级 警戒",
            3: "Ⅲ级 严重",
            4: "Ⅳ级 特别严重",
        }
        self.risk_text = labels[self.risk_level]

    def current_stage(self) -> dict:
        elapsed = self.elapsed_seconds()
        current = DIFFICULTY_STAGES[0]
        for stage in DIFFICULTY_STAGES:
            if elapsed >= stage["start"]:
                current = stage
        return current

    def update_stage(self):
        stage = self.current_stage()
        new_index = DIFFICULTY_STAGES.index(stage)
        if new_index > self.stage_index:
            self.stage_index = new_index
            if new_index not in self.announced_stages:
                self.announced_stages.add(new_index)
                self.message = "风险等级提升：现场情况正在恶化"
                self.message_timer = 3.0
            self.reset_event_cooldown()
            self.update_risk()
            self.schedule_safe_zone_relocation()

    def update_tutorial_hints(self):
        if not self.tutorial_mode:
            return
        elapsed = self.elapsed_seconds()
        if (
            self.tutorial_rescue_done
            and not self.tutorial_second_hint_shown
            and TUTORIAL_FIRST_WINDOW_SECONDS <= elapsed < TUTORIAL_TOTAL_SECONDS
        ):
            self.tutorial_second_hint_shown = True
            self.message = "继续搜救第二名群众，或先回安全区"
            self.message_timer = 4.0

    def grow_obstacles(self, dt: float):
        if self.elapsed_seconds() < TUTORIAL_FIRST_WINDOW_SECONDS:
            return
        target = self.current_stage()["max_obstacles"]
        if len(self.obstacles) >= target:
            return
        self.obstacle_growth_timer += dt
        if self.obstacle_growth_timer >= 8.0:
            self.spawn_obstacle_safe()
            self.obstacle_growth_timer = 0.0

    def events_allowed(self) -> bool:
        stage = self.current_stage()
        return self.elapsed_seconds() >= TUTORIAL_TOTAL_SECONDS and bool(stage["event_kinds"])

    def reset_event_cooldown(self):
        interval = self.current_stage()["event_interval"]
        if interval is None:
            self.event_cooldown = 9999
        else:
            self.event_cooldown = random.randint(*interval)

    def schedule_safe_zone_relocation(self):
        if (
            self.tutorial_mode
            and self.elapsed_seconds() < TUTORIAL_TOTAL_SECONDS
        ) or self.safe_zone_relocation_pending or len(self.safe_zones) < 2:
            return
        self.safe_zone_relocation_pending = True
        self.safe_zone_relocation_timer = SAFE_ZONE_RELOCATION_WARNING_SECONDS
        self.message = "临时安置点即将调整"
        self.message_timer = SAFE_ZONE_RELOCATION_WARNING_SECONDS

    def update_safe_zone_relocation(self, dt: float):
        if not self.safe_zone_relocation_pending:
            return
        self.safe_zone_relocation_timer -= dt
        if self.safe_zone_relocation_timer <= 0:
            self.relocate_safe_zone()
            self.safe_zone_relocation_pending = False
            self.safe_zone_relocation_timer = 0.0

    def relocate_safe_zone(self):
        new_position = self.find_reachable_safe_zone_position()
        if new_position is None:
            self.message = "安置点调整取消：未找到安全路线"
            self.message_timer = 2.0
            return

        old_zone = self.safe_zone_to_close()
        if old_zone is not None:
            self.safe_zones.remove(old_zone)
        self.safe_zones.append(SafeZone(*new_position))
        self.message = "新的临时安置点已开放"
        self.message_timer = 2.5

    def safe_zone_to_close(self) -> Optional[SafeZone]:
        if not self.safe_zones:
            return None
        hx, hy = self.team[0]
        return max(self.safe_zones, key=lambda zone: abs(zone.x - hx) + abs(zone.y - hy))

    def find_reachable_safe_zone_position(self) -> Optional[tuple[int, int]]:
        reachable = self.reachable_cells()
        candidates = []
        for x, y in reachable:
            distance = self.distance_from_head(x, y)
            if distance < SAFE_ZONE_RELOCATION_MIN_DISTANCE:
                continue
            if distance > SAFE_ZONE_RELOCATION_MAX_DISTANCE:
                continue
            if self.cell_blocked(x, y):
                continue
            if any(zone.x == x and zone.y == y for zone in self.safe_zones):
                continue
            candidates.append((x, y))
        if not candidates:
            candidates = [
                (x, y)
                for x, y in reachable
                if not self.cell_blocked(x, y)
                and not any(zone.x == x and zone.y == y for zone in self.safe_zones)
            ]
        return random.choice(candidates) if candidates else None

    def reachable_cells(self) -> set[tuple[int, int]]:
        start = self.team[0]
        blocked = set(self.obstacles)
        blocked.update(self.water)
        blocked.update(self.team[1:])
        visited = {start}
        frontier = [start]
        while frontier:
            x, y = frontier.pop(0)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                candidate = (nx, ny)
                if nx < 1 or nx >= GRID_SIZE - 1 or ny < 1 or ny >= GRID_SIZE - 1:
                    continue
                if candidate in visited or candidate in blocked:
                    continue
                visited.add(candidate)
                frontier.append(candidate)
        return visited

    def move_team(self):
        """把救援队按网格方向前进一个格。"""
        dx, dy = self.next_direction

        if len(self.team) > 1:
            if (self.team[0][0] + dx, self.team[0][1] + dy) == self.team[1]:
                dx, dy = self.direction
        self.direction = (dx, dy)

        old_head = self.team[0]
        nx = old_head[0] + dx
        ny = old_head[1] + dy

        if nx < 0 or nx >= GRID_SIZE or ny < 0 or ny >= GRID_SIZE:
            self.finish_game("应急队驶出地图，响应中断")
            return

        if (nx, ny) in self.obstacles:
            if self.eagle_support_timer > 0:
                self.obstacles.remove((nx, ny))
                self.message = "求是鹰支援：已清开障碍"
                self.message_timer = 1.2
            else:
                self.finish_game("道路障碍拦截救援队")
                return

        if (nx, ny) in self.water and self.eagle_support_timer <= 0:
            self.finish_game("积水困住救援队")
            return
        elif (nx, ny) in self.water:
            self.message = "求是鹰支援：安全通过积水"
            self.message_timer = 1.2

        target_resource = self.resource_at(nx, ny)
        target_survivor = self.survivor_at(nx, ny)
        should_grow = target_resource is not None or target_survivor is not None
        body_for_collision = self.team[1:] if should_grow else self.team[1:-1]
        if (nx, ny) in body_for_collision:
            if self.eagle_support_timer > 0:
                self.message = "求是鹰支援：队列避险成功"
                self.message_timer = 1.2
                return
            else:
                self.finish_game("救援队发生撞线")
                return

        if target_resource is not None:
            self.collect_resource(target_resource)
        if target_survivor is not None:
            self.pick_survivor(target_survivor)

        previous_positions = self.render_vehicle_positions()
        self.team.insert(0, (nx, ny))
        self.route.append((nx, ny))
        if len(self.route) > MAX_ROUTE_POINTS:
            self.route.pop(0)

        if not should_grow:
            self.team.pop()

        if self.is_safe_zone(nx, ny):
            self.complete_safe_zone_transfer()

        self.previous_positions = [
            previous_positions[min(i, len(previous_positions) - 1)]
            for i in range(len(self.team))
        ]
        self.target_positions = list(self.team)
        self.visual_elapsed_ms = 0.0
        self.visual_move_interval_ms = self.move_interval

        # 检查是否被完全困住
        if self.is_deadlocked():
            self.finish_game("道路封锁，路线无路可走")
        return True

    def survivor_at(self, x: int, y: int) -> Optional[Survivor]:
        return next((s for s in self.survivors if not s.carried and s.x == x and s.y == y), None)

    def resource_at(self, x: int, y: int) -> Optional[Resource]:
        return next((r for r in self.resources if r.x == x and r.y == y), None)

    def is_safe_zone(self, x: int, y: int) -> bool:
        return any(sz.x == x and sz.y == y for sz in self.safe_zones)

    def pick_survivor(self, survivor: Survivor):
        """接触受困群众后装车；只有送到安全区才得分。"""
        survivor.carried = True
        self.onboard_survivors.append(survivor)
        if self.tutorial_mode and not self.tutorial_picked_survivor:
            self.tutorial_picked_survivor = True
            self.message = "群众已上车 → 请前往绿色安置点"
        else:
            self.message = f"群众已上车：待转移 {len(self.onboard_survivors)} 人"
        self.message_timer = 2.0

    def complete_safe_zone_transfer(self):
        """在安全区统一结算人员和物资，并卸下对应负载。"""
        delivered_survivors = len(self.onboard_survivors)
        delivered_resources = self.inventory_value()
        if delivered_survivors == 0 and delivered_resources == 0:
            return

        rescue_score = self.current_stage()["rescue_score"]
        if self.tutorial_mode and not self.tutorial_rescue_done and delivered_survivors > 0:
            rescue_score = TUTORIAL_RESCUE_SCORE
        gained = delivered_survivors * rescue_score
        gained += delivered_resources * RESOURCE_DELIVERY_SCORE
        self.score += gained
        self.rescued += delivered_survivors
        self.resources_collected += delivered_resources

        unloaded_items = delivered_survivors + len(self.inventory)
        self.survivors = [s for s in self.survivors if s not in self.onboard_survivors]
        self.onboard_survivors.clear()
        self.inventory.clear()
        self.unload_team_segments(unloaded_items)

        if self.tutorial_mode and not self.tutorial_rescue_done and delivered_survivors > 0:
            self.tutorial_rescue_done = True
            self.mark_tutorial_completed()
            self.message = "救援完成 +5：现在你已经掌握基本救援流程"
            self.message_timer = 5.0
        elif delivered_survivors > 0 and self.rescued % RESCUE_STREAK_SIZE == 0:
            self.score += RESCUE_STREAK_BONUS
            self.streak_bonus_timer = 3.0
            self.message = f"连续转移完成：+{gained + RESCUE_STREAK_BONUS}"
            self.message_timer = 3.0
        else:
            self.message = f"安全区结算：+{gained}"
            self.message_timer = 2.2

        self.spawn_resources(1)
        self.spawn_survivors(1)
        self.schedule_safe_zone_relocation_after_rescue()

    def schedule_safe_zone_relocation_after_rescue(self):
        milestone = self.rescued // SAFE_ZONE_RELOCATION_RESCUES
        if milestone > self.last_safe_zone_rescue_milestone:
            self.last_safe_zone_rescue_milestone = milestone
            self.schedule_safe_zone_relocation()

    def mark_tutorial_completed(self):
        if self.tutorial_completed:
            return
        self.tutorial_completed = True
        data = load_save()
        data["tutorial_completed"] = True
        write_save(data)

    def collect_resource(self, r: Resource):
        """装载物资；得分留到安全区结算，辅助效果立即生效。"""
        kind = r.kind
        if kind == "supply":
            self.inventory.append("supply")
            self.message = "应急物资已装车，前往安全区结算"
            self.message_timer = 1.0
        elif kind == "battery":
            self.inventory.append("battery")
            self.remove_random_obstacle()
            self.message = "通讯电池已装车，清除一处道路障碍"
            self.message_timer = 2.0
        elif kind == "medical":
            self.inventory.append("medical")
            self.message = "医疗包已装车，短时风险扫描"
            self.message_timer = 2.0
            self.skill_timer = SKILL_DURATION_SECONDS
        elif kind == "eagle":
            self.inventory.append("eagle")
            self.remove_random_obstacle()
            self.remove_random_obstacle()
            self.eagle_support_timer = EAGLE_SUPPORT_SECONDS
            self.message = "求是鹰支援：短时清障护航"
            self.message_timer = 3.0

        self.resources.remove(r)

    def inventory_value(self) -> int:
        return sum(EAGLE_RESOURCE_VALUE if item == "eagle" else RESOURCE_SCORE for item in self.inventory)

    def pending_load_count(self) -> int:
        return len(self.onboard_survivors) + len(self.inventory)

    def pending_load_text(self) -> str:
        return f"{len(self.onboard_survivors)}人/{self.inventory_value()}物资"

    def unload_team_segments(self, count: int):
        min_length = len(INITIAL_TEAM)
        removable = max(0, min(count, len(self.team) - min_length))
        for _ in range(removable):
            self.team.pop()

    def remove_random_obstacle(self):
        """电池与鹰支援可移除随机障碍。"""
        if self.obstacles:
            idx = random.randrange(len(self.obstacles))
            self.obstacles.pop(idx)

    def trigger_radio_message(self):
        """生成一次现场无线电的短剧情消息，30 秒内最多一条。"""
        if self.state != GameState.PLAYING:
            return
        if random.random() < RADIO_EASTER_EGG_CHANCE:
            msg = random.choice(RADIO_EASTER_EGG_MESSAGES)
        else:
            msg = random.choice(RADIO_MESSAGES)
        self.radio_message = msg
        self.radio_timer = RADIO_DURATION_SECONDS
        self.radio_alive = True

    def trigger_event(self):
        """根据当前阶段触发会实际影响操作的灾害事件。"""
        available_kinds = [
            kind
            for kind in self.current_stage()["event_kinds"]
            if kind in EVENT_DURATIONS_SECONDS
        ]
        if not available_kinds:
            return

        bias = self.scenario.get("event_bias", "rain")
        if bias in available_kinds and random.random() < 0.45:
            kind = bias
        else:
            kind = random.choice(available_kinds)
        self.start_event(kind)

    def start_event(self, kind: str):
        """启动一种灾害事件；每种事件在 finish_event 中统一恢复。"""
        strength = self.current_stage()["event_obstacles"]
        if kind == "earthquake":
            timing = EVENT_DURATIONS_SECONDS[kind]
            self.message = "⚠ 余震预警"
            self.message_timer = 3.0
            self.event = DisasterEvent(kind, timing, "⚠ 余震预警", timing)
            for _ in range(strength):
                self.spawn_obstacle_safe()
        elif kind == "communication":
            self.message = "⚠ 通讯中断"
            self.message_timer = 2.0
            duration = EVENT_DURATIONS_SECONDS[kind]
            self.event = DisasterEvent(kind, duration, "⚠ 通讯中断", duration)
            self.show_hud = False
        elif kind == "rain":
            self.message = "⚠ 暴雨：积水区域预警"
            self.message_timer = 2.0
            duration = EVENT_DURATIONS_SECONDS[kind]
            self.event = DisasterEvent(kind, duration, "⚠ 暴雨", duration)
            self.spawn_water_cells(self.current_stage()["water_cells"] or RAIN_WATER_CELL_COUNT)

    def spawn_obstacle_safe(self):
        """新增障碍，避免落在安全区、资源、身体、队伍与群众处。"""
        if len(self.obstacles) >= self.current_stage()["max_obstacles"]:
            return
        free = []
        for y in range(1, GRID_SIZE - 1):
            for x in range(1, GRID_SIZE - 1):
                if self.in_start_protection(x, y):
                    continue
                if (x, y) in self.team:
                    continue
                if (x, y) in self.obstacles:
                    continue
                if any(sz.x == x and sz.y == y for sz in self.safe_zones):
                    continue
                if any(s.x == x and s.y == y for s in self.survivors):
                    continue
                if any(r.x == x and r.y == y for r in self.resources):
                    continue
                free.append((x, y))
        if free:
            self.obstacles.append(random.choice(free))

    def spawn_water_cells(self, count: int):
        """暴雨新增积水区域，数量受风险等级影响。"""
        self.water = []
        free = []
        for y in range(1, GRID_SIZE - 1):
            for x in range(1, GRID_SIZE - 1):
                if self.cell_blocked(x, y):
                    continue
                free.append((x, y))
        for _ in range(min(count, len(free))):
            if free:
                x, y = random.choice(free)
                self.water.append((x, y))
                free.remove((x, y))

    def finish_event(self):
        """结束事件，通讯、雨水、余震等恢复正常。"""
        if not self.event:
            return
        kind = self.event.kind
        if kind == "communication":
            self.show_hud = True
            self.message = "通讯恢复"
            self.message_timer = 1.1
        elif kind == "rain":
            self.water = []
        elif kind == "earthquake":
            self.message = "余震警报结束"
        self.event = None

    def is_deadlocked(self):
        """检查地图附近四个方向是否都被障碍或墙体封住。"""
        hx, hy = self.team[0]
        blocked = 0
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = hx + dx, hy + dy
            if nx < 0 or nx >= GRID_SIZE or ny < 0 or ny >= GRID_SIZE:
                blocked += 1
            elif (nx, ny) in self.obstacles or (nx, ny) in self.team:
                blocked += 1
        return blocked >= 4

    def use_skill(self):
        """按E使用风险扫描技能，持续3秒高亮附近重要元素。"""
        if self.state != GameState.PLAYING:
            return
        if self.skill_cooldown > 0:
            self.message = f"技能冷却：{round(self.skill_cooldown, 1)}s"
            self.message_timer = 1.0
            return
        self.skill_cooldown = SKILL_COOLDOWN_SECONDS
        self.skill_timer = SKILL_DURATION_SECONDS
        if self.tutorial_mode and not self.tutorial_e_hint_shown:
            self.tutorial_e_hint_shown = True
            self.message = "风险扫描可以帮助寻找安全路线"
        else:
            self.message = "[E] 风险扫描 ACTIVE"
        self.message_timer = 3.0

    def finish_game(self, reason: str):
        """结束一局并保存记录；结束语与称号、任务结算都在这里一次性随机，不再在 draw() 中重选。"""
        self.state = GameState.GAME_OVER
        self.message = reason
        self.game_over_message = random.choice(GAME_OVER_MESSAGES)
        # 如果少量得分靠近高评价，生成相应称号
        if self.score < 21:
            self.game_over_rank = "应急萌新"
        elif self.score < 51:
            self.game_over_rank = "现场响应员"
        elif self.score < 101:
            self.game_over_rank = "救援先锋"
        else:
            self.game_over_rank = "应急指挥官"
        self.save_record()

    def save_record(self):
        """保存本地最高分与最高救援人数。"""
        data = load_save()
        if self.score > data["best_score"]:
            data["best_score"] = self.score
        if self.rescued > data["best_rescued"]:
            data["best_rescued"] = self.rescued
        write_save(data)

    def elapsed_seconds(self) -> int:
        return max(0, (pygame.time.get_ticks() - self.started_at_ms) // 1000)

    def handle_events(self, events):
        """转发 Pygame 消息到控制器。"""
        for e in events:
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                self.handle_key(e.key)
            elif e.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mouse(e.pos)

    def handle_key(self, key):
        """按键映射：WASD/方向键移动；空格暂停；E技能；R重开；ESC返回菜单。"""
        if key in (pygame.K_w, pygame.K_UP):
            self.next_direction = (0, -1)
        elif key in (pygame.K_s, pygame.K_DOWN):
            self.next_direction = (0, 1)
        elif key in (pygame.K_a, pygame.K_LEFT):
            self.next_direction = (-1, 0)
        elif key in (pygame.K_d, pygame.K_RIGHT):
            self.next_direction = (1, 0)
        elif key == pygame.K_SPACE:
            if self.state == GameState.PLAYING:
                self.state = GameState.PAUSED
            elif self.state == GameState.PAUSED:
                self.state = GameState.PLAYING
        elif key == pygame.K_e:
            self.use_skill()
        elif key == pygame.K_r:
            self.reset_game()
        elif key == pygame.K_ESCAPE:
            self.state = GameState.MENU

    def handle_mouse(self, pos):
        """菜单、教程、GameOver 的鼠标点击入口。"""
        if self.state == GameState.MENU:
            for key, rect in self.menu_buttons.items():
                if rect.collidepoint(pos):
                    if key == "start":
                        self.start_from_menu()
                    elif key == "tutorial":
                        self.state = GameState.GUIDE
                    elif key == "quit":
                        self.running = False
        elif self.state == GameState.MISSION_BRIEF:
            if self.brief_button.collidepoint(pos):
                self.reset_game(
                    tutorial_mode=self.force_tutorial or not self.tutorial_completed,
                    scenario=self.scenario,
                )
            elif self.entry_back_button.collidepoint(pos):
                self.state = GameState.MENU
        elif self.state == GameState.GUIDE:
            if self.guide_buttons["back"].collidepoint(pos):
                self.state = GameState.MENU
            elif self.guide_buttons["learn"].collidepoint(pos):
                self.start_from_menu(force_tutorial=True)
        elif self.state == GameState.GAME_OVER:
            for key, rect in self.gameover_buttons.items():
                if rect.collidepoint(pos):
                    if key == "again":
                        self.reset_game()
                    elif key == "menu":
                        self.state = GameState.MENU

    def draw(self):
        """统一画面入口。"""
        if self.state == GameState.MENU:
            self.draw_menu()
        elif self.state == GameState.MISSION_BRIEF:
            self.draw_mission_brief()
        elif self.state == GameState.GUIDE:
            self.draw_guide()
        elif self.state == GameState.PAUSED:
            self.draw_game()
            self.draw_pause_overlay()
        elif self.state == GameState.GAME_OVER:
            self.draw_gameover()
        else:
            self.draw_game()

    def palette(self, name: str) -> tuple[int, int, int]:
        return VISUAL["colors"][name]

    def draw_paper_background(self):
        self.screen.blit(self.paper_background, (0, 0))

    def draw_paper_card(self, rect: pygame.Rect, fill: tuple[int, int, int] | None = None, outline: tuple[int, int, int] | None = None, radius: int | None = None):
        fill = fill or self.palette("paper_warm")
        outline = outline or self.palette("pencil")
        radius = min(radius or VISUAL["radius"]["card"], VISUAL["radius"]["card"])
        key = (rect.size, fill, outline, radius)
        if key not in self.paper_cards:
            dx, dy = VISUAL["shadow"]["offset"]
            card = pygame.Surface((rect.width + dx, rect.height + dy), pygame.SRCALPHA)
            pygame.draw.rect(card, (*self.palette("paper_shadow"), VISUAL["shadow"]["alpha"]),
                             (dx, dy, rect.width, rect.height), border_radius=radius)
            material = pygame.transform.smoothscale(self.map_art.paper_texture, rect.size)
            tint = pygame.Surface(rect.size, pygame.SRCALPHA)
            tint.fill((*fill, 200))
            material.blit(tint, (0, 0))
            mask = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 244), mask.get_rect(), border_radius=radius)
            material.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            pygame.draw.rect(material, outline, material.get_rect(), 1, border_radius=radius)
            card.blit(material, (0, 0))
            self.paper_cards[key] = card
        self.screen.blit(self.paper_cards[key], rect.topleft)

    def cached_text(self, font, text, color):
        key = (id(font), text, color)
        if key not in self.text_cache:
            if len(self.text_cache) >= 512:
                self.text_cache.clear()
            self.text_cache[key] = font.render(text, True, color)
        return self.text_cache[key]

    def draw_sticker_button(self, rect: pygame.Rect, label: str, fill: tuple[int, int, int], text_color: tuple[int, int, int] | None = None):
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        offset_y = -2 if hovered else 0
        draw_rect = rect.move(0, offset_y)
        text_color = text_color or self.palette("paper_warm")
        pygame.draw.rect(self.screen, (176, 153, 118), rect.move(3, 5), border_radius=VISUAL["radius"]["button"])
        pygame.draw.rect(self.screen, fill, draw_rect, border_radius=VISUAL["radius"]["button"])
        pygame.draw.rect(self.screen, self.palette("ink"), draw_rect, 2, border_radius=VISUAL["radius"]["button"])
        if hovered:
            pygame.draw.rect(self.screen, (255, 246, 180), draw_rect.inflate(8, 8), 2, border_radius=VISUAL["radius"]["button"] + 3)
        text = self.font_body.render(label, True, text_color)
        self.screen.blit(text, text.get_rect(center=draw_rect.center))

    def blit_center(self, surf: pygame.Surface, center: tuple[int, int]):
        self.screen.blit(surf, surf.get_rect(center=center))

    def draw_rescue_car_at(self, cx, cy, direction=(1, 0)):
        self.map_art.sprite(self.screen, "rescue", (cx, cy), VISUAL["sprite_size"]["rescue"], direction)

    def draw_tent_icon(self, cx, cy):
        self.map_art.sprite(self.screen, "tent", (cx, cy), VISUAL["sprite_size"]["tent"])

    def draw_menu(self):
        self.entry_art.draw_scene(self.screen)
        self.screen.blit(self.font_small.render("救援基地 / 出发前简报", True, self.palette("pencil")), (97, 83))
        self.screen.blit(self.font_title.render("EMERGENCY RUN", True, self.palette("ink")), (93, 117))
        self.screen.blit(self.font_title.render("应急行动", True, self.palette("ink")), (96, 166))
        self.screen.blit(self.font_body.render("今天，也要把大家平安带回来。", True, self.palette("ink")), (97, 231))
        labels = {"start": "开始行动", "tutorial": "游戏说明", "quit": "退出"}
        colors = {"start": (190, 203, 166), "tutorial": (226, 222, 202), "quit": (226, 222, 202)}
        for key, rect in self.menu_buttons.items():
            self.entry_art.draw_tag(self.screen, rect, labels[key], self.font_body, colors[key])

    def draw_mission_brief(self):
        self.entry_art.draw_scene(self.screen, animated=False)
        self.screen.blit(self.entry_art.shade, (0, 0))
        panel = pygame.Rect(230, 88, 640, 544)
        self.entry_art.draw_sheet(self.screen, panel)
        self.entry_art.draw_tag(self.screen, self.entry_back_button, "返回", self.font_small, (224, 225, 189))
        self.screen.blit(self.font_title.render("本次行动", True, self.palette("ink")), (280, 166))
        self.screen.blit(self.font_body.render(self.scenario["title"], True, self.palette("tent_dark")), (281, 220))
        self.screen.blit(self.font_small.render("目标", True, self.palette("pencil")), (281, 277))
        self.screen.blit(self.font_body.render("搜救群众 → 安全转移 → 应对现场风险", True, self.palette("ink")), (281, 306))
        for kind, x, size in (("person", 343, 86), ("transport", 518, 105), ("tent", 719, 120)):
            self.entry_art.image(self.screen, kind, size, (x, 393))
        controls = [("WASD / 方向键", "移动"), ("E", "风险扫描"), ("SPACE", "暂停")]
        for i, (key, label) in enumerate(controls):
            x = 281 + i * 180
            self.screen.blit(self.font_small.render(key, True, self.palette("tent_dark")), (x, 478))
            self.screen.blit(self.font_small.render(label, True, self.palette("ink")), (x, 506))
        self.entry_art.draw_tag(self.screen, self.brief_button, "出发", self.font_body, (163, 211, 135))

    def draw_guide(self):
        self.entry_art.draw_scene(self.screen, animated=False)
        self.screen.blit(self.entry_art.shade, (0, 0))
        self.entry_art.draw_sheet(self.screen, pygame.Rect(100, 65, 900, 545))
        self.screen.blit(self.font_title.render("救援行动 · 四步出发", True, self.palette("ink")), (140, 94))
        steps = [
            ("person", 86, "① 找到受困群众", "寻找举手求助的人"),
            ("transport", 105, "② 接触后进入转运", "群众上车，车队变长"),
            ("tent", 120, "③ 前往绿色安置点", "抵达帐篷，完成转移"),
            ("rubble", 90, "④ 风险升高时", "及时撤离，安全优先"),
        ]
        for i, (kind, size, title, note) in enumerate(steps):
            x = 213 + i * 224
            self.entry_art.image(self.screen, kind, size, (x, 210))
            self.blit_center(self.cached_text(self.font_small, title, self.palette("ink")), (x, 279))
            self.blit_center(self.cached_text(self.font_small, note, self.palette("pencil")), (x, 307))
        pygame.draw.line(self.screen, self.palette("pencil"), (140, 340), (960, 340), 1)
        self.screen.blit(self.cached_text(self.font_body, "地图图例", self.palette("ink")), (140, 357))
        for i, (kind, name, appearance, effect) in enumerate(self.entry_art.legend):
            x = 185 + i * 145
            self.entry_art.image(self.screen, kind, 76, (x, 438))
            self.blit_center(self.cached_text(self.font_small, name, self.palette("ink")), (x, 491))
            self.blit_center(self.cached_text(self.font_mini, appearance, self.palette("pencil")), (x, 521))
            self.blit_center(self.cached_text(self.font_mini, effect, self.palette("pencil")), (x, 546))
        self.entry_art.draw_tag(self.screen, self.guide_buttons["back"], "返回基地", self.font_body, (224, 225, 189))
        learn = "再次学习玩法" if self.tutorial_completed else "学习并出发"
        self.entry_art.draw_tag(self.screen, self.guide_buttons["learn"], learn, self.font_body, (163, 211, 135))

    def draw_pause_overlay(self):
        """暂停遮罩。"""
        s = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        s.fill((76, 65, 45, 85))
        self.screen.blit(s, (0, 0))
        panel = pygame.Rect(385, 245, 330, 160)
        self.draw_paper_card(panel, self.palette("paper_warm"), self.palette("pencil"), 18)
        title = self.font_title.render("暂停", True, self.palette("ink"))
        note = self.font_small.render("按 SPACE 继续行动", True, self.palette("pencil"))
        self.blit_center(title, (panel.centerx, panel.y + 58))
        self.blit_center(note, (panel.centerx, panel.y + 105))

    def draw_game(self):
        """主游戏地图与右侧HUD渲染。"""
        self.draw_paper_background()

        # 地图背景
        map_rect = pygame.Rect(BOARD_X, BOARD_Y, BOARD_SIZE, BOARD_SIZE)
        self.draw_paper_card(map_rect, self.palette("paper_green"), self.palette("pencil"), 20)

        # 手绘灾区地图：柔和米白地图背景与纸张纹理
        self.draw_map_scenery()

        # 逻辑图层：去掉长时间虚线路径污染感，保留关键信息层
        self.draw_route()
        self.draw_water()
        self.draw_obstacles()
        if self.safe_zones_visible():
            self.draw_safe_zones()
        self.draw_resources()
        self.draw_survivors()
        self.draw_team()
        self.draw_tutorial_guidance()

        if self.event:
            self.draw_event_text()

        # 现场无线电信息：2-3 秒后淡出
        if self.radio_alive and self.radio_message:
            alpha = max(60, min(255, int(255 * (self.radio_timer / RADIO_DURATION_SECONDS))))
            radio_rect = pygame.Rect(BOARD_X + 150, BOARD_Y + 34, 395, 38)
            radio = pygame.Surface((radio_rect.width, radio_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(radio, (*self.palette("paper_warm"), alpha), radio.get_rect(), border_radius=12)
            pygame.draw.rect(radio, (*self.palette("river_dark"), alpha), radio.get_rect(), 2, border_radius=12)
            pygame.draw.circle(radio, (*self.palette("vehicle_aux"), alpha), (21, 19), 8, 2)
            t = self.font_small.render("现场无线电：" + self.radio_message, True, self.palette("ink"))
            t.set_alpha(alpha)
            radio.blit(t, (38, 9))
            self.screen.blit(radio, radio_rect.topleft)
        self.draw_streak_bonus()

        # 右侧 HUD
        self.draw_hud()

        # 如果通讯中断，画遮罩
        if not self.show_hud:
            self.screen.blit(self.communication_overlay, (HUD_X - 4, 118))
            card = pygame.Rect(HUD_X + 35, 245, 205, 80)
            pygame.draw.rect(self.screen, self.palette("paper_warm"), card, border_radius=16)
            pygame.draw.rect(self.screen, self.palette("danger"), card, 2, border_radius=16)
            t = self.font_body.render("通讯中断", True, self.palette("danger"))
            self.blit_center(t, card.center)

        # 底部消息
        if self.message_timer > 0:
            colors = self.palette("danger") if self.message.startswith("⚠") or self.message.startswith("道路") else self.palette("tent_dark")
            t = self.font_body.render(self.message, True, colors)
            self.screen.blit(t, (BOARD_X + 12, 40))
        self.apply_earthquake_shake()

    def apply_earthquake_shake(self):
        if not self.event or self.event.kind != "earthquake":
            return
        dx = random.randint(-EARTHQUAKE_SHAKE_PIXELS, EARTHQUAKE_SHAKE_PIXELS)
        dy = random.randint(-EARTHQUAKE_SHAKE_PIXELS, EARTHQUAKE_SHAKE_PIXELS)
        self.shake_frame.blit(self.screen, (0, 0))
        self.screen.fill(self.palette("paper"))
        self.screen.blit(self.shake_frame, (dx, dy))

    def draw_streak_bonus(self):
        if self.streak_bonus_timer <= 0:
            return
        pulse = 0.5 + 0.5 * abs((pygame.time.get_ticks() % 800) / 400 - 1)
        alpha = int(110 + pulse * 95)
        text = self.font_body.render("黄金72小时：救援效率提升", True, self.palette("tent_dark"))
        banner_width = text.get_width() + 36
        banner = pygame.Surface((banner_width, 36), pygame.SRCALPHA)
        pygame.draw.rect(banner, (*self.palette("eagle"), alpha), (0, 0, banner_width, 36), border_radius=12)
        banner.blit(text, (18, 5))
        self.screen.blit(banner, (BOARD_X + (BOARD_SIZE - banner_width) // 2, BOARD_Y + BOARD_SIZE - 56))

    def draw_map_scenery(self):
        """Paint the cached scene below every interactive map object."""
        self.screen.blit(self.map_art.background, (BOARD_X, BOARD_Y))

    def draw_safe_zones(self):
        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 350)
        glow = self.safe_zone_glow
        glow.fill((0, 0, 0, 0))
        pygame.draw.circle(glow, (117, 170, 111, int(44 + pulse * 20)), (37, 37), int(27 + pulse * 4))
        pygame.draw.circle(glow, (92, 176, 107, 90), (37, 37), int(28 + pulse * 4), 1)
        for zone in self.safe_zones:
            center = self.cell_center(zone.x, zone.y)
            self.screen.blit(glow, (center[0] - 37, center[1] - 37))
            self.map_art.sprite(self.screen, "tent", center, VISUAL["sprite_size"]["tent"])

    def draw_tutorial_guidance(self):
        if not self.safe_zones_visible():
            return
        if not self.tutorial_mode or self.elapsed_seconds() >= TUTORIAL_TOTAL_SECONDS:
            return
        target = None
        label = ""
        if not self.tutorial_picked_survivor:
            survivor = self.survivor_at(*TUTORIAL_SURVIVOR_POS)
            if survivor is not None:
                target = (survivor.x, survivor.y)
                label = "先前往这里，接触受困群众"
        elif self.onboard_survivors:
            zone = self.nearest_safe_zone()
            if zone is not None:
                target = (zone.x, zone.y)
                label = "群众已上车 → 请前往绿色安置点"

        if target is None:
            return

        tx, ty = self.cell_center(*target)
        hx, hy = self.cell_center(*self.team[0])
        pygame.draw.circle(self.screen, (255, 234, 161), (tx, ty), CELL_SIZE, 3)
        pygame.draw.line(self.screen, self.palette("danger"), (hx, hy), (tx, ty), 3)
        pygame.draw.polygon(
            self.screen,
            self.palette("danger"),
            ((tx, ty), (tx - 8, ty - 5), (tx - 5, ty + 8)),
        )
        note = self.font_small.render(label, True, self.palette("danger"))
        self.screen.blit(note, (BOARD_X + 12, BOARD_Y + BOARD_SIZE - 34))

    def cell_center(self, x: int, y: int) -> tuple[int, int]:
        return BOARD_X + x * CELL_SIZE + CELL_SIZE // 2, BOARD_Y + y * CELL_SIZE + CELL_SIZE // 2

    def nearest_safe_zone(self) -> Optional[SafeZone]:
        if not self.safe_zones:
            return None
        hx, hy = self.team[0]
        return min(self.safe_zones, key=lambda zone: abs(zone.x - hx) + abs(zone.y - hy))

    def safe_zones_visible(self) -> bool:
        return self.show_hud or self.skill_timer > 0

    def draw_route(self):
        """画出救援路线轨迹；为了用户体验，路线用简洁点位作为局部信息，避免一条很长的连线显得冗长。"""
        if len(self.route) < 2:
            return
        # 仅保留路径中的少量稀疏节点，不再把整条路线用长线拉满
        max_points = 8
        sample = self.route[::max(1, len(self.route) // max_points)]
        for x, y in sample[-max_points:]:
            px = BOARD_X + x * CELL_SIZE + CELL_SIZE // 2
            py = BOARD_Y + y * CELL_SIZE + CELL_SIZE // 2
            pygame.draw.circle(self.screen, (116, 180, 205), (px, py), 3)

    def draw_water(self):
        self.map_art.water(self.screen, self.water, (BOARD_X, BOARD_Y))

    def draw_obstacles(self):
        for x, y in self.obstacles:
            self.map_art.sprite(self.screen, "rubble", self.cell_center(x, y), VISUAL["sprite_size"]["rubble"])

    def draw_resources(self):
        bob = int(math.sin(pygame.time.get_ticks() / 260) * 2)
        for resource in self.resources:
            cx, cy = self.cell_center(resource.x, resource.y)
            self.map_art.sprite(self.screen, resource.kind, (cx, cy + bob), VISUAL["sprite_size"]["resource"])

    def draw_survivors(self):
        for survivor in self.survivors:
            if not survivor.carried:
                self.map_art.sprite(self.screen, "person", self.cell_center(survivor.x, survivor.y), VISUAL["sprite_size"]["person"])

    def reset_vehicle_motion(self):
        self.previous_positions = list(self.team)
        self.target_positions = list(self.team)
        self.visual_elapsed_ms = 0.0
        self.visual_move_interval_ms = self.move_interval
        self.move_progress = 0.0

    def render_vehicle_positions(self):
        progress = min(1.0, self.visual_elapsed_ms / self.visual_move_interval_ms)
        return [
            (old_x + (new_x - old_x) * progress, old_y + (new_y - old_y) * progress)
            for (old_x, old_y), (new_x, new_y) in zip(self.previous_positions, self.target_positions)
        ]

    def draw_team(self):
        """救援车队绘制：头部是救援车，身体是后勤车辆。"""
        self.move_progress = min(1.0, self.visual_elapsed_ms / self.visual_move_interval_ms)
        for i, (render_x, render_y) in enumerate(self.render_vehicle_positions()):
            x, y = self.team[i]
            cx = round(BOARD_X + render_x * CELL_SIZE + CELL_SIZE // 2)
            cy = round(BOARD_Y + render_y * CELL_SIZE + CELL_SIZE // 2)
            if i == 0:
                if self.eagle_support_timer > 0:
                    pygame.draw.circle(self.screen, self.palette("eagle"), (cx, cy), 24, 2)
                    pygame.draw.arc(self.screen, self.palette("eagle_dark"), (cx - 28, cy - 16, 24, 24), 0.1, 2.6, 2)
                    pygame.draw.arc(self.screen, self.palette("eagle_dark"), (cx + 4, cy - 16, 24, 24), 0.5, 3.0, 2)
                self.map_art.sprite(self.screen, "rescue", (cx, cy), VISUAL["sprite_size"]["rescue"], self.direction)
            else:
                ahead_x, ahead_y = self.team[i - 1]
                heading = (ahead_x - x, ahead_y - y)
                if heading not in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    heading = self.direction
                kind = ("cargo", "transport", "logistics")[(i - 1) % 3]
                self.map_art.sprite(self.screen, kind, (cx, cy), VISUAL["sprite_size"]["body"], heading)

        # 风险扫描高亮
        if self.skill_timer > 0:
            for z in self.safe_zones:
                px = BOARD_X + z.x * CELL_SIZE
                py = BOARD_Y + z.y * CELL_SIZE
                pygame.draw.rect(self.screen, (255, 234, 161), (px, py, CELL_SIZE, CELL_SIZE), 2, border_radius=4)
            for x, y in self.obstacles:
                px = BOARD_X + x * CELL_SIZE
                py = BOARD_Y + y * CELL_SIZE
                pygame.draw.rect(self.screen, (247, 129, 113), (px, py, CELL_SIZE, CELL_SIZE), 2, border_radius=4)

    def draw_event_text(self):
        """事件文字在地图左上显示。"""
        if not self.event:
            return
        text = self.event.text
        t = self.font_body.render(text, True, self.palette("danger"))
        badge = pygame.Rect(BOARD_X + 245, 32, max(165, t.get_width() + 26), 40)
        self.draw_paper_card(badge, self.palette("paper_warm"), self.palette("danger"), 14)
        self.screen.blit(t, (badge.x + 13, badge.y + 7))

    def draw_hud(self):
        """右侧 HUD：地图边缘的便签信息。"""
        title_card = pygame.Rect(HUD_X, 82, 300, 70)
        self.draw_paper_card(title_card, self.palette("paper_warm"), self.palette("pencil"), 16)
        title = self.cached_text(self.font_body, "EMERGENCY RUN", self.palette("ink"))
        t = self.cached_text(self.font_mini, "救援行动地图", self.palette("pencil"))
        self.screen.blit(title, (HUD_X + 22, 98))
        self.screen.blit(t, (HUD_X + 23, 128))

        self.draw_hud_line("响应得分", str(self.score), 170, self.palette("paper_warm"))
        self.draw_hud_line("成功转移", str(self.rescued), 230, self.palette("paper_green"))
        self.draw_hud_line("风险等级", self.risk_text, 290, self.palette("paper_blue"))
        event_names = {"earthquake": "余震", "rain": "暴雨", "communication": "通讯中断"}
        self.draw_hud_line("灾害事件", (event_names[self.event.kind] if self.event else "无"), 350, self.palette("paper_warm"))
        self.draw_hud_line("待结算", self.pending_load_text(), 410, self.palette("paper_green"))

        skill_panel = pygame.Rect(HUD_X + 10, 475, 280, 56)
        self.draw_paper_card(skill_panel, self.palette("paper_blue"), self.palette("river_dark"), 15)
        if self.skill_cooldown > 0:
            skill_text = f"[E] 风险扫描 {round(self.skill_cooldown, 1)}s"
            skill_color = self.palette("danger")
        else:
            skill_text = "[E] 风险扫描 READY"
            skill_color = self.palette("tent_dark")
        t = self.cached_text(self.font_small, skill_text, skill_color)
        self.screen.blit(t, (skill_panel.x + 22, skill_panel.y + 18))

        tape = pygame.Rect(HUD_X + 28, 548, 245, 88)
        self.draw_paper_card(tape, self.palette("paper_warm"), self.palette("pencil"), 7)
        op = [
            "WASD / ARROWS 移动",
            "SPACE 暂停",
            "E 扫描",
            "R 重启",
            "ESC 返回菜单",
        ]
        y = tape.y + 8
        for s in op:
            t = self.cached_text(self.font_mini, s, self.palette("pencil"))
            self.screen.blit(t, (tape.x + 14, y))
            y += 16

    def draw_hud_line(self, label: str, value: str, y: int, fill: tuple[int, int, int]):
        """绘制HUD一行。"""
        rect = pygame.Rect(HUD_X + 10, y, 280, 46)
        self.draw_paper_card(rect, fill, self.palette("pencil"), 13)
        k = self.cached_text(self.font_mini, label, self.palette("pencil"))
        color = self.palette("danger") if label == "风险等级" and self.risk_level >= 3 else self.palette("ink")
        v = self.cached_text(self.font_body, str(value), color)
        self.screen.blit(k, (rect.x + 15, rect.y + 8))
        self.screen.blit(v, (rect.x + 132, rect.y + 6))

    def draw_gameover(self):
        """本次应急响应报告。"""
        self.draw_paper_background()
        panel = pygame.Rect(150, 100, 760, 500)
        self.draw_paper_card(panel, self.palette("paper_warm"), self.palette("pencil"), 22)
        title = self.font_title.render("本次行动报告卡", True, self.palette("ink"))
        self.screen.blit(title, (290, 130))
        self.draw_rescue_car_at(235, 150, direction=(1, 0))
        self.draw_tent_icon(815, 158)

        items = [
            ("响应得分", str(self.score)),
            ("成功救援人数", str(self.rescued)),
            ("持续时间", f"{self.elapsed_seconds()}s"),
            ("最高风险等级", self.risk_text),
            ("交付物资价值", str(self.resources_collected)),
        ]
        y = 190
        for label, value in items:
            row = pygame.Rect(235, y - 6, 520, 34)
            pygame.draw.rect(self.screen, (249, 241, 219), row, border_radius=9)
            pygame.draw.line(self.screen, (229, 214, 178), (row.x + 12, row.bottom - 3), (row.right - 12, row.bottom - 3), 1)
            t1 = self.font_body.render(label, True, self.palette("ink"))
            t2 = self.font_body.render(value, True, self.palette("tent_dark"))
            self.screen.blit(t1, (250, y))
            self.screen.blit(t2, (560, y))
            y += 42

        rank_card = pygame.Rect(240, 420, 470, 42)
        pygame.draw.rect(self.screen, self.palette("paper_green"), rank_card, border_radius=12)
        pygame.draw.rect(self.screen, self.palette("tent_dark"), rank_card, 2, border_radius=12)
        self.screen.blit(self.font_body.render(f"称号：{self.game_over_rank}", True, self.palette("tent_dark")), (260, 427))

        # 结束语只在 finish_game 完成时一次性选择并写入 self.game_over_message，draw 只负责画出来
        self.screen.blit(self.font_small.render(self.game_over_message, True, self.palette("pencil")), (250, 482))

        for key, rect in self.gameover_buttons.items():
            color = self.palette("tent") if key == "again" else self.palette("river")
            self.draw_sticker_button(rect, "再次行动" if key == "again" else "返回主页", color)

    def run(self):
        """主循环。"""
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            events = pygame.event.get()
            self.handle_events(events)
            self.update(dt)
            self.draw()
            pygame.display.flip()
