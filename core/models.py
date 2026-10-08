from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass(slots=True)
class Target:
    id: str = "current"
    x: float = 0.0
    y: float = 0.0
    hp_ratio: float = 1.0
    distance_px: float = 0.0
    selected: bool = False

@dataclass(slots=True)
class PlayerStatus:
    hp_ratio: float = 1.0
    mp_ratio: float = 1.0
    in_combat: bool = False
    dead: bool = False

@dataclass(slots=True)
class Perception:
    player: PlayerStatus
    target: Optional[Target] = None
    loot_available: bool = False
    unexpected_window: bool = False
    stuck: bool = False
