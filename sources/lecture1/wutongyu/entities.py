from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class GameState(Enum):
    MENU = auto()
    MISSION_BRIEF = auto()
    GUIDE = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()


@dataclass
class Resource:
    kind: str
    x: int
    y: int


@dataclass
class Survivor:
    x: int
    y: int
    carried: bool = False


@dataclass
class SafeZone:
    x: int
    y: int


@dataclass
class DisasterEvent:
    kind: str
    duration: float
    text: str
    timer: float
