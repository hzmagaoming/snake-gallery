"""Cached, deterministic artwork for the playable map only."""

import math
import random
import warnings
from pathlib import Path

import pygame

from config import BOARD_SIZE, CELL_SIZE, SCENARIO_BACKGROUNDS, VISUAL


MAP_COLORS = {
    "paper": (231, 235, 218), "sky": (221, 231, 225),
    "distant": (204, 216, 203), "hill": (211, 222, 201),
    "meadow": (222, 229, 209), "bank": (215, 225, 214),
    "river": (202, 220, 220), "road": (233, 228, 211),
    "pencil": (192, 203, 185), "buildings": (215, 211, 197),
    "ink": VISUAL["colors"]["ink"], "rim": (237, 232, 211),
    "orange": VISUAL["colors"]["vehicle"], "gold": VISUAL["colors"]["supply_box"],
    "green": VISUAL["colors"]["tent"], "white": VISUAL["colors"]["medical"],
    "window": VISUAL["colors"]["window"], "red": VISUAL["colors"]["danger"],
    "skin": VISUAL["colors"]["survivor_skin"], "water": VISUAL["colors"]["water"],
}


def curve(points, steps=18):
    """Catmull-Rom samples give paths a continuous pencil-drawn silhouette."""
    extended = [points[0], *points, points[-1]]
    result = []
    for i in range(1, len(extended) - 2):
        a, b, c, d = extended[i - 1:i + 3]
        for j in range(steps):
            t = j / steps
            result.append(tuple(int(0.5 * ((2 * b[k]) + (-a[k] + c[k]) * t
                + (2 * a[k] - 5 * b[k] + 4 * c[k] - d[k]) * t * t
                + (-a[k] + 3 * b[k] - 3 * c[k] + d[k]) * t ** 3)) for k in (0, 1)))
    return [*result, points[-1]]


