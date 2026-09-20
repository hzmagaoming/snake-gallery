"""Cached cover artwork and light animation for the entry screens."""

import math
import warnings
from pathlib import Path

import pygame

from config import BOARD_SIZE, CELL_SIZE, WINDOW_HEIGHT, WINDOW_WIDTH
from map_art import curve


class EntryArt:
    def __init__(self, map_art):
        self.cover = None
        cover_path = Path(__file__).resolve().parent / "assets" / "images" / "menu_cover.png"
        try:
            image = pygame.image.load(str(cover_path)).convert_alpha()
            self.cover = pygame.transform.smoothscale(image, (WINDOW_WIDTH, WINDOW_HEIGHT))
        except (OSError, pygame.error) as error:
            warnings.warn(f"Cover illustration unavailable; using drawn fallback: {error}", RuntimeWarning)
            self.scene = self.make_scene()
            self.vehicle = self.make_vehicle()
        self.images = {}
        for kind, size in (("tent", 120),
                           ("person", 86), ("transport", 105), ("rubble", 90)):
            self.images[(kind, size)] = pygame.transform.smoothscale(map_art.sprites[kind], (size, size))
        self.legend = (
            ("supply", "应急物资", "纸箱与胶带", "送到安置点结算"),
            ("medical", "医疗包", "米白包体、红十字", "获得后短时扫描"),
            ("battery", "通讯电池", "蓝灰箱体、闪电", "获得后清除一处障碍"),
            ("eagle", "求是鹰支援", "金黄箱体、鹰标", "限时清障与护航"),
            ("rubble", "危险障碍", "碎石、倒木、路障", "避开，不要碰撞"),
            ("water", "危险积水", "蓝灰水面与波纹", "避开积水区域"),
        )
        for kind, *_ in self.legend:
            if kind != "water":
                self.images[(kind, 76)] = pygame.transform.smoothscale(map_art.sprites[kind], (76, 76))
        preview = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
        map_art.water(preview, ((0, 0), (1, 0), (0, 1)), (0, 0))
        self.images[("water", 76)] = pygame.transform.smoothscale(
            preview.subsurface((0, 0, CELL_SIZE * 2, CELL_SIZE * 2)), (76, 76))
        self.cloud = pygame.Surface((168, 50), pygame.SRCALPHA)
        points = curve([(3, 35), (23, 24), (40, 25), (56, 9), (78, 7),
                        (99, 24), (124, 20), (147, 29), (164, 37)])
        pygame.draw.polygon(self.cloud, (247, 247, 228, 175), [*points, (160, 43), (6, 43)])
        self.shade = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        self.shade.fill((57, 73, 61, 48))

    def make_scene(self):
        surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        surface.fill((231, 235, 218, 255))
        horizon = curve([(0, 357), (168, 290), (340, 334), (518, 258),
                         (717, 319), (894, 259), (1100, 292)])
        pygame.draw.polygon(surface, (204, 216, 203), [*horizon, (1100, 720), (0, 720)])
        hillside = curve([(0, 441), (191, 368), (382, 426), (606, 356), (838, 385), (1100, 336)])
        pygame.draw.polygon(surface, (216, 225, 206), [*hillside, (1100, 720), (0, 720)])
        district = [(779, 292), (779, 264), (805, 264), (811, 252), (833, 263),
                    (833, 281), (859, 281), (859, 244), (877, 244), (893, 265),
                    (914, 258), (946, 265), (946, 286), (997, 286), (997, 304)]
        pygame.draw.polygon(surface, (192, 205, 192), district)
        river = curve([(1100, 380), (1012, 433), (926, 478), (914, 574), (995, 720)])
        pygame.draw.lines(surface, (210, 223, 217), False, river, 94)
        pygame.draw.lines(surface, (202, 220, 220), False, river, 58)
        road = curve([(-50, 700), (184, 563), (385, 543), (634, 447), (802, 355), (911, 297)])
        for inset, color in ((0, (213, 213, 197)), (3, (235, 229, 210))):
            left, right = [], []
            for i, (x, y) in enumerate(road):
                a, b = road[max(0, i - 1)], road[min(len(road) - 1, i + 1)]
                dx, dy = b[0] - a[0], b[1] - a[1]
                length = max(1, math.hypot(dx, dy))
                width = 87 * (1 - i / (len(road) - 1)) + 4 - inset
                left.append((x - dy / length * width, y + dx / length * width))
                right.append((x + dy / length * width, y - dx / length * width))
            pygame.draw.polygon(surface, color, left + right[::-1])
        pygame.draw.lines(surface, (224, 218, 200), False, road, 1)
        # Sparse pencil marks follow terrain margins rather than filling the cover.
        for i in range(18):
            x, y = 35 + i * 34, 665 + (i * 11) % 35
            pygame.draw.line(surface, (202, 213, 187), (x, y), (x + 10, y - 2), 1)
        return surface.convert_alpha()

    def make_vehicle(self):
        # Supersampled original illustration: shared ink, glazing and rescue markings,
        # without the map sprite's enlarged sticker rim.
        surface = pygame.Surface((840, 420), pygame.SRCALPHA)
        ink = (66, 70, 56)
        def shape(points, color, width=2):
            points = [(x * 2, y * 2) for x, y in points]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.lines(surface, ink, True, points, width * 2)
        def line(points, color=ink, width=2):
            pygame.draw.lines(surface, color, False, [(x * 2, y * 2) for x, y in points], width * 2)
        pygame.draw.ellipse(surface, (93, 98, 77, 33), (80, 345, 692, 40))
        shape([(34, 64), (52, 46), (243, 48), (278, 68), (325, 72),
               (365, 122), (368, 161), (43, 165), (29, 147)], (222, 104, 73), 3)
        shape([(49, 62), (233, 62), (250, 81), (250, 139), (45, 139)], (244, 236, 211), 2)
        shape([(271, 81), (315, 83), (344, 121), (272, 121)], (106, 165, 173), 2)
        line([(282, 87), (286, 114)], (188, 218, 212), 4)
        line([(325, 92), (340, 115)], (188, 218, 212), 3)
        line([(260, 82), (260, 144)], width=2)
        line([(280, 133), (296, 133)], width=3)
        shape([(98, 73), (122, 73), (122, 89), (139, 89), (139, 111),
               (122, 111), (122, 128), (99, 128), (99, 111), (82, 111), (82, 89), (98, 89)], (210, 73, 57), 1)
        line([(51, 151), (351, 149)], (178, 77, 57), 3)
        shape([(244, 42), (281, 43), (283, 54), (242, 54)], (155, 176, 171), 2)
        line([(246, 46), (261, 46)], (217, 89, 65), 4)
        for x in (87, 312):
            pygame.draw.circle(surface, ink, (x * 2, 164 * 2), 29 * 2)
            pygame.draw.circle(surface, (166, 171, 153), (x * 2, 164 * 2), 14 * 2)
            pygame.draw.circle(surface, (217, 217, 195), (x * 2, 164 * 2), 5 * 2)
            pygame.draw.arc(surface, (102, 113, 91), ((x - 26) * 2, 138 * 2, 52 * 2, 52 * 2), .15, 2.9, 3)
        shape([(345, 132), (360, 133), (361, 143), (347, 144)], (245, 224, 161), 1)
        line([(333, 162), (379, 160)], width=5)
        line([(31, 161), (55, 161)], width=4)
        return pygame.transform.smoothscale(surface, (420, 210))

    def image(self, target, kind, size, center):
        image = self.images[(kind, size)]
        target.blit(image, (round(center[0] - size / 2), round(center[1] - size / 2)))

    def draw_scene(self, target, animated=True):
        if self.cover is not None:
            target.blit(self.cover, (0, 0))
            return
        target.blit(self.scene, (0, 0))
        seconds = pygame.time.get_ticks() / 1000 if animated else 0
        for x, y, phase in ((624, 122, 0), (907, 172, 1.4)):
            target.blit(self.cloud, (round(x + 10 * math.sin(seconds / 16 + phase)), y))
        target.blit(self.vehicle, (171, round(378 + .5 * math.sin(seconds * 1.4))))

    def draw_tag(self, target, rect, text, font, fill, text_color=(65, 64, 55)):
        hover = rect.collidepoint(pygame.mouse.get_pos())
        if hover:
            fill = tuple(min(255, channel + 12) for channel in fill)
        y = rect.y - (2 if hover else 0)
        points = [(rect.x, y + 12), (rect.x + 18, y + 1), (rect.right - 5, y + 3),
                  (rect.right, y + rect.height - 8), (rect.right - 16, y + rect.height),
                  (rect.x + 7, y + rect.height - 3)]
        pygame.draw.polygon(target, (172, 169, 149), [(x + 2, py + 3) for x, py in points])
        pygame.draw.polygon(target, fill, points)
        pygame.draw.lines(target, (89, 91, 75), True, points, 2)
        pygame.draw.line(target, (248, 242, 220), (rect.x + 30, y + 7), (rect.right - 15, y + 8), 1)
        pygame.draw.circle(target, (65, 64, 55), (rect.x + 19, y + rect.height // 2), 4, 2)
        label = font.render(text, True, text_color)
        target.blit(label, label.get_rect(center=(rect.centerx + 8, y + rect.height // 2)))

    def draw_sheet(self, target, rect):
        pygame.draw.polygon(target, (116, 125, 94),
                            [(rect.x - 13, rect.y + 18), (rect.right + 8, rect.y - 9),
                             (rect.right + 19, rect.bottom + 15), (rect.x - 1, rect.bottom + 20)])
        corners = [(rect.x, rect.y + 4), (rect.right - 6, rect.y),
                   (rect.right, rect.bottom - 5), (rect.x + 4, rect.bottom)]
        pygame.draw.polygon(target, (248, 239, 205), corners)
        pygame.draw.lines(target, (65, 64, 55), True, corners, 3)
        for i in range(8):
            y = rect.y + 62 + i * 47
            if y < rect.bottom - 18:
                pygame.draw.line(target, (230, 221, 191), (rect.x + 25, y), (rect.right - 25, y), 1)
        clip = pygame.Rect(rect.centerx - 45, rect.y - 15, 90, 25)
        pygame.draw.rect(target, (194, 195, 158), clip, border_radius=5)
        pygame.draw.rect(target, (65, 64, 55), clip, 2, border_radius=5)
