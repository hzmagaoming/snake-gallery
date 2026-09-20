"""一个使用 Pygame 编写的中文贪吃蛇游戏。"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable

import pygame


CELL_SIZE = 26
GRID_WIDTH = 26
GRID_HEIGHT = 20
BOARD_WIDTH = CELL_SIZE * GRID_WIDTH
BOARD_HEIGHT = CELL_SIZE * GRID_HEIGHT
BOARD_X = 28
HEADER_HEIGHT = 154
SIDEBAR_X = BOARD_X + BOARD_WIDTH + 28
SIDEBAR_WIDTH = 280
WINDOW_WIDTH = SIDEBAR_X + SIDEBAR_WIDTH + 28
WINDOW_HEIGHT = 720


class ScreenMode(Enum):
    MENU = "menu"
    INSTRUCTIONS = "instructions"
    SETUP = "setup"
    PLAYING = "playing"
    GAME_OVER = "game_over"


class Leaderboard:
    """保存在本地 JSON 文件中的排行榜。"""

    MAX_SAVED_ENTRIES = 100

    def __init__(self, path: Path) -> None:
        self.path = path
        self.entries: list[dict[str, object]] = []
        self._load()

    @property
    def high_score(self) -> int:
        return int(self.entries[0]["score"]) if self.entries else 0

    def top(self, count: int = 10) -> list[dict[str, object]]:
        return self.entries[:count]

    def best_for(self, nickname: str) -> int:
        key = nickname.strip().casefold()
        for entry in self.entries:
            if str(entry["nickname"]).casefold() == key:
                return int(entry["score"])
        return 0

    def has_nickname(self, nickname: str) -> bool:
        key = nickname.strip().casefold()
        return bool(key) and any(
            str(entry["nickname"]).strip().casefold() == key for entry in self.entries
        )

    def record(self, nickname: str, score: int) -> int:
        cleaned_name = nickname.strip()[:12] or "玩家"
        new_score = max(0, int(score))
        entry = next(
            (
                item
                for item in self.entries
                if str(item["nickname"]).casefold() == cleaned_name.casefold()
            ),
            None,
        )
        if entry is None:
            entry = {"nickname": cleaned_name, "score": new_score}
            self.entries.append(entry)
        elif new_score > int(entry["score"]):
            entry["score"] = new_score

        self.entries.sort(key=lambda item: int(item["score"]), reverse=True)
        rank = next(index for index, item in enumerate(self.entries, start=1) if item is entry)
        self.entries = self.entries[: self.MAX_SAVED_ENTRIES]
        self._save()
        return rank

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            valid_entries = [
                {"nickname": str(item["nickname"])[:12], "score": max(0, int(item["score"]))}
                for item in raw
                if isinstance(item, dict) and "nickname" in item and "score" in item
            ]
            # 兼容旧版排行榜：同名记录只保留最高成绩。
            best_by_name: dict[str, dict[str, object]] = {}
            for entry in valid_entries:
                key = str(entry["nickname"]).strip().casefold()
                previous = best_by_name.get(key)
                if previous is None or int(entry["score"]) > int(previous["score"]):
                    best_by_name[key] = entry
            deduplicated = list(best_by_name.values())
            deduplicated.sort(key=lambda item: int(item["score"]), reverse=True)
            self.entries = deduplicated[: self.MAX_SAVED_ENTRIES]
            if len(deduplicated) != len(valid_entries):
                self._save()
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            self.entries = []

    def _save(self) -> None:
        try:
            self.path.write_text(
                json.dumps(self.entries, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            # 即使目录暂时不可写，当前游戏仍可继续并保留内存中的成绩。
            pass


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def opposite(self) -> "Direction":
        dx, dy = self.value
        return Direction((-dx, -dy))


@dataclass(frozen=True)
class Position:
    x: int
    y: int

    def moved(self, direction: Direction) -> "Position":
        dx, dy = direction.value
        return Position(self.x + dx, self.y + dy)


class SnakeGameState:
    """与界面无关的游戏状态，便于可靠地自动测试。"""

    DEFAULT_BASE_SPEED = 7
    MIN_SPEED = 1
    MAX_SPEED = 18
    DEFAULT_OBSTACLE_COUNT = 14

    def __init__(
        self,
        width: int = GRID_WIDTH,
        height: int = GRID_HEIGHT,
        rng: random.Random | None = None,
        base_speed: int = DEFAULT_BASE_SPEED,
        obstacle_count: int = DEFAULT_OBSTACLE_COUNT,
    ) -> None:
        self.width = width
        self.height = height
        self.rng = rng or random.Random()
        self.base_speed = max(self.MIN_SPEED, min(base_speed, self.MAX_SPEED))
        self.obstacle_count = max(0, obstacle_count)
        self.reset()

    def reset(self) -> None:
        center_x = self.width // 2
        center_y = self.height // 2
        self.snake = [
            Position(center_x, center_y),
            Position(center_x - 1, center_y),
            Position(center_x - 2, center_y),
        ]
        self.direction = Direction.RIGHT
        self.queued_direction = Direction.RIGHT
        self.score = 0
        self.paused = False
        self.game_over = False
        self.obstacles = self._spawn_obstacles()
        self.food = self._spawn_food()

    @property
    def speed(self) -> int:
        return min(self.base_speed + self.score // 3, self.MAX_SPEED)

    def adjust_base_speed(self, amount: int) -> None:
        self.base_speed = max(self.MIN_SPEED, min(self.base_speed + amount, self.MAX_SPEED))

    def set_direction(self, direction: Direction) -> None:
        if self.game_over or direction is self.direction.opposite:
            return
        self.queued_direction = direction

    def toggle_pause(self) -> None:
        if not self.game_over:
            self.paused = not self.paused

    def step(self) -> None:
        if self.paused or self.game_over:
            return

        self.direction = self.queued_direction
        new_head = self.snake[0].moved(self.direction)
        hit_wall = not (0 <= new_head.x < self.width and 0 <= new_head.y < self.height)
        hit_obstacle = new_head in self.obstacles
        eating = new_head == self.food
        occupied_body = self.snake if eating else self.snake[:-1]

        if hit_wall or hit_obstacle or new_head in occupied_body:
            self.game_over = True
            return

        self.snake.insert(0, new_head)
        if eating:
            self.score += 1
            self.food = self._spawn_food()
        else:
            self.snake.pop()

    def _spawn_food(self) -> Position | None:
        occupied = set(self.snake) | self.obstacles
        empty_cells = [
            Position(x, y)
            for y in range(self.height)
            for x in range(self.width)
            if Position(x, y) not in occupied
        ]
        return self.rng.choice(empty_cells) if empty_cells else None

    def _spawn_obstacles(self) -> set[Position]:
        head = self.snake[0]
        snake_cells = set(self.snake)
        available = [
            Position(x, y)
            for y in range(self.height)
            for x in range(self.width)
            if Position(x, y) not in snake_cells
            # 给出生点留出足够空间，避免游戏一开始就无路可走。
            and abs(x - head.x) + abs(y - head.y) > 3
        ]
        count = min(self.obstacle_count, len(available))
        return set(self.rng.sample(available, count))


class SnakeGame:
    BG = (7, 18, 27)
    BG_BOTTOM = (10, 32, 41)
    BOARD_BG = (10, 27, 36)
    BOARD_BOTTOM = (12, 38, 46)
    GRID = (30, 65, 72)
    PANEL = (19, 43, 53)
    PANEL_BORDER = (45, 92, 97)
    TEXT = (238, 249, 247)
    MUTED = (143, 171, 172)
    GREEN_DARK = (11, 118, 99)
    GREEN = (35, 203, 151)
    GREEN_LIGHT = (105, 240, 190)
    GREEN_HEAD = (74, 225, 165)
    CREAM = (248, 250, 229)
    INK = (10, 55, 48)
    BLUSH = (255, 137, 151)
    RED = (255, 91, 112)
    YELLOW = (255, 211, 92)
    ROCK = (103, 128, 136)
    ROCK_LIGHT = (171, 194, 197)
    ROCK_DARK = (43, 68, 76)

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("贪吃蛇 · Snake Game")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.state = SnakeGameState()
        self.leaderboard = Leaderboard(Path(__file__).with_name("leaderboard.json"))
        self.font_hero = self._font(56)
        self.font_title = self._font(44)
        self.font_large = self._font(34)
        self.font_medium = self._font(24)
        self.font_small = self._font(17)
        self.font_tiny = self._font(14)
        self.background_surface = self._make_gradient_surface(
            (WINDOW_WIDTH, WINDOW_HEIGHT), self.BG, self.BG_BOTTOM
        )
        self.board_surface = self._make_gradient_surface(
            (BOARD_WIDTH, BOARD_HEIGHT), self.BOARD_BG, self.BOARD_BOTTOM
        )
        self.running = True
        self.mode = ScreenMode.MENU
        self.nickname = ""
        self.setup_error = ""
        self.current_rank: int | None = None
        self.round_score = 0
        self.personal_best = 0
        self.last_move_at = pygame.time.get_ticks()

        self.menu_start_button = pygame.Rect(WINDOW_WIDTH // 2 - 170, 458, 340, 58)
        self.menu_help_button = pygame.Rect(WINDOW_WIDTH // 2 - 170, 530, 340, 54)
        self.back_button = pygame.Rect(224, 622, 150, 44)
        self.nickname_box = pygame.Rect(WINDOW_WIDTH // 2 - 230, 246, 460, 58)
        self.speed_minus_button = pygame.Rect(WINDOW_WIDTH // 2 - 142, 378, 56, 50)
        self.speed_plus_button = pygame.Rect(WINDOW_WIDTH // 2 + 86, 378, 56, 50)
        self.setup_start_button = pygame.Rect(WINDOW_WIDTH // 2 - 170, 515, 340, 56)
        self.replay_button = pygame.Rect(WINDOW_WIDTH // 2 - 238, 615, 220, 46)
        self.gameover_menu_button = pygame.Rect(WINDOW_WIDTH // 2 + 18, 615, 220, 46)
        self.pause_button = pygame.Rect(SIDEBAR_X + 20, 573, SIDEBAR_WIDTH - 40, 44)
        self.play_menu_button = pygame.Rect(SIDEBAR_X + 20, 629, SIDEBAR_WIDTH - 40, 36)

    @staticmethod
    def _font(size: int) -> pygame.font.Font:
        candidates: Iterable[str] = (
            "PingFang SC",
            "Hiragino Sans GB",
            "Microsoft YaHei",
            "Noto Sans CJK SC",
            "Arial Unicode MS",
        )
        path = pygame.font.match_font(list(candidates))
        return pygame.font.Font(path, size)

    @staticmethod
    def _make_gradient_surface(
        size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]
    ) -> pygame.Surface:
        surface = pygame.Surface(size)
        height = max(1, size[1] - 1)
        for y in range(size[1]):
            ratio = y / height
            color = tuple(round(top[channel] * (1 - ratio) + bottom[channel] * ratio) for channel in range(3))
            pygame.draw.line(surface, color, (0, y), (size[0], y))
        return surface

    def _draw_glow(
        self,
        center: tuple[int, int],
        color: tuple[int, int, int],
        radius: int,
        strength: int = 52,
    ) -> None:
        glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for current_radius in range(radius, 4, -6):
            alpha = round(strength * (1 - current_radius / radius) ** 2)
            pygame.draw.circle(glow, (*color, alpha), (radius, radius), current_radius)
        self.screen.blit(glow, (center[0] - radius, center[1] - radius))

    def _draw_background_details(self) -> None:
        """绘制克制的网格、光晕与星点，让所有页面保持统一质感。"""
        self._draw_glow((95, 105), self.GREEN, 180, 25)
        self._draw_glow((WINDOW_WIDTH - 90, WINDOW_HEIGHT - 70), (41, 173, 196), 220, 20)
        for x in range(0, WINDOW_WIDTH, CELL_SIZE):
            pygame.draw.line(self.screen, (14, 38, 47), (x, 0), (x, WINDOW_HEIGHT))
        for y in range(0, WINDOW_HEIGHT, CELL_SIZE):
            pygame.draw.line(self.screen, (14, 38, 47), (0, y), (WINDOW_WIDTH, y))
        sparkle_points = ((92, 52), (344, 116), (693, 72), (954, 126), (870, 693), (44, 637))
        pulse = 1 + (pygame.time.get_ticks() // 360) % 2
        for x, y in sparkle_points:
            pygame.draw.circle(self.screen, self.GREEN_LIGHT, (x, y), pulse)

    def _draw_glass_panel(self, rect: pygame.Rect, radius: int = 16) -> None:
        shadow = pygame.Surface((rect.width + 20, rect.height + 20), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 80), (10, 13, rect.width, rect.height), border_radius=radius)
        self.screen.blit(shadow, (rect.x - 10, rect.y - 10))
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(panel, (*self.PANEL, 224), panel.get_rect(), border_radius=radius)
        pygame.draw.line(panel, (105, 240, 190, 60), (radius, 1), (rect.width - radius, 1), 2)
        pygame.draw.rect(panel, (*self.PANEL_BORDER, 185), panel.get_rect(), 1, border_radius=radius)
        self.screen.blit(panel, rect.topleft)

    def run(self, smoke_frames: int | None = None) -> None:
        frame_count = 0
        while self.running:
            self._handle_events()
            now = pygame.time.get_ticks()
            interval = 1000 / self.state.speed
            if (
                self.mode is ScreenMode.PLAYING
                and not self.state.paused
                and not self.state.game_over
                and now - self.last_move_at >= interval
            ):
                self.state.step()
                self.last_move_at = now
                if self.state.game_over:
                    self._finish_round()

            self._draw()
            pygame.display.flip()
            self.clock.tick(60)

            frame_count += 1
            if smoke_frames is not None and frame_count >= smoke_frames:
                self.running = False

        pygame.quit()

    def _handle_events(self) -> None:
        direction_keys = {
            pygame.K_UP: Direction.UP,
            pygame.K_w: Direction.UP,
            pygame.K_DOWN: Direction.DOWN,
            pygame.K_s: Direction.DOWN,
            pygame.K_LEFT: Direction.LEFT,
            pygame.K_a: Direction.LEFT,
            pygame.K_RIGHT: Direction.RIGHT,
            pygame.K_d: Direction.RIGHT,
        }
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue

            if self.mode is ScreenMode.MENU:
                self._handle_menu_event(event)
            elif self.mode is ScreenMode.INSTRUCTIONS:
                self._handle_instructions_event(event)
            elif self.mode is ScreenMode.SETUP:
                self._handle_setup_event(event)
            elif self.mode is ScreenMode.PLAYING:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._set_mode(ScreenMode.MENU)
                    elif event.key in direction_keys:
                        self.state.set_direction(direction_keys[event.key])
                    elif event.key in (pygame.K_SPACE, pygame.K_p):
                        self.state.toggle_pause()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.pause_button.collidepoint(event.pos):
                        self.state.toggle_pause()
                    elif self.play_menu_button.collidepoint(event.pos):
                        self._set_mode(ScreenMode.MENU)
            elif self.mode is ScreenMode.GAME_OVER:
                self._handle_game_over_event(event)

    def _handle_menu_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_1):
                self._open_setup()
            elif event.key in (pygame.K_i, pygame.K_2):
                self._set_mode(ScreenMode.INSTRUCTIONS)
            elif event.key == pygame.K_ESCAPE:
                self.running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.menu_start_button.collidepoint(event.pos):
                self._open_setup()
            elif self.menu_help_button.collidepoint(event.pos):
                self._set_mode(ScreenMode.INSTRUCTIONS)

    def _handle_instructions_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key in (
            pygame.K_ESCAPE,
            pygame.K_BACKSPACE,
            pygame.K_RETURN,
        ):
            self._set_mode(ScreenMode.MENU)
        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.back_button.collidepoint(event.pos)
        ):
            self._set_mode(ScreenMode.MENU)

    def _handle_setup_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.TEXTINPUT:
            remaining = 12 - len(self.nickname)
            if remaining > 0:
                self.nickname += event.text[:remaining]
                self.setup_error = ""
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._set_mode(ScreenMode.MENU)
            elif event.key == pygame.K_BACKSPACE:
                self.nickname = self.nickname[:-1]
                self.setup_error = ""
            elif event.key in (pygame.K_LEFT, pygame.K_MINUS, pygame.K_KP_MINUS):
                self.state.adjust_base_speed(-1)
            elif event.key in (
                pygame.K_RIGHT,
                pygame.K_PLUS,
                pygame.K_EQUALS,
                pygame.K_KP_PLUS,
            ):
                self.state.adjust_base_speed(1)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._start_new_game()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.speed_minus_button.collidepoint(event.pos):
                self.state.adjust_base_speed(-1)
            elif self.speed_plus_button.collidepoint(event.pos):
                self.state.adjust_base_speed(1)
            elif self.setup_start_button.collidepoint(event.pos):
                self._start_new_game()
            elif self.back_button.collidepoint(event.pos):
                self._set_mode(ScreenMode.MENU)

    def _handle_game_over_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_r, pygame.K_RETURN, pygame.K_KP_ENTER):
                self._replay()
            elif event.key in (pygame.K_ESCAPE, pygame.K_m):
                self._set_mode(ScreenMode.MENU)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.replay_button.collidepoint(event.pos):
                self._replay()
            elif self.gameover_menu_button.collidepoint(event.pos):
                self._set_mode(ScreenMode.MENU)

    def _set_mode(self, mode: ScreenMode) -> None:
        self.mode = mode
        if mode is ScreenMode.SETUP:
            pygame.key.start_text_input()
        else:
            pygame.key.stop_text_input()

    def _open_setup(self) -> None:
        self.nickname = ""
        self.setup_error = ""
        self._set_mode(ScreenMode.SETUP)

    def _start_new_game(self) -> None:
        cleaned_name = self.nickname.strip()[:12]
        if not cleaned_name:
            self.setup_error = "请先输入昵称"
            return
        if self.leaderboard.has_nickname(cleaned_name):
            self.setup_error = "昵称已存在，请更换一个昵称"
            return
        self.nickname = cleaned_name
        self.current_rank = None
        self.round_score = 0
        self.state.reset()
        self.last_move_at = pygame.time.get_ticks()
        self._set_mode(ScreenMode.PLAYING)

    def _replay(self) -> None:
        self.current_rank = None
        self.round_score = 0
        self.state.reset()
        self.last_move_at = pygame.time.get_ticks()
        self._set_mode(ScreenMode.PLAYING)

    def _finish_round(self) -> None:
        self.round_score = self.state.score
        self.current_rank = self.leaderboard.record(self.nickname, self.round_score)
        self.personal_best = self.leaderboard.best_for(self.nickname)
        self._set_mode(ScreenMode.GAME_OVER)

    def _draw(self) -> None:
        self.screen.blit(self.background_surface, (0, 0))
        if self.mode is ScreenMode.MENU:
            self._draw_menu()
            return
        if self.mode is ScreenMode.INSTRUCTIONS:
            self._draw_instructions()
            return
        if self.mode is ScreenMode.SETUP:
            self._draw_setup()
            return

        self._draw_header()
        self._draw_board()
        self._draw_game_sidebar()
        if self.mode is ScreenMode.GAME_OVER:
            self._draw_game_over()
        elif self.state.paused:
            self._draw_overlay("游戏暂停", "按空格或 P 继续")

    def _draw_header(self) -> None:
        self._draw_background_details()
        brand = self.font_tiny.render("FRESH ARCADE", True, self.YELLOW)
        title = self.font_large.render("卡通贪吃蛇", True, self.GREEN_LIGHT)
        subtitle = self.font_tiny.render("吃苹果 · 躲岩石 · 刷新纪录", True, self.MUTED)
        self.screen.blit(brand, (BOARD_X, 22))
        self.screen.blit(title, (BOARD_X, 45))
        self.screen.blit(subtitle, (BOARD_X + 2, 91))

        live_high_score = max(self.leaderboard.high_score, self.state.score)
        chips = [
            (pygame.Rect(400, 27, 174, 78), "本轮得分", str(self.state.score), self.TEXT),
            (pygame.Rect(590, 27, 190, 78), "历史最高", str(live_high_score), self.GREEN_LIGHT),
            (pygame.Rect(796, 27, 216, 78), "当前速度", f"{self.state.speed} / 18", self.YELLOW),
        ]
        for rect, label, value, color in chips:
            self._draw_glass_panel(rect, 17)
            label_surface = self.font_tiny.render(label, True, self.MUTED)
            value_surface = self.font_medium.render(value, True, color)
            self.screen.blit(label_surface, (rect.x + 18, rect.y + 13))
            self.screen.blit(value_surface, (rect.x + 18, rect.y + 37))
        pygame.draw.line(
            self.screen,
            (39, 91, 93),
            (BOARD_X, HEADER_HEIGHT - 18),
            (WINDOW_WIDTH - BOARD_X, HEADER_HEIGHT - 18),
        )

    def _draw_board(self) -> None:
        board = pygame.Rect(BOARD_X, HEADER_HEIGHT, BOARD_WIDTH, BOARD_HEIGHT)
        shadow = pygame.Rect(board.x + 5, board.y + 8, board.width, board.height)
        pygame.draw.rect(self.screen, (2, 10, 15), shadow, border_radius=20)
        pygame.draw.rect(self.screen, self.PANEL_BORDER, board.inflate(8, 8), border_radius=22)
        self.screen.blit(self.board_surface, board.topleft)
        for x in range(BOARD_X, BOARD_X + BOARD_WIDTH + 1, CELL_SIZE):
            pygame.draw.line(self.screen, self.GRID, (x, HEADER_HEIGHT), (x, HEADER_HEIGHT + BOARD_HEIGHT))
        for y in range(HEADER_HEIGHT, HEADER_HEIGHT + BOARD_HEIGHT + 1, CELL_SIZE):
            pygame.draw.line(self.screen, self.GRID, (BOARD_X, y), (BOARD_X + BOARD_WIDTH, y))
        pygame.draw.rect(self.screen, self.GREEN_DARK, board, 2, border_radius=16)

        for obstacle in self.state.obstacles:
            self._draw_obstacle(obstacle)

        if self.state.food is not None:
            self._draw_apple(self.state.food)

        self._draw_snake()

    def _draw_game_sidebar(self) -> None:
        player_card = pygame.Rect(SIDEBAR_X, HEADER_HEIGHT, SIDEBAR_WIDTH, 92)
        controls_card = pygame.Rect(SIDEBAR_X, 264, SIDEBAR_WIDTH, 286)
        actions_card = pygame.Rect(SIDEBAR_X, 562, SIDEBAR_WIDTH, 112)
        for card in (player_card, controls_card, actions_card):
            self._draw_glass_panel(card, 18)

        avatar = (player_card.x + 42, player_card.centery)
        pygame.draw.circle(self.screen, self.GREEN_DARK, avatar, 24)
        pygame.draw.circle(self.screen, self.GREEN_HEAD, avatar, 19)
        pygame.draw.circle(self.screen, self.CREAM, (avatar[0] - 6, avatar[1] - 4), 4)
        pygame.draw.circle(self.screen, self.CREAM, (avatar[0] + 6, avatar[1] - 4), 4)
        pygame.draw.circle(self.screen, self.INK, (avatar[0] - 5, avatar[1] - 4), 2)
        pygame.draw.circle(self.screen, self.INK, (avatar[0] + 7, avatar[1] - 4), 2)
        nickname_label = self.font_tiny.render("当前玩家", True, self.MUTED)
        nickname = self.font_medium.render(self.nickname or "玩家", True, self.TEXT)
        self.screen.blit(nickname_label, (player_card.x + 80, player_card.y + 21))
        self.screen.blit(nickname, (player_card.x + 80, player_card.y + 43))

        label = self.font_tiny.render("方向控制", True, self.MUTED)
        self.screen.blit(label, (controls_card.x + 20, controls_card.y + 18))
        key_size = 54
        key_gap = 9
        center_x = controls_card.centerx
        key_positions = [
            (pygame.Rect(center_x - key_size // 2, controls_card.y + 54, key_size, key_size), "W", "↑"),
            (pygame.Rect(center_x - key_size - key_gap, controls_card.y + 117, key_size, key_size), "A", "←"),
            (pygame.Rect(center_x - key_size // 2, controls_card.y + 117, key_size, key_size), "S", "↓"),
            (pygame.Rect(center_x + key_gap, controls_card.y + 117, key_size, key_size), "D", "→"),
        ]
        for rect, letter, arrow in key_positions:
            pygame.draw.rect(self.screen, (7, 27, 35), rect.move(0, 3), border_radius=13)
            pygame.draw.rect(self.screen, (31, 64, 72), rect, border_radius=13)
            pygame.draw.rect(self.screen, (67, 112, 116), rect, 1, border_radius=13)
            letter_surface = self.font_tiny.render(letter, True, self.MUTED)
            arrow_surface = self.font_medium.render(arrow, True, self.GREEN_LIGHT)
            self.screen.blit(letter_surface, (rect.x + 8, rect.y + 5))
            self.screen.blit(arrow_surface, (rect.centerx - arrow_surface.get_width() // 2, rect.y + 21))
        tips = ["方向键或 WASD 移动", "空格 / P 暂停", "Esc 返回主菜单"]
        for index, tip in enumerate(tips):
            surface = self.font_tiny.render(tip, True, self.MUTED)
            self.screen.blit(surface, (controls_card.x + 24, controls_card.y + 194 + index * 25))

        self._draw_button(self.pause_button, "继续游戏" if self.state.paused else "暂停游戏", accent=self.state.paused)
        menu_text = self.font_tiny.render("退出本轮并返回主菜单", True, self.MUTED)
        if self.play_menu_button.collidepoint(pygame.mouse.get_pos()):
            menu_text = self.font_tiny.render("退出本轮并返回主菜单", True, self.TEXT)
        self.screen.blit(menu_text, (self.play_menu_button.centerx - menu_text.get_width() // 2, self.play_menu_button.y + 8))

    def _draw_snake(self) -> None:
        """绘制连贯、渐细并带有拟人面部的卡通蛇。"""
        snake = self.state.snake
        centers = [self._cell_center(segment) for segment in snake]

        # 阴影和身体连接线让方格移动看起来仍像一条完整的蛇。
        for shadow in (True, False):
            offset = (2, 3) if shadow else (0, 0)
            color = (12, 54, 38) if shadow else self.GREEN_DARK
            for index in range(len(centers) - 1):
                start = (centers[index][0] + offset[0], centers[index][1] + offset[1])
                end = (centers[index + 1][0] + offset[0], centers[index + 1][1] + offset[1])
                width = max(8, 19 - index // 2)
                pygame.draw.line(self.screen, color, start, end, width)

        # 从尾部往头部画，身体越靠近尾巴越细。
        snake_length = max(1, len(snake) - 1)
        for index in range(len(snake) - 1, 0, -1):
            center = centers[index]
            taper = index / snake_length
            radius = max(6, round(10 - taper * 3))
            shade = (
                max(35, self.GREEN[0] - index * 2),
                max(145, self.GREEN[1] - index * 2),
                max(75, self.GREEN[2] - index),
            )
            pygame.draw.circle(self.screen, (11, 65, 43), (center[0] + 2, center[1] + 3), radius)
            pygame.draw.circle(self.screen, shade, center, radius)
            pygame.draw.circle(self.screen, self.GREEN_LIGHT, (center[0] - 3, center[1] - 3), 2)
            if index % 2 == 0:
                pygame.draw.circle(self.screen, self.GREEN_DARK, (center[0] + 3, center[1] + 3), 2)

        self._draw_tail(centers)
        self._draw_head(centers[0])

    def _draw_tail(self, centers: list[tuple[int, int]]) -> None:
        if len(centers) < 2:
            return
        tail_x, tail_y = centers[-1]
        previous_x, previous_y = centers[-2]
        dx = 0 if tail_x == previous_x else (1 if tail_x > previous_x else -1)
        dy = 0 if tail_y == previous_y else (1 if tail_y > previous_y else -1)
        side_x, side_y = -dy, dx
        tip = (tail_x + dx * 11, tail_y + dy * 11)
        base = (tail_x - dx * 3, tail_y - dy * 3)
        points = [
            tip,
            (base[0] + side_x * 6, base[1] + side_y * 6),
            (base[0] - side_x * 6, base[1] - side_y * 6),
        ]
        pygame.draw.polygon(self.screen, self.GREEN, points)
        pygame.draw.circle(self.screen, self.GREEN_LIGHT, (tail_x - 2, tail_y - 2), 2)

    def _draw_head(self, center: tuple[int, int]) -> None:
        cx, cy = center
        dx, dy = self.state.direction.value
        side_x, side_y = -dy, dx
        head_center = (cx + dx * 2, cy + dy * 2)
        if dx:
            head_rect = pygame.Rect(0, 0, 31, 25)
        else:
            head_rect = pygame.Rect(0, 0, 25, 31)
        head_rect.center = head_center

        shadow_rect = head_rect.move(2, 3)
        pygame.draw.ellipse(self.screen, (11, 65, 43), shadow_rect)
        pygame.draw.ellipse(self.screen, self.GREEN_DARK, head_rect.inflate(2, 2))
        pygame.draw.ellipse(self.screen, self.GREEN_HEAD, head_rect)
        highlight = (head_center[0] - dx * 3 - 4, head_center[1] - dy * 3 - 4)
        pygame.draw.circle(self.screen, self.GREEN_LIGHT, highlight, 3)

        # 两只奶白色大眼睛会朝移动方向看。
        eye_centers: list[tuple[int, int]] = []
        for side in (-1, 1):
            eye = (
                head_center[0] + dx * 5 + side_x * side * 6,
                head_center[1] + dy * 5 + side_y * side * 6,
            )
            eye_centers.append(eye)
            pygame.draw.circle(self.screen, self.INK, eye, 6)
            pygame.draw.circle(self.screen, self.CREAM, eye, 5)
            pupil = (eye[0] + dx * 2, eye[1] + dy * 2)
            pygame.draw.circle(self.screen, self.INK, pupil, 2)
            pygame.draw.circle(self.screen, (255, 255, 255), (pupil[0] - 1, pupil[1] - 1), 1)

            # 微微上扬的眉毛强化表情。
            brow_center = (eye[0] - dx * 5, eye[1] - dy * 5)
            pygame.draw.line(
                self.screen,
                self.INK,
                (brow_center[0] - side_x * 3, brow_center[1] - side_y * 3),
                (brow_center[0] + side_x * 3, brow_center[1] + side_y * 3),
                2,
            )

        # 腮红和笑脸。
        for side in (-1, 1):
            cheek = (
                head_center[0] + dx * 8 + side_x * side * 9,
                head_center[1] + dy * 8 + side_y * side * 9,
            )
            pygame.draw.circle(self.screen, self.BLUSH, cheek, 2)

        mouth_center = (head_center[0] + dx * 10, head_center[1] + dy * 10)
        smile = [
            (mouth_center[0] - side_x * 3, mouth_center[1] - side_y * 3),
            (mouth_center[0] + dx * 2, mouth_center[1] + dy * 2),
            (mouth_center[0] + side_x * 3, mouth_center[1] + side_y * 3),
        ]
        pygame.draw.lines(self.screen, self.INK, False, smile, 2)

        # 舌头间歇伸出，形成轻微动画。
        if (pygame.time.get_ticks() // 420) % 4 == 0 and not self.state.paused:
            tongue_start = (head_center[0] + dx * 13, head_center[1] + dy * 13)
            tongue_end = (tongue_start[0] + dx * 8, tongue_start[1] + dy * 8)
            pygame.draw.line(self.screen, self.RED, tongue_start, tongue_end, 2)
            for side in (-1, 1):
                fork = (
                    tongue_end[0] + dx * 4 + side_x * side * 3,
                    tongue_end[1] + dy * 4 + side_y * side * 3,
                )
                pygame.draw.line(self.screen, self.RED, tongue_end, fork, 2)

    def _draw_apple(self, position: Position) -> None:
        cx, cy = self._cell_center(position)
        pygame.draw.circle(self.screen, (94, 27, 38), (cx + 2, cy + 3), 10)
        pygame.draw.circle(self.screen, self.RED, (cx, cy + 1), 9)
        pygame.draw.circle(self.screen, (255, 148, 158), (cx - 3, cy - 2), 3)
        pygame.draw.line(self.screen, (111, 72, 42), (cx, cy - 7), (cx + 2, cy - 13), 3)
        leaf = pygame.Rect(cx + 1, cy - 13, 10, 6)
        pygame.draw.ellipse(self.screen, self.GREEN_LIGHT, leaf)

    def _draw_obstacle(self, position: Position) -> None:
        """把障碍画成有高光和裂纹的小岩石。"""
        cx, cy = self._cell_center(position)
        shadow = pygame.Rect(0, 0, 22, 16)
        shadow.center = (cx + 2, cy + 5)
        pygame.draw.ellipse(self.screen, (11, 16, 23), shadow)

        rock_points = [
            (cx - 10, cy + 6),
            (cx - 8, cy - 5),
            (cx - 3, cy - 10),
            (cx + 6, cy - 8),
            (cx + 10, cy - 1),
            (cx + 8, cy + 8),
            (cx - 4, cy + 9),
        ]
        pygame.draw.polygon(self.screen, self.ROCK_DARK, rock_points)
        inner_points = [(x, y - 2) for x, y in rock_points[:-1]] + [(rock_points[-1][0], rock_points[-1][1] - 1)]
        pygame.draw.polygon(self.screen, self.ROCK, inner_points)
        pygame.draw.line(self.screen, self.ROCK_LIGHT, (cx - 5, cy - 6), (cx + 3, cy - 7), 3)
        pygame.draw.lines(
            self.screen,
            self.ROCK_DARK,
            False,
            [(cx + 2, cy - 5), (cx - 1, cy), (cx + 4, cy + 4)],
            2,
        )

    @staticmethod
    def _cell_center(position: Position) -> tuple[int, int]:
        return (
            BOARD_X + position.x * CELL_SIZE + CELL_SIZE // 2,
            HEADER_HEIGHT + position.y * CELL_SIZE + CELL_SIZE // 2,
        )

    @staticmethod
    def _cell_rect(position: Position, inset: int = 0) -> pygame.Rect:
        return pygame.Rect(
            BOARD_X + position.x * CELL_SIZE + inset,
            HEADER_HEIGHT + position.y * CELL_SIZE + inset,
            CELL_SIZE - inset * 2,
            CELL_SIZE - inset * 2,
        )

    def _draw_overlay(self, title: str, subtitle: str) -> None:
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT - HEADER_HEIGHT), pygame.SRCALPHA)
        overlay.fill((7, 10, 16, 205))
        self.screen.blit(overlay, (0, HEADER_HEIGHT))
        title_surface = self.font_large.render(title, True, self.TEXT)
        subtitle_surface = self.font_medium.render(subtitle, True, self.YELLOW)
        center_y = HEADER_HEIGHT + (WINDOW_HEIGHT - HEADER_HEIGHT) // 2
        self.screen.blit(title_surface, ((WINDOW_WIDTH - title_surface.get_width()) // 2, center_y - 55))
        self.screen.blit(
            subtitle_surface,
            ((WINDOW_WIDTH - subtitle_surface.get_width()) // 2, center_y + 5),
        )

    def _draw_menu(self) -> None:
        self.screen.blit(self.background_surface, (0, 0))
        self._draw_background_details()
        hero = pygame.Rect(170, 48, WINDOW_WIDTH - 340, 610)
        self._draw_glass_panel(hero, 28)

        brand = self.font_tiny.render("FRESH ARCADE · DESKTOP EDITION", True, self.YELLOW)
        brand_rect = pygame.Rect(WINDOW_WIDTH // 2 - brand.get_width() // 2 - 15, 76, brand.get_width() + 30, 30)
        pygame.draw.rect(self.screen, (18, 55, 58), brand_rect, border_radius=15)
        pygame.draw.rect(self.screen, (57, 113, 105), brand_rect, 1, border_radius=15)
        self.screen.blit(brand, (brand_rect.centerx - brand.get_width() // 2, brand_rect.centery - brand.get_height() // 2))

        title = self.font_hero.render("卡通贪吃蛇", True, self.GREEN_LIGHT)
        subtitle = self.font_small.render("吃苹果 · 躲岩石 · 冲击好友排行榜", True, self.MUTED)
        self._blit_centered(title, 116)
        self._blit_centered(subtitle, 181)
        self._draw_menu_mascot((WINDOW_WIDTH // 2, 286))

        high_card = pygame.Rect(WINDOW_WIDTH // 2 - 116, 376, 232, 58)
        pygame.draw.rect(self.screen, (8, 31, 38), high_card, border_radius=18)
        pygame.draw.rect(self.screen, (52, 106, 103), high_card, 1, border_radius=18)
        high_label = self.font_tiny.render("历史最高分", True, self.MUTED)
        high_value = self.font_medium.render(str(self.leaderboard.high_score), True, self.YELLOW)
        self.screen.blit(high_label, (high_card.x + 22, high_card.y + 20))
        self.screen.blit(high_value, (high_card.right - 22 - high_value.get_width(), high_card.y + 15))
        self._draw_button(self.menu_start_button, "开始新游戏", accent=True)
        self._draw_button(self.menu_help_button, "游戏说明")
        tip = self.font_tiny.render("回车开始 · I 查看说明 · Esc 退出", True, self.MUTED)
        self._blit_centered(tip, 612)

    def _draw_menu_mascot(self, center: tuple[int, int]) -> None:
        """绘制菜单专用的盘绕蛇吉祥物，不依赖棋盘坐标。"""
        cx, cy = center
        self._draw_glow(center, self.GREEN, 116, 52)
        body_points = [(cx - 92, cy + 28), (cx - 48, cy + 54), (cx + 10, cy + 48), (cx + 59, cy + 24)]
        pygame.draw.lines(self.screen, (5, 35, 31), False, [(x + 3, y + 6) for x, y in body_points], 35)
        pygame.draw.lines(self.screen, self.GREEN_DARK, False, body_points, 32)
        pygame.draw.lines(self.screen, self.GREEN, False, body_points, 23)
        for index, point in enumerate(body_points[:-1]):
            pygame.draw.circle(self.screen, self.GREEN_LIGHT, (point[0] - 5, point[1] - 5), 3)
            if index % 2 == 0:
                pygame.draw.circle(self.screen, (17, 141, 104), (point[0] + 6, point[1] + 5), 3)
        head = (cx + 72, cy + 8)
        pygame.draw.ellipse(self.screen, (5, 35, 31), pygame.Rect(head[0] - 27 + 3, head[1] - 25 + 5, 54, 50))
        pygame.draw.ellipse(self.screen, self.GREEN_DARK, pygame.Rect(head[0] - 29, head[1] - 27, 58, 54))
        pygame.draw.ellipse(self.screen, self.GREEN_HEAD, pygame.Rect(head[0] - 27, head[1] - 25, 54, 50))
        for eye_x in (head[0] + 3, head[0] + 17):
            pygame.draw.circle(self.screen, self.CREAM, (eye_x, head[1] - 9), 8)
            pygame.draw.circle(self.screen, self.INK, (eye_x + 2, head[1] - 8), 4)
            pygame.draw.circle(self.screen, (255, 255, 255), (eye_x + 1, head[1] - 10), 1)
        pygame.draw.arc(self.screen, self.INK, pygame.Rect(head[0] + 1, head[1] - 1, 22, 17), 0.15, 2.6, 2)
        pygame.draw.line(self.screen, self.RED, (head[0] + 27, head[1] + 8), (head[0] + 42, head[1] + 9), 3)
        pygame.draw.line(self.screen, self.RED, (head[0] + 42, head[1] + 9), (head[0] + 48, head[1] + 4), 2)
        pygame.draw.line(self.screen, self.RED, (head[0] + 42, head[1] + 9), (head[0] + 48, head[1] + 14), 2)
        self._draw_apple_at((cx - 126, cy - 4), 15)

    def _draw_apple_at(self, center: tuple[int, int], radius: int) -> None:
        cx, cy = center
        pygame.draw.circle(self.screen, (76, 20, 34), (cx + 3, cy + 5), radius)
        pygame.draw.circle(self.screen, self.RED, center, radius)
        pygame.draw.circle(self.screen, (255, 169, 175), (cx - 5, cy - 5), max(2, radius // 4))
        pygame.draw.line(self.screen, (111, 72, 42), (cx, cy - radius + 2), (cx + 3, cy - radius - 9), 4)
        pygame.draw.ellipse(self.screen, self.GREEN_LIGHT, pygame.Rect(cx + 1, cy - radius - 9, 16, 8))

    def _draw_instructions(self) -> None:
        self.screen.blit(self.background_surface, (0, 0))
        self._draw_background_details()
        panel = pygame.Rect(140, 46, WINDOW_WIDTH - 280, 630)
        self._draw_glass_panel(panel, 26)
        eyebrow = self.font_tiny.render("HOW TO PLAY", True, self.YELLOW)
        title = self.font_title.render("游戏说明", True, self.GREEN_LIGHT)
        self._blit_centered(eyebrow, 76)
        self._blit_centered(title, 105)
        subtitle = self.font_small.render("掌握规则，刷新你的最高纪录", True, self.MUTED)
        self._blit_centered(subtitle, 160)

        rules = [
            "1. 输入未被使用的昵称，并选择 1–18 的初始速度。",
            "2. 用方向键或 WASD 移动；蛇不能直接反向行驶。",
            "3. 吃到一个苹果得 1 分，蛇身同时增长一格。",
            "4. 每获得 3 分，速度提高一级；最高速度为 18。",
            "5. 每局随机出现 14 块岩石，出生点附近不会生成岩石。",
            "6. 撞到边界、岩石或自身，都会立即结束本轮游戏。",
            "7. 空格或 P 暂停/继续；游戏中按 Esc 可退出。",
            "8. 成绩保存在本地；结束后显示排行榜和本轮名次。",
        ]
        for index, rule in enumerate(rules):
            column = index % 2
            row = index // 2
            card = pygame.Rect(174 + column * 350, 208 + row * 87, 330, 68)
            pygame.draw.rect(self.screen, (8, 29, 37), card, border_radius=14)
            pygame.draw.rect(self.screen, (43, 84, 89), card, 1, border_radius=14)
            badge = (card.x + 28, card.centery)
            pygame.draw.circle(self.screen, self.GREEN_DARK, badge, 17)
            number = self.font_tiny.render(str(index + 1), True, self.CREAM)
            self.screen.blit(number, (badge[0] - number.get_width() // 2, badge[1] - number.get_height() // 2))
            clean_rule = rule.split(". ", 1)[-1]
            surface = self.font_tiny.render(clean_rule, True, self.TEXT)
            self.screen.blit(surface, (card.x + 56, card.y + 24))

        self._draw_button(self.back_button, "返回")
        hint = self.font_tiny.render("Esc / Backspace / 回车也可返回", True, self.MUTED)
        self.screen.blit(hint, (self.back_button.right + 20, self.back_button.centery - hint.get_height() // 2))

    def _draw_setup(self) -> None:
        self.screen.blit(self.background_surface, (0, 0))
        self._draw_background_details()
        self._draw_glass_panel(pygame.Rect(205, 46, WINDOW_WIDTH - 410, 630), 26)
        eyebrow = self.font_tiny.render("NEW GAME", True, self.YELLOW)
        title = self.font_title.render("准备出发", True, self.GREEN_LIGHT)
        subtitle = self.font_small.render("设置本轮玩家信息", True, self.MUTED)
        self._blit_centered(eyebrow, 78)
        self._blit_centered(title, 108)
        self._blit_centered(subtitle, 161)

        nickname_label = self.font_small.render("玩家昵称（最多 12 个字符，不可与榜单重复）", True, self.TEXT)
        self.screen.blit(nickname_label, (self.nickname_box.left, self.nickname_box.top - 30))
        pygame.draw.rect(self.screen, (9, 29, 37), self.nickname_box, border_radius=10)
        pygame.draw.rect(
            self.screen,
            self.GREEN_LIGHT if self.nickname else self.PANEL_BORDER,
            self.nickname_box,
            2,
            border_radius=10,
        )
        cursor = "|" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
        shown_name = self.nickname + cursor if self.nickname else "请输入昵称" + cursor
        name_color = self.TEXT if self.nickname else self.MUTED
        name_surface = self.font_medium.render(shown_name, True, name_color)
        self.screen.blit(name_surface, (self.nickname_box.left + 16, self.nickname_box.top + 12))

        speed_label = self.font_small.render("选择初始速度", True, self.TEXT)
        self._blit_centered(speed_label, 336)
        self._draw_button(self.speed_minus_button, "-")
        self._draw_button(self.speed_plus_button, "+")
        speed = self.font_large.render(str(self.state.base_speed), True, self.YELLOW)
        self._blit_centered(speed, 382)
        dots_y = 457
        for value in range(1, 19):
            x = WINDOW_WIDTH // 2 - 153 + (value - 1) * 18
            color = self.GREEN_LIGHT if value <= self.state.base_speed else (48, 79, 84)
            pygame.draw.circle(self.screen, color, (x, dots_y), 4 if value == self.state.base_speed else 3)
        rule = self.font_tiny.render("左右键 / + - 调节 · 每 3 分速度 +1 · 最高 18", True, self.MUTED)
        self._blit_centered(rule, 475)

        self._draw_button(self.setup_start_button, "进入游戏", accent=True)
        self._draw_button(self.back_button, "返回")
        if self.setup_error:
            error = self.font_small.render(self.setup_error, True, self.RED)
            self._blit_centered(error, 584)

    def _draw_game_over(self) -> None:
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((3, 12, 18, 225))
        self.screen.blit(overlay, (0, 0))
        self._draw_glow((WINDOW_WIDTH // 2, 250), self.GREEN, 260, 32)
        panel = pygame.Rect(132, 36, WINDOW_WIDTH - 264, 646)
        self._draw_glass_panel(panel, 26)

        eyebrow = self.font_tiny.render("ROUND COMPLETE", True, self.YELLOW)
        title = self.font_title.render("本轮结束", True, self.TEXT)
        self._blit_centered(eyebrow, 62)
        self._blit_centered(title, 90)

        cards = [
            (pygame.Rect(170, 151, 210, 78), "玩家", self.nickname, self.TEXT),
            (pygame.Rect(415, 151, 210, 78), "本轮得分", str(self.round_score), self.YELLOW),
            (pygame.Rect(660, 151, 210, 78), "排行榜", f"第 {self.current_rank} 名", self.GREEN_LIGHT),
        ]
        for rect, label, value, color in cards:
            pygame.draw.rect(self.screen, (8, 29, 37), rect, border_radius=16)
            pygame.draw.rect(self.screen, (48, 94, 96), rect, 1, border_radius=16)
            label_surface = self.font_tiny.render(label, True, self.MUTED)
            value_surface = self.font_medium.render(value, True, color)
            self.screen.blit(label_surface, (rect.x + 17, rect.y + 12))
            self.screen.blit(value_surface, (rect.x + 17, rect.y + 37))

        personal = self.font_small.render(f"个人最佳  {self.personal_best}", True, self.GREEN_LIGHT)
        ranking_title = self.font_medium.render("排行榜", True, self.TEXT)
        self.screen.blit(ranking_title, (170, 256))
        self.screen.blit(personal, (870 - personal.get_width(), 261))

        header_y = 305
        rank_header = self.font_tiny.render("名次", True, self.MUTED)
        name_header = self.font_tiny.render("玩家", True, self.MUTED)
        score_header = self.font_tiny.render("最高得分", True, self.MUTED)
        self.screen.blit(rank_header, (190, header_y))
        self.screen.blit(name_header, (430, header_y))
        self.screen.blit(score_header, (765, header_y))
        pygame.draw.line(self.screen, self.PANEL_BORDER, (170, 332), (870, 332))

        top_entries = self.leaderboard.top(7)
        rows: list[tuple[int, str, int]] = [
            (index, str(entry["nickname"]), int(entry["score"]))
            for index, entry in enumerate(top_entries, start=1)
        ]
        if self.current_rank is not None and self.current_rank > 7:
            rows = rows[:6] + [(self.current_rank, self.nickname, self.personal_best)]

        for row_index, (rank, name, score) in enumerate(rows):
            y = 345 + row_index * 34
            is_current = rank == self.current_rank
            if is_current:
                highlight = pygame.Rect(170, y - 5, 700, 31)
                pygame.draw.rect(self.screen, (23, 99, 75), highlight, border_radius=7)
                pygame.draw.rect(self.screen, (70, 205, 153), highlight, 1, border_radius=7)
            color = self.YELLOW if rank == 1 else (self.GREEN_LIGHT if is_current else self.TEXT)
            self.screen.blit(self.font_small.render(str(rank), True, color), (198, y))
            self.screen.blit(self.font_small.render(name, True, color), (430, y))
            score_surface = self.font_small.render(str(score), True, color)
            self.screen.blit(score_surface, (828 - score_surface.get_width(), y))

        self._draw_button(self.replay_button, "再玩一局", accent=True)
        self._draw_button(self.gameover_menu_button, "返回主菜单")

    def _draw_button(self, rect: pygame.Rect, label: str, accent: bool = False) -> None:
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        if accent:
            color = self.GREEN_LIGHT if hovered else self.GREEN
            text_color = self.INK
        else:
            color = (55, 67, 84) if hovered else (39, 49, 64)
            text_color = self.TEXT
        if accent and hovered:
            glow = pygame.Surface((rect.width + 20, rect.height + 20), pygame.SRCALPHA)
            pygame.draw.rect(glow, (35, 203, 151, 42), glow.get_rect(), border_radius=17)
            self.screen.blit(glow, (rect.x - 10, rect.y - 10))
        pygame.draw.rect(self.screen, (3, 12, 17), rect.move(0, 4), border_radius=11)
        pygame.draw.rect(self.screen, color, rect, border_radius=11)
        pygame.draw.rect(self.screen, self.GREEN_DARK if accent else self.GRID, rect, 2, border_radius=11)
        pygame.draw.line(
            self.screen,
            (138, 255, 210) if accent else (82, 108, 117),
            (rect.left + 14, rect.top + 2),
            (rect.right - 14, rect.top + 2),
            1,
        )
        text_surface = self.font_medium.render(label, True, text_color)
        self.screen.blit(
            text_surface,
            (rect.centerx - text_surface.get_width() // 2, rect.centery - text_surface.get_height() // 2),
        )

    def _blit_centered(self, surface: pygame.Surface, y: int) -> None:
        self.screen.blit(surface, ((WINDOW_WIDTH - surface.get_width()) // 2, y))


def main() -> None:
    parser = argparse.ArgumentParser(description="中文贪吃蛇游戏")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="无交互启动若干帧后退出，用于自动检查",
    )
    args = parser.parse_args()
    SnakeGame().run(smoke_frames=5 if args.smoke_test else None)


if __name__ == "__main__":
    main()