class MapArt:
    def __init__(self):
        self.backgrounds = {}
        self.materials = {}
        asset_dir = Path(__file__).resolve().parent / "assets" / "images"
        for theme, variants in SCENARIO_BACKGROUNDS.items():
            sheet = self.load_image(asset_dir / f"world_{theme}.png")
            if sheet is None:
                continue
            width, height = sheet.get_width() // 2, sheet.get_height() // 2
            for index, variant in enumerate(variants):
                tile = sheet.subsurface((index % 2 * width, index // 2 * height, width, height))
                background = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
                background.fill((*MAP_COLORS["paper"], 255))
                background.blit(pygame.transform.smoothscale(tile, background.get_size()), (0, 0))
                wash = pygame.Surface(background.get_size(), pygame.SRCALPHA)
                wash.fill((*MAP_COLORS["paper"], 100))
                background.blit(wash, (0, 0))
                self.backgrounds[(theme, variant)] = background
            self.materials[theme] = sheet.subsurface((width, height, width, height)).copy()
        self.paper_texture = self.materials.get("rain")
        if self.paper_texture is None:
            self.paper_texture = pygame.Surface((128, 128), pygame.SRCALPHA)
            self.paper_texture.fill((244, 239, 220, 255))
        self.visual_random = random.Random()
        self.select_background("rain")
        self.sprites = {kind: self.make_sprite(kind) for kind in
            ("rescue", "cargo", "transport", "logistics", "person", "tent",
             "supply", "medical", "battery", "eagle", "rubble")}
        atlas = self.load_image(asset_dir / "world_sprites.png")
        if atlas is not None:
            try:
                self.load_sprite_atlas(atlas)
            except ValueError as error:
                warnings.warn(f"Sprite atlas invalid; using drawn fallback: {error}", RuntimeWarning)
        self.transformed = {}
        self.ground_shadows = {}
        directions = ((1, 0), (0, -1), (-1, 0), (0, 1))
        for kind in ("rescue", "cargo", "transport", "logistics"):
            for direction in directions:
                self.cache_sprite(kind, VISUAL["sprite_size"]["rescue" if kind == "rescue" else "body"], direction)
        for kind in ("supply", "medical", "battery", "eagle", "person", "tent", "rubble"):
            size = VISUAL["sprite_size"].get(kind, VISUAL["sprite_size"]["resource"])
            self.cache_sprite(kind, size, None)
        self.water_layer = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
        self.water_cells = None

    @staticmethod
    def load_image(path):
        try:
            return pygame.image.load(str(path)).convert_alpha()
        except (OSError, pygame.error) as error:
            warnings.warn(f"Artwork unavailable; using drawn fallback: {path.name}: {error}", RuntimeWarning)
            return None

    def load_sprite_atlas(self, atlas):
        if atlas.get_at((0, 0)).a > 0:
            corner = atlas.get_at((0, 0))
            if corner.r < 180 or corner.g > 80 or corner.b < 180:
                raise ValueError("Sprite sheet needs transparent or magenta-keyed background")
            matte = pygame.mask.from_threshold(atlas, (255, 0, 255, 255), (125, 120, 125, 255))
            alpha = matte.to_surface(surface=pygame.Surface(atlas.get_size(), pygame.SRCALPHA),
                                    setcolor=(0, 0, 0, 0), unsetcolor=(255, 255, 255, 255))
            atlas.blit(alpha, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        kinds = ("rescue", "cargo", "transport", "logistics", "person", "tent",
                 "supply", "medical", "battery", "eagle", "rubble")
        width, height = atlas.get_width() // 4, atlas.get_height() // 3
        for index, kind in enumerate(kinds):
            tile = atlas.subsurface((index % 4 * width, index // 4 * height, width, height)).copy()
            components = pygame.mask.from_surface(tile, 30).connected_components(max(30, width * height // 650))
            valid = pygame.mask.Mask(tile.get_size())
            for component in components:
                valid.draw(component, (0, 0))
            alpha = valid.to_surface(surface=pygame.Surface(tile.get_size(), pygame.SRCALPHA),
                                    setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
            tile.blit(alpha, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            bounds = tile.get_bounding_rect(min_alpha=30)
            if not bounds.width or not bounds.height:
                raise ValueError(f"Empty sprite atlas cell: {kind}")
            sprite = pygame.Surface((108, 108), pygame.SRCALPHA)
            scale = min(92 / bounds.width, 92 / bounds.height)
            size = (max(1, round(bounds.width * scale)), max(1, round(bounds.height * scale)))
            image = pygame.transform.smoothscale(tile.subsurface(bounds), size)
            sprite.blit(image, image.get_rect(center=(54, 54)))
            self.sprites[kind] = sprite

    def select_background(self, theme):
        variant = self.visual_random.choice(SCENARIO_BACKGROUNDS[theme])
        key = (theme, variant)
        if key not in self.backgrounds:
            try:
                self.backgrounds[key] = self.make_background(theme, SCENARIO_BACKGROUNDS[theme].index(variant))
            except (pygame.error, ValueError) as error:
                warnings.warn(f"Map background unavailable; using paper fallback: {error}", RuntimeWarning)
                fallback = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
                fallback.fill((*MAP_COLORS["paper"], 255))
                self.backgrounds[key] = fallback
        self.background_variant = variant
        self.background = self.backgrounds[key]

    def make_background(self, theme="rain", variant=0):
        surface = pygame.Surface((600, 600), pygame.SRCALPHA)
        palettes = {
            "rain": ((220, 228, 223), (195, 210, 204), (213, 225, 209), (226, 230, 218), (203, 220, 221)),
            "earthquake": ((234, 228, 216), (211, 205, 192), (224, 218, 204), (236, 230, 217), (220, 218, 205)),
            "flood": ((220, 230, 230), (199, 212, 210), (218, 225, 219), (231, 232, 222), (201, 220, 223)),
        }
        sky, far, ground, road_color, water = palettes[theme]
        # Color offsets and composition are deterministic for each cached variant.
        tint = (0, 3, -2)[variant]
        surface.fill(tuple(max(0, min(255, channel + tint)) for channel in ground) + (255,))
        pygame.draw.rect(surface, sky, (0, 0, 600, 119))
        if theme == "rain":
            ridge = curve([(0, 109), (72, 49 + variant * 10), (161, 93),
                           (260, 38 + variant * 9), (385, 102), (488, 61), (600, 109)])
            pygame.draw.polygon(surface, far, [*ridge, (600, 167), (0, 167)])
            slope = curve([(0, 211), (106, 151), (229, 207), (374, 133 + variant * 15), (600, 231)])
            pygame.draw.polygon(surface, (207 + tint, 219 + tint, 201 + tint),
                                [*slope, (600, 375), (0, 408)])
            river_paths = [
                [(593, 92), (543, 200), (565, 308), (513, 424), (592, 602)],
                [(5, 139), (65, 235), (44, 350), (108, 475), (45, 603)],
                [(600, 194), (482, 239), (512, 358), (438, 464), (463, 600)],
            ]
            river = curve(river_paths[variant])
            pygame.draw.lines(surface, (211, 223, 217), False, river, 74)
            pygame.draw.lines(surface, water, False, river, 44)
            pygame.draw.lines(surface, (192, 211, 212), False, river, 1)
            path = curve([(-25, 545), (143, 437 - variant * 22), (265, 319),
                          (382, 327 + variant * 23), (481, 131)])
            pygame.draw.lines(surface, (211, 218, 206), False, path, 34)
            pygame.draw.lines(surface, road_color, False, path, 30)
            pygame.draw.lines(surface, (215, 223, 214), False, path, 4)
            for i in range(17):
                x, y = (i * 43 + variant * 21) % 600, 12 + (i * 31) % 89
                pygame.draw.line(surface, (208, 220, 215), (x, y), (x - 3, y + 9))
            # A pale fallen trunk and distant shelter are scenery, not task icons.
            px = (22, 535, 37)[variant]
            pygame.draw.lines(surface, (183, 199, 180), False, [(px, 566), (px + 35, 579), (px + 48, 572)], 4)
            pygame.draw.line(surface, (183, 199, 180), (px + 17, 573), (px + 22, 560), 2)
            pygame.draw.polygon(surface, (199, 216, 192), [(514, 118), (535, 89), (558, 118)])
        else:
            # A single low-contrast streetscape mass keeps buildings out of the task layer.
            shift = (-40, 30, -10)[variant]
            skyline = [(0, 136)]
            for i in range(9):
                x, height = i * 74 + shift, 38 + (i * 19 + variant * 11) % 43
                skyline.extend([(x, 126), (x, 126 - height), (x + 19, 118 - height),
                                (x + 48, 126 - height), (x + 48, 136)])
            skyline.extend([(600, 136), (600, 181), (0, 181)])
            pygame.draw.polygon(surface, far, skyline)
            for i in range(10):
                x = i * 62 + shift
                pygame.draw.line(surface, (211, 218, 211) if theme == "flood" else (222, 215, 201),
                                 (x + 16, 104), (x + 16, 126), 2)
            paths = [
                [(0, 507), (144, 458), (314, 337), (471, 286), (600, 198)],
                [(67, 600), (165, 418), (277, 315), (474, 282), (600, 299)],
                [(0, 283), (194, 309), (358, 425), (515, 439), (600, 508)],
            ]
            street = curve(paths[variant])
            pygame.draw.lines(surface, (211, 211, 198), False, street, 64)
            pygame.draw.lines(surface, road_color, False, street, 60)
            second = curve([(217 + variant * 36, 600), (268, 418), (319, 306), (362, 139)])
            pygame.draw.lines(surface, road_color, False, second, 34)
            if theme == "earthquake":
                for i in range(6):
                    x, y = street[12 + i * 8]
                    pygame.draw.lines(surface, (190, 183, 168), False,
                                      [(x - 8, y - 13), (x + 3, y - 4), (x - 2, y + 6), (x + 9, y + 16)], 1)
                for i in range(9):
                    x, y = 21 + i * 17, 570 + (i * 7 + variant * 3) % 18
                    pygame.draw.polygon(surface, (202, 195, 180), [(x, y), (x + 5, y - 7), (x + 12, y + 2)])
                pygame.draw.line(surface, (190, 186, 169), (525, 135), (525, 171), 2)
                pygame.draw.line(surface, (229, 216, 176), (481, 153), (565, 161), 4)
                pygame.draw.line(surface, (194, 190, 175), (43, 152), (43, 199), 2)
                pygame.draw.polygon(surface, (230, 221, 186), [(37, 155), (49, 155), (54, 169), (32, 169)])
            else:
                waterways = [
                    [(591, 145), (532, 281), (566, 421), (522, 600)],
                    [(0, 514), (183, 551), (359, 518), (600, 571)],
                    [(16, 167), (54, 311), (25, 459), (85, 600)],
                ]
                channel = curve(waterways[variant])
                pygame.draw.lines(surface, water, False, channel, 92)
                pygame.draw.lines(surface, (210, 227, 226), False, channel, 2)
                for i in range(8):
                    x, y = channel[min(len(channel) - 1, 8 + i * 5)]
                    pygame.draw.arc(surface, (218, 231, 228), (x - 19, y - 4, 38, 9), 0.1, 2.9, 1)
                px, py = ((552, 540), (529, 564), (51, 527))[variant]
                pygame.draw.polygon(surface, (183, 204, 202),
                                    [(px - 22, py), (px + 24, py), (px + 12, py + 10), (px - 13, py + 10)])
                for i in range(4):
                    pygame.draw.ellipse(surface, (210, 213, 192), (px - 24 + i * 12, py + 20, 16, 8))
                pygame.draw.line(surface, (187, 204, 197), (550, 152), (550, 194), 2)
                pygame.draw.polygon(surface, (205, 218, 211), [(537, 151), (566, 152), (562, 164), (537, 164)])
        for i in range(70):
            x, y = (i * 137 + variant * 23) % 600, (i * 79 + 19) % 600
            pygame.draw.line(surface, tuple(min(255, ch + 3) for ch in ground), (x, y), (x + 3, y + 1))
        grid = pygame.Surface((600, 600), pygame.SRCALPHA)
        for pos in range(0, 600, CELL_SIZE):
            pygame.draw.line(grid, (126, 143, 121, 6), (pos, 140), (pos, 600))
            if pos > 140:
                pygame.draw.line(grid, (126, 143, 121, 6), (0, pos), (600, pos))
        surface.blit(grid, (0, 0))
        if surface.get_size() != (BOARD_SIZE, BOARD_SIZE):
            surface = pygame.transform.smoothscale(surface, (BOARD_SIZE, BOARD_SIZE))
        return surface.convert_alpha()

    def make_sprite(self, kind):
        surface = pygame.Surface((96, 96), pygame.SRCALPHA)
        c = MAP_COLORS

        def shape(points, fill, width=5):
            pygame.draw.polygon(surface, fill, points)
            pygame.draw.lines(surface, c["ink"], True, points, width)

        def line(points, color=None, width=5):
            pygame.draw.lines(surface, color or c["ink"], False, points, width)

        def cross(x, y, color, size=10):
            line([(x - size, y), (x + size, y)], color, 6)
            line([(x, y - size), (x, y + size)], color, 6)

        if kind in ("rescue", "cargo", "transport", "logistics"):
            for x in (26, 69):
                pygame.draw.rect(surface, c["ink"], (x - 6, 17, 13, 15), border_radius=4)
                pygame.draw.rect(surface, c["ink"], (x - 6, 64, 13, 15), border_radius=4)
            fill = c["orange"] if kind == "rescue" else c["gold"]
            shape([(14, 31), (20, 26), (67, 27), (83, 37), (83, 60), (72, 70), (19, 69), (13, 61)], fill)
            shape([(57, 32), (68, 32), (76, 38), (76, 58), (67, 64), (57, 63)], c["window"], 4)
            line([(63, 36), (63, 59)], (179, 219, 216), 3)
            if kind == "rescue":
                shape([(20, 34), (48, 35), (48, 61), (21, 62)], c["white"], 3)
                cross(34, 48, c["red"], 8)
                pygame.draw.rect(surface, c["red"], (50, 32, 7, 14), border_radius=2)
                pygame.draw.rect(surface, c["window"], (50, 49, 7, 14), border_radius=2)
                line([(83, 40), (83, 55)], c["white"], 4)
            elif kind == "transport":
                for y in (37, 54):
                    shape([(22, y), (46, y), (46, y + 8), (22, y + 8)], c["window"], 3)
            elif kind == "cargo":
                shape([(21, 34), (46, 36), (46, 62), (21, 62)], (210, 133, 41), 3)
                line([(32, 36), (32, 61)], c["white"], 5)
            else:
                cross(34, 48, c["white"], 8)
        elif kind == "person":
            line([(39, 64), (35, 81)], width=7)
            line([(53, 64), (59, 80)], width=7)
            line([(32, 47), (20, 58)], width=7)
            line([(59, 47), (69, 31)], width=7)
            shape([(32, 40), (56, 40), (61, 65), (30, 66)], c["orange"], 5)
            pygame.draw.circle(surface, c["skin"], (44, 26), 14)
            pygame.draw.circle(surface, c["ink"], (44, 26), 14, 4)
            line([(32, 21), (37, 13), (49, 13), (56, 19)], width=5)
            for x in (40, 49):
                pygame.draw.circle(surface, c["ink"], (x, 27), 2)
            shape([(69, 9), (89, 9), (89, 29), (75, 29), (69, 35)], c["gold"], 3)
            line([(79, 14), (79, 21)], c["red"], 4)
            pygame.draw.circle(surface, c["red"], (79, 25), 2)
        elif kind == "tent":
            shape([(10, 74), (34, 28), (60, 26), (86, 73)], c["green"])
            shape([(10, 74), (34, 28), (56, 73)], (87, 188, 107))
            shape([(25, 73), (34, 48), (44, 73)], (37, 103, 66), 3)
            line([(60, 29), (73, 65)], (181, 227, 161), 3)
            line([(68, 30), (68, 7)], width=4)
            shape([(69, 7), (88, 12), (69, 21)], c["green"], 3)
            cross(69, 14, c["white"], 3)
        elif kind in ("supply", "medical", "battery"):
            fill = {"supply": c["gold"], "medical": c["white"], "battery": c["window"]}[kind]
            shape([(18, 30), (67, 27), (79, 40), (77, 73), (19, 75)], fill)
            if kind == "supply":
                shape([(18, 30), (61, 20), (78, 34), (67, 44)], (255, 201, 93), 4)
                line([(45, 25), (49, 40), (49, 72)], c["white"], 8)
                cross(31, 55, (155, 94, 34), 6)
            elif kind == "medical":
                line([(33, 28), (34, 18), (58, 18), (60, 28)], width=5)
                cross(47, 52, c["red"], 13)
            else:
                shape([(79, 43), (87, 43), (87, 60), (79, 60)], c["ink"], 2)
                shape([(49, 36), (36, 54), (48, 54), (42, 68), (61, 47), (49, 47)], c["white"], 2)
        elif kind == "eagle":
            shape([(48, 8), (78, 23), (86, 54), (69, 79), (47, 87), (18, 69), (9, 43), (26, 17)], c["gold"])
            shape([(16, 36), (40, 42), (48, 30), (56, 42), (80, 33), (68, 59), (55, 59), (48, 73), (40, 59), (28, 60)], c["white"], 3)
            pygame.draw.circle(surface, c["ink"], (50, 40), 3)
        elif kind == "rubble":
            shape([(11, 73), (19, 48), (39, 37), (50, 56), (69, 47), (84, 71), (77, 81), (24, 81)], (151, 133, 117))
            line([(22, 55), (36, 52), (42, 68), (60, 61), (75, 72)], (109, 95, 84), 4)
            line([(22, 45), (17, 76)], width=5)
            line([(75, 37), (78, 73)], width=5)
            shape([(13, 30), (80, 24), (82, 43), (14, 49)], c["orange"], 4)
            for x in (25, 47, 68):
                line([(x, 31), (x + 7, 42)], c["white"], 5)
        # Consistent pale outer stroke and a soft southeast shadow, derived from silhouette.
        mask = pygame.mask.from_surface(surface)
        silhouette = mask.to_surface(surface=pygame.Surface((96, 96), pygame.SRCALPHA),
                                     setcolor=(*c["rim"], 255), unsetcolor=(0, 0, 0, 0))
        shadow = mask.to_surface(surface=pygame.Surface((96, 96), pygame.SRCALPHA),
                                setcolor=(72, 70, 54, 48), unsetcolor=(0, 0, 0, 0))
        result = pygame.Surface((108, 108), pygame.SRCALPHA)
        result.blit(shadow, (9, 11))
        for dx, dy in ((-4, 0), (4, 0), (0, -4), (0, 4), (-3, -3), (3, 3)):
            result.blit(silhouette, (6 + dx, 6 + dy))
        result.blit(surface, (6, 6))
        return result

    def cache_sprite(self, kind, size, direction):
        shadow_key = (kind, size)
        if shadow_key not in self.ground_shadows:
            shadow = pygame.Surface((size + 8, size + 8), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (54, 57, 45, 64),
                                (round(size * .18) + 3, round(size * .74) + 3, round(size * .68), 4))
            self.ground_shadows[shadow_key] = shadow
        key = (kind, size, direction)
        if key not in self.transformed:
            image = self.sprites[kind]
            if direction is not None:
                angle = {(1, 0): 0, (0, -1): 90, (-1, 0): 180, (0, 1): -90}[direction]
                image = pygame.transform.rotate(image, angle)
            self.transformed[key] = pygame.transform.smoothscale(image, (size, size))
            outline = pygame.mask.from_surface(self.transformed[key], 110).outline()
            if len(outline) > 2:
                pygame.draw.lines(self.transformed[key], (*MAP_COLORS["ink"], 200), True, outline, 1)

    def sprite(self, target, kind, center, size=None, direction=None):
        if size is None:
            size = VISUAL["sprite_size"].get(kind, VISUAL["sprite_size"]["body"]
                if kind in ("cargo", "transport", "logistics") else VISUAL["sprite_size"]["resource"])
        target.blit(self.ground_shadows[(kind, size)], (round(center[0] - size // 2), round(center[1] - size // 2)))
        target.blit(self.transformed[(kind, size, direction)], (round(center[0] - size // 2), round(center[1] - size // 2)))

    def water(self, target, cells, origin):
        occupied = frozenset(cells)
        if occupied == self.water_cells:
            if occupied:
                target.blit(self.water_layer, origin)
            return
        self.water_cells = occupied
        c = MAP_COLORS
        layer = self.water_layer
        layer.fill((0, 0, 0, 0))
        for x, y in occupied:
            px, py = x * CELL_SIZE, y * CELL_SIZE
            color = (*c["water"], 195)
            pygame.draw.rect(layer, color, (px, py, CELL_SIZE, CELL_SIZE), border_radius=7)
            if (x + 1, y) in occupied:
                pygame.draw.rect(layer, color, (px + CELL_SIZE - 7, py + 4, 14, CELL_SIZE - 8))
            if (x, y + 1) in occupied:
                pygame.draw.rect(layer, color, (px + 4, py + CELL_SIZE - 7, CELL_SIZE - 8, 14))
            if {(x + 1, y), (x, y + 1), (x + 1, y + 1)} <= occupied:
                pygame.draw.rect(layer, color, (px + CELL_SIZE - 7, py + CELL_SIZE - 7, 14, 14))
            for dx, dy, a in ((0, -1, (px, py)),
                              (0, 1, (px, py + CELL_SIZE - 1)),
                              (-1, 0, (px, py)),
                              (1, 0, (px + CELL_SIZE - 1, py))):
                if (x + dx, y + dy) not in occupied:
                    horizontal = dy != 0
                    edge = []
                    for i in range(CELL_SIZE + 1):
                        ripple = int(1.5 * math.sin(((px if horizontal else py) + i) / 5))
                        edge.append((a[0] + i, a[1] + ripple) if horizontal
                                    else (a[0] + ripple, a[1] + i))
                    pygame.draw.lines(layer, (62, 118, 139, 230), False, edge, 2)
            for offset in (9, 22):
                wave = [(px + i, py + offset + int(2 * math.sin((px + i) / 7))) for i in range(4, CELL_SIZE - 3)]
                pygame.draw.lines(layer, (222, 239, 224, 210), False, wave, 2)
        target.blit(layer, origin)
