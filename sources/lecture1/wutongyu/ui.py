from pathlib import Path

import pygame

from config import FONT_CANDIDATES


def load_font(size: int, bold: bool = False) -> pygame.font.Font:
    for font_path in FONT_CANDIDATES:
        if Path(font_path).exists():
            try:
                return pygame.font.Font(font_path, size)
            except pygame.error:
                continue
    return pygame.font.SysFont("Arial", size, bold=bold)
